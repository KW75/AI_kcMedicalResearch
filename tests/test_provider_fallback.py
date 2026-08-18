"""
Regression tests for provider fallback behavior.

Known Issue #21 (CRITICAL, resolved v2.4.8): --provider ollama used to fall
back to a cloud provider on a timeout, silently sending confidential input
to a third party. Known Issue #26 notes that fix has no regression test.
These tests guard it directly, and also cover Known Issue #25 (an auth
error must never be misclassified as a transient/retryable error just
because its message contains a word like "connection").

Run with: python -m pytest test_provider_fallback.py -v
"""
import pytest

import providers


def test_ollama_never_falls_back_to_cloud(monkeypatch):
    """A failing Ollama call must raise, not silently retry a cloud provider."""
    cloud_calls = []

    def fake_ollama(prompt, model=None, **kwargs):
        raise RuntimeError("Ollama connection error: timed out")

    def make_fake_cloud(name):
        def _fn(prompt, model=None, **kwargs):
            cloud_calls.append(name)
            return f"[{name} response]"
        return _fn

    monkeypatch.setitem(providers.PROVIDERS, "ollama", fake_ollama)
    for name in ("deepseek", "qwen", "groq", "openai", "anthropic"):
        monkeypatch.setitem(providers.PROVIDERS, name, make_fake_cloud(name))

    with pytest.raises(RuntimeError, match="local-only provider"):
        providers.call_ai_with_fallback(
            "confidential patient data",
            provider="ollama",
            fallback_chain=["ollama", "deepseek", "qwen", "groq"],
        )

    assert cloud_calls == [], (
        f"Ollama failure must never reach a cloud provider, but these were "
        f"called: {cloud_calls}"
    )


def test_non_local_provider_still_falls_back(monkeypatch):
    """Sanity check: cloud providers should still use the fallback chain normally."""
    calls = []

    def fake_deepseek(prompt, model=None, **kwargs):
        calls.append("deepseek")
        raise RuntimeError("DeepSeek HTTP error 503: Service Unavailable")

    def fake_qwen(prompt, model=None, **kwargs):
        calls.append("qwen")
        return "[qwen response]"

    monkeypatch.setitem(providers.PROVIDERS, "deepseek", fake_deepseek)
    monkeypatch.setitem(providers.PROVIDERS, "qwen", fake_qwen)

    result = providers.call_ai_with_fallback(
        "hello",
        provider="deepseek",
        fallback_chain=["deepseek", "qwen"],
    )

    assert result == "[qwen response]"
    assert calls == ["deepseek", "qwen"]


def test_auth_error_never_falls_back_even_if_message_mentions_connection(monkeypatch):
    """A 401/403 must raise immediately, never treated as transient (#25)."""
    calls = []

    def fake_deepseek(prompt, model=None, **kwargs):
        calls.append("deepseek")
        # Deliberately includes the word "connection" in an auth error, the
        # exact scenario that used to be misclassified as transient.
        raise RuntimeError(
            "DeepSeek HTTP error 401: Unauthorized (connection refused by auth proxy)"
        )

    def fake_qwen(prompt, model=None, **kwargs):
        calls.append("qwen")
        return "[qwen response]"

    monkeypatch.setitem(providers.PROVIDERS, "deepseek", fake_deepseek)
    monkeypatch.setitem(providers.PROVIDERS, "qwen", fake_qwen)

    with pytest.raises(RuntimeError, match="401"):
        providers.call_ai_with_fallback(
            "hello",
            provider="deepseek",
            fallback_chain=["deepseek", "qwen"],
        )

    assert calls == ["deepseek"], (
        "Auth error must not trigger fallback, even though its message "
        "mentions 'connection'"
    )


def test_importing_providers_does_not_probe_ollama(monkeypatch):
    """Regression guard for #17/#6: import must not touch the network."""
    import importlib
    import urllib.request

    def _fail_if_called(*args, **kwargs):
        raise AssertionError(
            "urllib.request.urlopen was called during import/reload of "
            "providers.py - the Ollama probe must be lazy, not eager."
        )

    monkeypatch.setattr(urllib.request, "urlopen", _fail_if_called)
    importlib.reload(providers)  # will raise via the monkeypatch if it probes
