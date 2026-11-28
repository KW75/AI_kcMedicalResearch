"""Session 52 (cont. 1): plural test names, lone '-' unit column, A/G naming.
Values are shaped like real reports but are not patient values."""
from pipelines.samd import report


def _row(test, value, unit, ref, flag, status):
    return {"test": test, "value": value, "unit": unit, "ref": ref, "flag": flag, "status": status}


PLT = _row("Platelet Count", "118", "x10e9/L", "160 - 420", "", "LOW")
MONO = _row("Monocyte", "13.0", "%", "2.0 - 12.0", "H", "HIGH")
RBC = _row("RBC Count", "4.21", "x10e12/L", "4.40 - 5.80", "", "LOW")
AG = _row("A/G Ratio", "2.2", "", "0.8 - 2.0", "H", "HIGH")


def _listed(rows, answer):
    w = report.unmentioned_abnormal(rows, answer)
    return w[0] if w else ""


def test_platelets_plural_names_platelet_count():
    # answer shape from run 20261128_065727
    assert "Platelet Count" not in _listed(
        [PLT], "The patient also has thrombocytopenia (platelets 118 x10\u2079/L).")


def test_monocytes_plural_names_monocyte():
    assert "Monocyte" not in _listed([MONO], "Monocytes are raised at 13.0%.")


def test_urine_rbcs_still_not_blood_rbc():
    assert "RBC Count" in _listed([RBC], "Urine shows 10\u201317 RBCs/ul.")


def test_singular_platelet_count_still_named():
    assert _listed([PLT], "Platelet count 118 x10e9/L is low.") == ""


def test_dash_unit_row_high_arrow():
    row = report.parse_line("A/G Ratio 2.2 \u2191 - 0.8 - 2.0")
    assert row is not None
    assert (row["value"], row["flag"], row["status"]) == ("2.2", "H", "HIGH")


def test_dash_unit_row_low_arrow():
    row = report.parse_line("A/G Ratio 0.6 \u2193 - 0.8 - 2.0")
    assert row is not None
    assert (row["value"], row["flag"], row["status"]) == ("0.6", "L", "LOW")


def test_dash_unit_row_no_arrow():
    row = report.parse_line("A/G Ratio 1.5 - 0.8 - 2.0")
    assert row is not None
    assert row["value"] == "1.5" and not row["flag"] and row["status"] == "normal"


def test_dash_unit_refuses_low_above_high():
    assert report.parse_line("A/G Ratio 2.2 - 3.0 - 2.0") is None


def test_normal_unit_row_unchanged():
    row = report.parse_line("GGT 12 U/L 10 - 71")
    assert row is not None
    assert (row["value"], row["status"]) == ("12", "normal")


def test_ag_named_by_ag():
    assert _listed([AG], "The A/G ratio is slightly elevated at 2.2 (normal: 0.8\u20132.0).") == ""


def test_acr_does_not_name_ag_ratio():
    assert "A/G Ratio" in _listed([AG], "Suggested next test: urine albumin-to-creatinine ratio.")


def test_ag_named_by_albumin_globulin():
    assert _listed([AG], "Albumin/globulin ratio 2.2 is high.") == ""
