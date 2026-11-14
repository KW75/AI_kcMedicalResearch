"""Session 37: screening and RoB2 read ONE shared text per paper
(paper_text.get_paper_text, saved under input/sr/paper_text/) instead of each
running its own pdfplumber/Tesseract pass. When a record carries
"paper_text", neither stage may open the PDF itself. The Anthropic file_id
path is unchanged."""
import json
import sys
import types
from pathlib import Path

import pytest

from pipelines.sr.src.screening.relevance_screener import RelevanceScreener
from pipelines.sr.src.screening.rob2_tool import RoB2Assessor

MARK = "SHARED-PAPER-TEXT-MARKER [?] p 12"
MAIN = Path(__file__).resolve().parents[1] / "SOURCE_CODE" / "pipelines" / "sr" / "main.py"


@pytest.fixture
def pdf_readers_forbidden(monkeypatch):
    """Fake pdfplumber / fitz / pytesseract that record any use."""
    used = []
    for name in ("pdfplumber", "fitz", "pytesseract"):
        mod = types.ModuleType(name)
        mod.open = lambda *a, _n=name, **k: used.append(_n) or (_ for _ in ()).throw(
            RuntimeError(f"{_n} must not be used"))
        mod.image_to_string = lambda *a, **k: used.append("pytesseract") or ""
        mod.Matrix = lambda *a, **k: None
        monkeypatch.setitem(sys.modules, name, mod)
    monkeypatch.setattr("time.sleep", lambda _s: None)
    return used


class _Resp:
    status = 200
    def __init__(self, body): self._b = body
    def read(self): return self._b
    def getcode(self): return 200
    def __enter__(self): return self
    def __exit__(self, *a): return False


def _ok():
    verdict = {"decision": "INCLUDE", "confidence": 0.9, "is_rct": True,
               "pico_match": {}, "rationale": "ok", "exclusion_reasons": []}
    return json.dumps({"choices": [{"message": {"content": json.dumps(verdict)}}]}).encode()


@pytest.fixture
def screener(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "dummy")
    return RelevanceScreener(pico_criteria={"population": "FM"}, inclusion_criteria=[],
                             exclusion_criteria=[], model="m", provider="qwen")


@pytest.fixture
def rob2(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "dummy")
    return RoB2Assessor(model="m", provider="qwen")


def test_screener_uses_given_text_and_never_opens_pdf(monkeypatch, screener, pdf_readers_forbidden):
    sent = []
    def _urlopen(req, timeout=None):
        sent.append((getattr(req, "data", b"") or b"").decode("utf-8", "replace"))
        return _Resp(_ok())
    monkeypatch.setattr("urllib.request.urlopen", _urlopen)
    screener.screen_by_pdf_path("missing.pdf", "a.pdf", paper_text=MARK)
    assert sent and MARK.split()[0] in sent[0]
    assert pdf_readers_forbidden == []


def test_screen_batch_passes_record_text(screener):
    seen = []
    screener.screen_by_pdf_path = lambda p, f="", paper_text=None: seen.append(paper_text) or {"filename": f}
    screener.screen_batch([{"filename": "a.pdf", "pdf_path": "x.pdf", "paper_text": MARK}], delay_seconds=0)
    assert seen == [MARK]


def test_screen_batch_without_text_still_works(screener):
    seen = []
    screener.screen_by_pdf_path = lambda p, f="", paper_text=None: seen.append(paper_text) or {"filename": f}
    screener.screen_batch([{"filename": "a.pdf", "pdf_path": "x.pdf"}], delay_seconds=0)
    assert seen == [None]


def test_rob2_uses_given_text_and_never_opens_pdf(rob2, pdf_readers_forbidden):
    sent = []
    rob2._call_with_text = lambda text, prompt: sent.append(text) or '{"domains": {}, "overall_judgment": "Low"}'
    rob2.assess_by_pdf_path("missing.pdf", "a.pdf", paper_text=MARK)
    assert sent and MARK in sent[0]
    assert pdf_readers_forbidden == []


def test_rob2_batch_passes_record_text(rob2):
    seen = []
    rob2.assess_by_pdf_path = lambda p, f="", paper_text=None: seen.append(paper_text) or {"filename": f}
    rob2.assess_batch([{"filename": "a.pdf", "pdf_path": "x.pdf", "paper_text": MARK}], delay_seconds=0)
    assert seen == [MARK]


def test_stage2_builds_shared_text_before_screening():
    s = MAIN.read_text(encoding="utf-8")
    j = s.find("RelevanceScreener(")
    i = s.find("get_paper_text(")
    assert i != -1 and i < j, "Stage 2 must call get_paper_text before screening"
    assert '["paper_text"] =' in s[:j], "text must be stored on each record"
    assert '/ "paper_text"' in s[:j], "cache folder must be input/sr/paper_text"
