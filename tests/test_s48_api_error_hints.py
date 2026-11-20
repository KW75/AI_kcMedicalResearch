"""Session 48: API errors show the provider reply and a hint.

A DeepSeek 400 took long to diagnose because the app printed only
"HTTP error 400: Bad Request"; the reply named the valid models.
providers.api_error_message keeps that first part, adds the reply and
a hint, and _is_transient_error ignores the added text, so fallback
behaviour is unchanged.
"""
import io
import urllib.error
from pathlib import Path

import pytest

import providers as p

ROOT = Path(__file__).resolve().parent.parent
CLOSING = "Update the LLM to the latest model"
TOKENS = "enough tokens"


def _err(code, body=b"", reason="Bad Request"):
    return urllib.error.HTTPError("https://x.test", code, reason, {}, io.BytesIO(body))


def _read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def test_message_keeps_first_part_and_adds_reply():
    msg = p.api_error_message("DeepSeek HTTP error", _err(
        400, b'{"error": {"message": "The supported API model names are deepseek-flash"}}'))
    assert msg.startswith("DeepSeek HTTP error 400: Bad Request")
    assert "The supported API model names are deepseek-flash" in msg
    assert CLOSING in msg and TOKENS in msg


def test_hint_depends_on_status_code():
    def m(code):
        return p.api_error_message("X HTTP error", _err(code, b"{}")).lower()
    assert "model name" in m(400)
    assert "model name" in m(404)
    assert "api key" in m(401)
    assert "api key" in m(403)
    assert "credit" in m(402)
    assert "credit" in m(429)
    assert "try again later" in m(503)


def test_long_reply_is_cut_to_one_line():
    msg = p.api_error_message("X HTTP error", _err(400, b"line1\nline2 " + b"a" * 1000))
    reply = msg.split("Server reply: ", 1)[1].split("\n", 1)[0]
    assert reply.startswith("line1 line2")
    assert len(reply) <= 300


def test_unreadable_reply_still_gives_message():
    class Broken(urllib.error.HTTPError):
        def read(self, *a):
            raise OSError("gone")
    exc = Broken("https://x.test", 500, "Server Error", {}, io.BytesIO(b""))
    msg = p.api_error_message("X HTTP error", exc)
    assert msg.startswith("X HTTP error 500: Server Error")
    assert CLOSING in msg


def test_reply_text_does_not_change_fallback():
    exc = RuntimeError(p.api_error_message(
        "DeepSeek HTTP error", _err(400, b"rate limit timeout timed out connection error")))
    assert p._is_transient_error(exc) is False


def test_transient_codes_still_fall_back():
    for code in (429, 503):
        exc = RuntimeError(p.api_error_message("DeepSeek HTTP error", _err(code, b"{}")))
        assert p._is_transient_error(exc) is True


def test_auth_errors_never_fall_back():
    exc = RuntimeError(p.api_error_message(
        "DeepSeek HTTP error", _err(401, b"connection error timeout")))
    assert p._is_transient_error(exc) is False


def test_deepseek_call_shows_server_reply(monkeypatch):
    def fake_urlopen(req, timeout=None):
        raise _err(400, b'{"error": {"message": "Model Not Exist"}}')
    monkeypatch.setattr(p, "DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setattr(p, "urlopen", fake_urlopen)
    with pytest.raises(RuntimeError) as err:
        p.call_deepseek_provider("hi")
    text = str(err.value)
    assert text.startswith("DeepSeek HTTP error 400: Bad Request")
    assert "Model Not Exist" in text and CLOSING in text


def test_no_bare_http_error_messages_left():
    pat = "{exc.code}: {exc.reason}"
    assert _read("SOURCE_CODE/providers.py").count(pat) == 1  # only in api_error_message
    assert pat not in _read("SOURCE_CODE/streaming.py")


def test_docs_carry_the_hint_wording():
    for rel in ("README.md", "Readme/Setup_Instructions_for_Users.txt"):
        text = _read(rel)
        assert CLOSING in text, rel
        assert TOKENS in text, rel


def test_env_example_explains_model_names():
    text = _read(".env.example")
    assert "copy the *_MODEL lines" in text
    assert "overrides the value in this file" in text
    assert "deepseek-flash, deepseek-v4-pro" in text
    assert "newest build" in text


def test_old_opus_name_gone():
    for rel in ("SOURCE_CODE/pipelines/sr/config/config.yaml",
                "SOURCE_CODE/pipelines/sr/src/screening/relevance_screener.py",
                "SOURCE_CODE/pipelines/sr/src/reporting/html_report.py",
                "SOURCE_CODE/pipelines/sr/src/reporting/pdf_report.py",
                "README.md"):
        assert "claude-opus-4" + "-7" not in _read(rel), rel
