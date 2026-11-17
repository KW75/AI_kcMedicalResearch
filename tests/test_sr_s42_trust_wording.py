"""Session 42 job 1: the Stage-4 summary says "this pooled estimate" only
when a pooled estimate exists (2 or more studies pooled). Run
k20261116_070736 (Karlsson only, held back by quote_not_found) said
"before trusting this pooled estimate" although nothing was pooled.

Pooled = included_in_meta True and no skip_reason (the error path sets
skip_reason without resetting included_in_meta). The checks, counts and
study lists are unchanged; only the wording changes.
"""
from __future__ import annotations

import logging
from pathlib import Path

import pytest

import SOURCE_CODE.pipelines.sr.main as M

POOLED = "this pooled estimate"
NOT_POOLED = "these values (no pooled estimate in this run)"
MAIN = Path(__file__).resolve().parents[1] / "SOURCE_CODE" / "pipelines" / "sr" / "main.py"


def _row(**kw) -> dict:
    row = {
        "run_id": "test", "first_author": "Karlsson", "year": 2015,
        "filename": "k.pdf", "outcome_match": True, "effect_measure": "SMD",
        "hedges_g": 0.226, "ci_lower": -0.34, "ci_upper": 0.79,
        "n_intervention": 24, "n_control": 24,
        "mean_intervention": 3.88, "sd_intervention": 1.05,
        "mean_control": 3.67, "sd_control": 0.75,
        "included_in_meta": False, "skip_reason": None,
        "plausibility_flag": None, "sd_se_warning": None,
        "group_timepoint_warning": None, "source_quote_warning": None,
        "nondet_flag": None, "nondet_runs": 3, "override_fields": "",
    }
    row.update(kw)
    return row


def _pooled(**kw) -> dict:
    kw.setdefault("included_in_meta", True)
    kw.setdefault("skip_reason", None)
    return _row(**kw)


FLAGS = {
    "plausibility": {"plausibility_flag": "|SMD|=2.100 exceeds plausibility bound (1.5)"},
    "sd_se": {"sd_se_warning": "SD quoted from a line containing 'SE'"},
    "group": {"group_timepoint_warning": "identical intervention/control labels"},
    "quote": {"source_quote_warning": "intervention source quote was not found verbatim"},
    "agreement": {"nondet_flag": "mean_control:majority"},
}


def _text(caplog, rows) -> str:
    with caplog.at_level(logging.INFO, logger="sr.main"):
        M._log_stage4_summary(rows, [], "SMD")
    return "\n".join(r.getMessage() for r in caplog.records)


@pytest.mark.parametrize("rows, expected", [
    ([], NOT_POOLED),
    ([_pooled()], NOT_POOLED),
    ([_pooled(), _pooled(first_author="Lami", year=2017)], POOLED),
    ([_pooled(), _row(included_in_meta=True, skip_reason="boom")], NOT_POOLED),
], ids=["none", "one", "two", "one_plus_errored"])
def test_trust_target(rows, expected):
    assert M._trust_target(rows) == expected


@pytest.mark.parametrize("block", sorted(FLAGS))
def test_not_pooled_run_does_not_say_pooled_estimate(caplog, block):
    rows = [_row(skip_reason="needs review: held back", **FLAGS[block])]
    text = _text(caplog, rows)
    assert NOT_POOLED in text, text
    assert POOLED not in text, text
    assert "Karlsson (2015)" in text  # the study is still listed


@pytest.mark.parametrize("block", sorted(FLAGS))
def test_pooled_run_keeps_pooled_estimate_wording(caplog, block):
    rows = [_pooled(**FLAGS[block]), _pooled(first_author="Lami", year=2017)]
    text = _text(caplog, rows)
    assert POOLED in text, text
    assert NOT_POOLED not in text, text


def test_summary_computes_the_target_once():
    src = MAIN.read_text(encoding="utf-8")
    assert "def _trust_target(" in src
    assert src.count("_trust_target(meta_audit)") == 1
