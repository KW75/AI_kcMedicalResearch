"""Session 51: fewer false warnings from check_answer.

Made-up sentences in the shape of the false warnings on a real run (no
patient data): a change over time ("increased from X to Y"), the same
number with another unit (ESR 69 mm/hr vs a 69 g/L row), a number inside
a test name (CA19-9 vs a 19 g/L row) and "above the normal range". Real
warnings must still fire.
"""
from pipelines.samd import report


def row(test, value, unit, ref, status):
    return {"test": test, "value": value, "unit": unit, "ref": ref,
            "flag": "", "status": status, "source": "s.pdf"}


def calls(rows, answer):
    return [w for w in report.check_answer(rows, answer, "")
            if w.startswith("The answer may call")]


def test_trend_values_not_called_abnormal():
    rows = [row("Urea", "5.4", "mmol/L", "2.9 - 8.2", "normal"),
            row("Creatinine", "88", "\u00b5mol/L", "62 - 106", "normal"),
            row("Creatinine", "100", "umol/L", "62 - 115", "normal")]
    answer = ("- Urea increased from 5.4 mmol/L to **9.2 mmol/L**, and creatinine "
              "rose from 88 \u00b5mol/L to **100 \u00b5mol/L**.")
    assert calls(rows, answer) == []


def test_number_with_other_unit_not_matched():
    rows = [row("Protein Total", "69", "g/L", "57 - 82", "normal")]
    answer = ("**Inflammatory condition** - Suggested by elevated ESR (**69 mm/hr**, "
              "reference <32 mm/hr), which is abnormal.")
    assert calls(rows, answer) == []


def test_number_inside_test_name_not_matched():
    rows = [row("Globulin", "19", "g/L", "20 - 38", "LOW")]
    answer = ("However, all other tumor markers (CEA, CA19-9, PSA) are within "
              "or near reference ranges.")
    assert calls(rows, answer) == []


def test_above_normal_range_not_called_normal():
    rows = [row("Glucose Fasting", "6.4", "mmol/L", "3.9 - 6.0", "HIGH")]
    answer = ("**Diabetes mellitus** - Supported by fasting glucose of **6.4 mmol/L**, "
              "which is above the normal range (3.9-6.0 mmol/L), but below the "
              "diagnostic threshold.")
    assert calls(rows, answer) == []


def test_real_called_normal_still_warns():
    rows = [row("Glucose Fasting", "6.4", "mmol/L", "3.9 - 6.0", "HIGH")]
    assert len(calls(rows, "Fasting glucose 6.4 mmol/L is normal.")) == 1


def test_real_in_range_called_abnormal_still_warns():
    rows = [row("Urea", "5.4", "mmol/L", "2.9 - 8.2", "normal")]
    assert len(calls(rows, "Urea 5.4 mmol/L is elevated.")) == 1


def test_same_unit_written_differently_still_matches():
    rows = [row("Creatinine", "88", "\u00b5mol/L", "62 - 106", "normal")]
    assert len(calls(rows, "Creatinine 88 umol/L is raised.")) == 1
    rows = [row("CPK", "248", "IU/l", "30 - 200", "HIGH")]
    assert len(calls(rows, "CPK 248 U/L is normal.")) == 1


def test_trend_does_not_hide_called_normal():
    rows = [row("Glucose Fasting", "6.4", "mmol/L", "3.9 - 6.0", "HIGH")]
    answer = "Glucose rose from 5.0 to 6.4 mmol/L and is normal."
    assert len(calls(rows, answer)) == 1
