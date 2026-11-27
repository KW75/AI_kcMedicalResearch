"""Session 51 (cont. 6): labelled ranges in other labs' reports.

Made-up lines with the shapes of a real report (no patient data): a sex
band on the result line with the other band below it (CPK), smoker bands
(CEA), 'under 4 ng/ml' (PSA) and a 'Recommended Range' band list (Vitamin
D). The program shows every band and does not pick one ('see bands'). A
value must never be taken from after the unit.
"""
from pipelines.samd import report


def rows(text):
    return report.parse_results([("s.jpg", "transcription", text)])


def test_sex_bands_row():
    got = rows("24 CPK 肌酸磷酸酶 ↑ 300 IU/l Female : 29-168\n"
               "Male : 30-200\n"
               "25 T4 甲狀腺素T4 90.0 nmol/l 62.7-150.8")
    assert len(got) == 2
    cpk = got[0]
    assert cpk["test"].startswith("CPK")
    assert (cpk["value"], cpk["unit"], cpk["flag"], cpk["status"]) == (
        "300", "IU/l", "H", "see bands")
    assert "Female 29-168" in cpk["ref"] and "Male 30-200" in cpk["ref"]
    assert "(value in band)" not in cpk["ref"]
    assert got[1]["test"].startswith("T4") and got[1]["ref"] == "62.7 - 150.8"


def test_smoker_bands_row():
    got = rows("28 CEA 癌胚抗原 2.00 ng/ml Non-smoker : < 5.0\nSmoker : < 10.0")
    assert len(got) == 1
    r = got[0]
    assert r["test"].startswith("CEA") and r["value"] == "2.00"
    assert r["status"] == "see bands"
    assert "Non-smoker" in r["ref"] and "; Smoker" in r["ref"]
    assert r["ref"].count("(value in band)") == 2


def test_under_limit_read_as_upper_limit():
    r = report.parse_line("31 Prostatic Specific Antigen 前列腺特異抗原 1.50 ng/ml under 4 ng/ml")
    assert r is not None
    assert r["test"].startswith("Prostatic Specific Antigen")
    assert (r["value"], r["unit"], r["ref"], r["status"]) == ("1.50", "ng/ml", "<4", "normal")


def test_value_never_taken_from_after_the_unit():
    r = report.parse_line("Ferritin 1.50 ng/ml around 4 ng/ml")
    assert r is None or r["value"] == "1.50"


def test_recommended_range_bands_row():
    got = rows("32 Vitamin D, 25-Hydroxy維他命D 40.0 ng/ml Recommended Range\n"
               "Lack of Vit-D <10\nInsufficiency 10-30\nEnough 30-100\nToxicosis >100")
    assert len(got) == 1
    r = got[0]
    assert r["test"].startswith("Vitamin D") and r["value"] == "40.0"
    assert r["status"] == "see bands"
    for part in ("Lack of Vit-D <10", "Insufficiency 10-30",
                 "Enough 30-100 (value in band)", "Toxicosis >100"):
        assert part in r["ref"], part
    assert r["ref"].count("(value in band)") == 1


def test_band_lines_alone_are_not_rows():
    for line in ("Male : 30-200", "Smoker : < 10.0", "Enough 30-100", "Toxicosis >100"):
        assert report.parse_line(line) is None, line


def test_existing_layouts_unchanged():
    assert report.parse_line("Glucose 5.2 mmol/L 3.9-6.1") == {
        "test": "Glucose", "value": "5.2", "unit": "mmol/L", "ref": "3.9 - 6.1",
        "flag": "", "status": "normal"}
    r = report.parse_line("SCC 鱗狀細胞癌相關抗原 ↑ 3.00 ng/ml Upto 2.5")
    assert (r["value"], r["ref"], r["flag"], r["status"]) == ("3.00", "<=2.5", "H", "HIGH")
    r = report.parse_line("AFP 甲種胎兒球蛋白 2.24 ng/ml < 15.0")
    assert (r["value"], r["ref"], r["status"]) == ("2.24", "<15.0", "normal")
