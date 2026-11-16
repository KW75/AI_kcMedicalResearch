"""Session 43: the SR/OCR model picker waits safely.

Listing local vision models can take a while; an Enter pressed during the
wait used to answer 'Model number' and pick the default. The picker now
drops keys typed before the question, and SR prints a wait line first.
"""
from pathlib import Path

import pytest

import ollama_models as om

MODELS = [
    {"name": "gemma4:e4b", "size_gb": 6.6, "params_b": 7.5},
    {"name": "qwen2.5vl:7b", "size_gb": 6.0, "params_b": 7.0},
]
MAIN = Path(__file__).resolve().parents[1] / "SOURCE_CODE" / "main.py"


@pytest.fixture(autouse=True)
def no_env_model(monkeypatch):
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)


def _quiet(*a):
    return None


def _models():
    return [dict(m) for m in MODELS]


def test_keys_dropped_before_question():
    order = []

    def ask(prompt=""):
        order.append("ask")
        return "2"
    got = om.pick_vision_model(_models(), input_fn=ask, log=_quiet,
                               flush_fn=lambda: order.append("flush"))
    assert order == ["flush", "ask"]
    assert got == "qwen2.5vl:7b"


def test_flush_error_does_not_stop_picker():
    def boom():
        raise OSError("no console")
    got = om.pick_vision_model(_models(), input_fn=lambda p="": "", log=_quiet,
                               flush_fn=boom)
    assert got == "gemma4:e4b"


def test_default_flush_used(monkeypatch):
    seen = []
    monkeypatch.setattr(om, "flush_keyboard", lambda: seen.append(1))
    om.pick_vision_model(_models(), input_fn=lambda p="": "", log=_quiet)
    assert seen == [1]


def test_flush_keyboard_quiet_without_console():
    assert om.flush_keyboard() is None


def test_wait_hint_wording():
    h = om.VISION_WAIT_HINT
    assert "do not press Enter" in h
    assert h.isascii()


def test_sr_prints_wait_line_before_model_check():
    src = MAIN.read_text(encoding="utf-8")
    call = src.index("ollama_models.vision_models(list_fn, caps_fn)")
    hint = src.rfind("ollama_models.VISION_WAIT_HINT", 0, call)
    assert hint != -1
    assert "def " not in src[hint:call]
