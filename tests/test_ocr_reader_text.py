"""OCR: .txt, .docx and .doc input. Read as text, no AI reading."""
import docx
import pytest

from pipelines.ocr import reader


def _docx(path):
    d = docx.Document()
    d.add_paragraph("Before table")
    t = d.add_table(rows=2, cols=2)
    t.cell(0, 0).text, t.cell(0, 1).text = "Test", "Result"
    t.cell(1, 0).text, t.cell(1, 1).text = "Hb", "13.2 g/dL"
    d.add_paragraph("After table")
    d.save(str(path))
    return path


def test_docx_reads_paragraphs_and_tables_in_order(tmp_path):
    pages = reader.read_input(_docx(tmp_path / "note.docx"))
    assert len(pages) == 1 and pages[0]["png"] is None
    text = pages[0]["text"]
    assert "Hb | 13.2 g/dL" in text
    assert text.index("Before table") < text.index("Hb") < text.index("After table")


def test_docx_merged_cell_is_not_repeated(tmp_path):
    d = docx.Document()
    t = d.add_table(rows=1, cols=2)
    t.cell(0, 0).merge(t.cell(0, 1)).text = "Merged"
    d.save(str(tmp_path / "m.docx"))
    assert reader.read_input(tmp_path / "m.docx")[0]["text"].count("Merged") == 1


def test_txt_utf8_with_and_without_bom(tmp_path):
    p = tmp_path / "a.txt"
    p.write_text("BP 140/90\nline 2", encoding="utf-8")
    q = tmp_path / "b.txt"
    q.write_bytes("\ufeffBOM start".encode("utf-8"))
    assert reader.read_input(p)[0]["text"] == "BP 140/90\nline 2"
    assert reader.read_input(q)[0]["text"] == "BOM start"


def test_txt_in_windows_ansi_still_reads(tmp_path):
    p = tmp_path / "c.txt"
    p.write_bytes("Temp 37°C".encode("cp1252"))
    assert reader.read_input(p)[0]["text"] == "Temp 37°C"


@pytest.mark.parametrize("name", ["empty.txt", "empty.docx"])
def test_file_with_no_text_is_refused(tmp_path, name):
    p = tmp_path / name
    if name.endswith(".txt"):
        p.write_text("  \n", encoding="utf-8")
    else:
        docx.Document().save(str(p))
    with pytest.raises(ValueError, match="no text"):
        reader.read_input(p)


def test_doc_says_save_as_docx(tmp_path):
    p = tmp_path / "old.doc"
    p.write_bytes(b"x")
    with pytest.raises(ValueError, match=r"save it as \.docx"):
        reader.read_input(p)


def test_list_inputs_includes_text_files(tmp_path):
    for n in ("a.txt", "b.DOCX", "c.doc", "d.xyz"):
        (tmp_path / n).write_bytes(b"x")
    assert [p.name for p in reader.list_inputs(tmp_path)] == ["a.txt", "b.DOCX", "c.doc"]


def test_reader_error_does_not_repeat_the_file_name(tmp_path):
    p = tmp_path / "old.doc"
    p.write_bytes(b"x")
    with pytest.raises(ValueError) as exc:
        reader.read_input(p)
    assert "old.doc" not in str(exc.value)
