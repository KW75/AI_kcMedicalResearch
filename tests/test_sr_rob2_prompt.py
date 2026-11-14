"""Session 38 (7c): RoB2 prompt names the review outcome and states the
Domain 4 self-report rule.

Runs 20261111_121950 and 20261111_161320 gave all five studies Low on
outcome_measurement: the model counted a blinded researcher handing out
questionnaires as blinded assessment (Lami, Jensen, McCrae), gave Low while
saying assessors were not blinded (Karlsson), and judged Ang on the NFR
threshold instead of the review's pain outcome. ROB2_PROMPT was only a JSON
template. Text is captured at client.chat.completions.create. No PDFs, no AI.
"""
import json
import types
from pathlib import Path

import pytest

try:
    from pipelines.sr.src.screening import rob2_tool as rt
except ImportError:
    from SOURCE_CODE.pipelines.sr.src.screening import rob2_tool as rt

ROOT = Path(__file__).resolve().parents[1]
RT_SRC = ROOT / "SOURCE_CODE" / "pipelines" / "sr" / "src" / "screening" / "rob2_tool.py"
MAIN_SRC = ROOT / "SOURCE_CODE" / "pipelines" / "sr" / "main.py"
OUTCOME = "Pain intensity at post intervention"

ANSWER = json.dumps({
    "study": "Test 2020",
    "domains": {k: "Some concerns" for k in ("randomisation", "deviations", "missing_data",
                                             "outcome_measurement", "reported_result")},
    "overall_judgment": "Some concerns",
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


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-key")
    monkeypatch.setattr(rt.time, "sleep", lambda s: None)


def test_prompt_keeps_json_template():
    p = rt.rob2_prompt()
    assert rt.ROB2_PROMPT in p
    assert '"outcome_measurement":"Low|Some concerns|High"' in p


def test_prompt_states_self_report_rule():
    p = rt.rob2_prompt(OUTCOME)
    assert "PARTICIPANT is the outcome assessor" in p
    assert "does NOT make the assessment blinded" in p
    assert "name the outcome assessed" in p


def test_outcome_named_when_given_and_fallback_without():
    assert OUTCOME in rt.rob2_prompt(OUTCOME)
    p = rt.rob2_prompt(None)
    assert "trial's primary outcome" in p
    assert "PARTICIPANT is the outcome assessor" in p


def test_default_assessor_has_no_outcome():
    # direct callers (tests, scripts) keep working without an outcome
    assert rt.RoB2Assessor(model="qwen-plus-latest", provider="qwen").outcome is None


def test_text_route_sends_rule_and_outcome_to_the_model():
    a = rt.RoB2Assessor(model="qwen-plus-latest", provider="qwen", outcome=OUTCOME)
    a.client = _FakeClient([ANSWER])
    a.assess_by_pdf_path("x.pdf", filename="x.pdf",
                         paper_text="Methods\nParticipants rated pain on a 0-10 scale.\n")
    assert len(a.client.sent) == 1, "model was not called"
    sent = a.client.sent[0]
    assert OUTCOME in sent
    assert "PARTICIPANT is the outcome assessor" in sent


def test_both_routes_use_rob2_prompt():
    s = RT_SRC.read_text(encoding="utf-8-sig")
    # Anthropic file route and text route must send the same prompt
    assert s.count("rob2_prompt(self.outcome)") >= 2
    assert '"text": ROB2_PROMPT' not in s
    assert "_call_with_text(pdf_text, ROB2_PROMPT)" not in s


def test_main_passes_review_outcome_to_rob2():
    s = MAIN_SRC.read_text(encoding="utf-8-sig")
    i = s.index("RoB2Assessor(")
    call = s[i:s.index(")", s.index("provider", i))]
    assert "outcome" in call, "main.py does not pass the PICO outcome to RoB2Assessor"

def test_domain4_rule_is_high_outright_for_unblinded_self_report():
    """Session 38 (7j): reviewer decision - self-reported subjective outcome with
    participants aware of their arm -> High (4.3 Yes, 4.4 Yes, 4.5 Probably yes).
    Run 20261111_171313 split Some concerns/High by model wording (Jensen High,
    Ang/Karlsson/McCrae Some concerns with the same reasoning)."""
    p = rt.rob2_prompt("Pain intensity at post intervention")
    assert 'judge "High"' in p
    assert "4.5 Probably yes" in p
    assert 'or "High" if' not in p, "old Some concerns/High split still in the rule"

def test_labels_mean_risk_of_bias_not_quality():
    """Session 41 rerun 20261114_184026: gemma4:e4b rated randomisation High
    for all 5 while describing adequate methods ('sealed envelopes, which
    meets criteria for high risk') and reported_result High because results
    were 'clearly reported'. It read High as high quality."""
    p = rt.rob2_prompt(OUTCOME)
    assert "RISK OF BIAS, not study quality" in p
    assert '"Low" = low risk' in p and '"High" = high risk' in p
    assert "label must match its justification" in p


def test_adequate_methods_map_to_low():
    p = rt.rob2_prompt(OUTCOME)
    assert "sealed opaque envelopes" in p and 'Domain 1 "Low"' in p
    assert 'Domain 5 "Low"' in p
    assert '"clearly reported" is never a reason for "High"' in p


def test_label_rule_keeps_template_and_domain4_rule():
    p = rt.rob2_prompt(OUTCOME)
    assert '"randomisation":"Low|Some concerns|High"' in p
    assert 'judge "High"' in p and 'or "High" if' not in p
    assert "{" not in rt._ROB2_RULES and "}" not in rt._ROB2_RULES
