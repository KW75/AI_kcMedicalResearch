"""Session 51 (cont. 10): urine rows printed as result - reference - unit."""
from pipelines.samd import report



def _urine(line):
    rows = report.parse_results([("made-up.pdf", "transcription", "URINALYSIS 尿液\n" + line)])
    assert len(rows) == 1, rows
    return rows[0]


def test_trace_with_star_is_high():
    r = _urine("Blood 尿血 Trace * Negative")
    assert r["test"] == "Blood - Urine 尿血"
    assert (r["value"], r["ref"], r["flag"], r["status"]) == ("TRACE", "Negative", "*", "HIGH")


def test_plus_against_nil_is_high():
    r = _urine("Mucus 粘液 + Nil")
    assert (r["value"], r["ref"], r["status"]) == ("+", "Nil", "HIGH")


def test_nil_nil_with_unit():
    r = _urine("Hyaline Cast 透明柱體 Nil Nil /HPF")
    assert r["test"] == "Hyaline Cast - Urine 透明柱體"
    assert (r["value"], r["unit"], r["ref"], r["status"]) == ("NIL", "/HPF", "Nil", "normal")


def test_nil_nil_without_unit():
    r = _urine("Bacteria 細菌 Nil Nil")
    assert (r["value"], r["unit"], r["ref"], r["status"]) == ("NIL", "", "Nil", "normal")


def test_count_value_range_unit():
    r = _urine("RBC 紅血球 1 - 2 < 5 cells/ul")
    assert (r["value"], r["unit"], r["ref"], r["status"]) == ("1-2", "cells/ul", "<5", "normal")


def test_count_above_limit_is_high():
    r = _urine("WBC 白血球 10 - 20 < 5 cells/ul")
    assert r["status"] == "HIGH"


def test_protein_row_unchanged():
    """A row the old parser already read with a reference is kept as it was."""
    r = _urine("Protein 蛋白 1+ Negative")
    assert (r["value"], r["ref"], r["status"]) == ("1+", "Negative", "HIGH")
