"""Session 43: the launcher's INPUT FOLDER CHECK must not empty input/sr/.

A plain Enter at 'Keep them?' returned '' (safe_input uses its default only
on Ctrl+C / EOF), so the files were moved out - PDFs and the reviewer's
study_overrides.yaml with them. Now Enter keeps, only a typed N moves,
run settings never move, and keys typed during a wait are dropped first.
"""
import importlib.util
from pathlib import Path

import pytest

import ollama_models as om

ROOT = Path(__file__).resolve().parents[1]
SETTINGS = ("study_overrides.yaml", "prisma_criteria.yaml")


@pytest.fixture(scope="module")
def launcher():
    spec = importlib.util.spec_from_file_location("launcher_s43", ROOT / "scripts" / "launcher.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def folder(launcher, tmp_path, monkeypatch):
    inp = tmp_path / "input" / "sr"
    inp.mkdir(parents=True)
    (inp / "paper_text").mkdir()
    for name in ("a.pdf", "b.pdf") + SETTINGS:
        (inp / name).write_text("x", encoding="utf-8")
    dest = tmp_path / "moved"
    monkeypatch.setattr(launcher, "BASE", tmp_path)
    monkeypatch.setattr(launcher, "_find_move_destination", lambda mode: dest)
    monkeypatch.setattr(om, "flush_keyboard", lambda: None)
    return inp, dest


def _answer(launcher, monkeypatch, answer, asked=None):
    def fake(prompt, default=""):
        if asked is not None:
            asked.append(prompt)
        return default if answer is None else answer
    monkeypatch.setattr(launcher, "safe_input", fake)


def _names(p):
    return sorted(f.name for f in p.iterdir() if f.is_file()) if p.exists() else []


def test_enter_keeps_files(launcher, folder, monkeypatch):
    inp, dest = folder
    _answer(launcher, monkeypatch, "")
    launcher.check_input_folder("sr")
    assert _names(inp) == sorted(("a.pdf", "b.pdf") + SETTINGS)
    assert _names(dest) == []


def test_ctrl_c_keeps_files(launcher, folder, monkeypatch):
    inp, dest = folder
    _answer(launcher, monkeypatch, None)
    launcher.check_input_folder("sr")
    assert _names(dest) == []


def test_y_keeps_files(launcher, folder, monkeypatch):
    inp, dest = folder
    _answer(launcher, monkeypatch, "y")
    launcher.check_input_folder("sr")
    assert _names(dest) == []


def test_n_moves_papers_but_not_settings(launcher, folder, monkeypatch):
    inp, dest = folder
    _answer(launcher, monkeypatch, "n")
    launcher.check_input_folder("sr")
    assert _names(dest) == ["a.pdf", "b.pdf"]
    assert _names(inp) == sorted(SETTINGS)
    assert (inp / "paper_text").is_dir()


def test_settings_only_asks_nothing(launcher, folder, monkeypatch):
    inp, dest = folder
    (inp / "a.pdf").unlink()
    (inp / "b.pdf").unlink()
    asked = []
    _answer(launcher, monkeypatch, "n", asked)
    launcher.check_input_folder("sr")
    assert asked == []
    assert _names(inp) == sorted(SETTINGS)


def test_keys_dropped_before_question(launcher, folder, monkeypatch):
    order = []
    monkeypatch.setattr(om, "flush_keyboard", lambda: order.append("flush"))

    def fake(prompt, default=""):
        order.append("ask")
        return "y"
    monkeypatch.setattr(launcher, "safe_input", fake)
    launcher.check_input_folder("sr")
    assert order == ["flush", "ask"]
