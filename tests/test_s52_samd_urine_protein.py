"""Session 52 (cont. 6): 'urine protein' does not name serum Protein(Total); the blood
group letter is part of the value. Values below are synthetic."""
from pipelines.samd import report

TP = {"test": "Protein(Total)", "value": "55", "unit": "g/L", "ref": "64 - 83", "flag": "",
      "status": "LOW", "source": "x.pdf"}
UP = {"test": "Protein - Urine", "value": "1+", "unit": "", "ref": "Negative", "flag": "",
      "status": "HIGH", "source": "x.pdf"}


def _listed(rows, answer, name):
    w = report.unmentioned_abnormal([dict(r) for r in rows], answer)
    return bool(w) and name in w[0]


def test_urine_protein_does_not_name_total_protein():
    assert _listed([TP], "Working diagnosis: CKD with mild proteinuria (urine protein 1+).", "Protein(Total)")


def test_urinary_protein_does_not_name_total_protein():
    assert _listed([TP], "Urinary protein excretion should be quantified.", "Protein(Total)")


def test_protein_in_urine_does_not_name_total_protein():
    assert _listed([TP], "There is 1+ protein in the urine.", "Protein(Total)")


def test_total_protein_still_named():
    assert not _listed([TP], "Total protein 55 g/L is low.", "Protein(Total)")


def test_urine_protein_row_still_named():
    assert report.unmentioned_abnormal([dict(UP)], "Urine protein 1+ suggests glomerular damage.") == []


def test_blood_group_letter_in_value():
    r = report.parse_line("Blood group                           O Positive")
    assert r["test"].strip() == "Blood group"
    assert r["value"] == "O POSITIVE"
    assert r["status"] == "no range"
