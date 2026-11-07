"""OCR input reader (Session 35 design).

PDF pages with a text layer are read directly (no AI); pages without text
and image files become PNG for the vision model. Multi-page TIFF gives one
page per frame. Test files are made in tmp_path; no real documents used.
"""
import fitz
import pytest
from PIL import Image

from pipelines.ocr import reader

PNG_MAGIC = b"\x89PNG"
IMAGE_EXTS = [".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".gif", ".webp"]


def _make_pdf(path, texts):
    doc = fitz.open()
    for text in texts:
        page = doc.new_page()
        if text:
            page.insert_text((72, 72), text)
    doc.save(str(path))
    doc.close()


def test_list_inputs_keeps_supported_files_in_name_order(tmp_path):
    for name in ["c.xyz", "b.PNG", "a.pdf", "d.webp", "notes.xlsx"]:
        (tmp_path / name).write_bytes(b"x")
    names = [p.name for p in reader.list_inputs(tmp_path)]
    assert names == ["a.pdf", "b.PNG", "d.webp"]


def test_pdf_page_with_text_is_read_directly(tmp_path):
    pdf = tmp_path / "typed.pdf"
    _make_pdf(pdf, ["This page has a real text layer for OCR."])
    pages = reader.read_input(pdf)
    assert len(pages) == 1
    assert pages[0]["page"] == 1
    assert "real text layer" in pages[0]["text"]
    assert pages[0]["png"] is None


def test_pdf_page_without_text_becomes_png(tmp_path):
    pdf = tmp_path / "scan.pdf"
    _make_pdf(pdf, ["Typed first page with enough text here.", "", "12"])
    pages = reader.read_input(pdf)
    assert [p["page"] for p in pages] == [1, 2, 3]
    assert pages[0]["text"] and pages[0]["png"] is None
    for p in pages[1:]:          # blank page and page-number-only page
        assert p["text"] is None
        assert p["png"].startswith(PNG_MAGIC)


@pytest.mark.parametrize("ext", IMAGE_EXTS)
def test_each_image_format_becomes_png(tmp_path, ext):
    path = tmp_path / f"photo{ext}"
    Image.new("RGB", (60, 40), "white").save(path)
    pages = reader.read_input(path)
    assert len(pages) == 1
    assert pages[0]["text"] is None
    assert pages[0]["png"].startswith(PNG_MAGIC)


def test_multipage_tiff_gives_one_page_per_frame(tmp_path):
    path = tmp_path / "scanner.tif"
    first = Image.new("RGB", (60, 40), "white")
    second = Image.new("RGB", (60, 40), "black")
    first.save(path, save_all=True, append_images=[second])
    pages = reader.read_input(path)
    assert [p["page"] for p in pages] == [1, 2]
    assert all(p["png"].startswith(PNG_MAGIC) for p in pages)


def test_unsupported_file_is_refused(tmp_path):
    path = tmp_path / "notes.xlsx"
    path.write_text("hello", encoding="utf-8")
    with pytest.raises(ValueError):
        reader.read_input(path)
