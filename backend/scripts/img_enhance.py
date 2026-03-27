import numpy as np

import requests
from PIL import Image
from io import BytesIO
from pathlib import Path

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