"""Writing input: old Word .doc files are skipped with a message, not silently."""
from pipelines.writing import writing


def test_doc_is_skipped_with_a_message(tmp_path, capsys):
    (tmp_path / "notes.txt").write_text("Hb 13.2 g/dL", encoding="utf-8")
    (tmp_path / "Old Report.doc").write_bytes(b"\xd0\xcf\x11\xe0 not a real doc")
    files = writing._load_input_files(tmp_path)
    assert [(stem, suffix) for stem, _, suffix in files] == [("notes", ".txt")]
    out = capsys.readouterr().out
    assert "[SKIP] Old Report.doc" in out
    assert "save it as .docx" in out


def test_uppercase_doc_is_also_reported(tmp_path, capsys):
    (tmp_path / "A.DOC").write_bytes(b"x")
    assert writing._load_input_files(tmp_path) == []
    assert "[SKIP] A.DOC" in capsys.readouterr().out


def test_no_doc_means_no_skip_message(tmp_path, capsys):
    (tmp_path / "a.md").write_text("x", encoding="utf-8")
    writing._load_input_files(tmp_path)
    assert "[SKIP]" not in capsys.readouterr().out
