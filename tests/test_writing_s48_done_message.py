"""Session 48: menu 2 end line reports how many one-pass files were written
and skipped, instead of always saying 'Done. Check output/writing/'."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "SOURCE_CODE"))

import pipelines.writing.writing as w  # noqa: E402

ANSWER = "# Title\n\nBody.\n\n=== REVIEW ===\n\nRECOMMENDATION: APPROVE\n"


def _run(tmp_path, files, **kwargs):
    paths = {k: tmp_path / k for k in ("doc_root", "input", "output", "reports")}
    for p in paths.values():
        p.mkdir(parents=True)
    with patch.object(w, "_paths", return_value=paths), \
         patch.object(w, "_load_input_files", return_value=files):
        return w.run_one_pass(direct_instructions=[],
                              call_llm_fn=lambda s, u: ANSWER,
                              track=w.TRACK_TOPIC, verbose=False, **kwargs)


def test_scratch_returns_one_written(tmp_path):
    assert _run(tmp_path, []) == (1, 0)


def test_local_skip_only_returns_zero_written(tmp_path, monkeypatch):
    monkeypatch.setattr(w, "SYNOPSIS_LOCAL_MAX_CHARS", 10)
    assert _run(tmp_path, [("big", "x" * 50, ".txt")], local=True) == (0, 1)


def test_mixed_returns_counts(tmp_path, monkeypatch):
    monkeypatch.setattr(w, "SYNOPSIS_LOCAL_MAX_CHARS", 10)
    files = [("a", "short", ".txt"), ("big", "x" * 50, ".txt")]
    assert _run(tmp_path, files, local=True) == (1, 1)


def test_done_line_counts():
    line = w.one_pass_done_line(w.TRACK_TOPIC, (2, 1))
    assert "[WRITING | TOPIC] Done: 2 written, 1 skipped." in line
    assert "Check output/writing/" in line


def test_done_line_nothing_written():
    line = w.one_pass_done_line(w.TRACK_TOPIC, (0, 1))
    assert "Nothing written: 1 file(s) skipped" in line
    assert "Check output/writing/" not in line


def test_done_line_plain_for_non_tuple():
    line = w.one_pass_done_line(w.TRACK_TOPIC, MagicMock())
    assert "[WRITING | TOPIC] Done. Check output/writing/" in line


def test_menu_2_prints_done_line():
    src = (PROJECT_ROOT / "SOURCE_CODE" / "main.py").read_text(encoding="utf-8")
    assert "result = run_one_pass(" in src
    assert "print(one_pass_done_line(track, result))" in src
    assert '] Done. "\n          "Check output/writing/' not in src
