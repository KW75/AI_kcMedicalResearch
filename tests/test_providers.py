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


class TestOllamaModelRule:
    """Session 33: OLLAMA_MODEL from .env if set, otherwise gemma4:e4b.
    No auto-detect, no network probe, no silent switch to another model."""

    def test_env_model_wins(self, monkeypatch):
        import providers
        monkeypatch.setattr(providers, "OLLAMA_MODEL", "qwen3:8b")
        assert providers._resolve_ollama_model() == "qwen3:8b"

    def test_unset_uses_default(self, monkeypatch):
        import providers
        monkeypatch.setattr(providers, "OLLAMA_MODEL", "")
        assert providers._resolve_ollama_model() == "gemma4:e4b"

    def test_resolving_never_contacts_ollama(self, monkeypatch):
        import providers
        calls = []

        def fake_urlopen(*args, **kwargs):
            calls.append(args)
            raise OSError("refused")

        monkeypatch.setattr(providers, "OLLAMA_MODEL", "")
        monkeypatch.setattr(providers, "_OLLAMA_MODEL_RESOLVED", None, raising=False)
        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            assert providers._resolve_ollama_model() == providers.OLLAMA_DEFAULT_MODEL
        assert calls == []

    def test_auto_detect_is_gone(self):
        import providers
        assert not hasattr(providers, "_ollama_detect_best_model")
        assert not hasattr(providers, "_OLLAMA_MODEL_RESOLVED")
        src = (Path(__file__).resolve().parent.parent
               / "SOURCE_CODE" / "providers.py").read_text(encoding="utf-8")
        assert "_ollama_detect_best_model" not in src
        assert "Auto-detected" not in src

    def test_get_default_model_shows_the_real_model(self, monkeypatch):
        import providers
        monkeypatch.setattr(providers, "OLLAMA_MODEL", "")
        assert providers.get_default_model("ollama") == "gemma4:e4b"
        monkeypatch.setattr(providers, "OLLAMA_MODEL", "qwen3:8b")
        assert providers.get_default_model("ollama") == "qwen3:8b"

    def test_docs_name_the_same_default_model_as_code(self):
        """README and .env.example must recommend the model the code falls back to.

        Session 28 changed the docs to qwen2.5 while the code still fell back
        to llama3.2, and nothing caught it. Every uncommented OLLAMA_MODEL=
        line in both files must match OLLAMA_DEFAULT_MODEL. Each file must
        contain at least one such line, so the test can't pass on nothing.
        """
        import re
        from providers import OLLAMA_DEFAULT_MODEL

        root = Path(__file__).resolve().parent.parent
        pattern = re.compile(r"^\s*OLLAMA_MODEL=(\S+)", re.MULTILINE)

        for name in ("README.md", ".env.example"):
            text = (root / name).read_text(encoding="utf-8")
            found = pattern.findall(text)
            assert found, f"{name}: no uncommented OLLAMA_MODEL= line found"
            for value in found:
                assert value == OLLAMA_DEFAULT_MODEL, (
                    f"{name} says OLLAMA_MODEL={value}, "
                    f"but providers.OLLAMA_DEFAULT_MODEL is {OLLAMA_DEFAULT_MODEL}"
                )


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


def test_ollama_404_tells_user_to_pull_model(monkeypatch):
    """A 404 from Ollama (model not pulled yet) must produce an actionable
    'ollama pull <model>' message, not the raw 'HTTP error 404: Not Found'
    that a non-technical user cannot act on. Runs without a live server."""
    import urllib.error
    import providers

    def fake_urlopen(req, timeout=0):
        raise urllib.error.HTTPError(
            url="http://localhost:11434/api/generate",
            code=404, msg="Not Found", hdrs=None, fp=None,
        )

    monkeypatch.setattr(providers, "urlopen", fake_urlopen)

    with pytest.raises(RuntimeError) as exc:
        providers.call_ollama_provider("hello", model="qwen2.5:14b-instruct")

    message = str(exc.value)
    assert "ollama pull qwen2.5:14b-instruct" in message
    assert "not installed" in message.lower()

class TestLocalFirstDefault:
    """Local-first: with no DEFAULT_PROVIDER in .env, input must stay local."""

    def test_code_default_provider_is_local_only(self):
        from providers import CODE_DEFAULT_PROVIDER, LOCAL_ONLY_PROVIDERS
        assert CODE_DEFAULT_PROVIDER in LOCAL_ONLY_PROVIDERS, (
            f"CODE_DEFAULT_PROVIDER={CODE_DEFAULT_PROVIDER} sends input off this "
            f"machine when .env sets no provider"
        )

    def test_docs_name_the_same_default_provider_as_code(self):
        """README and .env.example must show the default the code uses."""
        import re
        from providers import CODE_DEFAULT_PROVIDER

        root = Path(__file__).resolve().parent.parent
        pattern = re.compile(r"^\s*DEFAULT_PROVIDER=(\S+)", re.MULTILINE)

        for name in ("README.md", ".env.example"):
            text = (root / name).read_text(encoding="utf-8")
            found = pattern.findall(text)
            assert found, f"{name}: no uncommented DEFAULT_PROVIDER= line found"
            for value in found:
                assert value == CODE_DEFAULT_PROVIDER, (
                    f"{name} says DEFAULT_PROVIDER={value}, "
                    f"but providers.CODE_DEFAULT_PROVIDER is {CODE_DEFAULT_PROVIDER}"
                )

class TestOllamaThinkOff:
    """Every Ollama request must send think=False.

    qwen3 and gemma4 think by default (`ollama show`: thinking default true).
    Measured Session 30 on Ollama 0.40.8: qwen3:8b used 229 tokens with no
    think field and 3 with think=False, same answer. qwen2.5 (no thinking
    support) accepts think=False without error, so it is safe on every call.
    """

    @staticmethod
    def _fake_resp(body):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(body).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    def test_call_ollama_provider_sends_think_false(self, monkeypatch):
        import providers
        sent = {}

        def fake_urlopen(req, timeout=0):
            sent["body"] = json.loads(req.data)
            return self._fake_resp({"response": "42"})

        monkeypatch.setattr(providers, "urlopen", fake_urlopen)
        assert providers.call_ollama_provider("hi", model="qwen3:8b") == "42"
        assert sent["body"].get("think") is False

    def test_probe_sends_think_false(self):
        import providers
        sent = []

        def fake_urlopen(req, timeout=0):
            if req.data is not None:  # POST /api/generate
                sent.append(json.loads(req.data))
                return self._fake_resp(
                    {"response": "1", "eval_count": 3, "eval_duration": 1_000_000}
                )
            return self._fake_resp({"models": []})  # GET /api/tags (model size)

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            result = providers.ollama_probe_performance(
                host="http://localhost:11434", model="qwen3:8b"
            )
        # The probe swallows exceptions; reachable=True proves the mock was hit.
        assert result["reachable"] is True
        assert sent and sent[0].get("think") is False

