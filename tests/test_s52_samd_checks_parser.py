"""Session 52: SaMD answer checks (power-of-ten units, negation after the term,
'no data on', 'C-reactive protein') and parser leftovers (Colour with a reference
word, Crystals rows, Ep. Cell as a urine name)."""
from pipelines.samd import report


def _row(test, value, unit, ref, status, flag=""):
    return {"test": test, "value": value, "unit": unit, "ref": ref, "flag": flag,
            "status": status, "source": "CKW_Blood test_2025.07.28_HK6, PSA.pdf"}


RBC = _row("RBC 紅血球", "4.45", "x 10^12/L", "4.50 - 6.30", "LOW", "L")
PLT = _row("Platelets 血小板數量", "138", "x 10^9/L", "150 - 400", "LOW", "L")
EOS = _row("Eosinophils", "10", "%", "1 - 6", "HIGH")
PTOT = _row("Protein(Total)", "58", "g/L", "64 - 83", "LOW")
UPROT = _row("Protein - Urine 蛋白質", "1+", "", "Negative", "HIGH")
UBLOOD = _row("Blood - Urine 尿血", "TRACE", "", "Negative", "HIGH", "*")


def _called_normal(rows, s, name):
    return [w for w in report.check_answer(rows, s, s)
            if "out-of-range result normal" in w and name in w]


def test_spaced_power_unit_names_row():
    assert len(_called_normal([RBC], "RBC 4.45 x 10^12/L is within normal range.", "RBC")) == 1


def test_x10e_unit_names_spaced_row():
    assert len(_called_normal([RBC], "RBC 4.45 x10e12/L is within normal range.", "RBC")) == 1


def test_platelets_spaced_unit_names_row():
    assert len(_called_normal([PLT], "Platelets 138 x 10^9/L are normal.", "Platelets")) == 1


def test_superscript_unit_still_names_row():
    s = "RBC 4.45 x10\u00b9\u00b2/L is within normal range."
    assert len(_called_normal([RBC], s, "RBC")) == 1


def test_power_of_ten_is_not_a_value_of_10():
    s = "RBC 4.45 \u00d7 10\u00b9\u00b2/L is normal."
    assert [w for w in report.check_answer([EOS], s, s) if "Eosinophils" in w] == []


def test_proteinuria_is_absent_denied():
    assert len(report.denied_urine_findings([UPROT], "Proteinuria is absent.")) == 1


def test_proteinuria_not_seen_denied():
    assert len(report.denied_urine_findings([UPROT], "Proteinuria was not seen.")) == 1


def test_no_data_on_proteinuria_not_denied():
    assert report.denied_urine_findings([UPROT], "No data on proteinuria are available.") == []


def test_no_evidence_still_denied():
    assert len(report.denied_urine_findings([UPROT], "No evidence of proteinuria.")) == 1


def test_does_not_exclude_is_not_a_denial():
    assert report.denied_urine_findings([UPROT], "This does not exclude proteinuria.") == []


def test_absent_after_contrast_names_right_term():
    out = report.denied_urine_findings(
        [UPROT, UBLOOD], "Proteinuria is present but haematuria is absent.")
    assert len(out) == 1 and "Blood - Urine" in out[0] and "Protein - Urine" not in out[0]


def test_c_reactive_protein_does_not_name_total_protein():
    out = report.unmentioned_abnormal([PTOT], "C-reactive protein is normal.")
    assert len(out) == 1 and "Protein(Total)" in out[0]


def test_total_protein_by_name_still_named():
    assert report.unmentioned_abnormal([PTOT], "Total protein 58 g/L is low.") == []


BODY = "\n".join([
    "URINALYSIS",
    "Colour 顏色 Yellow Yellow",
    "Appearance 外觀 Clear Clear",
    "Ep. Cell 表皮細胞 10 - 17 < 50 cells/ul",
    "Crystals (1) 結晶 Nil",
    "Crystals (2) 結晶 Nil",
    "Released By",
])


def _parsed(body=BODY):
    return report.parse_results([("CKW_Blood test_2025.07.28_HK6, PSA.pdf", "text layer", body)])


def test_colour_with_reference_row():
    rows = [r for r in _parsed() if r["test"].startswith("Colour - Urine")]
    assert len(rows) == 1 and rows[0]["value"] == "YELLOW" and rows[0]["status"] == "normal"


def test_crystals_rows():
    rows = [r for r in _parsed() if r["test"].startswith("Crystals (")]
    assert len(rows) == 2
    assert all("- Urine" in r["test"] and r["value"] == "NIL" for r in rows)


def test_ep_cell_named_urine():
    assert any(r["test"].startswith("Ep. Cell - Urine") for r in _parsed())


def test_upper_case_colour_unchanged():
    body = "\n".join(["URINALYSIS", "Colour 顏色 YELLOW -", "Released By"])
    rows = [r for r in _parsed(body) if r["test"].startswith("Colour")]
    assert len(rows) == 1 and rows[0]["value"] == "YELLOW" and rows[0]["status"] == "no range"
