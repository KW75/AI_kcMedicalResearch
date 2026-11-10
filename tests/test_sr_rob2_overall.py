"""RoB 2 overall judgement follows the domain rule, not the model's guess.

Session 37: Ang had Missing data = High but overall 'Some concerns' in two
runs (20261110_234448, 20261111_001942). RoB 2: any High domain -> overall
High; all Low -> Low; otherwise Some concerns. A failed assessment is
'Not assessed', not 'High'.
"""
import importlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "SOURCE_CODE" / "pipelines" / "sr" / "src" / "screening" / "rob2_tool.py"
KEYS = ("randomisation", "deviations", "missing_data",
        "outcome_measurement", "reported_result")


@pytest.fixture(scope="module")
def rt():
    return importlib.import_module("pipelines.sr.src.screening.rob2_tool")


@pytest.fixture(scope="module")
def rule(rt):
    fn = getattr(rt, "apply_rob2_overall", None)
    if fn is None:
        pytest.fail("rob2_tool.apply_rob2_overall missing (RoB2 overall rule)")
    return fn


def _res(values, overall):
    return {"domains": dict(zip(KEYS, values)), "overall_judgment": overall}


ANG = ["Some concerns", "Some concerns", "High", "Low", "Low"]


def test_any_high_domain_makes_overall_high(rule):
    r = rule(_res(ANG, "Some concerns"))
    assert r["overall_judgment"] == "High"
    assert r["overall_model"] == "Some concerns"


def test_all_low_is_low(rule):
    assert rule(_res(["Low"] * 5, "Some concerns"))["overall_judgment"] == "Low"


def test_mixed_low_and_some_is_some_concerns(rule):
    r = rule(_res(["Low", "Some concerns", "Low", "Low", "Low"], "Low"))
    assert r["overall_judgment"] == "Some concerns"
    assert r["overall_model"] == "Low"


def test_wording_is_normalised(rule):
    r = rule(_res(["LOW", "some concerns", "High risk", "low", "Low risk"], "low"))
    assert r["domains"]["randomisation"] == "Low"
    assert r["domains"]["deviations"] == "Some concerns"
    assert r["domains"]["missing_data"] == "High"
    assert r["domains"]["outcome_measurement"] == "Low"
    assert r["overall_judgment"] == "High"


def test_incomplete_domains(rule):
    no_high = {"domains": {"randomisation": "Low", "deviations": "Low"},
               "overall_judgment": "Low"}
    assert rule(no_high)["overall_judgment"] == "Not assessed"
    with_high = {"domains": {"randomisation": "High"}, "overall_judgment": "Low"}
    assert rule(with_high)["overall_judgment"] == "High"


def _assessor(rt, monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-key")
    monkeypatch.setattr("time.sleep", lambda _s: None)
    return rt.RoB2Assessor(model="qwen-plus-latest", provider="qwen")


def test_text_path_applies_rule(rt, monkeypatch):
    a = _assessor(rt, monkeypatch)
    answer = json.dumps(_res(ANG, "Some concerns"))
    monkeypatch.setattr(a, "_call_with_text", lambda text, prompt: answer)
    r = a.assess_by_pdf_path("Ang.pdf", "Ang.pdf", paper_text="Methods ... Results ...")
    assert r["error"] is None
    assert r["overall_judgment"] == "High"
    assert r["overall_model"] == "Some concerns"


def test_failed_assessment_is_not_assessed_not_high(rt, monkeypatch):
    a = _assessor(rt, monkeypatch)

    def boom(text, prompt):
        raise RuntimeError("model down")
    monkeypatch.setattr(a, "_call_with_text", boom)
    r = a.assess_by_pdf_path("x.pdf", "x.pdf", paper_text="some text")
    assert r["error"]
    assert r["overall_judgment"] == "Not assessed"


def test_both_paths_use_rule_and_no_high_fallback():
    src = SRC.read_text(encoding="utf-8")
    assert src.count("apply_rob2_overall(") >= 3, "def + Anthropic path + text path"
    assert '"overall_judgment": "High"' not in src, "failure must not be reported as High"


def test_html_not_assessed_has_no_high_badge():
    hr = importlib.import_module("pipelines.sr.src.reporting.html_report")
    rows = hr.HTMLReportGenerator()._rob_rows(
        [{"filename": "x.pdf", "domains": {}, "overall_judgment": "Not assessed"}])
    assert "Not assessed" in rows
    assert 'class="rh"' not in rows
