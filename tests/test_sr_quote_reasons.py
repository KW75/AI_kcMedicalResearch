"""Each quote-gate case gets its own wording (item 6, Session 43).

The gate token stays quote_not_found and all three cases are cleared the
same way; only the reason text, the report wording and the [SENSITIVITY]
label now say which case it was.
"""
from __future__ import annotations

import importlib

import SOURCE_CODE.pipelines.sr.main as main_mod
from pipelines.sr.src.utils import audit_logger as audit

NOT_FOUND = ("control source quote was not found verbatim in the extracted "
             "source text - it may be paraphrased or fabricated")
MISSING = ("no source quote provided for the intervention values - the numbers "
           "cannot be audited against the source text")
UNCHECKED = ("intervention source quote could not be checked against the paper "
             "text - no paper text was available")
UNCHECKED_CTRL = UNCHECKED.replace("intervention", "control", 1)
ALL_FOUR = ("mean_intervention(3.61->3.88); sd_intervention(0.85->1.05); "
            "mean_control(confirmed 3.67); sd_control(0.92->0.75)")
TAIL = ("numbers read from page images; verify all four means/SDs against the "
        "PDF and enter them in input/sr/study_overrides.yaml with a "
        "source-page note")


def reason(warn, overrides=None, method="vision"):
    return audit.review_skip_reason("", overrides, quote_warning=warn,
                                    extraction_method=method)


def _hr():
    return importlib.import_module("pipelines.sr.src.reporting.html_report")


def test_each_case_gets_its_own_reason():
    assert reason(NOT_FOUND) == audit.QUOTE_GATE_REASON
    assert reason(MISSING) == audit.QUOTE_MISSING_REASON
    assert reason(UNCHECKED) == audit.QUOTE_UNCHECKED_REASON


def test_all_three_keep_token_and_tail():
    for r in (audit.QUOTE_GATE_REASON, audit.QUOTE_MISSING_REASON,
              audit.QUOTE_UNCHECKED_REASON):
        assert "(quote_not_found)" in r
        assert r.endswith(TAIL)


def test_mixed_warning_names_each_case():
    r = reason(MISSING + "; " + NOT_FOUND)
    assert "no source quote given" in r and "source quote not found" in r
    assert r.count("(quote_not_found)") == 2


def test_same_case_on_two_arms_named_once():
    r = reason(UNCHECKED + "; " + UNCHECKED_CTRL)
    assert r.count("(quote_not_found)") == 1


def test_all_four_overrides_clear_each_case():
    for w in (NOT_FOUND, MISSING, UNCHECKED, MISSING + "; " + NOT_FOUND):
        assert reason(w, overrides=ALL_FOUR) is None


def test_text_path_unchanged():
    for w in (NOT_FOUND, MISSING, UNCHECKED):
        assert reason(w, method="text_fallback") is None


def test_report_wording_per_case():
    hr = _hr()
    nf = hr.plain_skip_reason(audit.QUOTE_GATE_REASON)
    mi = hr.plain_skip_reason(audit.QUOTE_MISSING_REASON)
    un = hr.plain_skip_reason(audit.QUOTE_UNCHECKED_REASON)
    assert "not found in the paper" in nf and "missing" not in nf
    assert "missing" in mi and "not found" not in mi
    assert "could not be checked" in un and "no paper text" in un


def test_report_wording_for_mixed_reason():
    s = _hr().plain_skip_reason(reason(MISSING + "; " + NOT_FOUND))
    assert "quote was missing." in s
    assert "not found in the paper" in s
    assert "missing, could not be checked, or" not in s


def test_sensitivity_labels_per_case():
    assert main_mod._review_labels(audit.QUOTE_GATE_REASON) == ["quote not found"]
    assert main_mod._review_labels(audit.QUOTE_MISSING_REASON) == ["no quote"]
    assert main_mod._review_labels(audit.QUOTE_UNCHECKED_REASON) == ["quote not checked"]