"""Session 48: coding mode skips input files too large for local AI.

Ollama's window (OLLAMA_CONTEXT, 32,768 tokens) holds prompt + answer
(8,192-token reserve). Without a check, a long file pushes the
guidelines and instructions out of the prompt with no message.
"""
import inspect
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
    calls = []

    def fn(system_prompt, user_prompt):
        calls.append(user_prompt)
        return answer
    return fn, calls


def test_limit_value():
    assert c.CODING_LOCAL_MAX_CHARS == 40_000


@pytest.mark.parametrize("runner,tag,answer", [
    ("run_reviewer", "REVIEWER", "REVIEW_PASS"),
    ("run_tester", "TESTER", "TEST_PASS"),
])
def test_local_skips_long_file_runs_others(tmp_path, monkeypatch, capsys,
                                           runner, tag, answer):
    monkeypatch.setattr(c, "CODING_LOCAL_MAX_CHARS", 100)
    paths = _setup(tmp_path, {"big.py": "x" * 150, "small.py": "print(1)\n"})
    fn, calls = _fake(answer)
    with patch.object(c, "_paths", return_value=paths):
        getattr(c, runner)([], fn, verbose=False, local=True)
    out = capsys.readouterr().out
    assert len(calls) == 1
    assert ("big: 150 characters - too large for local AI "
            "(limit 100). Skipped.") in out
    names = [p.name for p in paths["reports"].iterdir()]
    assert any(n.startswith(f"{tag}_small_") for n in names)
    assert not any(n.startswith(f"{tag}_big_") for n in names)


def test_local_sends_file_at_limit(tmp_path, monkeypatch):
    monkeypatch.setattr(c, "CODING_LOCAL_MAX_CHARS", 100)
    paths = _setup(tmp_path, {"edge.py": "x" * 100})
    fn, calls = _fake("REVIEW_PASS")
    with patch.object(c, "_paths", return_value=paths):
        c.run_reviewer([], fn, verbose=False, local=True)
    assert len(calls) == 1


def test_default_cloud_sends_long_file(tmp_path, monkeypatch):
    monkeypatch.setattr(c, "CODING_LOCAL_MAX_CHARS", 100, raising=False)
    paths = _setup(tmp_path, {"big.py": "x" * 150})
    fn, calls = _fake("TEST_PASS")
    with patch.object(c, "_paths", return_value=paths):
        c.run_tester([], fn, verbose=False)
    assert len(calls) == 1


def test_default_is_not_local():
    for name in ("run_builder", "run_reviewer", "run_tester"):
        p = inspect.signature(getattr(c, name)).parameters.get("local")
        assert p is not None and p.default is False, name


def test_builder_local_skips_long_file(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(c, "CODING_LOCAL_MAX_CHARS", 100)
    paths = _setup(tmp_path, {"big.py": "x" * 150})
    fn, calls = _fake("REVIEW_PASS")
    with patch.object(c, "_paths", return_value=paths):
        c.run_builder([], fn, verbose=False, local=True)
    assert calls == []
    assert ("[BUILDER] big: 150 characters - too large for local AI"
            in capsys.readouterr().out)
    assert list(paths["output"].glob("BUILDER_big_*")) == []


def test_menu1_passes_local_flag():
    src = (ROOT / "SOURCE_CODE" / "main.py").read_text(encoding="utf-8")
    body = src.split("def handle_coding_mode(", 1)[1]
    body = body.split("def handle_appraisal_mode(", 1)[0]
    assert body.count('local=(provider == "ollama")') == 3
