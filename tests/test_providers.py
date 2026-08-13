"""
Tests for the extracted providers module.
Covers: validation, capabilities, fallback logic, Ollama detection.
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import json

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "SOURCE_CODE"))


class TestProviderValidation:
    """Test validate_provider() pre-flight checks."""

    def test_unknown_provider_fails(self):
        from providers import validate_provider
        valid, msg = validate_provider("nonexistent")
        assert not valid
        assert "Unknown provider" in msg

    def test_deepseek_without_key_fails(self):
        from providers import validate_provider
        with patch("providers.DEEPSEEK_API_KEY", ""):
            valid, msg = validate_provider("deepseek")
            assert not valid
            assert "DEEPSEEK_API_KEY" in msg

    def test_deepseek_with_key_passes(self):
        from providers import validate_provider
        with patch("providers.DEEPSEEK_API_KEY", "sk-test123"):
            valid, msg = validate_provider("deepseek")
            assert valid
            assert msg == ""

    def test_ollama_unreachable_fails(self):
        from providers import validate_provider
        with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
            valid, msg = validate_provider("ollama")
            assert not valid
            assert "not reachable" in msg


class TestProviderCapabilities:
    """Test capability queries."""

    def test_vision_providers(self):
        from providers import supports_vision
        assert supports_vision("qwen") is True
        assert supports_vision("openai") is True
        assert supports_vision("anthropic") is True
        assert supports_vision("deepseek") is False
        assert supports_vision("ollama") is False

    def test_unknown_provider_no_vision(self):
        from providers import supports_vision
        assert supports_vision("unknown_provider") is False

    def test_get_capabilities_returns_dict(self):
        from providers import get_provider_capabilities
        caps = get_provider_capabilities("deepseek")
        assert "vision" in caps
        assert "streaming" in caps
        assert "max_context" in caps


class TestOllamaAutoDetect:
    """Test Ollama model auto-detection."""

    def test_selects_largest_non_embedding(self):
        from providers import _ollama_detect_best_model
        mock_response = json.dumps({
            "models": [
                {"name": "qwen3.6:latest", "details": {"parameter_size": "36.0B"}},
                {"name": "llama3.2:latest", "details": {"parameter_size": "3.2B"}},
                {"name": "nomic-embed-text:latest", "details": {"parameter_size": "137M"}},
            ]
        }).encode()

        mock_resp = MagicMock()
        mock_resp.read.return_value = mock_response
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = _ollama_detect_best_model("http://localhost:11434")
        assert result == "qwen3.6:latest"

    def test_skips_embedding_models(self):
        from providers import _ollama_detect_best_model
        mock_response = json.dumps({
            "models": [
                {"name": "nomic-embed-text:latest", "details": {"parameter_size": "137M"}},
                {"name": "all-minilm:latest", "details": {"parameter_size": "33M"}},
                {"name": "llama3.2:latest", "details": {"parameter_size": "3.2B"}},
            ]
        }).encode()

        mock_resp = MagicMock()
        mock_resp.read.return_value = mock_response
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = _ollama_detect_best_model("http://localhost:11434")
        assert result == "llama3.2:latest"

    def test_empty_models_returns_default(self):
        from providers import _ollama_detect_best_model
        mock_response = json.dumps({"models": []}).encode()

        mock_resp = MagicMock()
        mock_resp.read.return_value = mock_response
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = _ollama_detect_best_model("http://localhost:11434")
        assert result == "llama3.2"

    def test_connection_failure_returns_default(self):
        from providers import _ollama_detect_best_model
        with patch("urllib.request.urlopen", side_effect=Exception("timeout")):
            result = _ollama_detect_best_model("http://localhost:11434")
        assert result == "llama3.2"


class TestFallbackChain:
    """Test call_ai_with_fallback logic."""

    def test_primary_succeeds_no_fallback(self):
        from providers import call_ai_with_fallback
        with patch("providers.call_ai", return_value="success"):
            result = call_ai_with_fallback("test prompt", provider="deepseek")
        assert result == "success"

    def test_transient_error_triggers_fallback(self):
        from providers import call_ai_with_fallback

        def mock_call_ai(prompt, provider=None, model=None):
            if provider == "deepseek":
                raise RuntimeError("connection timed out")
            return f"success from {provider}"

        with patch("providers.call_ai", side_effect=mock_call_ai):
            result = call_ai_with_fallback(
                "test", provider="deepseek",
                fallback_chain=["deepseek", "qwen", "groq"]
            )
        assert "success from qwen" in result

    def test_auth_error_does_not_trigger_fallback(self):
        from providers import call_ai_with_fallback

        def mock_call_ai(prompt, provider=None, model=None):
            raise RuntimeError("DEEPSEEK_API_KEY is not set. Add it to your .env file.")

        with patch("providers.call_ai", side_effect=mock_call_ai):
            with pytest.raises(RuntimeError, match="API_KEY"):
                call_ai_with_fallback("test", provider="deepseek")

    def test_all_providers_fail_raises(self):
        from providers import call_ai_with_fallback

        def mock_call_ai(prompt, provider=None, model=None):
            raise RuntimeError("connection timed out")

        with patch("providers.call_ai", side_effect=mock_call_ai):
            with pytest.raises(RuntimeError, match="All providers failed"):
                call_ai_with_fallback(
                    "test", provider="deepseek",
                    fallback_chain=["deepseek", "qwen"]
                )


class TestOllamaProbe:
    """Test ollama_probe_performance."""

    def test_successful_probe(self):
        from providers import ollama_probe_performance
        mock_response = json.dumps({
            "response": "1\n2\n3\n4\n5",
            "eval_count": 20,
            "eval_duration": 1_000_000_000,
        }).encode()

        mock_resp = MagicMock()
        mock_resp.read.return_value = mock_response
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = ollama_probe_performance("http://localhost:11434", "test-model")
        assert result["reachable"] is True
        assert result["tokens_per_second"] == 20.0

    def test_unreachable_probe(self):
        from providers import ollama_probe_performance
        with patch("urllib.request.urlopen", side_effect=Exception("refused")):
            result = ollama_probe_performance("http://localhost:11434", "test-model")
        assert result["reachable"] is False
        assert result["tokens_per_second"] == 0.0


class TestDefaultModel:
    """Test get_default_model."""

    def test_returns_configured_model(self):
        from providers import get_default_model
        model = get_default_model("deepseek")
        assert model != ""

    def test_unknown_provider_returns_empty(self):
        from providers import get_default_model
        assert get_default_model("nonexistent") == ""
