"""Session 48: a late failure must not lose the OCR work.

_process_file wrote the record only after the summary call and caught only
TooLongError there, so an Ollama timeout at the summary step, or a failed
save (Ang: [Errno 22]), lost every page read and every [?] filled. A
synopsis timeout escaped run_set. Now: any summary error -> record kept
with a placeholder summary; failed save -> <header>_FULLTEXT.txt kept in
out_dir; synopsis error -> synopsis file holds the per-file summaries.
"""
from datetime import datetime
from pathlib import Path

from pipelines.ocr import engine

NOW = datetime(2026, 11, 18, 14, 30)
TEXT = "Pain fell from 32.5 +/- 15 to 21.0 +/- 9"


def _page(monkeypatch):
    monkeypatch.setattr(engine.reader, "read_input",
                        lambda p: [{"page": 1, "text": TEXT}])


def _dirs(tmp_path):
    out, rep = tmp_path / "out", tmp_path / "rep"
    out.mkdir()
    rep.mkdir()
    return out, rep


def test_summary_error_still_writes_record(tmp_path, monkeypatch):
    _page(monkeypatch)
    out, rep = _dirs(tmp_path)

    def call(prompt, images=None):
        raise RuntimeError("Ollama timed out")

    logs = []
    res = engine.run_single(tmp_path / "a.pdf", out, "T", "m", call=call,
                            now=NOW, log=logs.append, records_root=rep)
    assert res["records"] == ["a.pdf"] and res["failed"] == []
    md = list(rep.rglob("*.md"))
    assert md, "no record written"
    body = md[0].read_text(encoding="utf-8")
    assert TEXT in body and "Summary not written" in body
    assert any("WARNING" in l and "timed out" in l for l in logs)


def test_save_error_keeps_full_text(tmp_path, monkeypatch):
    _page(monkeypatch)
    out, rep = _dirs(tmp_path)

    def boom(*a, **k):
        raise OSError(22, "Invalid argument")

    monkeypatch.setattr(engine.output, "write_record", boom)
    logs = []
    res = engine.run_single(tmp_path / "a.pdf", out, "T", "m",
                            call=lambda p, images=None: "Sum", now=NOW,
                            log=logs.append, records_root=rep)
    assert [n for n, _ in res["failed"]] == ["a.pdf"]
    kept = out / "T_2026-11-18_FULLTEXT.txt"
    assert kept.exists(), "full text not kept"
    txt = kept.read_text(encoding="utf-8")
    assert TEXT in txt and "Sum" in txt
    assert any(str(kept) in l for l in logs)


def test_synopsis_error_keeps_file_summaries(tmp_path, monkeypatch):
    _page(monkeypatch)
    out, rep = _dirs(tmp_path)
    files = [tmp_path / "a.pdf", tmp_path / "b.pdf"]
    monkeypatch.setattr(engine.reader, "list_inputs", lambda folder: files)
    marker = engine.SYNOPSIS_PROMPT[:30]
    hit = []

    def call(prompt, images=None):
        if marker in prompt:
            hit.append(1)
            raise RuntimeError("Ollama timed out")
        return "File summary"

    res = engine.run_set(tmp_path, out, "T", "m", call=call, now=NOW,
                         log=lambda m: None, records_root=rep)
    assert hit, "synopsis call never reached the fake (marker not in prompt)"
    assert res["records"] == ["a.pdf", "b.pdf"]
    syn = out / "T_2026-11-18_SYNOPSIS.md"
    assert syn.exists()
    body = syn.read_text(encoding="utf-8")
    assert "Synopsis not written" in body and "File summary" in body


def test_not_included_wording():
    src = Path(engine.__file__).read_text(encoding="utf-8")
    assert "Not included (could not be read)" not in src
