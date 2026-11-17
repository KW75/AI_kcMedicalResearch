"""Session 47 item (f): code-side outcome check.

The model sets outcome_match=true for every pain-related measure: runs
20261116_214126, 20261116_230750 and 20261117_232734 picked PCS, FIQ, NFR and MPQ,
all with outcome_match True, so the gate at main.py (outcome_match is False) never fired.
"""
import importlib

import pytest

PICO = "Pain intensity at post-intervention"
ALL4 = "mean_intervention(1->2); sd_intervention(1->2); mean_control(1->2); sd_control(1->2)"


def _al():
    for name in ("pipelines.sr.src.utils.audit_logger",
                 "SOURCE_CODE.pipelines.sr.src.utils.audit_logger"):
        try:
            return importlib.import_module(name)
        except ImportError:
            continue
    raise AssertionError("audit_logger not importable")


def _fn(name):
    fn = getattr(_al(), name, None)
    assert fn is not None, f"audit_logger.{name} missing"
    return fn


@pytest.mark.parametrize("sel", [
    "Average weekly pain intensity (0-100 VAS)",
    "Average weekly FM pain (0-100 VAS)",
    "Pain severity",
    "Clinical pain intensity",
    "FIQ pain score",
])
def test_match(sel):
    assert _fn("outcome_check")(sel, PICO)[0] == "match"


@pytest.mark.parametrize("sel", [
    "Pain catastrophizing (PCS)",
    "Fibromyalgia Impact Questionnaire (FIQ)",
    "NFR threshold",
    "NFR pain rating",
    "Pain interference",
])
def test_mismatch(sel):
    assert _fn("outcome_check")(sel, PICO)[0] == "mismatch"


@pytest.mark.parametrize("sel", ["Pain", "MPQ", None, ""])
def test_unclear(sel):
    assert _fn("outcome_check")(sel, PICO)[0] == "unclear"


def test_not_checked_when_pico_is_not_pain_intensity():
    assert _fn("outcome_check")("BDI-II", "Depressive symptoms")[0] == "not_checked"


def test_mismatch_reason_carries_token():
    r = _fn("outcome_mismatch_reason")("Pain catastrophizing (PCS)", PICO)
    assert r and "outcome_mismatch" in r and "needs review" in r


def test_no_reason_for_match_or_unclear():
    f = _fn("outcome_mismatch_reason")
    assert f("Pain severity", PICO) is None
    assert f("MPQ", PICO) is None


def test_reviewer_override_of_all_four_clears():
    f = _fn("outcome_mismatch_reason")
    assert f("Fibromyalgia Impact Questionnaire (FIQ)", PICO, ALL4) is None


def test_partial_override_does_not_clear():
    f = _fn("outcome_mismatch_reason")
    assert f("Fibromyalgia Impact Questionnaire (FIQ)", PICO, "mean_control(1->2)")


def test_sensitivity_label_for_outcome_mismatch():
    import SOURCE_CODE.pipelines.sr.main as main_mod
    r = _fn("outcome_mismatch_reason")("NFR threshold", PICO)
    assert main_mod._review_labels(r) == ["outcome mismatch"]


def test_gate_calls_outcome_check_once():
    import pathlib
    src = (pathlib.Path(__file__).resolve().parents[1] / "SOURCE_CODE" / "pipelines"
           / "sr" / "main.py").read_text(encoding="utf-8")
    assert src.count('outcome_mismatch_reason(po.get("outcome_selected")') == 1
