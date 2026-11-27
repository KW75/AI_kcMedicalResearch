"""Session 51 (cont. 15): answer checks (made-up rows and sentences)."""
from pipelines.samd import report


def row(test, value, unit, ref, status, flag=""):
    return {"test": test, "value": value, "unit": unit, "ref": ref,
            "flag": flag, "status": status, "source": "made-up"}


PROT = row("Protein - Urine 蛋白質", "1+", "", "Negative", "HIGH")
RBC = row("RBC - Urine 紅血球", "10-17", "cells/ul", "<9", "HIGH")
BLOOD = row("Blood - Urine 尿血", "TRACE", "", "Negative", "HIGH", "*")
GLOB = row("Globulin 球蛋白", "19", "g/L", "20 - 38", "LOW")
CREA = row("Creatinine 肌酸酐, 血清", "100", "umol/L", "62 - 115", "normal")


def test_urine_word_without_value_not_mentioned():
    a = ("Urine protein quantification (e.g., albumin-to-creatinine ratio) - "
         "Needed to determine presence of proteinuria.")
    w = report.unmentioned_abnormal([PROT], a)
    assert w and "urine: Protein" in w[0]


def test_urine_value_named_is_mentioned():
    assert report.unmentioned_abnormal([PROT], "Urine protein is 1+ on dipstick.") == []


def test_urine_range_with_en_dash():
    assert report.unmentioned_abnormal([RBC], "Urine RBC 10–17 cells/uL is raised.") == []


def test_trace_blood_in_urine():
    assert report.unmentioned_abnormal([BLOOD], "There is trace blood in the urine.") == []


def test_blood_rows_still_by_name():
    assert report.unmentioned_abnormal([GLOB], "Globulin is slightly low.") == []


def test_elevation_called_abnormal():
    a = ("Dehydration could explain mild elevation in serum urea (9.2 mmol/L) "
         "and creatinine (100 umol/L).")
    w = report.check_answer([CREA], a, a)
    assert any("in-range" in x and "Creatinine" in x for x in w)
