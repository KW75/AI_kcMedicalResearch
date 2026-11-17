"""Session 42 small fixes (tests first).

1) [SOURCE QUOTE CHECK] summary: a study whose four means/SDs a reviewer
   overrode is no longer listed as "verify each". Run 20261115_213016 still
   listed Karlsson after its override cleared quote_not_found.
2) too_few_runs has its own reason: with only one usable run nothing could
   disagree, so "runs disagree (too_few_runs)" was wrong (Lami, same run).
"""
from pathlib import Path

from pipelines.sr.src.utils import audit_logger as audit

MAIN = (Path(__file__).resolve().parents[1]
        / "SOURCE_CODE" / "pipelines" / "sr" / "main.py")

TOO_FEW = ("needs review: too few usable runs (too_few_runs) - only one "
           "reading returned numbers, so nothing could be compared; "
           "verify against the PDF, or enter all four means/SDs in "
           "input/sr/study_overrides.yaml with a source-page note")
NOT_FOUND = ("intervention source quote was not found verbatim in the extracted "
             "source text | control source quote was not found verbatim in the "
             "extracted source text")
# Karlsson's override_fields from live run 20261115_213016
KARLSSON_ALL_FOUR = ("first_author; year; n_intervention(confirmed 24); "
                     "n_control(confirmed 24); mean_intervention(3.61->3.88); "
                     "sd_intervention(0.85->1.05); mean_control(3.7->3.67); "
                     "sd_control(0.92->0.75)")
THREE = ("mean_intervention(3.61->3.88); sd_intervention(0.85->1.05); "
         "mean_control(3.7->3.67)")


# --- fix 2: too_few_runs wording ---------------------------------------------

def test_too_few_reason_constant():
    assert audit.TOO_FEW_RUNS_REASON == TOO_FEW


def test_too_few_reason_does_not_say_runs_disagree():
    r = audit.review_skip_reason("usable_runs:1/3|too_few_runs")
    assert r and "runs disagree" not in r


def test_too_few_and_quote_gate_named_together():
    r = audit.review_skip_reason("usable_runs:1/3|too_few_runs", "",
                                 NOT_FOUND, "image")
    assert r and "too few usable runs" in r and "quote_not_found" in r


def test_too_few_reason_still_starts_with_needs_review():
    # main.py checks startswith("needs review") to keep it out of the pool
    r = audit.review_skip_reason("usable_runs:1/3|too_few_runs")
    assert r and r.startswith("needs review")


def test_table_shift_wording_unchanged():
    r = audit.review_skip_reason("table_shift")
    assert r.startswith("needs review: runs disagree (table_shift)")


# --- fix 1: quote summary skips reviewer-cleared studies ---------------------

def test_means_sds_overridden():
    assert audit.means_sds_overridden(KARLSSON_ALL_FOUR) is True
    assert audit.means_sds_overridden(THREE) is False
    assert audit.means_sds_overridden(None) is False


def test_split_moves_overridden_study_to_cleared():
    rows = [
        {"first_author": "Karlsson", "source_quote_warning": NOT_FOUND,
         "override_fields": KARLSSON_ALL_FOUR},
        {"first_author": "Jensen", "source_quote_warning": NOT_FOUND,
         "override_fields": None},
    ]
    flagged, cleared = audit.split_quote_flagged(rows)
    assert [r["first_author"] for r in flagged] == ["Jensen"]
    assert [r["first_author"] for r in cleared] == ["Karlsson"]


def test_split_three_overrides_stay_flagged():
    rows = [{"first_author": "Karlsson", "source_quote_warning": NOT_FOUND,
             "override_fields": THREE}]
    flagged, cleared = audit.split_quote_flagged(rows)
    assert len(flagged) == 1 and cleared == []


def test_split_study_without_warning_is_in_neither():
    rows = [{"first_author": "McCrae", "source_quote_warning": None,
             "override_fields": KARLSSON_ALL_FOUR}]
    assert audit.split_quote_flagged(rows) == ([], [])


def test_stage4_summary_uses_split_and_names_cleared_studies():
    src = MAIN.read_text(encoding="utf-8")
    start = src.index("def _log_stage4_summary")
    end = src.find("\ndef ", start + 1)
    body = src[start:end if end != -1 else None]
    assert "split_quote_flagged(" in body
    assert "cleared by reviewer override" in body
