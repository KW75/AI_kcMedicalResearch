"""
Session 24, #65: the SR CLI passed --model's None default through to every
stage, so Qwen failed on the first call. resolve_model must fall back to
the provider's configured default and fail loudly when there isn't one.
"""
import pytest

import providers
from pipelines.sr.main import resolve_model


def test_explicit_model_wins(monkeypatch):
    monkeypatch.setattr(providers, "QWEN_MODEL", "qwen-from-env")
    assert resolve_model("qwen", "qwen-explicit") == "qwen-explicit"


def test_falls_back_to_provider_default(monkeypatch):
    monkeypatch.setattr(providers, "QWEN_MODEL", "qwen-from-env")
    assert resolve_model("qwen", None) == "qwen-from-env"
    assert resolve_model("qwen", "") == "qwen-from-env"


def test_fails_loudly_when_no_default(monkeypatch):
    monkeypatch.setattr(providers, "QWEN_MODEL", "")
    with pytest.raises(SystemExit, match="QWEN_MODEL"):
        resolve_model("qwen", None)


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
