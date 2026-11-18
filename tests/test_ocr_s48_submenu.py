"""Session 48: OCR submenu when input/ocr holds several files (menu 8).

1 Papers   - each file is its own paper: run_single per file, header = the
             file's name; own record + own SUMMARY; no SYNOPSIS, no title.
2 Synopsis - one record each + one SYNOPSIS summarising all papers (as before).
Enter / no keyboard = Synopsis; bad answer = job not run; one file = no
question. run() default kind="synopsis" (old tests unchanged); main.py
passes kind="ask".
"""
from pathlib import Path

import pytest

import main
from pipelines.ocr import cli

PULLED = [{"name": "gemma4:e4b", "size_gb": 6.6, "params_b": 7.5}]


@pytest.fixture(autouse=True)
def _no_env_model(monkeypatch):
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)


def fake_list(host=None):
    return [dict(m) for m in PULLED]


def fake_caps(host, name):
    return {"completion", "vision"}


class FakeEngine:
    def __init__(self):
        self.calls = []

    def single(self, path, out_dir, name, model, log=print, records_root=None):
        self.calls.append(("single", path.name, name))
        return {"header": name, "records": [path.name], "failed": [], "summary": None}

    def set(self, folder, out_dir, name, model, log=print, records_root=None):
        self.calls.append(("set", None, name))
        return {"header": "H", "records": [], "failed": [], "summary": None}


def _answers(*items, asked):
    it = iter(items)

    def _input(prompt=""):
        asked.append(prompt)
        return next(it)
    return _input


def _base(tmp_path, files):
    inp = tmp_path / "input" / "ocr"
    inp.mkdir(parents=True)
    for f in files:
        (inp / f).write_bytes(b"x")
    return tmp_path


def _run(tmp_path, *answers, files=("a.pdf", "b.png"), kind="ask"):
    eng, asked, logs = FakeEngine(), [], []
    kw = {} if kind is None else {"kind": kind}
    result = cli.run(_base(tmp_path, files), input_fn=_answers(*answers, asked=asked),
                     list_fn=fake_list, caps_fn=fake_caps, run_single=eng.single,
                     run_set=eng.set, log=logs.append, **kw)
    return result, eng, asked, logs


def test_default_kind_is_synopsis_without_question(tmp_path):
    result, eng, asked, _ = _run(tmp_path, "Scan", "", kind=None)
    assert eng.calls == [("set", None, "Scan")]
    assert not any("Synopsis" in p for p in asked)


def test_papers_runs_single_per_file_with_file_name(tmp_path):
    result, eng, asked, _ = _run(tmp_path, "1", "")
    assert sorted(eng.calls) == [("single", "a.pdf", "a"), ("single", "b.png", "b")]


def test_papers_skips_the_scan_title_question(tmp_path):
    result, eng, asked, _ = _run(tmp_path, "1", "")
    assert not any("Scan title" in p for p in asked)


def test_papers_result_lists_every_record(tmp_path):
    result, eng, asked, _ = _run(tmp_path, "1", "")
    assert sorted(result["records"]) == ["a.pdf", "b.png"]


def test_answer_2_is_synopsis(tmp_path):
    result, eng, asked, _ = _run(tmp_path, "2", "Scan", "")
    assert eng.calls == [("set", None, "Scan")]


def test_enter_is_synopsis(tmp_path):
    result, eng, asked, _ = _run(tmp_path, "", "Scan", "")
    assert eng.calls == [("set", None, "Scan")]


def test_no_keyboard_is_synopsis(tmp_path):
    eng, state = FakeEngine(), {"n": 0}

    def _input(prompt=""):
        state["n"] += 1
        if state["n"] == 1:
            raise EOFError
        return ""
    cli.run(_base(tmp_path, ("a.pdf", "b.png")), input_fn=_input, list_fn=fake_list,
            caps_fn=fake_caps, run_single=eng.single, run_set=eng.set,
            log=lambda *a: None, kind="ask")
    assert [c[0] for c in eng.calls] == ["set"]


def test_bad_answer_does_not_run(tmp_path):
    result, eng, asked, _ = _run(tmp_path, "9")
    assert result is None
    assert eng.calls == []


def test_one_file_asks_no_kind_question(tmp_path):
    result, eng, asked, _ = _run(tmp_path, "Scan", "", files=("a.pdf",))
    assert eng.calls == [("single", "a.pdf", "Scan")]
    assert not any("Synopsis" in p for p in asked)


def test_menu_says_synopsis_summarises_all_papers(tmp_path):
    result, eng, asked, logs = _run(tmp_path, "2", "Scan", "")
    assert any("Papers" in line and "SUMMARY" in line for line in logs)
    assert any("summarising all papers" in line for line in logs)


def test_main_menu_8_asks():
    src = Path(main.__file__).read_text(encoding="utf-8")
    assert 'kind="ask"' in src
