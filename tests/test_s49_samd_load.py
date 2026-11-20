"""Session 49 PR D: SaMD loads inputs and saves step 1 (no AI call).

Pinned:
- run_id is YYYYMMDD_HHMMSS (same shape as SR run folders).
- File choice: Enter = all; "3,1" = those, in list order; a bad number
  stops the job (None), nothing written.
- The doctor's text ends at an empty line or end of input.
- reports/samd/<run_id>/ gets clinician_input.txt, inputs.json, run.log;
  output/samd/ is not touched; no AI call.
- No files and no text: job not run, nothing written.
"""
import json
from datetime import datetime

import pytest

from SOURCE_CODE.pipelines.samd import cli

NOW = datetime(2026, 11, 20, 15, 30, 0)


@pytest.fixture(autouse=True)
def _no_ai(monkeypatch):
    # PR E: run() goes on to the AI steps; these tests stop after step 1.
    monkeypatch.setattr(cli, "choose_call", lambda *a, **k: None, raising=False)
    monkeypatch.setattr(cli, "read_pages", lambda p: [], raising=False)

def _answers(*items):
    it = iter(items)
    return lambda _prompt="": next(it)


def _case(tmp_path, names=("labs.png", "notes.txt", "rash.jpg")):
    d = tmp_path / "input" / "samd"
    d.mkdir(parents=True)
    for n in names:
        (d / n).write_bytes(b"abc")
    return d


def test_run_id_format():
    assert cli.new_run_id(NOW) == "20261120_153000"


def test_choose_enter_means_all():
    assert cli.choose_files(["a", "b"], _answers(""), lambda m: None) == ["a", "b"]


def test_choose_numbers_in_list_order_without_duplicates():
    got = cli.choose_files(["a", "b", "c"], _answers("3, 1,1"), lambda m: None)
    assert got == ["a", "c"]


@pytest.mark.parametrize("typed", ["0", "4", "x", "1,,2"])
def test_choose_bad_number_stops(typed):
    msgs = []
    assert cli.choose_files(["a", "b", "c"], _answers(typed), msgs.append) is None
    assert "Job not run" in msgs[-1]


def test_clinician_text_ends_at_empty_line():
    txt = cli.read_clinician_text(
        _answers("55F, fever 3 days", "CRP 120", "", "ignored"), lambda m: None)
    assert txt == "55F, fever 3 days\nCRP 120"


def test_clinician_text_ends_at_eof():
    def eof(_p=""):
        raise EOFError
    assert cli.read_clinician_text(eof, lambda m: None) == ""


def test_file_kinds():
    names = ("a.JPG", "b.txt", "c.docx", "d.pdf")
    assert [cli.file_kind(n) for n in names] == ["image", "txt", "docx", "pdf"]


def test_run_saves_step1(tmp_path):
    _case(tmp_path)
    lines = []
    res = cli.run(tmp_path, provider="ollama", model="gemma4:e4b",
                  input_fn=_answers("1,3", "55F, rash", ""),
                  log=lines.append, now=NOW)
    run_dir = tmp_path / "reports" / "samd" / "20261120_153000"
    assert res["run_dir"] == run_dir
    assert res["files"] == ["labs.png", "rash.jpg"]
    assert res["ai_called"] is False
    assert (run_dir / "clinician_input.txt").read_text(encoding="utf-8") == "55F, rash\n"
    info = json.loads((run_dir / "inputs.json").read_text(encoding="utf-8"))
    assert info["run_id"] == "20261120_153000"
    assert info["model"] == "gemma4:e4b"
    assert [(f["name"], f["kind"], f["bytes"]) for f in info["files"]] == [
        ("labs.png", "image", 3), ("rash.jpg", "image", 3)]
    assert info["clinician_text_chars"] == 9
    assert cli.INTENDED_USE in (run_dir / "run.log").read_text(encoding="utf-8")
    assert not (tmp_path / "output").exists()


def test_text_only_case_runs(tmp_path):
    res = cli.run(tmp_path, input_fn=_answers("Chest pain, troponin 45", ""),
                  log=lambda m: None, now=NOW)
    assert res["files"] == []
    assert (res["run_dir"] / "clinician_input.txt").exists()


def test_nothing_to_analyse_writes_nothing(tmp_path):
    msgs = []
    assert cli.run(tmp_path, input_fn=_answers(""), log=msgs.append, now=NOW) is None
    assert not (tmp_path / "reports").exists()
    assert "Job not run" in msgs[-1]


def test_bad_choice_writes_nothing(tmp_path):
    _case(tmp_path)
    assert cli.run(tmp_path, input_fn=_answers("9"), log=lambda m: None, now=NOW) is None
    assert not (tmp_path / "reports").exists()
