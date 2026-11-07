"""OCR input reader.

Turns one file from input/ocr/ into a list of pages for the OCR pipeline.
Each page is {"page": n, "text": str | None, "png": bytes | None}; exactly
one of text/png is set:
- PDF page with a text layer (>= MIN_TEXT_CHARS characters): text, no AI.
- PDF page without text (scan, blank, page number only): PNG for the model.
- Image file (any supported format): converted to PNG. A multi-page TIFF
  gives one page per frame.
- .txt and .docx: one text page, no AI. .docx reads paragraphs and tables
  in document order (a row becomes "cell | cell"; a merged cell appears once).
- .doc (old Word): refused with "save it as .docx" (no reliable reader yet).
A file with no text raises ValueError, so the engine lists it as failed.
Uses pymupdf (fitz), pillow and python-docx, all in requirements-local.txt.
"""
from __future__ import annotations

import io
from pathlib import Path

import docx
import fitz
from docx.table import Table
from docx.text.paragraph import Paragraph
from PIL import Image, ImageSequence

PDF_EXTS = {".pdf"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".gif", ".webp"}
TEXT_EXTS = {".txt"}
DOCX_EXTS = {".docx"}
DOC_EXTS = {".doc"}
SUPPORTED_EXTS = PDF_EXTS | IMAGE_EXTS | TEXT_EXTS | DOCX_EXTS | DOC_EXTS
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
    if ext in TEXT_EXTS:
        return _read_txt(path)
    if ext in DOCX_EXTS:
        return _read_docx(path)
    if ext in DOC_EXTS:
        raise ValueError("old Word .doc files cannot be read yet - "
                         "open it in Word and save it as .docx")
    raise ValueError(f"Unsupported file type for OCR: {path.name}")


def _text_page(path: Path, text: str) -> list[dict]:
    """One text page; ValueError if the file holds no text."""
    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        raise ValueError("no text found in the file")
    return [_page(1, text=text)]


def _read_txt(path: Path) -> list[dict]:
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8-sig")          # UTF-8, with or without BOM
    except UnicodeDecodeError:
        text = raw.decode("cp1252", errors="replace")  # older Windows "ANSI"
    return _text_page(path, text)


def _read_docx(path: Path) -> list[dict]:
    document = docx.Document(str(path))
    lines = []
    for child in document.element.body.iterchildren():
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "p":
            text = Paragraph(child, document).text
            if text.strip():
                lines.append(text)
        elif tag == "tbl":
            for row in Table(child, document).rows:
                seen, cells = [], []
                for cell in row.cells:
                    if cell._tc in seen:        # merged cell: same element repeats
                        continue
                    seen.append(cell._tc)
                    cells.append(cell.text.strip())
                if any(cells):
                    lines.append(" | ".join(cells))
    return _text_page(path, "\n".join(lines))


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
