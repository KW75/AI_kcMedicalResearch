"""Session 49: a flagged urine row is named by its test word next to 'urine' or
'urinary', so "urine protein is normal" is warned without the value 1+."""
from pipelines.samd import report

SECTION = "\n".join([
    "URINALYSIS 尿液常規檢驗",
    "Colour 順色 RED -",
    "Blood - Urine 潛血 2+ Up to trace",
    "Protein - Urine 蛋白質 1+ \u2191 Up to trace",
    "Urine Released By: Lai Wai Hung on 14/NOV/2022 13:07",
])
ROWS = report.parse_results([("labs.pdf", "transcription", SECTION)])
KEY = "out-of-range result normal"


def _warn(answer):
    return [w for w in report.check_answer(ROWS, answer, case="") if KEY in w]


def test_guard_rows():
    st = {r["test"]: r["status"] for r in ROWS}
    assert st == {"Colour - Urine 順色": "ABNORMAL", "Blood - Urine 潛血": "HIGH",
                  "Protein - Urine 蛋白質": "HIGH"}


def test_urine_protein_called_normal_warns():
    w = _warn("Urine protein is normal.")
    assert len(w) == 1 and "Protein - Urine 蛋白質 1+ (HIGH" in w[0]


def test_protein_in_the_urine_called_normal_warns():
    w = _warn("Protein in the urine is normal.")
    assert len(w) == 1 and "Protein - Urine" in w[0]


def test_urine_colour_called_normal_warns():
    w = _warn("The urine colour is normal.")
    assert len(w) == 1 and "Colour - Urine 順色 RED (ABNORMAL)" in w[0]


def test_urinary_protein_within_limits_warns():
    w = _warn("Urinary protein was within normal limits.")
    assert len(w) == 1 and "Protein - Urine" in w[0]


def test_value_still_names_row():
    assert len(_warn("Urine protein 1+ is normal.")) == 1


def test_raised_in_sentence_no_warning():
    assert _warn("Urine protein is mildly raised; glucose is normal.") == []


def test_no_urine_word_no_warning():
    assert _warn("Protein intake is normal.") == []


def test_blood_not_next_to_urine_no_warning():
    assert _warn("Blood counts and urine glucose are normal.") == []


def test_not_normal_no_warning():
    assert _warn("Urine protein is not normal.") == []
