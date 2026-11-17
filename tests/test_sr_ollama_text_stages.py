"""
Session 40, commit 3a (item 12): SR screening and RoB2 on local Ollama go
through providers.call_ollama_provider (native /api/generate, num_ctx from
OLLAMA_CONTEXT), not the OpenAI-style /v1 route, which sets no num_ctx and
can cut a long prompt silently. RoB2 reads OLLAMA_HOST like the rest of
the app (OLLAMA_URL is gone). call_ollama_provider is faked: no network.
"""
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "SOURCE_CODE"))

import openai  # noqa: E402
import providers  # noqa: E402
from pipelines.sr.src.screening import relevance_screener as rs  # noqa: E402
from pipelines.sr.src.screening import rob2_tool  # noqa: E402

GOOD_SCREEN = ('{"decision": "INCLUDE", "confidence": 0.9, "pico_match": {}, '
               '"exclusion_reasons": [], "rationale": "ok", "is_rct": true}')
EMPTY = "Ollama returned an empty response."


def _fake_ollama(monkeypatch, answers):
    """Replace call_ollama_provider; each answer is a string or an exception."""
    calls, answers = [], list(answers)

    def fake(prompt, model=None, max_tokens=8192, images=None):
        calls.append((prompt, {"model": model, "max_tokens": max_tokens,
                               "images": images}))
        a = answers.pop(0)
        if isinstance(a, Exception):
            raise a
        return a

    monkeypatch.setattr(providers, "call_ollama_provider", fake)
    return calls


class _NoV1Client:
    """Stands in for openai.OpenAI: any use means Ollama took the /v1 route."""
    def __init__(self, *a, **k):
        pass

    @property
    def chat(self):
        raise AssertionError("Ollama went through the OpenAI-style /v1 client")


# ---------- screening ----------

def _screen(tmp_path):
    fitz = pytest.importorskip("fitz")
    pdf = tmp_path / "trial.pdf"
    doc = fitz.open()
    doc.new_page().insert_text(
        (72, 72), "Randomised controlled trial of CBT versus usual care\n"
                  "in adults with fibromyalgia. Primary outcome: pain.")
    doc.save(str(pdf))
    doc.close()
    s = rs.RelevanceScreener(
        pico_criteria={"population": "adults with fibromyalgia",
                       "intervention": "CBT", "comparison": "usual care",
                       "outcome": "pain"},
        inclusion_criteria=["randomised controlled trial"],
        exclusion_criteria=["animal study"],
        model="gemma4:e4b", api_key="unused", provider="ollama")
    with patch("urllib.request.urlopen",
               side_effect=AssertionError("network call attempted")):
        return s.screen_by_pdf_path(str(pdf), "trial.pdf")


def test_screening_on_ollama_uses_call_ollama_provider(tmp_path, monkeypatch):
    calls = _fake_ollama(monkeypatch, [GOOD_SCREEN])
    result = _screen(tmp_path)
    assert result["error"] is None, result
    assert result["decision"] == "INCLUDE"
    assert len(calls) == 1
    prompt, kw = calls[0]
    assert "fibromyalgia" in prompt
    assert kw["model"] == "gemma4:e4b"
    assert kw["max_tokens"] == 1024
    assert kw["images"] is None


def test_screening_on_ollama_retries_a_failed_call(tmp_path, monkeypatch):
    monkeypatch.setattr(rs.time, "sleep", lambda s: None)
    calls = _fake_ollama(monkeypatch, [RuntimeError(EMPTY), GOOD_SCREEN])
    result = _screen(tmp_path)
    assert result["error"] is None, result
    assert result["decision"] == "INCLUDE"
    assert len(calls) == 2


# ---------- RoB2 ----------

def _rob2(monkeypatch):
    monkeypatch.setattr(openai, "OpenAI", _NoV1Client)
    monkeypatch.setattr(rob2_tool.time, "sleep", lambda s: None)
    return rob2_tool.RoB2Assessor(model="gemma4:e4b", provider="ollama")


def test_rob2_on_ollama_builds_no_v1_client(monkeypatch):
    assert _rob2(monkeypatch).client is None


def test_rob2_text_call_goes_to_ollama(monkeypatch):
    a = _rob2(monkeypatch)
    calls = _fake_ollama(monkeypatch, ['{"domains": {}}'])
    out = a._call_with_text("Methods: randomised by computer.", "RoB2 PROMPT")
    assert out == '{"domains": {}}'
    prompt, kw = calls[0]
    assert "RoB2 PROMPT" in prompt and "randomised by computer" in prompt
    assert kw["model"] == "gemma4:e4b"
    assert kw["max_tokens"] == 2048
    assert kw["images"] is None


def test_rob2_empty_answer_retries_with_shorter_text(monkeypatch):
    a = _rob2(monkeypatch)
    text = "#" * (rob2_tool.MAX_ROB2_CHARS + 4000)
    calls = _fake_ollama(monkeypatch, [RuntimeError(EMPTY), '{"ok": 1}'])
    assert a._call_with_text(text, "P") == '{"ok": 1}'
    assert len(calls) == 2
    assert calls[0][0].count("#") == len(text)
    assert calls[1][0].count("#") == rob2_tool.MAX_ROB2_CHARS


def test_rob2_two_empty_answers_raise_the_usual_error(monkeypatch):
    a = _rob2(monkeypatch)
    _fake_ollama(monkeypatch, [RuntimeError(EMPTY), RuntimeError(EMPTY)])
    with pytest.raises(ValueError, match="Empty response"):
        a._call_with_text("Methods.", "P")


def test_rob2_other_ollama_errors_are_not_retried(monkeypatch):
    a = _rob2(monkeypatch)
    calls = _fake_ollama(monkeypatch,
                         [RuntimeError("Cannot reach Ollama at localhost")])
    with pytest.raises(RuntimeError, match="Cannot reach"):
        a._call_with_text("Methods.", "P")
    assert len(calls) == 1


def test_rob2_image_call_refuses_ollama_clearly(monkeypatch):
    a = _rob2(monkeypatch)
    with pytest.raises(RuntimeError, match="(?i)ollama"):
        a._call_with_images(["aGk="], "P")


def test_rob2_reads_ollama_host_not_ollama_url(monkeypatch):
    monkeypatch.setenv("OLLAMA_HOST", "http://gpu-box:11434")
    monkeypatch.setenv("OLLAMA_URL", "http://wrong:1")
    _key, base = rob2_tool._openai_compat_creds("ollama")
    assert base == "http://gpu-box:11434/v1"
    src = Path(rob2_tool.__file__).read_text(encoding="utf-8")
    assert "OLLAMA_URL" not in src
