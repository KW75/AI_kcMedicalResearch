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


def test_ollama_placeholder_is_not_a_model(monkeypatch):
    monkeypatch.setattr(providers, "OLLAMA_MODEL", "")
    with pytest.raises(SystemExit, match="OLLAMA_MODEL"):
        resolve_model("ollama", None)