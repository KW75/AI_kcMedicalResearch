"""Session 48: Word tables and a visible PDF cut for writing / appraisal input.

Before: every .docx reader used doc.paragraphs only, so Word tables were
never read; main._read_pdf_pymupdf cut at max_chars with no warning.
Now: pipelines/shared/doc_reader.read_docx walks paragraphs and tables in
document order (row = 'cell | cell | cell', merged cells once, empty
paragraphs skipped) and main.py, writing.py and appraisal.py use it.
A cut PDF ends with a visible note.
"""
import docx
import fitz

import main
from pipelines.writing import writing as W
from pipelines.appraisal import appraisal as A


def _reader():
    from pipelines.shared import doc_reader
    return doc_reader


def _docx(path):
    d = docx.Document()
    d.add_paragraph("Intro text")
    d.add_paragraph("")
    t = d.add_table(rows=2, cols=3)
    for c, v in zip(t.rows[0].cells, ("Group", "Mean", "SD")):
        c.text = v
    for c, v in zip(t.rows[1].cells, ("CBT", "4.1", "1.2")):
        c.text = v
    d.add_paragraph("After table")
    d.save(str(path))
    return path


def _pdf(path, n=30):
    d = fitz.open()
    page = d.new_page()
    page.insert_text((72, 72), "\n".join(f"Row {i} value 12.{i}" for i in range(n)),
                     fontsize=9)
    d.save(str(path))
    d.close()
    return path


def test_docx_table_rows_read(tmp_path):
    text = _reader().read_docx(_docx(tmp_path / "a.docx"))
    assert "Group | Mean | SD" in text
    assert "CBT | 4.1 | 1.2" in text


def test_docx_order_paragraph_table_paragraph(tmp_path):
    text = _reader().read_docx(_docx(tmp_path / "a.docx"))
    pos = [text.index(s) for s in ("Intro text", "Group | Mean | SD",
                                   "CBT | 4.1 | 1.2", "After table")]
    assert pos == sorted(pos)


def test_docx_merged_cells_once(tmp_path):
    d = docx.Document()
    t = d.add_table(rows=1, cols=3)
    merged = t.cell(0, 0).merge(t.cell(0, 1))
    merged.text = "Baseline"
    t.cell(0, 2).text = "Week 12"
    p = tmp_path / "m.docx"
    d.save(str(p))
    text = _reader().read_docx(p)
    assert "Baseline | Week 12" in text


def test_docx_empty_paragraphs_skipped(tmp_path):
    text = _reader().read_docx(_docx(tmp_path / "a.docx"))
    assert "" not in text.split("\n")


def test_main_read_docx_includes_tables(tmp_path):
    assert "CBT | 4.1 | 1.2" in main._read_docx(_docx(tmp_path / "a.docx"))


def test_writing_loader_includes_tables(tmp_path):
    d = tmp_path / "in"
    d.mkdir()
    _docx(d / "a.docx")
    assert "CBT | 4.1 | 1.2" in " ".join(str(x) for x in W._load_input_files(d))


def test_appraisal_loader_includes_tables(tmp_path):
    d = tmp_path / "in"
    d.mkdir()
    _docx(d / "a.docx")
    assert "CBT | 4.1 | 1.2" in " ".join(str(x) for x in A._load_input_files(d))


def test_pdf_cut_is_visible(tmp_path):
    text = main._read_pdf_pymupdf(_pdf(tmp_path / "a.pdf"), max_chars=100)
    assert "[Text cut at 100 characters" in text
    assert "Row 29" not in text


def test_pdf_not_cut_has_no_note(tmp_path):
    text = main._read_pdf_pymupdf(_pdf(tmp_path / "a.pdf"), max_chars=30_000)
    assert "Row 29" in text
    assert "[Text cut" not in text
