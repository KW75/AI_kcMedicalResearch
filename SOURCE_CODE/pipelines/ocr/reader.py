"""OCR input reader.

Turns one file from input/ocr/ into a list of pages for the OCR pipeline.
Each page is {"page": n, "text": str | None, "png": bytes | None}; exactly
one of text/png is set:
- PDF page with a text layer (>= MIN_TEXT_CHARS characters): text, no AI.
- PDF page without text (scan, blank, page number only): PNG for the model.
- Image file (any supported format): converted to PNG. A multi-page TIFF
  gives one page per frame.
Uses pymupdf (fitz) and pillow, both in requirements-local.txt.
"""
from __future__ import annotations

import io
from pathlib import Path

import fitz
from PIL import Image, ImageSequence

PDF_EXTS = {".pdf"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".gif", ".webp"}
SUPPORTED_EXTS = PDF_EXTS | IMAGE_EXTS
MIN_TEXT_CHARS = 20
PDF_RENDER_DPI = 200


def list_inputs(folder) -> list[Path]:
    """Supported files in `folder`, sorted by name (case-insensitive)."""
    folder = Path(folder)
    if not folder.is_dir():
        return []
    files = [p for p in folder.iterdir()
             if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS]
    return sorted(files, key=lambda p: p.name.lower())


def read_input(path) -> list[dict]:
    """Pages of one input file. Raises ValueError for unsupported types."""
    path = Path(path)
    ext = path.suffix.lower()
    if ext in PDF_EXTS:
        return _read_pdf(path)
    if ext in IMAGE_EXTS:
        return _read_image(path)
    raise ValueError(f"Unsupported file type for OCR: {path.name}")


def _page(number: int, text: str | None = None, png: bytes | None = None) -> dict:
    return {"page": number, "text": text, "png": png}


def _read_pdf(path: Path) -> list[dict]:
    pages = []
    with fitz.open(str(path)) as doc:
        for number, page in enumerate(doc, start=1):
            text = page.get_text().strip()
            if len(text) >= MIN_TEXT_CHARS:
                pages.append(_page(number, text=text))
            else:
                pix = page.get_pixmap(dpi=PDF_RENDER_DPI)
                pages.append(_page(number, png=pix.tobytes("png")))
    return pages


def _read_image(path: Path) -> list[dict]:
    pages = []
    with Image.open(path) as img:
        for number, frame in enumerate(ImageSequence.Iterator(img), start=1):
            pages.append(_page(number, png=_to_png(frame)))
    return pages


def _to_png(frame: Image.Image) -> bytes:
    buf = io.BytesIO()
    frame.convert("RGB").save(buf, format="PNG")
    return buf.getvalue()
