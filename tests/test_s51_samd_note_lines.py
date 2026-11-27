"""Session 51 (cont. 7): reference-note lines in a lipid section are not results."""
from pipelines.samd import report


def test_band_label_note_not_a_row():
    """'Normal : < 1.7 mmol/L' under a lipid result is a band note."""
    assert report.parse_line("Normal        :     < 1.7 mmol/L") is None
    assert report.parse_line("Very High     :     > 4.9 mmol/L") is None


def test_risk_factor_note_not_a_row():
    """Risk-factor targets; '0-1' is a count, not a value (PR #104 extra row)."""
    assert report.parse_line("Target in patients 0-1 risk factors       : < 3.4 mmol/L") is None
    assert report.parse_line("Target in patients 2 or more risk factors : < 2.6 mmol/L") is None


def test_dash_note_not_a_row():
    assert report.parse_line("Optimal for adults - Low risk 2.6 mmol/L") is None


def test_group_target_note_not_a_row():
    assert report.parse_line("CHD & DM High Risk               <1.8 mmol/L") is None


def test_result_with_range_kept():
    """A note word in the name is fine when the row has a printed range."""
    row = report.parse_line("Low Density Lipoprotein 2.90 < 3.40 mmol/L")
    assert row is not None
    assert row["value"] == "2.90" and row["ref"]


def test_high_sensitivity_and_density_kept():
    row = report.parse_line("High Sensitivity CRP 0.8 mg/L")
    assert row is not None and row["value"] == "0.8"
    row = report.parse_line("Low Density Lipoprotein 2.9 mmol/L")
    assert row is not None and row["value"] == "2.9"
