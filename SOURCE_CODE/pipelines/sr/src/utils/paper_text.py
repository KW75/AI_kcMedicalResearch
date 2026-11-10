"""One shared text per paper for SR screening, RoB2 and extraction (Session 37).

Built on the OCR pipeline reader (pipelines/ocr/reader.py):
  - text-layer page        -> its text
  - broken-symbol page     -> text layer with each lost symbol shown as [?]
  - broken-font page       -> Tesseract (local), because the text layer is
                              mostly garbage (Karlsson 2015, McCrae 2019:
                              10-14% broken characters on every page, digits
                              wrong even after the CMap offset decode)
  - scanned page (no text) -> Tesseract (local)
The result is saved as <cache_dir>/<pdf stem>.txt. A rerun uses that file
instead of re-reading the PDF, so a doctor can replace [?] by hand and rerun.

Not yet here (later steps): AI vote to fill [?], Tesseract counter-check of
the [?] left over.
"""
import logging
import os
import re
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

UNKNOWN = "[?]"
# Broken-font rule (Session 37 trial): Ang/Jensen/Lami <= 0.013 per page,
# Karlsson/McCrae >= 0.101 on every page. Minimum count keeps a short line
# like "(n [?] 32)" on the [?] route.
BROKEN_FONT_RATIO = 0.05
BROKEN_FONT_MIN_MARKS = 20

_SCAN_TAG = "(Tesseract)"
_FONT_TAG = "(Tesseract, broken font)"
_SCAN_RE = re.compile(r"^--- page (\d+) --- \(Tesseract\)", re.M)
_FONT_RE = re.compile(r"^--- page (\d+) --- \(Tesseract, broken font\)", re.M)
_UNREADABLE_RE = re.compile(r"\[page (\d+): no text layer")
_WIN_TESSERACT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def _default_read_pages(pdf_path):
    """Pages from the OCR pipeline reader (lazy import: fitz only when used)."""
    try:
        from pipelines.ocr.reader import read_input
    except ModuleNotFoundError:
        from SOURCE_CODE.pipelines.ocr.reader import read_input
    return read_input(pdf_path)


def _default_ocr_png(png: bytes) -> str:
    """Tesseract on one page image. Raises if Tesseract is not available."""
    import io
    import pytesseract
    from PIL import Image
    if sys.platform == "win32" and os.path.exists(_WIN_TESSERACT):
        pytesseract.pytesseract.tesseract_cmd = _WIN_TESSERACT
    return pytesseract.image_to_string(Image.open(io.BytesIO(png))).strip()


def is_broken_font(hint: str) -> bool:
    """True if a [?]-marked text layer is mostly lost symbols.

    Ratio is measured on the original layer: each [?] stood for one character.
    """
    marks = (hint or "").count(UNKNOWN)
    if marks < BROKEN_FONT_MIN_MARKS:
        return False
    original_len = max(len(hint) - 2 * marks, 1)
    return marks / original_len >= BROKEN_FONT_RATIO


def _summary(text: str, path: Path, from_cache: bool,
             scanned=None, unreadable=None, broken_font=None) -> dict:
    if scanned is None:
        scanned = [int(n) for n in _SCAN_RE.findall(text)]
    if unreadable is None:
        unreadable = [int(n) for n in _UNREADABLE_RE.findall(text)]
    if broken_font is None:
        broken_font = [int(n) for n in _FONT_RE.findall(text)]
    return {
        "text": text,
        "unknown": text.count(UNKNOWN),
        "scanned_pages": scanned,
        "unreadable_pages": unreadable,
        "broken_font_pages": broken_font,
        "from_cache": from_cache,
        "path": path,
    }


def _tesseract(ocr_png, png, pdf_name, n, what, path_name):
    """Tesseract text of one page, or "" with a warning if it fails."""
    try:
        return (ocr_png(png) or "").strip()
    except Exception as e:
        logger.warning(f"[PAPER TEXT] {pdf_name} page {n}: Tesseract could not "
                       f"read this {what} page ({e}). Install Tesseract or type "
                       f"the page into {path_name}.")
        return ""


def get_paper_text(pdf_path, cache_dir, read_pages=None, ocr_png=None) -> dict:
    """Text of one paper, read once and saved; see module docstring."""
    read_pages = read_pages or _default_read_pages
    ocr_png = ocr_png or _default_ocr_png
    cache_dir = Path(cache_dir)
    path = cache_dir / (Path(pdf_path).stem + ".txt")
    pdf_name = Path(pdf_path).name

    if path.exists():
        # utf-8-sig: Notepad may add a BOM when the doctor saves a correction
        saved = path.read_bytes().decode("utf-8-sig").replace("\r\n", "\n")
        if saved.strip():
            logger.info(f"[PAPER TEXT] {path.name}: using saved text "
                        f"({saved.count(UNKNOWN)} [?] left)")
            return _summary(saved, path, from_cache=True)

    parts, scanned, unreadable, broken_font = [], [], [], []
    for page in read_pages(pdf_path):
        n = page.get("page")
        hint = page.get("hint")
        if page.get("text"):
            parts.append(f"--- page {n} ---\n{page['text']}")
        elif hint and is_broken_font(hint) and page.get("png"):
            t = _tesseract(ocr_png, page["png"], pdf_name, n, "broken-font", path.name)
            if t:
                broken_font.append(n)
                parts.append(f"--- page {n} --- {_FONT_TAG}\n{t}")
            else:
                parts.append(f"--- page {n} ---\n{hint}")
        elif hint:
            parts.append(f"--- page {n} ---\n{hint}")
        elif page.get("png"):
            t = _tesseract(ocr_png, page["png"], pdf_name, n, "scanned", path.name)
            if t:
                scanned.append(n)
                parts.append(f"--- page {n} --- {_SCAN_TAG}\n{t}")
            else:
                unreadable.append(n)
                parts.append(f"--- page {n} ---\n[page {n}: no text layer, "
                             f"Tesseract could not read it]")
        else:
            unreadable.append(n)
            parts.append(f"--- page {n} ---\n[page {n}: no text layer, no image]")

    text = "\n\n".join(parts)
    cache_dir.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))  # no BOM
    result = _summary(text, path, from_cache=False, scanned=scanned,
                      unreadable=unreadable, broken_font=broken_font)
    logger.info(f"[PAPER TEXT] {path.name}: {result['unknown']} [?], "
                f"broken-font pages {broken_font or 'none'}, "
                f"scanned pages {scanned or 'none'}, "
                f"unreadable pages {unreadable or 'none'}")
    return result
