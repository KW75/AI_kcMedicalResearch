"""Session 49: urinalysis rows the main pattern skipped. Lines from
reports/samd/20261120_170939 (step2_02, lines 422-441): text results,
count ranges, numbers without a unit and 'up to N' references. Protein 1+
with the report's up arrow was abnormal and missing from the table.
"""
import pytest

from pipelines.samd import report

ROWS = [
    ("Glucose - Urine 尿糖 NEGATIVE Negative", "NEGATIVE", "", "Negative", "", "normal"),
    ("Blood - Urine 潛血 NEGATIVE Up to trace", "NEGATIVE", "", "Up to trace", "", "normal"),
    ("Protein - Urine 蛋白質 1+ \u2191 Up to trace", "1+", "", "Up to trace", "H", "HIGH"),
    ("Urobiligen - Urine 尿膽原 < 16 umol/L up to 16", "<16", "umol/L", "<=16", "", "normal"),
    ("WBC 白血球 NIL cell/HPF \u22645", "NIL", "cell/HPF", "<=5", "", "normal"),
    ("RBC 紅血球 1-3 cell/HPF \u22645", "1-3", "cell/HPF", "<=5", "", "normal"),
    ("Casts 圓柱類 NOT SEEN", "NOT SEEN", "", "", "", "no range"),
    ("Mucous 粘液絲 TRACE", "TRACE", "", "", "", "no range"),
    ("pH - Urine 酸鹼度 5.5 5.0 - 8.0", "5.5", "", "5.0 - 8.0", "", "normal"),
    ("Specific Gravity 比重 1.025 1.005 - 1.030", "1.025", "", "1.005 - 1.030", "", "normal"),
    ("Epithelial Cell 上皮細胞 3-5 cell/LPF", "3-5", "cell/LPF", "", "", "no range"),
]


@pytest.mark.parametrize("line, value, unit, ref, flag, status", ROWS)
def test_urinalysis_row(line, value, unit, ref, flag, status):
    r = report.parse_line(line)
    assert r is not None
    assert r["test"].split()[0] == line.split()[0]
    assert (r["value"], r["unit"], r["ref"], r["flag"], r["status"]) == (
        value, unit, ref, flag, status)


@pytest.mark.parametrize("line", [
    "Ketones - Urine TRACE Negative",
    "Protein - Urine 2+ Negative",
])
def test_text_result_above_reference_is_high(line):
    assert report.parse_line(line)["status"] == "HIGH"


@pytest.mark.parametrize("line", [
    "Negative",
    "Less than 9.0 U EBV-(VCA)IgA",
    "Between 9.0 to 11.0 U Borderline",
    "Greater than 11.0 U Positive",
    "Non Diabetic patient < 6.4 3.9 - 6.0",
    "HKLAS 825",
    "Non Smoker: Upto 5.0",
    "6.9 U <9.0",
    "Page 1 of 3",
])
def test_not_a_result(line):
    assert report.parse_line(line) is None


def test_text_row_not_in_in_range_check():
    rows = [report.parse_line("Glucose - Urine NEGATIVE Negative")]
    w = report.check_answer(rows, "Urine glucose NEGATIVE is abnormal.", case="")
    assert not any("in-range" in x for x in w)


def test_text_row_in_report_table():
    rows = report.parse_results([("labs.pdf", "transcription",
                                  "Protein - Urine 蛋白質 1+ \u2191 Up to trace")])
    md = report.build_markdown(run_id="r", intended_use="u", doctor_text="",
                               rows=rows, warnings=[], answer="", sources=[])
    assert "| Protein - Urine 蛋白質 | 1+ | - | Up to trace | H | **HIGH** | labs.pdf |" in md
