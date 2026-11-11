"""Session 38: what RoB2 actually sends to the model.

The 908f889/306d838/de15a59 tests captured the text going INTO
_call_with_text, one step before its own [6000, 3000] cut, so they passed
while the model still saw only the first 6000 chars (run 20261111_114651:
registration lines and McCrae's ITT line never reached the model). These
tests capture the text at client.chat.completions.create. No PDFs, no AI.
"""
import json
import logging
import types

import pytest

try:
    from pipelines.sr.src.screening import rob2_tool as rt
except ImportError:
    from SOURCE_CODE.pipelines.sr.src.screening import rob2_tool as rt

ANSWER = json.dumps({
    "study": "Test 2020",
    "domains": {k: "Low" for k in ("randomisation", "deviations", "missing_data",
                                   "outcome_measurement", "reported_result")},
    "overall_judgment": "Low",
    "justifications": {},
})


class _FakeClient:
    """Stands in for the OpenAI client; records every message sent."""
    def __init__(self, answers):
        self.sent = []
        self._answers = list(answers)
        self.chat = types.SimpleNamespace(
            completions=types.SimpleNamespace(create=self._create))

    def _create(self, **kw):
        self.sent.append(kw["messages"][0]["content"])
        content = self._answers.pop(0) if self._answers else ""
        msg = types.SimpleNamespace(content=content)
        return types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)])


@pytest.fixture
def assessor(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-key")
    monkeypatch.setattr(rt.time, "sleep", lambda s: None)
    return rt.RoB2Assessor(model="qwen-plus-latest", provider="qwen")


def _long_text(n=30000):
    return ("Participants were recruited from clinics. " * (n // 42 + 1))[:n - 12] + "END_MARKER_Z"


def test_call_with_text_sends_whole_text(assessor):
    assessor.client = _FakeClient([ANSWER])
    text = _long_text()
    assessor._call_with_text(text, "PROMPT")
    assert len(assessor.client.sent) == 1
    assert "END_MARKER_Z" in assessor.client.sent[0], "model saw a cut text"


def test_retry_after_empty_answer_uses_shorter_text(assessor):
    assessor.client = _FakeClient(["", ANSWER])
    text = _long_text()
    assessor._call_with_text(text, "PROMPT")
    first, second = assessor.client.sent
    assert "END_MARKER_Z" in first
    assert "END_MARKER_Z" not in second
    assert text[:rt.MAX_ROB2_CHARS] in second
    assert len(second) < len(first)


def test_logs_chars_actually_sent(assessor, caplog):
    caplog.set_level(logging.INFO)
    assessor.client = _FakeClient([ANSWER])
    assessor._call_with_text(_long_text(), "PROMPT")
    assert "[ROB2 SEND] attempt 1: 30000 of 30000 chars" in caplog.text


def test_deep_methods_and_results_reach_the_model(assessor):
    abstract = "Abstract\n" + "Background words here. " * 100
    methods = ("Methods\n" + "Participants were recruited from clinics. " * 300
               + "\nData were analyzed using the intention to treat principle.\n")
    results = ("Results\n" + "Scores improved over time in all groups. " * 100
               + "\nCompleted follow-up n=24, 27, 23.\n")
    rest = ("Discussion\n" + "discussionbody " * 50
            + "\nReferences\n" + "referencesbody " * 50)
    text = ("--- page 1 ---\nA randomised trial of CBT\n" + abstract + "\n"
            + methods + "\n" + results + "\n" + rest)
    assessor.client = _FakeClient([ANSWER])
    assessor.assess_by_pdf_path("x.pdf", filename="x.pdf", paper_text=text)
    sent = assessor.client.sent[0]
    assert "intention to treat principle" in sent, "deep Methods line cut"
    assert "Completed follow-up n=24, 27, 23." in sent, "Results cut"
    assert "referencesbody" not in sent
