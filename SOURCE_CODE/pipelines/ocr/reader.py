"""OCR input reader.

Turns one file from input/ocr/ into a list of pages for the OCR pipeline.
Each page is {"page": n, "text": str | None, "png": bytes | None}; exactly
one of text/png is set:
- PDF page with a clean text layer (>= MIN_TEXT_CHARS characters, no broken
  symbols): text, no AI.
- PDF page without text (scan, blank, page number only): PNG for the model.
- Image file (any supported format): converted to PNG. A multi-page TIFF
  gives one page per frame.
- .txt and .docx: one text page, no AI. .docx reads paragraphs and tables
  in document order (a row becomes "cell | cell"; a merged cell appears once).
- .doc (old Word): refused with "save it as .docx" (no reliable reader yet).
- .eml (Session 50): Email date / From / Subject and the text body; an
  HTML-only body is turned into text. PDF and image attachments become
  extra pages. A .txt file that starts with email headers is read the same.
A file with no text raises ValueError, so the engine lists it as failed.
Uses pymupdf (fitz), pillow and python-docx, all in requirements-local.txt.
"""
from __future__ import annotations

import io
import re
from email import policy
from email.parser import BytesParser
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
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
EML_EXTS = {".eml"}  # Session 50
SUPPORTED_EXTS = (PDF_EXTS | IMAGE_EXTS | TEXT_EXTS | DOCX_EXTS | DOC_EXTS
                  | EML_EXTS)
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
    if ext in EML_EXTS:
        return _read_eml(path)
    if ext in TEXT_EXTS:
        if _looks_like_email(path.read_bytes()):  # e.g. receipt.eml.txt
            return _read_eml(path)
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


def _page(number: int, text: str | None = None, png: bytes | None = None,
          hint: str | None = None) -> dict:
    page = {"page": number, "text": text, "png": png}
    if hint is not None:
        page["hint"] = hint  # text layer with [?] for each lost symbol
    return page


# A PDF text layer with control characters (tab, newline, CR excepted) or the
# replacement character U+FFFD means a symbol font lost its signs. Ang 2010:
# "4.4 \x02 13.7" (the ± is lost), "(n \x01 32)" (the = is lost). The codes
# differ per font, so they cannot be mapped back; such pages are read from
# the image by the vision model instead.
_BROKEN_SYMBOLS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\ufffd]")


def has_broken_symbols(text) -> bool:
    """True if a text layer contains characters its font failed to map."""
    return bool(_BROKEN_SYMBOLS.search(text or ""))


def mark_broken(text) -> str:
    """Text layer with each character its font failed to map shown as [?]."""
    return _BROKEN_SYMBOLS.sub("[?]", text or "")


def symbol_codes(page, text):
    """font:code of each broken character in text, in order, or None.

    The same code means different signs in different fonts (Ang 2010: 0x2 in
    MathematicalPi-Four and in Universal-GreekwithMathP), so checks need the
    font. Read from get_text("dict"); None if its broken characters are not
    exactly those of text (then the page gets no per-code check).
    """
    found = []
    data = page.get_text("dict")
    if not isinstance(data, dict):
        return None
    for block in data.get("blocks", []):
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                found += [(span.get("font", ""), ch) for ch in span.get("text", "")
                          if _BROKEN_SYMBOLS.fullmatch(ch)]
    if [ch for _, ch in found] != _BROKEN_SYMBOLS.findall(text or ""):
        return None
    return [f"{font}:{hex(ord(ch))}" for font, ch in found]


def _read_pdf(path: Path) -> list[dict]:
    with fitz.open(str(path)) as doc:
        return _pdf_pages(doc, 1)


def _pdf_pages(doc, start: int) -> list[dict]:
    """Pages of an open PDF, numbered from start (also email attachments)."""
    pages = []
    for number, page in enumerate(doc, start=start):
        text = page.get_text().strip()
        if len(text) >= MIN_TEXT_CHARS and not has_broken_symbols(text):
            pages.append(_page(number, text=text))
        else:
            pix = page.get_pixmap(dpi=PDF_RENDER_DPI)
            hint = mark_broken(text) if len(text) >= MIN_TEXT_CHARS else None
            entry = _page(number, png=pix.tobytes("png"), hint=hint)
            if hint:
                entry["codes"] = symbol_codes(page, text)
            pages.append(entry)
    return pages


def _read_image(path: Path) -> list[dict]:
    with Image.open(path) as img:
        return _image_pages(img, 1)


def _image_pages(img, start: int) -> list[dict]:
    """One PNG page per frame, numbered from start (also email attachments)."""
    return [_page(number, png=_to_png(frame))
            for number, frame in enumerate(ImageSequence.Iterator(img), start=start)]


def _to_png(frame: Image.Image) -> bytes:
    buf = io.BytesIO()
    frame.convert("RGB").save(buf, format="PNG")
    return buf.getvalue()


# ---- Session 50: e-mail receipts (.eml, or a .txt that is an email) ----
_HEADER_LINE = re.compile(r"([A-Za-z][A-Za-z0-9-]*):")
_SPACES = re.compile(r"[ \t\u00a0\u2007\u202f\u3000]+")


def _looks_like_email(raw: bytes) -> bool:
    """True if the bytes start with email headers: From plus Content-Type or
    MIME-Version before the first blank line."""
    head = raw[:65536]
    if head.startswith(b"\xef\xbb\xbf"):
        head = head[3:]
    text = head.decode("utf-8", errors="replace").replace("\r\n", "\n")
    block = text.split("\n\n", 1)[0].split("\n")
    if not block or not _HEADER_LINE.match(block[0]):
        return False
    names = set()
    for line in block:
        m = _HEADER_LINE.match(line)
        if m:
            names.add(m.group(1).lower())
    return "from" in names and bool(names & {"content-type", "mime-version"})


def _clean_text(text: str) -> str:
    """Non-breaking and other wide spaces -> one space; no empty lines."""
    lines = (_SPACES.sub(" ", line).strip()
             for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"))
    return "\n".join(line for line in lines if line)


class _HTMLText(HTMLParser):
    BLOCK = {"br", "p", "div", "tr", "table", "li", "ul", "ol", "hr", "h1", "h2",
             "h3", "h4", "h5", "h6", "section", "article", "header", "footer"}
    SKIP = {"style", "script", "head", "title"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip += 1
        elif tag in self.BLOCK:
            self.parts.append("\n")
        elif tag in ("td", "th"):
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self.skip = max(0, self.skip - 1)
        elif tag in self.BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def html_to_text(markup: str) -> str:
    """Visible text of an HTML email body, one block per line."""
    p = _HTMLText()
    p.feed(markup)
    p.close()
    return _clean_text("".join(p.parts))


def _email_date(value) -> str:
    if not value:
        return ""
    try:
        return parsedate_to_datetime(str(value)).date().isoformat()
    except (TypeError, ValueError, IndexError, OverflowError):
        return ""


def _part_text(part) -> str:
    try:
        return part.get_content()
    except (LookupError, ValueError, AssertionError):
        data = part.get_payload(decode=True) or b""
        return data.decode("utf-8", errors="replace")


def _read_eml(path: Path) -> list[dict]:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    msg = BytesParser(policy=policy.default).parsebytes(raw)
    head = []
    when = _email_date(msg.get("Date"))
    if when:
        head.append(f"Email date: {when}")
    for name in ("From", "Subject"):
        try:
            value = msg.get(name)
        except Exception:
            value = None
        if value:
            head.append(f"{name}: {_clean_text(str(value))}")
    body = ""
    part = msg.get_body(preferencelist=("plain", "html"))
    if part is not None:
        body = _part_text(part)
        if part.get_content_type() == "text/html":
            body = html_to_text(body)
        else:
            body = _clean_text(body)
    pages = []
    if body.strip():
        pages.append(_page(1, text="\n".join(head + ["", body]).strip()))
    for att in msg.iter_attachments():
        ext = Path(att.get_filename() or "").suffix.lower()
        ctype = att.get_content_type()
        data = att.get_payload(decode=True) or b""
        if not data:
            continue
        start = len(pages) + 1
        if ext in PDF_EXTS or ctype == "application/pdf":
            with fitz.open(stream=data, filetype="pdf") as doc:
                pages += _pdf_pages(doc, start)
        elif att.get_content_disposition() == "attachment" and (
                ext in IMAGE_EXTS or ctype.startswith("image/")):
            with Image.open(io.BytesIO(data)) as img:
                pages += _image_pages(img, start)
    if not pages:
        raise ValueError("no text found in the email")
    return pages
