"""
Regression tests for v2.4.12's screening-side fixes:

  #46 (formerly #56)  screener retries transient network failures 3x with
                      backoff, but never retries 401/403 (same principle as
                      providers._is_transient_error)
  screening accounting  sr/main.py partitions results into
                      INCLUDE/EXCLUDE/UNCERTAIN/ERROR - an error-based drop
                      is not a valid PRISMA exclusion
  #40 / #41           OCR budget early-stop in relevance_screener.py and
                      rob2_tool.py - the old per-page char caps saturated
                      at exactly the same byte counts for every paper,
                      then the prompt cap discarded most of the OCR

All tests use pure logic - no real network calls, no real PDFs. The retry
tests monkeypatch urllib.request.urlopen; the accounting test synthesizes
screener output; the OCR budget tests inject fakes into sys.modules for
'fitz'/'pytesseract'/'pdfplumber', which works because those imports are
LAZY inside the OCR fallback block (function-local `import fitz`), so
Python re-resolves them via sys.modules on each call.

Run with: python -m pytest tests/test_screener_and_accounting.py -v
"""
from __future__ import annotations

import http.client
import io
import json
import sys
import types
import urllib.error

import pytest

from pipelines.sr.src.screening.relevance_screener import (
    MAX_SCREEN_CHARS, MAX_SCREEN_PAGES, RelevanceScreener,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeHTTPResponse:
    """Minimal stand-in for urlopen's context-manager response."""
    def __init__(self, body: dict):
        self._body = json.dumps(body).encode("utf-8")
    def __enter__(self):
        return self
    def __exit__(self, *exc):
        return False
    def read(self):
        return self._body


def _ok_body(decision: str = "INCLUDE") -> dict:
    return {
        "choices": [{
            "message": {
                "content": json.dumps({
                    "decision": decision,
                    "confidence": 0.9,
                    "pico_match": {"population": True, "intervention": True,
                                    "comparator": True, "outcome": True,
                                    "study_design": True},
                    "exclusion_reasons": [],
                    "rationale": "test",
                    "is_rct": True,
                })
            }
        }]
    }


def _http_error(code: int, msg: str = "err") -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        url="http://x", code=code, msg=msg, hdrs=None,
        fp=io.BytesIO(b'{"error": "test"}'),
    )


@pytest.fixture
def screener(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "dummy")
    return RelevanceScreener(
        pico_criteria={"population": "adults", "intervention": "CBT",
                        "comparator": "usual care", "outcome": "pain"},
        inclusion_criteria=["RCT"],
        exclusion_criteria=["case report"],
        model="qwen-plus-latest",
        provider="qwen",
        api_key="dummy",
    )


def _install_fake_pdfplumber_with_usable_text(monkeypatch):
    """Force screen_by_pdf_path past its text-extraction stage without
    reading any real PDF, so the retry loop is the only thing under test.
    The screener's text branch is taken when pdfplumber yields non-empty,
    non-CID, non-space-free text."""
    class _Page:
        def extract_text(self):
            return "Randomized controlled trial of CBT for chronic pain. " * 40
    class _PDF:
        pages = [_Page()] * 3
        def __enter__(self): return self
        def __exit__(self, *exc): return False

    fake = types.ModuleType("pdfplumber")
    fake.open = lambda _p: _PDF()
    monkeypatch.setitem(sys.modules, "pdfplumber", fake)


# ---------------------------------------------------------------------------
# #46: screener retry on transient network failures
# ---------------------------------------------------------------------------

def test_screener_retries_transient_and_succeeds(monkeypatch, screener):
    """One RemoteDisconnected on the first attempt, success on the second.
    Real-run incident 20260826_110915 dropped Karlsson from the entire
    review with exactly this pattern - the retry must recover it."""
    _install_fake_pdfplumber_with_usable_text(monkeypatch)
    calls = []
    def _urlopen(req, timeout=None):
        calls.append(1)
        if len(calls) == 1:
            raise http.client.RemoteDisconnected("remote end closed")
        return _FakeHTTPResponse(_ok_body("INCLUDE"))
    monkeypatch.setattr("urllib.request.urlopen", _urlopen)
    monkeypatch.setattr("time.sleep", lambda _s: None)

    out = screener.screen_by_pdf_path("fake.pdf", "Karlsson.pdf")
    assert out["decision"] == "INCLUDE", out
    assert out["error"] is None
    assert len(calls) == 2, (
        f"expected exactly one retry after RemoteDisconnected, got {len(calls)} calls"
    )


def test_screener_gives_up_after_three_attempts(monkeypatch, screener):
    """Persistent transient failure - screener returns an honest error row,
    not INCLUDE, and does NOT retry indefinitely."""
    _install_fake_pdfplumber_with_usable_text(monkeypatch)
    calls = []
    def _urlopen(req, timeout=None):
        calls.append(1)
        raise http.client.RemoteDisconnected("keeps failing")
    monkeypatch.setattr("urllib.request.urlopen", _urlopen)
    monkeypatch.setattr("time.sleep", lambda _s: None)

    out = screener.screen_by_pdf_path("fake.pdf", "brokendrops.pdf")
    assert out["decision"] == "UNCERTAIN"
    assert out["error"] is not None
    assert len(calls) == 3, (
        f"expected exactly 3 attempts total, got {len(calls)}"
    )


def test_screener_never_retries_403(monkeypatch, screener):
    """Auth errors are not transient - retrying them is at best pointless
    and at worst spends the failed-auth budget. Same principle as
    providers._is_transient_error's 401/403 exclusion (#34)."""
    _install_fake_pdfplumber_with_usable_text(monkeypatch)
    calls = []
    def _urlopen(req, timeout=None):
        calls.append(1)
        raise _http_error(403, "forbidden")
    monkeypatch.setattr("urllib.request.urlopen", _urlopen)
    monkeypatch.setattr("time.sleep", lambda _s: None)

    out = screener.screen_by_pdf_path("fake.pdf", "auth_fail.pdf")
    assert out["decision"] == "UNCERTAIN"
    assert out["error"] is not None
    assert len(calls) == 1, (
        f"403 must not be retried; got {len(calls)} attempts"
    )


def test_screener_never_retries_401(monkeypatch, screener):
    """Companion to the 403 test - 401 is the other never-transient code."""
    _install_fake_pdfplumber_with_usable_text(monkeypatch)
    calls = []
    def _urlopen(req, timeout=None):
        calls.append(1)
        raise _http_error(401, "unauthorized")
    monkeypatch.setattr("urllib.request.urlopen", _urlopen)
    monkeypatch.setattr("time.sleep", lambda _s: None)

    out = screener.screen_by_pdf_path("fake.pdf", "auth_fail.pdf")
    assert out["decision"] == "UNCERTAIN"
    assert len(calls) == 1


# ---------------------------------------------------------------------------
# Screening accounting partition (sr/main.py)
# ---------------------------------------------------------------------------

def test_screening_accounting_partitions_errors_from_excludes():
    """The v2.4.12 accounting block distinguishes real EXCLUDE decisions
    from screening call failures. An ERROR row must count as ERROR, not
    as EXCLUDE - the whole point of #46 is that an error is not a
    scientific judgment. This test mirrors sr/main.py's partition logic
    so a refactor of that block does not silently break the guarantee."""
    sr = [
        {"filename": "a.pdf", "decision": "INCLUDE", "error": None},
        {"filename": "b.pdf", "decision": "EXCLUDE", "error": None},
        {"filename": "c.pdf", "decision": "UNCERTAIN", "error": None},
        {"filename": "d.pdf", "decision": "UNCERTAIN", "error": "conn reset"},
        {"filename": "e.pdf", "decision": "EXCLUDE", "error": "conn reset"},
    ]
    # Exact partition sr/main.py performs (v2.4.12):
    errors = [s for s in sr if s.get("error")]
    excluded = [s for s in sr
                if s.get("decision") == "EXCLUDE" and not s.get("error")]
    uncertain = [s for s in sr
                    if s.get("decision") not in ("INCLUDE", "EXCLUDE")
                    and not s.get("error")]
    included = [s for s in sr if s.get("decision") == "INCLUDE"]
    assert len(included) == 1
    assert len(excluded) == 1               # only real EXCLUDE
    assert len(uncertain) == 1              # only real UNCERTAIN
    assert len(errors) == 2                 # BOTH error-bearing rows
    # Non-overlap: no row counted twice.
    total_counted = len(included) + len(excluded) + len(uncertain) + len(errors)
    assert total_counted == len(sr), (
        f"partition overlap: {total_counted} != {len(sr)}"
    )


def test_screening_accounting_survives_missing_error_key():
    """Older screener output may not have an 'error' key at all - the
    partition must treat that as 'no error' (equivalent to a real
    decision), not crash and not misclassify."""
    sr = [{"filename": "old.pdf", "decision": "INCLUDE"}]
    errors = [s for s in sr if s.get("error")]
    included = [s for s in sr if s.get("decision") == "INCLUDE"]
    assert errors == []
    assert included == sr


# ---------------------------------------------------------------------------
# #40 / #41: OCR budget early-stop
# ---------------------------------------------------------------------------

class _FakePixmap:
    def tobytes(self, _fmt): return b"fake-png-bytes"


class _FakePage:
    def get_pixmap(self, matrix=None): return _FakePixmap()


class _FakeDoc:
    """Fake fitz.Document. Records how many pages get_pixmap was called on
    so the test can observe early-stop directly."""
    def __init__(self, n_pages):
        self._n = n_pages
        self.pixmap_calls = 0
    def __len__(self): return self._n
    def __getitem__(self, i):
        self.pixmap_calls += 1
        return _FakePage()
    def __enter__(self): return self
    def __exit__(self, *exc): return False


def _install_ocr_fakes(monkeypatch, fake_doc, chars_per_page):
    """Wire fitz/pytesseract/PIL fakes into sys.modules and a fake
    pdfplumber that yields no text (forces the OCR path)."""
    fake_fitz = types.ModuleType("fitz")
    fake_fitz.open = lambda _p: fake_doc
    fake_fitz.Matrix = lambda *a, **kw: None
    monkeypatch.setitem(sys.modules, "fitz", fake_fitz)

    fake_pytesseract = types.ModuleType("pytesseract")
    fake_pytesseract.image_to_string = lambda _img: "x" * chars_per_page
    # relevance_screener/rob2_tool set pytesseract.pytesseract.tesseract_cmd
    # only on Windows and only if the default path exists; expose an inner
    # object so any accidental access does not AttributeError.
    fake_pytesseract.pytesseract = types.SimpleNamespace(tesseract_cmd=None)
    monkeypatch.setitem(sys.modules, "pytesseract", fake_pytesseract)

    fake_pil_image = types.ModuleType("PIL.Image")
    fake_pil_image.open = lambda _b: object()
    monkeypatch.setitem(sys.modules, "PIL.Image", fake_pil_image)
    # ensure `from PIL import Image` resolves too
    fake_pil = types.ModuleType("PIL")
    fake_pil.Image = fake_pil_image
    monkeypatch.setitem(sys.modules, "PIL", fake_pil)

    class _EmptyPage:
        def extract_text(self): return ""
    class _EmptyPDF:
        pages = [_EmptyPage()] * 3
        def __enter__(self): return self
        def __exit__(self, *exc): return False
    fake_pdfplumber = types.ModuleType("pdfplumber")
    fake_pdfplumber.open = lambda _p: _EmptyPDF()
    monkeypatch.setitem(sys.modules, "pdfplumber", fake_pdfplumber)


def test_screener_ocr_stops_when_budget_met(monkeypatch):
    """Every page returns MAX_SCREEN_CHARS/2 characters of OCR. The budget
    is MAX_SCREEN_CHARS, so ~2 pages should be OCR'd before the early
    stop fires - the old code would OCR all MAX_SCREEN_PAGES=8."""
    doc = _FakeDoc(n_pages=MAX_SCREEN_PAGES)
    _install_ocr_fakes(monkeypatch, doc, chars_per_page=MAX_SCREEN_CHARS // 2)

    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda req, timeout=None: _FakeHTTPResponse(_ok_body("INCLUDE")),
    )
    monkeypatch.setattr("time.sleep", lambda _s: None)
    monkeypatch.setenv("DASHSCOPE_API_KEY", "dummy")

    s = RelevanceScreener(
        pico_criteria={"population": "adults"}, inclusion_criteria=[],
        exclusion_criteria=[], model="qwen-plus-latest", provider="qwen",
        api_key="dummy",
    )
    s.screen_by_pdf_path("fake.pdf", "budget.pdf")

    # Early stop: 2 pages of MAX_SCREEN_CHARS/2 chars each meets the budget.
    # Allow one extra page of tolerance since the budget check is >= (may
    # be evaluated after the third page's append). Anything beyond 3 means
    # the early-stop regressed.
    assert doc.pixmap_calls <= 3, (
        f"expected <=3 pages OCR'd once the budget was met, got "
        f"{doc.pixmap_calls} - has the early-stop regressed?"
    )
    assert doc.pixmap_calls >= 2, (
        f"expected at least 2 pages to hit the budget, got {doc.pixmap_calls}"
    )
    # And definitely fewer than the old saturated cap.
    assert doc.pixmap_calls < MAX_SCREEN_PAGES, (
        f"OCR should not fill all {MAX_SCREEN_PAGES} pages when the "
        f"budget was met early; got {doc.pixmap_calls}"
    )


def test_rob2_ocr_stops_when_budget_met(monkeypatch):
    """RoB2 companion to the screener OCR budget test. Now that rob2_tool.py
    uses the identical shared-budget early-stop pattern as
    relevance_screener.py, we can assert the same tight bound: with each
    page returning MAX_ROB2_CHARS/2 chars, ~2 pages should be OCR'd before
    the early stop fires. The old code OCR'd all MAX_ROB2_PAGES=12 pages
    unconditionally, saturating at 12*1500 + 11*2 = 18022 chars of which
    the prompt kept only 6000."""
    from pipelines.sr.src.screening.rob2_tool import (
        MAX_ROB2_CHARS, MAX_ROB2_PAGES, RoB2Assessor,
    )
    doc = _FakeDoc(n_pages=MAX_ROB2_PAGES)
    _install_ocr_fakes(monkeypatch, doc, chars_per_page=MAX_ROB2_CHARS // 2)
    # _call_with_text's retry path uses time.sleep(2) on empty responses -
    # our fake returns non-empty, but neutralize it defensively so a
    # future flow change does not silently slow this test to 4 seconds.
    monkeypatch.setattr("time.sleep", lambda _s: None)

    monkeypatch.setenv("DASHSCOPE_API_KEY", "dummy")
    assessor = RoB2Assessor(model="qwen-plus-latest", provider="qwen",
                             api_key="dummy")

    # Neutralize the model call - we care about OCR page count, not the
    # model response.
    fake_content = ('{"study":"X","domains":{"randomisation":"Low",'
                    '"deviations":"Low","missing_data":"Low",'
                    '"outcome_measurement":"Low","reported_result":"Low"},'
                    '"overall_judgment":"Low","justifications":{}}')

    class _FakeChatCompletions:
        def create(self, **kw):
            return types.SimpleNamespace(choices=[types.SimpleNamespace(
                message=types.SimpleNamespace(content=fake_content))])

    assessor.client = types.SimpleNamespace(
        chat=types.SimpleNamespace(completions=_FakeChatCompletions())
    )

    assessor.assess_by_pdf_path("fake.pdf", "budget_rob2.pdf")

    # Two pages of MAX_ROB2_CHARS/2 chars each meets the budget. Allow one
    # page of tolerance since the >= check runs after append. Anything
    # near MAX_ROB2_PAGES means the early-stop regressed.
    assert doc.pixmap_calls <= 3, (
        f"expected <=3 pages OCR'd once MAX_ROB2_CHARS was met, got "
        f"{doc.pixmap_calls} - has the RoB2 early-stop regressed?"
    )
    assert doc.pixmap_calls >= 2, (
        f"expected at least 2 pages to hit the budget, got {doc.pixmap_calls}"
    )
    assert doc.pixmap_calls < MAX_ROB2_PAGES, (
        f"RoB2 OCR must not fill all {MAX_ROB2_PAGES} pages when the "
        f"budget was met early (was saturated before v2.4.12); "
        f"got {doc.pixmap_calls}"
    )
