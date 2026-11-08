"""OCR reader: PDF text layers with broken symbol fonts go to the vision model.

Ang 2010: the text layer gives '4.4 \\x02 13.7 mA' (the ± is lost) and
'(n \\x01 32)' (the = is lost). Such pages are read from the image instead.
"""
import fitz
import pytest

from pipelines.ocr import reader


def _pdf(path, text="Plain page text that is long enough to count as a text layer."):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    doc.save(str(path))
    doc.close()


@pytest.mark.parametrize("text", [
    "4.4 \x02 13.7 mA", "(n \x01 32)", "a\x00b", "x\x1fy", "a\ufffdb",
])
def test_control_characters_mark_text_as_broken(text):
    assert reader.has_broken_symbols(text)


@pytest.mark.parametrize("text", [
    "4.4 \u00b1 13.7 mA", "line one\nline two\ttab\r\n", "",
])
def test_normal_text_is_not_broken(text):
    assert not reader.has_broken_symbols(text)


def test_pdf_page_with_broken_symbols_is_read_by_ai(tmp_path, monkeypatch):
    path = tmp_path / "ang.pdf"
    _pdf(path)
    broken = "Participants (n \x01 32) had 4.4 \x02 13.7 mA at baseline."
    monkeypatch.setattr(fitz.Page, "get_text", lambda self, *a, **k: broken)
    pages = reader.read_input(path)
    assert pages[0]["text"] is None
    assert pages[0]["png"]
