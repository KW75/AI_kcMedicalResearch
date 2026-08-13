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
