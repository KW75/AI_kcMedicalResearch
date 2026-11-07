"""OCR output files (Session 35 design).

Records: summary on top, full OCR text below, one heading per page saying how
it was read. OCR text is written verbatim: no markdown -> Word list or heading
conversion, so "3) BP 140/90" is never renumbered. Every file names the model
and says the content is AI-produced. Files go to tmp_path only.
"""
from datetime import datetime

import docx
import pytest

from pipelines.ocr import output

NOW = datetime(2026, 11, 7, 14, 30)
PAGES = [
    {"page": 1, "text": "Typed page one.", "method": "text"},
    {"page": 2, "text": "3) BP 140/90\n- not a bullet\n# not a heading",
     "method": "vision"},
]


def _docx_paragraphs(path):
    return [(p.text, p.style.name) for p in docx.Document(str(path)).paragraphs]


def test_header_from_typed_name():
    assert output.make_header("Cardio lectures", NOW) == "Cardio_lectures_2026-11-07"


def test_header_default_when_blank():
    assert output.make_header("", NOW) == "OCR_2026-11-07_1430"
    assert output.make_header("   ", NOW) == "OCR_2026-11-07_1430"


def test_header_drops_unsafe_characters():
    assert output.make_header("PT/01:a", NOW) == "PT01a_2026-11-07"
    assert output.make_header("///", NOW) == "OCR_2026-11-07_1430"


def test_record_paths_keep_extension_so_names_cannot_clash(tmp_path):
    header = "PT0123_2026-11-07"
    a = output.write_record(tmp_path, header, "scan01.pdf", "S", PAGES, "gemma4:e4b")
    b = output.write_record(tmp_path, header, "scan01.png", "S", PAGES, "gemma4:e4b")
    assert a[0] == tmp_path / "records" / "PT0123_2026-11-07_scan01_pdf.docx"
    assert a[1] == tmp_path / "records" / "PT0123_2026-11-07_scan01_pdf.md"
    assert b[0].name == "PT0123_2026-11-07_scan01_png.docx"
    assert all(p.exists() for p in (*a, *b))


def test_record_md_has_summary_then_full_text_verbatim(tmp_path):
    _, md = output.write_record(tmp_path, "H", "scan.pdf", "Short summary.",
                                PAGES, "gemma4:e4b")
    text = md.read_text(encoding="utf-8")
    assert text.index("## Summary") < text.index("Short summary.") < text.index("## Full text")
    assert "### Page 1 (text layer)" in text
    assert "### Page 2 (AI read)" in text
    assert "3) BP 140/90\n- not a bullet\n# not a heading" in text


def test_record_docx_keeps_ocr_lines_as_plain_text(tmp_path):
    path, _ = output.write_record(tmp_path, "H", "scan.pdf", "Short summary.",
                                  PAGES, "gemma4:e4b")
    paras = _docx_paragraphs(path)
    for line in ("3) BP 140/90", "- not a bullet", "# not a heading"):
        assert (line, "Normal") in paras
    assert ("Page 2 (AI read)", "Heading 3") in paras


def test_every_file_names_the_model_and_says_ai(tmp_path):
    rec = output.write_record(tmp_path, "H", "scan.pdf", "S", PAGES, "gemma4:e4b")
    summ = output.write_summary(tmp_path, "H", "SYNOPSIS", "All files.", "gemma4:e4b")
    for md in (rec[1], summ[1]):
        note = md.read_text(encoding="utf-8")
        assert "gemma4:e4b" in note and "AI" in note
    for path in (rec[0], summ[0]):
        assert any("gemma4:e4b" in t for t, _ in _docx_paragraphs(path))


def test_summary_and_synopsis_file_names(tmp_path):
    s = output.write_summary(tmp_path, "H", "SUMMARY", "One file.", "m")
    y = output.write_summary(tmp_path, "H", "SYNOPSIS", "All files.", "m")
    assert s[0] == tmp_path / "H_SUMMARY.docx" and s[1] == tmp_path / "H_SUMMARY.md"
    assert y[0] == tmp_path / "H_SYNOPSIS.docx"


def test_summary_kind_must_be_known(tmp_path):
    with pytest.raises(ValueError):
        output.write_summary(tmp_path, "H", "REPORT", "x", "m")
