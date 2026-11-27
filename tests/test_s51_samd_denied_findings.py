"""Session 51 (cont. 17): negated words and denied urine findings (made-up rows)."""
from pathlib import Path

from pipelines.samd import report


def row(test, value, unit, ref, status, flag=""):
    return {"test": test, "value": value, "unit": unit, "ref": ref,
            "flag": flag, "status": status, "source": "made-up"}


PROT = row("Protein - Urine 蛋白質", "1+", "", "Negative", "HIGH")
PROT_NEG = row("Protein - Urine 蛋白質", "NEGATIVE", "", "Negative", "normal")
BLOOD = row("Blood - Urine 尿血", "TRACE", "", "Negative", "HIGH", "*")
RBC_U = row("RBC - Urine 紅血球", "10-17", "cells/ul", "<9", "HIGH")
RBC = row("RBC 紅血球", "4.45", "x 10^12/L", "4.50 - 6.30", "LOW", "L")
HB = row("Haemoglobin 血紅素", "13.8", "g/dl", "13.5 - 18.0", "normal")


def test_no_proteinuria_warns():
    w = report.denied_urine_findings([PROT], "No proteinuria or significant albuminuria is reported.")
    assert len(w) == 1 and "Protein - Urine" in w[0]


def test_no_hematuria_warns_blood_and_rbc():
    w = report.denied_urine_findings([BLOOD, RBC_U], "Trace blood is noted but no hematuria confirmed.")
    assert len(w) == 1 and "Blood - Urine" in w[0] and "RBC - Urine" in w[0]


def test_proteinuria_present_no_warning():
    assert report.denied_urine_findings([PROT], "Dipstick shows proteinuria (protein 1+).") == []


def test_normal_urine_protein_no_warning():
    assert report.denied_urine_findings([PROT_NEG], "No proteinuria.") == []


def test_no_anaemia_does_not_hide_called_normal():
    s = ("There is no evidence of anaemia as haemoglobin is 13.8 g/dL and RBC count "
         "is 4.45 x10¹²/L (both within normal range for age and sex).")
    w = report.check_answer([RBC], s, s)
    assert any("out-of-range" in x for x in w)


def test_no_anaemia_no_false_in_range():
    s = "Haemoglobin is 13.8 g/dl, so there is no anaemia."
    w = report.check_answer([HB], s, s)
    assert not any("in-range" in x for x in w)


def test_low_and_normal_words_unchanged():
    s = "RBC count is slightly low at 4.45 x 10^12/L while haemoglobin is normal."
    w = report.check_answer([RBC], s, s)
    assert not any("out-of-range" in x for x in w)


def test_cli_shows_the_warning():
    cli = Path(report.__file__).with_name("cli.py").read_text(encoding="utf-8")
    assert "denied_urine_findings(rows, answer)" in cli
