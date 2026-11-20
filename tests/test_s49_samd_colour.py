"""Session 49: urinalysis Colour / Clarity / Appearance rows are read as
text results with no printed reference (status 'no range')."""
import pytest

from pipelines.samd import report


@pytest.mark.parametrize("line, name, value", [
    ("Colour 順色 YELLOW -", "Colour 順色", "YELLOW"),
    ("Clarity 清晰度 CLEAR -", "Clarity 清晰度", "CLEAR"),
    ("Colour PALE YELLOW", "Colour", "PALE YELLOW"),
    ("Appearance SLIGHTLY TURBID -", "Appearance", "SLIGHTLY TURBID"),
    ("Colour RED -", "Colour", "RED"),
])
def test_descriptive_row(line, name, value):
    r = report.parse_line(line)
    assert r is not None
    assert (r["test"], r["value"], r["unit"], r["ref"], r["flag"], r["status"]) == (
        name, value, "", "", "", "no range")


@pytest.mark.parametrize("line", [
    "Colour 順色 BLUE -",
    "Priority: ROUTINE",
    "Colour of urine was yellow",
])
def test_not_a_descriptive_result(line):
    assert report.parse_line(line) is None


def test_descriptive_row_in_report_table():
    rows = report.parse_results([("labs.pdf", "transcription",
                                  "Colour 順色 YELLOW -\nClarity 清晰度 CLEAR -")])
    assert [(r["test"], r["value"]) for r in rows] == [
        ("Colour 順色", "YELLOW"), ("Clarity 清晰度", "CLEAR")]
    md = report.build_markdown(run_id="r", intended_use="u", doctor_text="",
                               rows=rows, warnings=[], answer="", sources=[])
    assert "| Colour 順色 | YELLOW |" in md
    assert "| Clarity 清晰度 | CLEAR |" in md


def test_descriptive_row_not_in_in_range_check():
    row = report.parse_line("Colour 順色 YELLOW -")
    assert row is not None
    w = report.check_answer([row], "Urine colour YELLOW is abnormal.", case="")
    assert not any("in-range" in x for x in w)
