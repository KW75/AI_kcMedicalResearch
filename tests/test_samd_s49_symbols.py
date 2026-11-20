"""Session 49: SaMD lab-line parser handles <=/>= symbols and skips
reference-note lines.

Lab reports print limits as \u2264 / \u2265 (or full-width \uff1c / \uff1e)
and ranges with an en dash; parse_line only knew ASCII, so those rows were
dropped. A risk-band note line was read as a result with unit "(IFG)".
"""
from SOURCE_CODE.pipelines.samd import report as r


def _row(line):
    row = r.parse_line(line)
    assert row is not None, line
    return row


def test_le_reference():
    row = _row("ALT (SGPT)   28   U/L   \u226441")
    assert (row["test"], row["value"], row["unit"], row["ref"], row["status"]) == (
        "ALT (SGPT)", "28", "U/L", "<=41", "normal")


def test_ge_value_and_reference():
    row = _row("eGFR \u226560 mL/min \u226560")
    assert (row["value"], row["ref"], row["status"]) == (">=60", ">=60", "normal")


def test_le_boundary_and_high():
    assert _row("Bilirubin 11 umol/L \u226421")["status"] == "normal"
    assert _row("Bilirubin 21 umol/L \u226421")["status"] == "normal"
    assert _row("Bilirubin 25 umol/L \u226421")["status"] == "HIGH"


def test_fullwidth_less_than():
    row = _row("Glucose 5.2 mmol/L \uff1c7.8")
    assert (row["ref"], row["status"]) == ("<7.8", "normal")


def test_en_dash_range():
    row = _row("Platelets 134 x10^9/L 160 \u2013 420")
    assert (row["ref"], row["status"]) == ("160 - 420", "LOW")


def test_real_platelet_line_with_chinese_name():
    row = _row("Platelet Count          \u8840\u5c0f\u677f\u8a08\u6578"
               "         134            x10e9/L          160 - 420")
    assert row["test"].startswith("Platelet Count")
    assert (row["value"], row["unit"], row["ref"], row["status"]) == (
        "134", "x10e9/L", "160 - 420", "LOW")


def test_risk_band_note_is_not_a_result():
    assert r.parse_line(
        "Increased risk for future diabetes 5.7 - 6.4 6.1 - 6.9 (IFG)") is None


def test_accreditation_and_note_lines_skipped():
    assert r.parse_line("HKLAS 825") is None
    assert r.parse_line("Non Smoker: Upto 5.0") is None


def test_ordinary_row_still_parses():
    row = _row("Vitamin B12 350 pmol/L 145 - 569")
    assert (row["test"], row["status"]) == ("Vitamin B12", "normal")
def test_superscript_unit_kept():
    """No NFKC here (the OCR pipeline uses it only to compare fills):
    it would turn x10^9 written with a superscript 9 into x109."""
    row = _row("WBC 6.2 x10\u2079/L 4.0 - 10.0")
    assert (row["unit"], row["status"]) == ("x10\u2079/L", "normal")
