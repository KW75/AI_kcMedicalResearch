"""Session 51 (cont. 12): warn when the answer leaves out abnormal results."""
from pipelines.samd import report

from pathlib import Path

PREFIX = "Abnormal results not mentioned in the answer: "


def _r(test, value, unit, ref, status, flag=""):
    return {"test": test, "value": value, "unit": unit, "ref": ref, "flag": flag,
            "status": status}


def _cli_source():
    return Path(report.__file__).with_name("cli.py").read_text(encoding="utf-8")


def test_urine_results_left_out():
    rows = [_r("Protein - Urine 蛋白", "1+", "", "Negative", "HIGH"),
            _r("Blood - Urine 尿血", "TRACE", "", "Negative", "HIGH", "*"),
            _r("RBC - Urine 紅血球", "10-17", "cells/ul", "<9", "HIGH"),
            _r("Creatinine 肌酸酐", "100", "umol/L", "62 - 115", "normal")]
    w = report.unmentioned_abnormal(rows, "Creatinine is 100 umol/L. Kidney function needs review.")
    assert w == [PREFIX + "urine: Protein, Blood, RBC"]


def test_blood_rbc_named_but_urine_rbc_not():
    rows = [_r("RBC 紅血球", "4.1", "x10e12/L", "4.4 - 5.9", "LOW"),
            _r("RBC - Urine 紅血球", "10-17", "cells/ul", "<9", "HIGH")]
    w = report.unmentioned_abnormal(rows, "The RBC count is low. Blood pressure is normal.")
    assert w == [PREFIX + "urine: RBC"]


def test_glucose_fasting_named_as_glucose():
    rows = [_r("Glucose Fasting 血葡萄糖,空腹", "6.4", "mmol/L", "3.9 - 6.0", "HIGH")]
    assert report.unmentioned_abnormal(rows, "Glucose is slightly raised.") == []


def test_lab_flagged_band_row_left_out():
    rows = [_r("CPK 肌酸激酶", "248", "IU/l", "Female 29-168; Male 30-200", "see bands", "H"),
            _r("CEA 癌胚抗原", "2.1", "ng/ml", "Non-smoker <5.0; Smoker <10.0", "see bands")]
    w = report.unmentioned_abnormal(rows, "Thyroid tests are normal.")
    assert w == [PREFIX + "CPK"]


def test_no_warning_when_all_named():
    rows = [_r("Platelet Count 血小板", "120", "x10e9/L", "150 - 400", "LOW"),
            _r("Protein - Urine 蛋白", "1+", "", "Negative", "HIGH")]
    answer = "Platelets are low (platelet count 120). Urine protein is 1+."
    assert report.unmentioned_abnormal(rows, answer) == []


def test_cli_shows_the_warning():
    assert "report.unmentioned_abnormal(" in _cli_source()
