"""Session 51 (cont. 9): '- Urine' only for known urine test names."""
from pipelines.samd import report


SEEN = ["Bacteria", "Bilirubin", "Blood", "Blood Trace *", "Casts", "Clarity", "Colour",
        "Epithelial Cell", "Glucose", "Granular Cast Nil", "Hyaline Cast Nil", "Ketone",
        "Ketones", "Leucocytes", "Leuk. esterase", "Mucous", "Mucus +", "Nitrite",
        "Nitrites", "Others", "pH", "Protein", "RBC", "Sp. Gravity", "Specific Gravity",
        "Urobiligen", "Urobililogen", "Urobilinogen", "WBC", "Yeast"]


def _row(test, unit=""):
    return {"test": test, "value": "", "unit": unit, "ref": "", "flag": "",
            "status": "no range"}


def test_all_seen_urine_names_kept():
    """The 30 English names named '- Urine' in the user's runs keep it."""
    for name in SEEN:
        row = _row(name)
        report._mark_urine(row, True)
        assert row["test"].startswith(name) and " - Urine" in row["test"], name


def test_blood_only_test_not_named_urine():
    row = _row("Sodium 鈉", "mmol/L")
    report._mark_urine(row, True)
    assert row["test"] == "Sodium 鈉"


def test_phosphate_not_taken_as_ph():
    row = _row("Phosphate", "mmol/L")
    report._mark_urine(row, True)
    assert row["test"] == "Phosphate"


def test_rows_after_urinalysis_without_end():
    """A report ending in 'Signed' (no 'Released By'): blood rows below the
    urine rows on the same page are not named '- Urine'."""
    body = "\n".join(["URINALYSIS", "Glucose 5.2 mmol/L 3.9-6.1", "Signed: lab staff",
                      "Sodium 140 mmol/L 135-145", "Potassium 4.1 mmol/L 3.5-5.1"])
    rows = report.parse_results([("made-up.pdf", "transcription", body)])
    names = {r["test"].split()[0]: r["test"] for r in rows}
    assert "- Urine" in names["Glucose"]
    assert "Urine" not in names["Sodium"]
    assert "Urine" not in names["Potassium"]


def test_per_field_unit_still_urine():
    row = _row("WBC 白血球", "cell/HPF")
    report._mark_urine(row, False)
    assert row["test"] == "WBC - Urine 白血球"


def test_name_with_urine_left_alone():
    row = _row("pH - Urine 酸鹼度")
    report._mark_urine(row, True)
    assert row["test"] == "pH - Urine 酸鹼度"


def test_blood_name_outside_section_unchanged():
    row = _row("Glucose", "mmol/L")
    report._mark_urine(row, False)
    assert row["test"] == "Glucose"
