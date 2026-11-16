"""Session 42: qwen3-vl:30b-a3b-instruct is the default vision model for the
SR pipeline only. gemma4:e4b is too small for SR extraction (Karlsson: 3 of 4
means/SDs wrong, all runs agreeing); the instruct model read all six values
right, AI alone (run k20261116_070736).

SR: the SR model wins when pulled, even over OLLAMA_MODEL in .env; not pulled
-> old rule plus a too-small warning. OCR, text modes and .env unchanged.
"""
from __future__ import annotations

from pathlib import Path

import pytest

import main as M
import ollama_models as OM

SR = "qwen3-vl:30b-a3b-instruct"
GEMMA = {"name": "gemma4:e4b", "params_b": 7.5, "size_gb": 6.6}
QWEN = {"name": SR, "params_b": 31.1, "size_gb": 19.6}
OCR_CLI = Path(__file__).resolve().parents[1] / "SOURCE_CODE" / "pipelines" / "ocr" / "cli.py"


@pytest.fixture(autouse=True)
def _no_env_model(monkeypatch):
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)


def _list(models):
    return lambda host=None: [dict(m) for m in models]


def _caps(host=None, name=""):
    return {"completion", "vision"}


def _choose(models, answer="", model=""):
    logs = []
    got = M.sr_choose_ollama_model(model, list_fn=_list(models), caps_fn=_caps,
                                   input_fn=lambda prompt: answer, log=logs.append)
    return got, logs


def test_sr_constant_is_the_instruct_model():
    assert OM.SR_VISION_MODEL == SR


def test_default_without_preference_is_unchanged():
    assert OM.default_vision_model(["gemma4:e4b", SR]) == "gemma4:e4b"


def test_preferred_model_wins_when_pulled():
    assert OM.default_vision_model(["gemma4:e4b", SR], preferred=SR) == SR


def test_preferred_model_wins_over_env(monkeypatch):
    monkeypatch.setenv("OLLAMA_MODEL", "gemma4:e4b")
    assert OM.default_vision_model(["gemma4:e4b", SR], preferred=SR) == SR


def test_preferred_not_pulled_falls_back_to_old_rule():
    assert OM.default_vision_model(["gemma4:e4b"], preferred=SR) == "gemma4:e4b"


def test_sr_enter_takes_the_sr_model():
    got, _ = _choose([GEMMA, QWEN])
    assert got == SR


def test_sr_picker_marks_the_sr_model_default():
    _, logs = _choose([GEMMA, QWEN])
    assert any(SR in l and "(default)" in l for l in logs), logs
    assert not any("gemma4:e4b" in l and "(default)" in l for l in logs), logs


def test_sr_model_not_pulled_warns_too_small():
    got, logs = _choose([GEMMA])
    assert got == "gemma4:e4b"
    assert any("too small" in l and SR in l for l in logs), logs


def test_sr_model_pulled_gives_no_warning():
    _, logs = _choose([GEMMA, QWEN])
    assert not any("too small" in l for l in logs), logs


def test_sr_typed_model_kept_without_asking():
    def boom(prompt):
        raise AssertionError("asked although --model was typed")
    got = M.sr_choose_ollama_model("gemma4:e4b", list_fn=_list([GEMMA, QWEN]),
                                   caps_fn=_caps, input_fn=boom, log=print)
    assert got == "gemma4:e4b"


def test_ocr_default_is_still_gemma():
    logs = []
    got = OM.pick_vision_model([dict(GEMMA), dict(QWEN)], input_fn=lambda p: "",
                               log=logs.append)
    assert got == "gemma4:e4b"
    assert "SR_VISION_MODEL" not in OCR_CLI.read_text(encoding="utf-8")


def test_sr_vision_hint_names_the_sr_model():
    msg = OM.sr_vision_error("tiny:1b", caps_fn=lambda host, name: set())
    assert SR in msg
    assert "pull gemma4:e4b" not in msg
