"""
Tests for streaming.py module.
Tests SSE parsing, provider dispatch, fallback on error, and tee_stream.
"""

import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import BytesIO

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "SOURCE_CODE"))


class TestSSEParser:
    """Test _parse_sse_lines."""

    def test_parses_openai_format(self):
        from streaming import _parse_sse_lines
        lines = [
            b'data: {"choices":[{"delta":{"content":"Hello"}}]}\n',
            b'data: {"choices":[{"delta":{"content":" world"}}]}\n',
            b'data: [DONE]\n',
        ]
        result = list(_parse_sse_lines(iter(lines)))
        assert result == ["Hello", " world"]

    def test_skips_empty_lines(self):
        from streaming import _parse_sse_lines
        lines = [
            b'\n',
            b'data: {"choices":[{"delta":{"content":"Hi"}}]}\n',
            b'\n',
            b'data: [DONE]\n',
        ]
        result = list(_parse_sse_lines(iter(lines)))
        assert result == ["Hi"]

    def test_skips_malformed_json(self):
        from streaming import _parse_sse_lines
        lines = [
            b'data: not json\n',
            b'data: {"choices":[{"delta":{"content":"ok"}}]}\n',
            b'data: [DONE]\n',
        ]
        result = list(_parse_sse_lines(iter(lines)))
        assert result == ["ok"]

    def test_skips_empty_content(self):
        from streaming import _parse_sse_lines
        lines = [
            b'data: {"choices":[{"delta":{"role":"assistant"}}]}\n',
            b'data: {"choices":[{"delta":{"content":""}}]}\n',
            b'data: {"choices":[{"delta":{"content":"text"}}]}\n',
            b'data: [DONE]\n',
        ]
        result = list(_parse_sse_lines(iter(lines)))
        assert result == ["text"]


class TestStreamAI:
    """Test stream_ai dispatcher."""

    def test_unknown_provider_raises(self):
        from streaming import stream_ai
        with pytest.raises(RuntimeError, match="Unknown streaming provider"):
            list(stream_ai("test", provider="nonexistent"))

    def test_missing_api_key_raises(self):
        from streaming import stream_ai
        with patch("streaming.DEEPSEEK_API_KEY", ""):
            with pytest.raises(RuntimeError, match="DEEPSEEK_API_KEY"):
                list(stream_ai("test", provider="deepseek"))

    def test_ollama_streaming_format(self):
        from streaming import _stream_ollama
        lines = [
            json.dumps({"response": "Hello"}).encode() + b'\n',
            json.dumps({"response": " there"}).encode() + b'\n',
            json.dumps({"response": "", "done": True}).encode() + b'\n',
        ]
        mock_resp = MagicMock()
        mock_resp.__iter__ = lambda self: iter(lines)
        mock_resp.close = MagicMock()

        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = list(_stream_ollama("test", model="test-model"))
        assert result == ["Hello", " there"]


class TestStreamToConsole:
    """Test stream_to_console convenience function."""

    def test_returns_full_text(self):
        from streaming import stream_to_console

        def mock_stream_ai(prompt, provider=None, model=None):
            yield "Hello"
            yield " world"

        with patch("streaming.stream_ai", side_effect=mock_stream_ai):
            result = stream_to_console("test", provider="deepseek")
        assert result == "Hello world"

    def test_fallback_on_streaming_failure(self):
        from streaming import stream_to_console

        def mock_stream_ai(prompt, provider=None, model=None):
            raise RuntimeError("connection timed out")
            yield  # make it a generator

        with patch("streaming.stream_ai", side_effect=mock_stream_ai):
            with patch("providers.call_ai", return_value="fallback response"):
                result = stream_to_console("test", provider="deepseek")
        assert result == "fallback response"


class TestTeeStream:
    """Test tee_stream with custom display function."""

    def test_calls_display_fn_for_each_chunk(self):
        from streaming import tee_stream
        displayed = []

        def mock_stream_ai(prompt, provider=None, model=None):
            yield "A"
            yield "B"
            yield "C"

        with patch("streaming.stream_ai", side_effect=mock_stream_ai):
            result = tee_stream("test", display_fn=lambda c: displayed.append(c))

        assert result == "ABC"
        assert displayed == ["A", "B", "C"]


def test_ollama_streaming_sends_think_false():
    """Streaming must send think=False too: while a model thinks, Ollama
    leaves `response` empty, so the user would see nothing until it finishes."""
    from streaming import _stream_ollama
    sent = {}
    lines = [json.dumps({"response": "42", "done": True}).encode() + b"\n"]
    mock_resp = MagicMock()
    mock_resp.__iter__ = lambda self: iter(lines)
    mock_resp.close = MagicMock()

    def fake_urlopen(req, timeout=0):
        sent["body"] = json.loads(req.data)
        return mock_resp

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        assert list(_stream_ollama("hi", model="qwen3:8b")) == ["42"]
    assert sent["body"].get("think") is False


def _run_stream_ollama_capturing_body(**kwargs):
    """Call _stream_ollama with urlopen patched; return the JSON body sent."""
    from streaming import _stream_ollama
    sent = {}
    lines = [json.dumps({"response": "ok", "done": True}).encode() + b"\n"]
    mock_resp = MagicMock()
    mock_resp.__iter__ = lambda self: iter(lines)
    mock_resp.close = MagicMock()

    def fake_urlopen(req, timeout=0):
        sent["body"] = json.loads(req.data)
        return mock_resp

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        assert list(_stream_ollama("hi", **kwargs)) == ["ok"]
    return sent["body"]


def test_ollama_streaming_resolves_model_when_none_configured(monkeypatch):
    """With no --model and no OLLAMA_MODEL in .env, streaming must use the
    same resolver as the batch route, not send an empty model name."""
    import providers
    import streaming
    detect_calls = []

    def fake_detect(*args, **kwargs):
        detect_calls.append(args)
        return "sentinel-model:1b"

    monkeypatch.setattr(providers, "OLLAMA_MODEL", "")
    monkeypatch.setattr(streaming, "OLLAMA_MODEL", "")
    monkeypatch.setattr(providers, "_OLLAMA_MODEL_RESOLVED", None)
    monkeypatch.setattr(providers, "_ollama_detect_best_model", fake_detect)

    body = _run_stream_ollama_capturing_body()
    assert body["model"] == "sentinel-model:1b"
    assert len(detect_calls) == 1


def test_ollama_streaming_explicit_model_wins(monkeypatch):
    """An explicit model (from --model or the pickers) is sent as-is and
    the detector is never called."""
    import providers
    import streaming

    def fail_detect(*args, **kwargs):
        raise AssertionError("detector must not run when a model is given")

    monkeypatch.setattr(providers, "OLLAMA_MODEL", "")
    monkeypatch.setattr(streaming, "OLLAMA_MODEL", "")
    monkeypatch.setattr(providers, "_OLLAMA_MODEL_RESOLVED", None)
    monkeypatch.setattr(providers, "_ollama_detect_best_model", fail_detect)

    body = _run_stream_ollama_capturing_body(model="gemma4:e4b")
    assert body["model"] == "gemma4:e4b"
