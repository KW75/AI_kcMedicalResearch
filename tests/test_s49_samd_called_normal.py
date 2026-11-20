"""Session 49: check_answer warns when the AI calls an out-of-range result
(HIGH, LOW, ABNORMAL) normal."""
from pipelines.samd import report

RED = "Colour 順色 RED -"
PROTEIN = "Protein - Urine 蛋白 1+ Up to trace"
GLU_HIGH = "Glucose 7.2 mmol/L 3.9 - 6.1"
GLU_OK = "Glucose 5.2 mmol/L 3.9 - 6.1"
KEY = "out-of-range result normal"


def _warn(line, answer):
    row = report.parse_line(line)
    assert row is not None
    return [w for w in report.check_answer([row], answer, case=line) if KEY in w]


def test_guard_statuses():
    assert report.parse_line(RED)["status"] == "ABNORMAL"
    assert report.parse_line(PROTEIN)["status"] == "HIGH"
    assert report.parse_line(GLU_HIGH)["status"] == "HIGH"
    assert report.parse_line(GLU_OK)["status"] == "normal"


def test_red_called_normal_warns():
    w = _warn(RED, "Urine colour RED is normal.")
    assert len(w) == 1 and "Colour 順色 RED (ABNORMAL)" in w[0]


def test_protein_called_normal_warns():
    w = _warn(PROTEIN, "Urine protein 1+ is normal.")
    assert len(w) == 1 and "(HIGH, range Up to trace)" in w[0]


def test_high_number_called_normal_warns():
    w = _warn(GLU_HIGH, "Fasting glucose 7.2 mmol/L is within normal limits.")
    assert len(w) == 1 and "Glucose 7.2 mmol/L (HIGH, range 3.9 - 6.1)" in w[0]


def test_mixed_sentence_no_warning():
    assert _warn(PROTEIN, "Protein 1+ is high, glucose is normal.") == []


def test_called_high_no_warning():
    assert _warn(GLU_HIGH, "Glucose 7.2 mmol/L is high.") == []


def test_not_normal_no_warning():
    assert _warn(RED, "Urine colour RED is not normal.") == []


def test_normal_row_called_normal_no_warning():
    assert _warn(GLU_OK, "Glucose 5.2 mmol/L is normal.") == []


def test_row_not_named_no_warning():
    assert _warn(RED, "The urine test is normal.") == []
