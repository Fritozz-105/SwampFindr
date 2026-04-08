"""Image enhancement pipeline using Stable Diffusion x4 upscaler.

SD upscaler generates plausible detail from very low-res sources (120x80),
unlike traditional upscalers that just sharpen existing pixels.

Usage:
    uv run --extra enhance python scripts/img_enhance.py --limit 5
    uv run --extra enhance python scripts/img_enhance.py --listing-id <id>
"""
import base64
import logging
import argparse
import sys
import os
from datetime import datetime, timezone
from io import BytesIO

import requests
from PIL import Image

logger = logging.getLogger(__name__)

# Lazy-loaded singleton
_pipeline = None


def _get_device() -> str:
    """Auto-detect best available torch device."""
    import torch

    if torch.cuda.is_available():
        return "cuda"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def _get_pipeline():
    """Lazy-load the Stable Diffusion x4 upscaler pipeline (singleton)."""
    global _pipeline
    if _pipeline is not None:
        return _pipeline

    import torch
    from diffusers import StableDiffusionUpscalePipeline

    device = _get_device()
    dtype = torch.float16 if device != "cpu" else torch.float32

    logger.info("Loading SD x4 upscaler on %s (dtype=%s)...", device, dtype)
    _pipeline = StableDiffusionUpscalePipeline.from_pretrained(
        "stabilityai/stable-diffusion-x4-upscaler",
        torch_dtype=dtype,
    )
    _pipeline = _pipeline.to(device)
    _pipeline.set_progress_bar_config(disable=True)
    logger.info("SD x4 upscaler loaded.")
    return _pipeline


def download_image(url: str) -> Image.Image:
    """Download an image from a URL and return as a PIL Image."""
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    try:
        return Image.open(BytesIO(response.content)).convert("RGB")
    except Exception as exc:
        raise ValueError(f"Could not decode image from {url!r}: {exc}") from exc


def _upscale_tiled(
    img: Image.Image,
    pipe,
    prompt: str,
    tile_size: int = 128,
    overlap: int = 16,
) -> Image.Image:
    """Upscale 4x by processing overlapping tiles to stay within VRAM limits.

    Each tile is tile_size x tile_size pixels from the input, producing a
    (tile_size*4) x (tile_size*4) output tile. Overlapping regions are
    blended with a linear gradient to avoid visible seams.
    """
    import numpy as np

    w, h = img.size
    out_scale = 4
    out_w, out_h = w * out_scale, h * out_scale
    output = np.zeros((out_h, out_w, 3), dtype=np.float64)
    weights = np.zeros((out_h, out_w, 1), dtype=np.float64)

    step = tile_size - overlap
    tiles_x = max(1, (w - overlap + step - 1) // step)
    tiles_y = max(1, (h - overlap + step - 1) // step)
    total = tiles_x * tiles_y
    count = 0

    for ty in range(tiles_y):
        for tx in range(tiles_x):
            # Input tile coordinates (clamped to image bounds)
            x1 = min(tx * step, max(0, w - tile_size))
            y1 = min(ty * step, max(0, h - tile_size))
            x2 = min(x1 + tile_size, w)
            y2 = min(y1 + tile_size, h)

            tile = img.crop((x1, y1, x2, y2))
            result = pipe(prompt=prompt, image=tile)
            tile_out = np.array(result.images[0], dtype=np.float64)

            # Output tile coordinates
            ox1, oy1 = x1 * out_scale, y1 * out_scale
            th, tw = tile_out.shape[:2]

            # Build a blend weight mask (feather edges in overlap region)
            mask = np.ones((th, tw, 1), dtype=np.float64)
            feather = overlap * out_scale
            if feather > 0:
                for i in range(min(feather, th)):
                    mask[i, :, :] *= i / feather
                    mask[th - 1 - i, :, :] *= i / feather
                for j in range(min(feather, tw)):
                    mask[:, j, :] *= j / feather
                    mask[:, tw - 1 - j, :] *= j / feather

            output[oy1:oy1 + th, ox1:ox1 + tw] += tile_out * mask
            weights[oy1:oy1 + th, ox1:ox1 + tw] += mask

            count += 1
            logger.info("  tile %d/%d", count, total)

    # Normalize by weight and convert back
    weights = np.maximum(weights, 1e-8)
    final = np.clip(output / weights, 0, 255).astype(np.uint8)
    return Image.fromarray(final)


def upscale_image(
    img: Image.Image,
    passes: int = 2,
    prompt: str = "a high quality photo of an apartment building exterior",
    tile_size: int = 128,
    overlap: int = 16,
) -> Image.Image:
    """Upscale a low-res PIL Image using the SD x4 upscaler with tiling.

    Each pass does 4x using tiled processing to stay within VRAM.
    passes=2 on a 120x80 source gives 1920x1280 (16x total).
    """
    pipe = _get_pipeline()
    current = img
    for i in range(passes):
        current = _upscale_tiled(current, pipe, prompt, tile_size, overlap)
        logger.info("  pass %d/%d complete: %dx%d", i + 1, passes,
                    current.width, current.height)
    return current


def image_to_jpeg_bytes(img: Image.Image, quality: int = 90) -> bytes:
    buff = BytesIO()
    img.save(buff, format="JPEG", quality=quality)
    return buff.getvalue()


def upload_cleaned_image_default(img: Image.Image) -> str:
    """Store as base64 data URI in Mongo. Replace with CDN/S3 upload for production."""
    encoded = base64.b64encode(image_to_jpeg_bytes(img)).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def get_listings_collection():
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from app.database.mongo import get_listings_collection as _get_listings_collection

    return _get_listings_collection()


def process_listings_images(
    listing_id: str | None = None,
    limit: int = 0,
    passes: int = 2,
    upload_fn=upload_cleaned_image_default,
):
    """
    Pipeline:
    1) Pull listings from Mongo
    2) Download each image
    3) Upscale via SD x4 upscaler
    4) Upload cleaned image (upload_fn)
    5) Write cleaned_photos back to listing ONLY if at least one image succeeded
       Failed images are skipped entirely (not written to cleaned_photos)
    """
    listings_collection = get_listings_collection()

    query = {"listing_id": listing_id} if listing_id else {}
    cursor = listings_collection.find(query, {"listing_id": 1, "photos": 1})
    if limit and limit > 0:
        cursor = cursor.limit(limit)

    processed_listings = 0
    processed_images = 0
    failed_images = 0

    for listing in cursor:
        lid = listing.get("listing_id")
        photos = listing.get("photos", []) or []
        cleaned_photos = []
        listing_failures = 0

        for idx, url in enumerate(photos):
            try:
                img = download_image(url)
                upscaled = upscale_image(img, passes=passes)
                uploaded = upload_fn(upscaled)
                cleaned_photos.append(uploaded)
                processed_images += 1
                logger.info("[OK] %s photo#%d upscaled (%dx%d -> %dx%d)",
                            lid, idx, img.width, img.height,
                            upscaled.width, upscaled.height)
            except Exception as exc:
                logger.warning("[WARN] %s photo#%d failed: %s", lid, idx, exc)
                listing_failures += 1
                failed_images += 1

        # Only update Mongo if at least one image was successfully enhanced
        if not cleaned_photos:
            print(f"[SKIP] Listing {lid}: all {len(photos)} images failed, not updating")
            continue

        listings_collection.update_one(
            {"_id": listing["_id"]},
            {"$set": {
                "cleaned_photos": cleaned_photos,
                "image_cleanup_meta": {
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "total_images": len(photos),
                    "enhanced_images": len(cleaned_photos),
                    "failed_images": listing_failures,
                },
            }},
        )
        processed_listings += 1
        print(f"[OK] Updated listing {lid} ({len(cleaned_photos)}/{len(photos)} images enhanced)")

    summary = {
        "processed_listings": processed_listings,
        "processed_images": processed_images,
        "failed_images": failed_images,
    }
    print(summary)
    return summary


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    parser = argparse.ArgumentParser(
        description="Upscale listing images using SD x4 and write cleaned_photos to Mongo."
    )
    parser.add_argument("--listing-id", type=str, default=None, help="Only process one listing_id")
    parser.add_argument("--limit", type=int, default=0, help="Process first N listings (0 = no limit)")
    parser.add_argument("--passes", type=int, default=2, help="Number of 4x upscale passes (default 2 = 16x)")
    args = parser.parse_args()

    process_listings_images(listing_id=args.listing_id, limit=args.limit, passes=args.passes)


if __name__ == "__main__":
    main()
