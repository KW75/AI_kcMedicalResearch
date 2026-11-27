"""Session 51 (cont. 18): SaMD answer checks - plural abbreviations ('RBCs',
urine rows only), urine ratios ('albumin-to-creatinine ratio') and comma lists
after 'No'."""
from pipelines.samd import report


def _row(test, value, unit, ref, status, flag=""):
    return {"test": test, "value": value, "unit": unit, "ref": ref, "flag": flag,
            "status": status, "source": "CKW_Blood test_2025.07.28_HK6, PSA.pdf"}


URINE_RBC = _row("RBC - Urine 紅血球", "10-17", "cells/ul", "<9", "HIGH")
URINE_BLOOD = _row("Blood - Urine 尿血", "TRACE", "", "Negative", "HIGH", "*")
URINE_PROTEIN = _row("Protein - Urine 蛋白質", "1+", "", "Negative", "HIGH")
BLOOD_RBC = _row("RBC 紅血球", "4.45", "x 10^12/L", "4.50 - 6.30", "LOW", "L")
ALBUMIN = _row("Albumin", "39", "g/L", "40 - 49", "LOW")
PROTEIN_TOTAL = _row("Protein(Total)", "58", "g/L", "64 - 83", "LOW")
AGAINST = ("- Against: No proteinuria, haematuria, or significant electrolyte "
           "disturbance; urine analysis shows trace blood and 10\u201317 RBCs/ul, "
           "which may be insignificant.")


def test_plural_rbcs_names_urine_rbc():
    assert report.unmentioned_abnormal([URINE_RBC], AGAINST) == []


def test_singular_rbc_still_named():
    assert report.unmentioned_abnormal([URINE_RBC], AGAINST.replace("RBCs", "RBC")) == []


def test_urine_rbcs_does_not_name_blood_rbc():
    out = report.unmentioned_abnormal([BLOOD_RBC], AGAINST)
    assert len(out) == 1 and "RBC" in out[0]


def test_uacr_does_not_name_serum_albumin():
    answer = ("2. **Urinary albumin-to-creatinine ratio (UACR)** to assess for "
              "proteinuria, which would suggest glomerular damage.")
    out = report.unmentioned_abnormal([ALBUMIN], answer)
    assert len(out) == 1 and "Albumin" in out[0]


def test_albumin_by_name_still_named():
    out = report.unmentioned_abnormal([ALBUMIN], "Albumin 39 g/L in 2024 was slightly low.")
    assert out == []


def test_protein_creatinine_ratio_does_not_name_total_protein():
    out = report.unmentioned_abnormal(
        [PROTEIN_TOTAL], "A urine protein-to-creatinine ratio would help.")
    assert len(out) == 1 and "Protein(Total)" in out[0]


def test_comma_list_denies_all_terms():
    out = report.denied_urine_findings([URINE_PROTEIN, URINE_BLOOD, URINE_RBC], AGAINST)
    assert len(out) == 1
    assert all(n in out[0] for n in ("Protein - Urine", "Blood - Urine", "RBC - Urine"))


def test_but_after_comma_is_not_a_denial():
    out = report.denied_urine_findings(
        [URINE_BLOOD, URINE_RBC], "No proteinuria, but haematuria is present.")
    assert out == []


def test_but_without_comma_is_not_a_denial():
    out = report.denied_urine_findings(
        [URINE_BLOOD, URINE_RBC], "No proteinuria but haematuria is present.")
    assert out == []


def test_semicolon_still_ends_the_list():
    out = report.denied_urine_findings(
        [URINE_BLOOD, URINE_RBC], "No proteinuria; haematuria is present.")
    assert out == []


def test_plain_denial_still_warns():
    out = report.denied_urine_findings([URINE_BLOOD, URINE_RBC], "No haematuria.")
    assert len(out) == 1 and "Blood - Urine" in out[0] and "RBC - Urine" in out[0]
