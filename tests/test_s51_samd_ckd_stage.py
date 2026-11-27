"""Session 51 (cont. 13): CKD stage in the answer against the eGFR (KDIGO)."""
from pipelines.samd import report

from pathlib import Path

PREFIX = "CKD stage in the answer does not match the eGFR"


def _egfr(v):
    return {"test": "eGFR 估算腎小球濾過率", "value": v, "unit": "mL/min/1.73m2",
            "ref": ">90", "flag": "", "status": "LOW"}


def _cli_source():
    return Path(report.__file__).with_name("cli.py").read_text(encoding="utf-8")


def test_stage_3_with_egfr_68_warns():
    w = report.ckd_stage_mismatch([_egfr("68")], "The most likely diagnosis is "
                                  "**chronic kidney disease (CKD) stage 3**, based on creatinine.")
    assert len(w) == 1 and w[0].startswith(PREFIX)
    assert "stage 3" in w[0] and "G2" in w[0]


def test_matching_stage_no_warning():
    assert report.ckd_stage_mismatch([_egfr("50")], "Findings fit CKD stage 3a.") == []
    assert report.ckd_stage_mismatch([_egfr("68")], "Findings fit CKD G2.") == []


def test_egfr_only_in_answer():
    w = report.ckd_stage_mismatch([], "Stage 3 CKD is likely. The eGFR of 68 mL/min/1.73 m2 is reduced.")
    assert len(w) == 1 and "(answer)" in w[0] and "G2" in w[0]


def test_negated_stage_no_warning():
    assert report.ckd_stage_mismatch([_egfr("68")], "This does not meet criteria for CKD stage 3.") == []


def test_greater_than_value():
    assert report.ckd_stage_mismatch([_egfr(">90")], "Consistent with CKD stage 1 if markers persist.") == []
    w = report.ckd_stage_mismatch([_egfr(">90")], "Consistent with CKD stage 3.")
    assert len(w) == 1 and "G1" in w[0]


def test_no_stage_no_egfr_no_warning():
    assert report.ckd_stage_mismatch([], "Kidney function needs review.") == []
    assert report.ckd_stage_mismatch([_egfr("68")], "Kidney function is mildly reduced.") == []


def test_cli_shows_the_warning():
    assert "report.ckd_stage_mismatch(" in _cli_source()
