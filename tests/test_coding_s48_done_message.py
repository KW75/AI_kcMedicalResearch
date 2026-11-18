"""Session 48: menu 1 end line says how many files were processed and skipped.

Before, menu 1 always printed "Done. Check output/coding/ and
reports/coding/", even when every file was skipped (PR #35 size check).
"""
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "SOURCE_CODE"))

import pipelines.coding.coding as c  # noqa: E402


def _setup(tmp_path, files):
    paths = {k: tmp_path / k for k in ("doc", "input", "output", "reports")}
    for p in paths.values():
        p.mkdir()
    for name, text in files.items():
        (paths["input"] / name).write_text(text, encoding="utf-8")
    return paths


def _fake(answer):
    return lambda system_prompt, user_prompt: answer


@pytest.mark.parametrize("runner,answer", [
    ("run_reviewer", "REVIEW_PASS"),
    ("run_tester", "TEST_PASS"),
])
def test_runner_returns_processed_and_skipped(tmp_path, monkeypatch,
                                              runner, answer):
    monkeypatch.setattr(c, "CODING_LOCAL_MAX_CHARS", 100)
    paths = _setup(tmp_path, {"big.py": "x" * 150, "small.py": "print(1)\n"})
    with patch.object(c, "_paths", return_value=paths):
        result = getattr(c, runner)([], _fake(answer), verbose=False,
                                    local=True)
    assert result == (1, 1)


def test_builder_all_skipped_returns_counts(tmp_path, monkeypatch):
    monkeypatch.setattr(c, "CODING_LOCAL_MAX_CHARS", 100)
    paths = _setup(tmp_path, {"big.py": "x" * 150})
    with patch.object(c, "_paths", return_value=paths):
        result = c.run_builder([], _fake("REVIEW_PASS"), verbose=False,
                               local=True)
    assert result == (0, 1)


@pytest.mark.parametrize("runner", ["run_reviewer", "run_tester"])
def test_no_files_returns_zero(tmp_path, runner):
    paths = _setup(tmp_path, {})
    with patch.object(c, "_paths", return_value=paths):
        assert getattr(c, runner)([], _fake("x"), verbose=False) == (0, 0)


@pytest.mark.parametrize("tag,p,s,expected", [
    ("REVIEWER", 1, 1,
     "[REVIEWER] Done: 1 processed, 1 skipped. "
     "Check reports/coding/ for results."),
    ("BUILDER", 2, 0,
     "[BUILDER] Done: 2 processed, 0 skipped. "
     "Check output/coding/ and reports/coding/ for results."),
    ("TESTER", 0, 2,
     "[TESTER] Nothing processed: 2 file(s) skipped "
     "(too large for local AI). See the messages above."),
    ("REVIEWER", 0, 0,
     "[REVIEWER] Nothing processed: no files in input/coding/."),
])
def test_done_line(tag, p, s, expected):
    assert c.coding_done_line(tag, p, s) == expected


def test_menu1_prints_counted_end_line():
    src = (ROOT / "SOURCE_CODE" / "main.py").read_text(encoding="utf-8")
    body = src.split("def handle_coding_mode(", 1)[1]
    body = body.split("def handle_appraisal_mode(", 1)[0]
    assert body.count("result = run_") == 3
    assert "coding_done_line(" in body
    assert "Check output/coding/ and reports/coding/ for results" not in body
