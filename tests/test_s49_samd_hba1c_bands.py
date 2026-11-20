"""Session 49: a result printed without a range (HbA1c 6.1 %) with a band
table on the lines below it. Lines from reports/samd/20261120_170939
(step2_03, lipid/HbA1c photo). Bands may overlap, so every band the value
falls in is marked and no single status is picked.
"""
from pipelines.samd import report

BODY = "\n".join([
    "Glucose Fasting                空腹血糖           5.7       mmol/L    3.9 - 6.0",
    "HbA1c                          糖化血色素         6.1       %",
    "Interpretation                 HbA1c (%)         FBS",
    "Non Diabetic patient            < 6.4             3.9 - 6.0",
    "Increased risk for future diabetes   5.7 - 6.4     6.1 - 6.9 (IFG)",
    "Diagnostic for Diabetes (ADA)    >= 6.5          >= 7.0",
    "Target of Glycaemic Control      <= 7.0",
    "for Diabetic patient",
    "",
    "Note:-1.Some factors may influence HbA1c result",
])


def _rows():
    return report.parse_results([("labs.jpg", "transcription", BODY)])


def _hba1c():
    return next(r for r in _rows() if r["test"].startswith("HbA1c"))


def test_hba1c_gets_printed_bands():
    r = _hba1c()
    assert r["status"] == "see bands"
    assert "Diagnostic for Diabetes (ADA) >= 6.5" in r["ref"]
    assert "Diagnostic for Diabetes (ADA) >= 6.5 (value in band)" not in r["ref"]


def test_bands_come_from_the_hba1c_column_not_fbs():
    ref = _hba1c()["ref"]
    assert ref and "3.9 - 6.0" not in ref and "6.1 - 6.9" not in ref


def test_band_label_continues_on_next_line():
    assert ("Target of Glycaemic Control for Diabetic patient <= 7.0 "
            "(value in band)") in _hba1c()["ref"]


def test_overlapping_bands_are_all_marked():
    ref = _hba1c()["ref"]
    assert "Non Diabetic patient < 6.4 (value in band)" in ref
    assert "Increased risk for future diabetes 5.7 - 6.4 (value in band)" in ref


def test_note_after_blank_line_is_not_a_band():
    assert "Note" not in _hba1c()["ref"]


def test_row_with_own_range_keeps_it():
    g = next(r for r in _rows() if r["test"].startswith("Glucose"))
    assert g["ref"] == "3.9 - 6.0" and g["status"] == "normal"


def test_band_lines_are_not_results():
    assert len(_rows()) == 2


def test_no_band_table_stays_no_range():
    rows = report.parse_results([("x", "transcription",
                                  "HbA1c 6.1 %\n\nCholesterol Total 3.20 mmol/L <5.17")])
    assert rows[0]["status"] == "no range"


def test_band_row_is_not_checked_as_in_range():
    w = report.check_answer(_rows(), "HbA1c 6.1 % is raised.", case=BODY)
    assert not any("HbA1c" in x for x in w)


def test_band_row_listed_before_normal_rows():
    md = report.build_markdown(run_id="r", intended_use="u", doctor_text="",
                               rows=_rows(), warnings=[], answer="", sources=[])
    assert md.index("HbA1c") < md.index("Glucose Fasting")
