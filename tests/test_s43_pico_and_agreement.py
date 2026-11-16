"""Session 43: PICO files are run settings; [AGREEMENT] names too_few_runs right.

Run 20261116_181723 listed pico_20261112_210735.json with the papers, so a
typed N would have moved it out. The [AGREEMENT] header said too_few_runs
means 'the runs read different table cells'; it means too few runs gave
usable numbers.
"""
import importlib.util
from pathlib import Path

import pytest

import ollama_models as om

ROOT = Path(__file__).resolve().parents[1]
PICO = "pico_20261112_210735.json"


@pytest.fixture(scope="module")
def launcher():
    spec = importlib.util.spec_from_file_location("launcher_s43b", ROOT / "scripts" / "launcher.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def folder(launcher, tmp_path, monkeypatch):
    inp = tmp_path / "input" / "sr"
    inp.mkdir(parents=True)
    dest = tmp_path / "moved"
    monkeypatch.setattr(launcher, "BASE", tmp_path)
    monkeypatch.setattr(launcher, "_find_move_destination", lambda mode: dest)
    monkeypatch.setattr(om, "flush_keyboard", lambda: None)
    return inp, dest


def _answer(launcher, monkeypatch, answer, asked):
    def fake(prompt, default=""):
        asked.append(prompt)
        return answer
    monkeypatch.setattr(launcher, "safe_input", fake)


def _names(p):
    return sorted(f.name for f in p.iterdir() if f.is_file()) if p.exists() else []


def _make(inp, *names):
    for n in names:
        (inp / n).write_text("x", encoding="utf-8")


def test_n_keeps_pico(launcher, folder, monkeypatch):
    inp, dest = folder
    _make(inp, "a.pdf", PICO, "study_overrides.yaml")
    _answer(launcher, monkeypatch, "n", [])
    launcher.check_input_folder("sr")
    assert _names(dest) == ["a.pdf"]
    assert _names(inp) == sorted([PICO, "study_overrides.yaml"])


def test_pico_and_settings_only_asks_nothing(launcher, folder, monkeypatch):
    inp, dest = folder
    _make(inp, PICO, "study_overrides.yaml", "prisma_criteria.yaml")
    asked = []
    _answer(launcher, monkeypatch, "n", asked)
    launcher.check_input_folder("sr")
    assert asked == []
    assert _names(dest) == []


def test_other_json_still_moves(launcher, folder, monkeypatch):
    inp, dest = folder
    _make(inp, "a.pdf", "data.json")
    _answer(launcher, monkeypatch, "n", [])
    launcher.check_input_folder("sr")
    assert _names(dest) == ["a.pdf", "data.json"]


def test_agreement_header_names_too_few_runs_right():
    src = (ROOT / "SOURCE_CODE" / "pipelines" / "sr" / "main.py").read_text(encoding="utf-8")
    assert "too_few_runs = too few runs gave usable numbers" in src
    assert "mixed_runs/too_few_runs = the runs read different" not in src
