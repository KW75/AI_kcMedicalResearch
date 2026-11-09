"""Not-pulled Ollama model: streaming and non-streaming give the same clear message.

Nothing here touches the real Ollama: urllib.request.urlopen is patched.
"""
import sys
import urllib.error
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "SOURCE_CODE"))

import providers  # noqa: E402
import streaming  # noqa: E402


def _http_error(code, reason):
    return urllib.error.HTTPError("http://localhost:11434/api/generate", code, reason, None, None)


def test_helper_names_the_model_and_the_pull_command():
    msg = providers.ollama_model_missing_message("qwen3:4b")
    assert "not installed yet" in msg
    assert "ollama pull qwen3:4b" in msg


def test_streaming_404_gives_the_same_message():
    with patch("urllib.request.urlopen", side_effect=_http_error(404, "Not Found")):
        with pytest.raises(RuntimeError) as err:
            list(streaming._stream_ollama("hi", model="qwen3:4b"))
    assert str(err.value) == providers.ollama_model_missing_message("qwen3:4b")


def test_streaming_other_http_errors_unchanged():
    with patch("urllib.request.urlopen", side_effect=_http_error(500, "Server Error")):
        with pytest.raises(RuntimeError) as err:
            list(streaming._stream_ollama("hi", model="qwen3:4b"))
    assert "Ollama streaming error 500" in str(err.value)
