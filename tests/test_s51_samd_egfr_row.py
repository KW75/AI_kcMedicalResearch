"""Session 51 (cont. 14): eGFR printed as name + value only (made-up lines)."""
from pipelines.samd import report

LINE = "e-GFR 腎小球濾過率, 估算 68"


def test_egfr_value_only_line():
    row = report.parse_line(LINE)
    assert row is not None
    assert row["test"].startswith("e-GFR")
    assert row["value"] == "68"


def test_egfr_row_has_no_range():
    row = report.parse_line(LINE)
    assert row is not None
    assert (row["unit"], row["ref"], row["status"]) == ("", "", "no range")


def test_ckd_check_reads_the_row():
    rows = [r for r in (report.parse_line(LINE),) if r]
    w = report.ckd_stage_mismatch(
        rows, "Working diagnosis: chronic kidney disease (CKD) stage 3.")
    assert w and "68" in " ".join(w)


def test_note_lines_not_rows():
    for line in ("2. eGFR >90 is normal unless there is other evidence of kidney disease",
                 "1. eGFR unit: ml/min/1.73m².",
                 "3. eGFR result is calculated using 'CKD-EPI 2021 Creatinine' equation,",
                 "Glomerular Filtration Rate (eGFR) 腎",
                 "eGFR"):
        assert report.parse_line(line) is None, line


def test_full_egfr_line_unchanged():
    row = report.parse_line("eGFR ≥60 mL/min ≥60")
    assert (row["value"], row["unit"], row["ref"]) == (">=60", "mL/min", ">=60")
