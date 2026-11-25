"""Read text out of a screenshot (OCR = Optical Character Recognition).

Uses Tesseract, a free open-source OCR engine, with English + Hindi models.
Install on Ubuntu/Debian:  sudo apt install tesseract-ocr tesseract-ocr-hin
Install on Windows/Mac: see https://github.com/tesseract-ocr/tesseract

The image is processed in memory and never saved. We talk to the tesseract
program through a pipe (``tesseract stdin stdout``) instead of the pytesseract
library, because pytesseract writes the picture AND the text it reads to
temporary files on disk, which would break the privacy promise.

Safety limits, because a screenshot comes from a stranger:
  * at most 6 MB and 4000 x 4000 pixels (16 million) before decoding;
  * only PNG, JPEG and WebP are decoded (Pillow can read many old, rarely used
    formats; we don't need them, so we don't expose their decoders);
  * enlarging small images never goes over the same pixel limit (a 2-pixel-wide
    picture must not become a 4,000,000,000-pixel one);
  * Tesseract is stopped after ``TIMEOUT_SECONDS``.
"""

from __future__ import annotations

import io
import math
import shutil
import subprocess

MAX_BYTES = 6 * 1024 * 1024  # 6 MB
MAX_PIXELS = 4000 * 4000
TIMEOUT_SECONDS = 60  # a phone screenshot takes about 1 s on a laptop; slow free hosts need more
ALLOWED_FORMATS = ("PNG", "JPEG", "WEBP")
_TARGET_WIDTH = 1000  # small screenshots are enlarged to about this width


class OcrUnavailable(RuntimeError):
    pass


def ocr_available() -> bool:
    try:
        import PIL  # noqa: F401
    except ImportError:
        return False
    return shutil.which("tesseract") is not None


def _prepare(image_bytes: bytes):
    """Decode, check and clean up the image. Raises ValueError if it is too big."""
    from PIL import Image, ImageOps

    Image.MAX_IMAGE_PIXELS = MAX_PIXELS  # protects against "decompression bomb" images
    img = Image.open(io.BytesIO(image_bytes), formats=ALLOWED_FORMATS)
    # Pillow only warns (does not refuse) between 1x and 2x MAX_IMAGE_PIXELS,
    # so check the size ourselves before decoding the pixels.
    if img.width * img.height > MAX_PIXELS:
        raise ValueError("Image is too large (max 4000 x 4000 pixels).")
    img = ImageOps.exif_transpose(img)  # fix photos taken sideways
    img = img.convert("L")  # greyscale helps OCR
    # Small screenshots: enlarge so letters are big enough for Tesseract, but
    # never beyond MAX_PIXELS in total.
    if img.width < _TARGET_WIDTH:
        scale = min(_TARGET_WIDTH / img.width, math.sqrt(MAX_PIXELS / (img.width * img.height)))
        if scale > 1:
            img = img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))))
    return img


def extract_text(image_bytes: bytes, langs: str = "eng+hin") -> str:
    """Return the text found in an image (PNG/JPEG/WebP)."""
    if not ocr_available():
        raise OcrUnavailable("Tesseract OCR is not installed on this server.")
    if len(image_bytes) > MAX_BYTES:
        raise ValueError("Image is too large (max 6 MB).")

    img = _prepare(image_bytes)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    del img
    try:
        proc = subprocess.run(
            ["tesseract", "stdin", "stdout", "-l", langs, "--psm", "6"],
            input=buf.getvalue(),
            capture_output=True,
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("Tesseract took too long.") from None
    if proc.returncode != 0:
        # stderr can quote parts of the image's text, so don't pass it on.
        raise RuntimeError(f"Tesseract failed (exit code {proc.returncode}).")
    return " ".join(proc.stdout.decode("utf-8", errors="replace").split())
