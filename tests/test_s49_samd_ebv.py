"""Session 49: a value row printed without a name ("6.9 U <9.0") takes its
name from the nearest line above that has ASCII letters, at most 2 lines up."""
from pipelines.samd import report

# reports/samd/20261120_170939/step2_02_labs_2022-11.pdf.txt lines 307-317
EBV = """Tests Results Unit Ref. Range Results Unit Ref. Range
EBV (VCA) IgA - NPC#
艾巴氏病毒抗體(鼻咽癌)
6.9 U <9.0
Epstein-Barr Virus viral capsid antigen (VCA) IgA - Nasopharyngeal carcinoma
screen
Interpretation
Less than 9.0 U EBV-(VCA)IgA
Negative
Between 9.0 to 11.0 U Borderline
Greater than 11.0 U Positive
"""

NAMED = "Glucose 5.2 mmol/L 3.9 - 6.1"


def _rows(body):
    return report.parse_results([("labs.pdf", "transcription", body)])


def test_ebv_value_takes_name_from_line_above():
    rows = _rows(EBV)
    assert len(rows) == 1  # interpretation lines are still not rows
    r = rows[0]
    assert r["test"] == "EBV (VCA) IgA - NPC"  # '#' marker stripped
    assert (r["value"], r["unit"], r["ref"]) == ("6.9", "U", "<9.0")
    assert r["status"] == "normal"
    assert r["source"] == "labs.pdf"


def test_name_without_marker():
    assert [r["test"] for r in _rows("Ferritin\n6.9 U <9.0")] == ["Ferritin"]


def test_blank_line_stops_lookback():
    assert _rows("EBV (VCA) IgA - NPC#\n\n6.9 U <9.0") == []


def test_three_lines_up_is_out_of_reach():
    assert _rows("EBV (VCA) IgA - NPC#\n艾巴氏\n病毒\n6.9 U <9.0") == []


def test_result_row_above_is_not_borrowed():
    assert report.parse_line(NAMED) is not None  # guard: really a result row
    assert [r["test"] for r in _rows(NAMED + "\n6.9 U <9.0")] == ["Glucose"]


def test_header_above_is_not_a_name():
    assert _rows("Tests Results Unit Ref. Range\n6.9 U <9.0") == []
    assert _rows("Interpretation\n6.9 U <9.0") == []


def test_named_row_unchanged():
    rows = _rows("EBV (VCA) IgA - NPC#\n" + NAMED)
    assert [r["test"] for r in rows] == ["Glucose"]


def test_date_line_is_not_a_result():
    assert _rows("Specimen Received:\n14/Nov/2022 @ 10:11") == []


def test_borderline_on_in_range_ebv_is_warned():
    rows = _rows(EBV)
    warnings = report.check_answer(rows, "EBV VCA IgA 6.9 U is borderline.", EBV)
    assert any("in-range result abnormal" in w and "EBV (VCA) IgA - NPC 6.9 U" in w
               for w in warnings)
    assert not any("not found in the sources" in w for w in warnings)
