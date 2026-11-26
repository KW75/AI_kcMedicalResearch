"""Session 50: an exception clause ('apart from', 'except for', 'other than',
'besides', 'aside from') names the rows that are NOT normal, so
"Urinalysis normal apart from protein 1+" is no longer warned."""
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


def test_apart_from_not_warned():
    assert _warn("Urinalysis normal apart from protein 1+.") == []


def test_except_for_not_warned():
    assert _warn("Urinalysis is normal except for protein 1+.") == []


def test_other_than_not_warned():
    assert _warn("Urine findings are normal other than protein 1+.") == []


def test_besides_two_rows_not_warned():
    assert _warn("Urinalysis normal besides protein 1+ and blood 2+.") == []


def test_leading_apart_from_clause_not_warned():
    assert _warn("Apart from protein 1+, the urinalysis is normal.") == []


def test_everything_except_not_warned():
    assert _warn("Everything except urine protein is normal.") == []


def test_row_named_before_the_clause_still_warned():
    w = _warn("Urine protein is normal apart from the colour.")
    assert len(w) == 1 and "Protein - Urine 蛋白質 1+ (HIGH" in w[0]


def test_warning_quotes_the_whole_sentence():
    w = _warn("Urine protein is normal, aside from the colour.")
    assert len(w) == 1 and "aside from the colour" in w[0]


def test_normal_claim_after_the_clause_warned():
    w = _warn("Urinalysis normal apart from protein 1+, and urine blood is normal.")
    assert len(w) == 1 and "Blood - Urine" in w[0]


def test_leading_clause_then_claim_warned():
    w = _warn("Apart from protein 1+, urine blood is normal.")
    assert len(w) == 1 and "Blood - Urine" in w[0]


def test_abnormal_word_in_the_clause_does_not_hide_the_claim():
    w = _warn("Urinalysis normal apart from raised protein 1+, urine blood is normal.")
    assert len(w) == 1 and "Blood - Urine" in w[0]


def test_word_starting_with_except_is_not_a_clause():
    w = _warn("Without exception, urine protein is normal.")
    assert len(w) == 1 and "Protein - Urine" in w[0]
