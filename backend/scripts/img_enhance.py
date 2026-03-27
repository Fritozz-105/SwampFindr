import numpy as np

import requests
from PIL import Image
from io import BytesIO
from pathlib import Path
import base64
from datetime import datetime, timezone
import argparse
import sys
import os

import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter


def blur_url(url: str):
    """
    Apply the guassian blur filter & increase resolution

    Args:
        url: Direct URL to the image.

    Returns:
        blurred image
    """
    return optimize_img(download_image_as_array(url))


def download_image_as_array(url: str, save_path: str = 'save.jpg', mode: str = "RGB",) -> np.ndarray:
    """
    Download an image from a URL and return it as a numpy array.

    Args:
        url:       Direct URL to the image.
        save_path: File path to save the image (e.g. "img.png").
        mode:      PIL colour mode — "RGB", "RGBA", "L" (grayscale), etc.

    Returns:
        numpy array of shape (H, W, C) for RGB/RGBA or (H, W) for grayscale.
        dtype is uint8, values in [0, 255].

    Raises:
        requests.HTTPError: if the download fails.
        ValueError:         if the response is not a valid image.
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()

    try:
        img = Image.open(BytesIO(response.content)).convert(mode)
    except Exception as exc:
        raise ValueError(f"Could not decode image from {url!r}: {exc}") from exc

    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(save_path)
    print(f"Saved → {save_path}")

    arr = np.array(img)
    print(f"Array shape: {arr.shape}  dtype: {arr.dtype}")
    return arr


def optimize_img(img, res_increase: int = 4):
    """
    Blur the image to aesthetically hide grainy features. This is done via a guassian filter.

    Args:
        img: The image to be blurred.
        res_increase: the multiplicative increase of the # of pixels

    Returns:
        blurred_img: The blurred image
    """
    mult = int(res_increase ** 0.5)

    high_res = np.zeros((img.shape[0] * mult, img.shape[1] * mult, 3), dtype=np.float64)

    for i in range(img.shape[0]):
        for j in range(img.shape[1]):
            high_res[i * mult:(i + 1) * mult, j * mult:(j + 1) * mult] = img[i, j]

    blurred_img = gaussian_filter(high_res, sigma=1.2)
    return np.clip(blurred_img, 0, 255).astype(np.uint8)


def array_to_jpeg_bytes(img: np.ndarray, quality: int = 90) -> bytes:
    pil_img = Image.fromarray(img.astype(np.uint8))
    buff = BytesIO()
    pil_img.save(buff, format="JPEG", quality=quality)
    return buff.getvalue()


def upload_cleaned_image_default(img: np.ndarray) -> str:
    """
    Default "upload back" implementation:
    store as base64 data URI string directly in Mongo listing doc.

    Replace this function if you want real CDN/S3 upload and return hosted URL.
    """
    encoded = base64.b64encode(array_to_jpeg_bytes(img)).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def get_listings_collection():
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from app.database.mongo import get_listings_collection as _get_listings_collection

    return _get_listings_collection()


def process_listings_images(
    listing_id: str | None = None,
    limit: int = 0,
    upload_fn=upload_cleaned_image_default,
):
    """
    Pipeline:
    1) Pull listings from Mongo
    2) Download each image
    3) Clean via optimize_img (numpy)
    4) Upload cleaned image (upload_fn)
    5) Write cleaned_photos back to listing
       Fallback: if any image fails, keep original URL for that image
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

        for idx, url in enumerate(photos):
            try:
                arr = download_image_as_array(url, save_path=f"tmp/original_{lid}_{idx}.jpg")
                cleaned = optimize_img(arr)
                uploaded = upload_fn(cleaned)
                cleaned_photos.append(uploaded)
                processed_images += 1
            except Exception as exc:
                print(f"[WARN] {lid} photo#{idx} failed: {exc}")
                cleaned_photos.append(url)  # Fallback to original URL
                failed_images += 1

        listings_collection.update_one(
            {"_id": listing["_id"]},
            {"$set": {
                "cleaned_photos": cleaned_photos,
                "image_cleanup_meta": {
                    "updated_at": datetime.now(timezone.utc),
                    "total_images": len(photos),
                    "failed_images": sum(1 for i, p in enumerate(cleaned_photos) if i < len(photos) and p == photos[i]),
                },
            }},
        )
        processed_listings += 1
        print(f"[OK] Updated listing {lid} ({len(photos)} images)")

    summary = {
        "processed_listings": processed_listings,
        "processed_images": processed_images,
        "failed_images": failed_images,
    }
    print(summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description="Clean listing images and upload cleaned URLs back to Mongo.")
    parser.add_argument("--listing-id", type=str, default=None, help="Only process one listing_id")
    parser.add_argument("--limit", type=int, default=0, help="Process first N listings (0 = no limit)")
    args = parser.parse_args()

    process_listings_images(listing_id=args.listing_id, limit=args.limit)


if __name__ == "__main__":
    main()
