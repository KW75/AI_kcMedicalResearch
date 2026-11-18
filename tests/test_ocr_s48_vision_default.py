"""Session 48: OCR prefers qwen3-vl:30b-a3b-instruct for reading images.

Test run (input/ocr: Ang PDF + 3 images): gemma4:e4b left most [?] on Ang,
lost table headers and misread values (IMG_1461 #8/#9 read 58.2/58; true
58.6/58.4). qwen3-vl filled every [?] on Ang correctly and read every
checked value right. Not pulled -> old rule plus a warning.
Text modes and .env keep OLLAMA_DEFAULT_MODEL (gemma4:e4b).
"""
from __future__ import annotations

from pathlib import Path

import pytest

import ollama_models as OM

try:
    from pipelines.ocr import cli as OCR
except ImportError:
    from SOURCE_CODE.pipelines.ocr import cli as OCR

QWEN_NAME = "qwen3-vl:30b-a3b-instruct"
GEMMA = {"name": "gemma4:e4b", "params_b": 7.5, "size_gb": 6.6}
QWEN = {"name": QWEN_NAME, "params_b": 31.1, "size_gb": 19.6}


@pytest.fixture(autouse=True)
def _no_env_model(monkeypatch):
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)


def _enter(prompt=""):
    return ""


def test_shared_vision_model_name():
    assert OM.VISION_MODEL == QWEN_NAME
    assert OM.SR_VISION_MODEL == OM.VISION_MODEL


def test_ocr_default_matches_shared_name():
    assert OCR.DEFAULT_VISION_MODEL == OM.VISION_MODEL


def test_text_default_unchanged():
    assert OM.OLLAMA_DEFAULT_MODEL == "gemma4:e4b"


def test_ocr_default_rule_prefers_qwen():
    assert OCR._default_model(["gemma4:e4b", QWEN_NAME]) == QWEN_NAME


def test_ocr_default_rule_falls_back_to_gemma():
    assert OCR._default_model(["gemma4:e4b"]) == "gemma4:e4b"


def test_ocr_pick_enter_takes_qwen_no_warning():
    logs = []
    got = OCR._pick_local_model([dict(GEMMA), dict(QWEN)], input_fn=_enter,
                                log=logs.append)
    assert got == QWEN_NAME
    assert not any("not pulled" in line for line in logs)


def test_ocr_pick_without_qwen_warns_and_uses_gemma():
    logs = []
    got = OCR._pick_local_model([dict(GEMMA)], input_fn=_enter, log=logs.append)
    assert got == "gemma4:e4b"
    assert any(QWEN_NAME in line and "not pulled" in line for line in logs)


def test_ocr_run_uses_the_helper():
    src = Path(OCR.__file__).read_text(encoding="utf-8")
    assert "_pick_local_model(models" in src
