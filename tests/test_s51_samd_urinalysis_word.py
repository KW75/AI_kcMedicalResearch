"""Session 51 (cont. 16): 'urinalysis' is a urine word (made-up rows and sentences)."""
from pipelines.samd import report


def row(test, value, unit, ref, status, flag=""):
    return {"test": test, "value": value, "unit": unit, "ref": ref,
            "flag": flag, "status": status, "source": "made-up"}


PROT = row("Protein - Urine 蛋白質", "1+", "", "Negative", "HIGH")
RBC = row("RBC - Urine 紅血球", "10-17", "cells/ul", "<9", "HIGH")
GLOB = row("Globulin 球蛋白", "19", "g/L", "20 - 38", "LOW")


def test_urinalysis_protein_value_mentioned():
    assert report.unmentioned_abnormal([PROT], "Urinalysis shows protein 1+.") == []


def test_urinalysis_rbc_value_mentioned():
    assert report.unmentioned_abnormal([RBC], "Urinalysis: RBC 10-17 cells/uL.") == []


def test_urinalysis_without_value_still_warns():
    w = report.unmentioned_abnormal([PROT], "Urinalysis was requested to look for protein.")
    assert w and "urine: Protein" in w[0]


def test_urine_word_still_works():
    assert report.unmentioned_abnormal([PROT], "Urine protein is 1+.") == []


def test_blood_rows_unchanged():
    assert report.unmentioned_abnormal([GLOB], "Globulin is slightly low.") == []
