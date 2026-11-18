"""Session 48: wording of the OCR submenu (menu 8, several files).

<n> files in <input/ocr>     (no '-> one record each + SYNOPSIS' when asking)
  <file names>
Write them as
1. Papers   - ...
2. Synopsis - ...
kind="synopsis" (no question) keeps the old header.
"""
import pytest

from pipelines.ocr import cli

PULLED = [{"name": "gemma4:e4b", "size_gb": 6.6, "params_b": 7.5}]


@pytest.fixture(autouse=True)
def _no_env_model(monkeypatch):
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)


def _done(*a, **k):
    return {"header": "H", "records": [], "failed": [], "summary": None}


def _run(tmp_path, *answers, kind="ask"):
    inp = tmp_path / "input" / "ocr"
    inp.mkdir(parents=True)
    for f in ("a.pdf", "b.png"):
        (inp / f).write_bytes(b"x")
    it = iter(answers)
    logs = []
    cli.run(tmp_path, input_fn=lambda p="": next(it),
            list_fn=lambda host=None: [dict(m) for m in PULLED],
            caps_fn=lambda host, name: {"completion", "vision"},
            run_single=_done, run_set=_done, log=logs.append, kind=kind)
    return logs, inp


def test_header_when_asking_has_no_synopsis_promise(tmp_path):
    logs, inp = _run(tmp_path, "2", "Scan", "")
    assert f"2 files in {inp}" in logs
    assert not any("-> one record each" in line for line in logs)


def test_question_line_says_write_them_as(tmp_path):
    logs, inp = _run(tmp_path, "2", "Scan", "")
    assert "Write them as" in logs
    assert not any("Several files" in line for line in logs)


def test_options_numbered_with_a_dot(tmp_path):
    logs, inp = _run(tmp_path, "2", "Scan", "")
    assert any(line.startswith("1. Papers") for line in logs)
    assert any(line.startswith("2. Synopsis") for line in logs)


def test_no_question_keeps_old_header(tmp_path):
    logs, inp = _run(tmp_path, "Scan", "", kind="synopsis")
    assert any(line.startswith("2 files in") and
               "-> one record each + SYNOPSIS" in line for line in logs)
