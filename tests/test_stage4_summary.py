"""Regression tests for the Stage-4 summary block (#66).

Pins the property that a zero-extraction run prints '0 of 0' and does
NOT assert that every value was bound to a source quote. Also pins that
the [OUTCOME/TIMEPOINT] block does not emit '? ():' lines for fully-
empty records.
"""
from __future__ import annotations

import logging

import pytest

from SOURCE_CODE.pipelines.sr.main import _log_stage4_summary


def _empty_audit_row(**overrides) -> dict:
    """A meta_audit row shaped as main() builds it, with all extracted
    fields None. Callers set only what a given test needs."""
    row = {
        "run_id": "test",
        "first_author": None,
        "year": None,
        "filename": "x.pdf",
        "outcome_match": None,
        "effect_measure": "SMD",
        "hedges_g": None,
        "ci_lower": None,
        "ci_upper": None,
        "n_intervention": None,
        "n_control": None,
        "mean_intervention": None,
        "sd_intervention": None,
        "mean_control": None,
        "sd_control": None,
        "included_in_meta": False,
        "skip_reason": None,
        "plausibility_flag": None,
        "sd_se_warning": None,
        "group_timepoint_warning": None,
        "source_quote_warning": None,
    }
    row.update(overrides)
    return row


def _all_text(caplog) -> str:
    return "\n".join(r.getMessage() for r in caplog.records)


def test_zero_extraction_run_prints_zero_of_zero(caplog):
    """The motivating case for #66: one included paper, extractor returned
    no data. Old code printed 'every extracted value was bound to a
    verbatim source quote' - a positive assertion that had no evidence."""
    meta_audit = [_empty_audit_row()]
    er = [{"filename": "x.pdf"}]  # no study_metadata, no primary_outcome
    with caplog.at_level(logging.INFO, logger="sr.main"):
        _log_stage4_summary(meta_audit, er, "SMD")
    text = _all_text(caplog)

    # The core #66 property: 0 of 0, not 0 of 1.
    assert "0 flagged of 0 extracted studies" in text, text
    # The false-positive sentence must NOT appear on an empty run.
    assert "every extracted value was bound" not in text, text
    # No '? ():' provenance line for the fully-empty er record.
    assert "? ():" not in text, text
    # But the label headers must still appear ('always set the key').
    for label in ("[PLAUSIBILITY]", "[SD/SE CHECK]",
                  "[GROUP/TIMEPOINT CHECK]", "[SOURCE QUOTE CHECK]",
                  "[OUTCOME/TIMEPOINT]"):
        assert label in text, f"missing {label} in:\n{text}"


def test_one_clean_study_still_asserts_positive(caplog):
    """Regression guard: don't accidentally suppress the 'clean' sentence
    on a real, non-empty run."""
    meta_audit = [_empty_audit_row(
        first_author="Smith", year=2020,
        mean_intervention=1.0, sd_intervention=0.5,
        mean_control=0.5, sd_control=0.5,
        n_intervention=30, n_control=30,
        hedges_g=1.0, ci_lower=0.5, ci_upper=1.5,
        included_in_meta=True,
    )]
    er = [{
        "filename": "smith2020.pdf",
        "extraction_method": "vision",
        "study_metadata": {"first_author": "Smith", "year": 2020},
        "primary_outcome": {"outcome_selected": "BDI",
                            "timepoint_selected": "post"},
    }]
    with caplog.at_level(logging.INFO, logger="sr.main"):
        _log_stage4_summary(meta_audit, er, "SMD")
    text = _all_text(caplog)

    assert "0 flagged of 1 extracted studies" in text, text
    assert "every extracted value was bound" in text, text
    # OUTCOME/TIMEPOINT should show the real study.
    assert "Smith (2020): outcome=BDI | timepoint=post" in text, text


def test_flagged_study_reports_real_denominator(caplog):
    """When something is flagged, the denominator is n_extracted, not
    len(meta_audit). Guard against the case where meta_audit contains
    skipped-empty rows alongside extracted ones."""
    meta_audit = [
        _empty_audit_row(),  # skipped, no data
        _empty_audit_row(
            first_author="Jones", year=2021,
            mean_intervention=2.0, sd_intervention=0.5,
            source_quote_warning="number not found in quote",
        ),
    ]
    er = [
        {"filename": "empty.pdf"},
        {"filename": "jones2021.pdf",
         "study_metadata": {"first_author": "Jones", "year": 2021},
         "primary_outcome": {}},
    ]
    with caplog.at_level(logging.INFO, logger="sr.main"):
        _log_stage4_summary(meta_audit, er, "SMD")
    text = _all_text(caplog)

    # One extracted, one flagged. NOT '1 of 2'.
    assert "1 of 1 extracted studies" in text, text
    assert "Jones (2021)" in text, text
