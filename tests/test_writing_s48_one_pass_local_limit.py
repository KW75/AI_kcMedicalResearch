"""Session 48: one-pass writing tracks (topic/article/report) on local AI
skip a file too large for the context window, as appraisal does (PR #20)."""

import inspect
import sys
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "SOURCE_CODE"))

import pipelines.writing.writing as w  # noqa: E402

ANSWER = "# Title\n\nBody.\n\n=== REVIEW ===\n\nRECOMMENDATION: APPROVE\n"


def _paths(tmp_path):
    paths = {
        "doc_root": tmp_path / "docs",
        "input": tmp_path / "input",
        "output": tmp_path / "output",
        "reports": tmp_path / "reports",
    }
    for p in paths.values():
        p.mkdir(parents=True)
    return paths


def _run(tmp_path, files, **kwargs):
    paths = _paths(tmp_path)
    calls = []

    def fake_llm(system_prompt, user_prompt):
        calls.append(user_prompt)
        return ANSWER

    with patch.object(w, "_paths", return_value=paths), \
         patch.object(w, "_load_input_files", return_value=files):
        w.run_one_pass(direct_instructions=[], call_llm_fn=fake_llm,
                       track=w.TRACK_TOPIC, verbose=False, **kwargs)
    return calls, sorted(paths["output"].glob("WRITING_*.docx"))


def test_limit_is_the_shared_local_budget():
    assert w.SYNOPSIS_LOCAL_MAX_CHARS == 80_000


def test_default_is_not_local():
    param = inspect.signature(w.run_one_pass).parameters.get("local")
    assert param is not None and param.default is False


def test_local_skips_file_over_limit_with_message(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(w, "SYNOPSIS_LOCAL_MAX_CHARS", 10)
    calls, docs = _run(tmp_path, [("big", "x" * 50, ".txt")], local=True)
    assert calls == []
    assert docs == []
    out = capsys.readouterr().out
    assert "big" in out and "too large for local AI" in out and "Skipped" in out


def test_local_other_files_still_written(tmp_path, monkeypatch):
    monkeypatch.setattr(w, "SYNOPSIS_LOCAL_MAX_CHARS", 10)
    files = [("a", "short", ".txt"), ("big", "x" * 50, ".txt")]
    calls, docs = _run(tmp_path, files, local=True)
    assert len(calls) == 1 and "short" in calls[0]
    assert len(docs) == 1 and "_a_" in docs[0].name


def test_local_file_at_limit_is_sent(tmp_path, monkeypatch):
    monkeypatch.setattr(w, "SYNOPSIS_LOCAL_MAX_CHARS", 10)
    calls, docs = _run(tmp_path, [("edge", "x" * 10, ".txt")], local=True)
    assert len(calls) == 1 and len(docs) == 1


def test_cloud_sends_long_file(tmp_path, monkeypatch):
    monkeypatch.setattr(w, "SYNOPSIS_LOCAL_MAX_CHARS", 10)
    calls, docs = _run(tmp_path, [("big", "x" * 50, ".txt")], local=False)
    assert len(calls) == 1 and len(docs) == 1


def test_local_scratch_still_writes(tmp_path, monkeypatch):
    monkeypatch.setattr(w, "SYNOPSIS_LOCAL_MAX_CHARS", 10)
    calls, docs = _run(tmp_path, [], local=True)
    assert len(calls) == 1 and len(docs) == 1


def test_menu_2_passes_local_flag():
    src = (PROJECT_ROOT / "SOURCE_CODE" / "main.py").read_text(encoding="utf-8")
    start = src.index("\n    run_one_pass(\n")
    block = src[start:src.index("\n    )\n", start)]
    assert 'local=(provider == "ollama")' in block
