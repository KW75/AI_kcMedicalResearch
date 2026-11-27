"""Session 51: the SaMD parser reads other labs' layouts.

Made-up lines with the shapes of two other labs' reports (no patient data):
a row number before the name, a Chinese name after the English one, an
up/down arrow before the value, and value - range - unit order with a (M)
marker. A reference limit must never be read as the value, and a numbered
row must never take its name from a band line above it.
"""
from pipelines.samd import report


def test_row_number_dropped():
    r = report.parse_line("22 SGOT/AST 谷草轉氨酶 25.0 IU/l 5-40")
    assert r is not None
    assert r["test"].startswith("SGOT/AST")
    assert (r["value"], r["unit"], r["ref"], r["status"]) == ("25.0", "IU/l", "5 - 40", "normal")


def test_numbered_row_not_named_from_band_line():
    rows = report.parse_results([("s.jpg", "transcription",
                                  "24 CPK 肌酸磷酸酶 ↑ 300 IU/l Female : 29-168\n"
                                  "Male : 30-200\n"
                                  "25 T4 甲狀腺素T4 90.0 nmol/l 62.7-150.8")])
    t4 = [r for r in rows if r["value"] == "90.0"]
    assert len(t4) == 1
    assert t4[0]["test"].startswith("T4")
    assert t4[0]["ref"] == "62.7 - 150.8"


def test_arrow_before_value_is_flag():
    r = report.parse_line("Glucose 血糖, 空腹 ↑ 7.1 3.9 - 6.0 mmol/L")
    assert r is not None
    assert r["test"] == "Glucose 血糖, 空腹"
    assert (r["value"], r["ref"], r["unit"], r["flag"], r["status"]) == (
        "7.1", "3.9 - 6.0", "mmol/L", "H", "HIGH")


def test_value_range_unit_order():
    r = report.parse_line("Hb 12.0 13.0-17.0 (M) g/dL")
    assert r is not None
    assert (r["test"], r["value"], r["ref"], r["unit"], r["status"]) == (
        "Hb", "12.0", "13.0 - 17.0", "g/dL", "LOW")
    r = report.parse_line("RBC ↓ 4.00 4.30-5.90 (M) x 10^12/L")
    assert r is not None
    assert (r["test"], r["unit"], r["flag"], r["status"]) == ("RBC", "x 10^12/L", "L", "LOW")


def test_limit_not_taken_as_value():
    r = report.parse_line("Total Cholesterol 總膽固醇 6.00 < 5.20 mmol/L")
    assert r is not None
    assert (r["value"], r["ref"], r["unit"], r["status"]) == ("6.00", "<5.20", "mmol/L", "HIGH")
    assert "6.00" not in r["test"]
    r = report.parse_line("ALT ↑ 60 <41 U/L")
    assert r is not None
    assert (r["test"], r["value"], r["ref"], r["flag"], r["status"]) == (
        "ALT", "60", "<41", "H", "HIGH")


def test_old_layout_unchanged():
    assert report.parse_line("Glucose 5.2 mmol/L 3.9-6.1") == {
        "test": "Glucose", "value": "5.2", "unit": "mmol/L", "ref": "3.9 - 6.1",
        "flag": "", "status": "normal"}


def test_nameless_value_line_still_named():
    rows = report.parse_results([("s.pdf", "transcription", "Gamma GT\n6.9 U <9.0")])
    assert [(r["test"], r["value"], r["ref"]) for r in rows] == [("Gamma GT", "6.9", "<9.0")]


def test_numbered_line_never_named_from_above():
    rows = report.parse_results([("s.jpg", "transcription",
                                  "Smoker : < 10.0\n"
                                  "28 CEA 癌胚抗原 2.00 ng/ml Non-smoker : < 5.0")])
    assert not any(r["test"].startswith("Smoker") for r in rows)
