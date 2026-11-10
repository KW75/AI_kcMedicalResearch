"""
Session 24, #65: the SR CLI passed --model's None default through to every
stage, so Qwen failed on the first call. resolve_model must fall back to a
default and fail loudly when there isn't one.

Session 37: the fallback is the SR rule (providers.sr_default_model), not
the chat default. SR sends page images, so Qwen must get QWEN_VISION_MODEL,
not the text model QWEN_MODEL. Before the fix, a direct run of
`python -m SOURCE_CODE.pipelines.sr.main --provider qwen` without --model
sent page images to the text model. The launcher route was safe because
main.py always passes --model.
"""
import pytest

import providers
from pipelines.sr.main import resolve_model


def test_explicit_model_wins(monkeypatch):
    monkeypatch.setattr(providers, "QWEN_VISION_MODEL", "qwen-vl-from-env")
    assert resolve_model("qwen", "qwen-explicit") == "qwen-explicit"


def test_qwen_falls_back_to_vision_model_not_text_model(monkeypatch):
    monkeypatch.setattr(providers, "QWEN_MODEL", "qwen-text-model")
    monkeypatch.setattr(providers, "QWEN_VISION_MODEL", "qwen-vl-from-env")
    assert resolve_model("qwen", None) == "qwen-vl-from-env"
    assert resolve_model("qwen", "") == "qwen-vl-from-env"


def test_fails_loudly_when_no_vision_default(monkeypatch):
    monkeypatch.setattr(providers, "QWEN_MODEL", "qwen-text-model")
    monkeypatch.setattr(providers, "QWEN_VISION_MODEL", "")
    with pytest.raises(SystemExit, match="QWEN_VISION_MODEL"):
        resolve_model("qwen", None)


def test_other_cloud_provider_uses_its_model(monkeypatch):
    monkeypatch.setattr(providers, "OPENAI_MODEL", "openai-from-env")
    assert resolve_model("openai", None) == "openai-from-env"


def test_fails_loudly_names_the_provider_variable(monkeypatch):
    monkeypatch.setattr(providers, "OPENAI_MODEL", "")
    with pytest.raises(SystemExit, match="OPENAI_MODEL"):
        resolve_model("openai", None)


def test_ollama_unset_uses_the_default_model(monkeypatch):
    """Session 33 rule: OLLAMA_MODEL unset -> OLLAMA_DEFAULT_MODEL (gemma4:e4b).

    The old '(auto-detected on first use)' placeholder is gone, so Ollama
    always has a real model name and resolve_model never stops for it.
    """
    monkeypatch.setattr(providers, "OLLAMA_MODEL", "")
    assert resolve_model("ollama", None) == providers.OLLAMA_DEFAULT_MODEL


def test_ollama_env_model_wins_over_default(monkeypatch):
    monkeypatch.setattr(providers, "OLLAMA_MODEL", "qwen3:8b")
    assert resolve_model("ollama", None) == "qwen3:8b"
