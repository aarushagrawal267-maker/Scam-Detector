"""Read text out of a screenshot (OCR = Optical Character Recognition).

Uses Tesseract, a free open-source OCR engine, with English + Hindi models.
Install on Ubuntu/Debian:  sudo apt install tesseract-ocr tesseract-ocr-hin
Install on Windows/Mac: see https://github.com/tesseract-ocr/tesseract

The image is processed in memory and never saved.
"""

from __future__ import annotations

import io
import shutil

MAX_BYTES = 6 * 1024 * 1024  # 6 MB
MAX_PIXELS = 4000 * 4000


class OcrUnavailable(RuntimeError):
    pass


def ocr_available() -> bool:
    try:
        import PIL  # noqa: F401
        import pytesseract  # noqa: F401
    except ImportError:
        return False
    return shutil.which("tesseract") is not None


def extract_text(image_bytes: bytes, langs: str = "eng+hin") -> str:
    """Return the text found in an image (PNG/JPEG/WebP)."""
    if not ocr_available():
        raise OcrUnavailable("Tesseract OCR is not installed on this server.")
    if len(image_bytes) > MAX_BYTES:
        raise ValueError("Image is too large (max 6 MB).")

    import pytesseract
    from PIL import Image, ImageOps

    Image.MAX_IMAGE_PIXELS = MAX_PIXELS  # protects against "decompression bomb" images
    img = Image.open(io.BytesIO(image_bytes))
    # Pillow only warns (does not refuse) between 1x and 2x MAX_IMAGE_PIXELS,
    # so check the size ourselves before decoding the pixels.
    if img.width * img.height > MAX_PIXELS:
        raise ValueError("Image is too large (max 4000 x 4000 pixels).")
    img = ImageOps.exif_transpose(img)  # fix photos taken sideways
    img = img.convert("L")  # greyscale helps OCR
    # Small screenshots: enlarge so letters are big enough for Tesseract.
    if img.width < 1000:
        scale = 1000 / img.width
        img = img.resize((int(img.width * scale), int(img.height * scale)))
    text = pytesseract.image_to_string(img, lang=langs, config="--psm 6")
    return " ".join(text.split())
