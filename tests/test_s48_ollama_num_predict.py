"""Session 48: OLLAMA_NUM_PREDICT is read, as README and .env.example say.

Before: README.md, .env.example and flashcard-help.html list
OLLAMA_NUM_PREDICT=8192 and two error messages say to raise it, but no
code read it: call_ollama_provider used max_tokens=8192, streaming a
fixed 8192, and the OCR and menu 5 size checks a constant 8192. Now
calls without max_tokens send OLLAMA_NUM_PREDICT, and both size checks
use it. SR stages keep their fixed limits (1024 / 2048 / 4096).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "SOURCE_CODE"))

import providers  # noqa: E402
from pipelines.ocr import engine  # noqa: E402
import pipelines.rct_search.rct_search as rct  # noqa: E402


class _Resp:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return json.dumps({"response": "ok"}).encode()


def _capture(monkeypatch):
    sent = []

    def fake(req, timeout=None):
        sent.append(json.loads(req.data))
        return _Resp()
    monkeypatch.setattr(providers, "urlopen", fake, raising=False)
    monkeypatch.setattr("urllib.request.urlopen", fake)
    return sent


def test_helper_default(monkeypatch):
    monkeypatch.delenv("OLLAMA_NUM_PREDICT", raising=False)
    assert providers.ollama_num_predict() == 8192


def test_helper_reads_env(monkeypatch):
    monkeypatch.setenv("OLLAMA_NUM_PREDICT", "16000")
    assert providers.ollama_num_predict() == 16000


def test_call_without_max_tokens_sends_env(monkeypatch):
    monkeypatch.setenv("OLLAMA_NUM_PREDICT", "16000")
    sent = _capture(monkeypatch)
    assert providers.call_ollama_provider("hi", model="m") == "ok"
    assert sent[0]["options"]["num_predict"] == 16000


def test_explicit_max_tokens_wins(monkeypatch):
    monkeypatch.setenv("OLLAMA_NUM_PREDICT", "16000")
    sent = _capture(monkeypatch)
    providers.call_ollama_provider("hi", model="m", max_tokens=2048)
    assert sent[0]["options"]["num_predict"] == 2048


def test_streaming_reads_env():
    text = (ROOT / "SOURCE_CODE" / "streaming.py").read_text(encoding="utf-8")
    assert '"num_predict": 8192' not in text
    assert "OLLAMA_NUM_PREDICT" in text


def test_ocr_budget_follows_env(monkeypatch):
    monkeypatch.setenv("OLLAMA_CONTEXT", "32768")
    monkeypatch.setenv("OLLAMA_NUM_PREDICT", "16384")
    assert engine._budget_chars() == (32768 - 16384 - 1000) * 3


def test_rank_batches_follow_env(monkeypatch):
    monkeypatch.setenv("OLLAMA_CONTEXT", "32768")
    monkeypatch.setenv("OLLAMA_NUM_PREDICT", "4096")
    batches = rct._rank_batches(["z" * 10] * 300, 3000, "ollama")
    assert [len(b) for b in batches] == [54, 54, 54, 54, 54, 30]


def test_error_messages_name_the_limit():
    text = (ROOT / "SOURCE_CODE" / "providers.py").read_text(encoding="utf-8")
    assert text.count("SR stages use fixed") == 2
