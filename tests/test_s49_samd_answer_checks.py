"""Session 49: SaMD answer checks and report notes.

Lines come from a real run (reports/samd/20261120_170939):
- "Repeat CBC in 3-6 months ... anaemia" was matched to Monocytes 6 %
  and gave a false "in-range result called abnormal" warning;
- accreditation numbers, percentile notes and "Smoker: Upto" lines were
  shown as lab results.
"""
import pytest

from pipelines.samd import report

NOT_RESULTS = [
    "HKLAS 825 S",
    "HOKLAS 825 S",
    "The 99th percentile of Troponin I for normal Male: <34 ng/L",
    "The 99th percentile of Troponin I for normal Female: <16 ng/L",
    "Non Smoker: Upto 5.0 ug/L",
    "Smoker     : Upto 6.5 ug/L",
]


@pytest.mark.parametrize("line", NOT_RESULTS)
def test_report_note_is_not_a_result(line):
    assert report.parse_line(line) is None


@pytest.mark.parametrize("line, status", [
    ("Monocytes 6 % 3 - 11", "normal"),
    ("Glucose: 5.2 mmol/L 3.9 - 6.0", "normal"),
    ("Troponin I-hs <10 ng/L <34", "normal"),
])
def test_real_rows_still_parsed(line, status):
    row = report.parse_line(line)
    assert row is not None and row["status"] == status


MONO = "Monocytes 6 % 3 - 11"


def _in_range_warnings(answer, line=MONO):
    rows = [report.parse_line(line)]
    return [w for w in report.check_answer(rows, answer, case=line)
            if "in-range" in w]


@pytest.mark.parametrize("answer", [
    "- **Repeat CBC in 3\u20136 months** \u2013 To monitor for any future "
    "development of anaemia.",
    "Fatigue for 6 weeks suggests anaemia.",
    "A ferritin of 2-6 would suggest anaemia.",
    "Hb 6.5 g/dL is low.",
])
def test_number_that_is_not_the_value_gives_no_warning(answer):
    assert _in_range_warnings(answer) == []


def test_in_range_value_called_abnormal_still_warns():
    assert _in_range_warnings("Monocytes 6 % is elevated.")


def test_unit_x10_is_not_a_time_word():
    line = "WBC 4.9 x10e9/L 3.7 - 9.3"
    assert _in_range_warnings("WBC 4.9 x10e9/L is low.", line)
