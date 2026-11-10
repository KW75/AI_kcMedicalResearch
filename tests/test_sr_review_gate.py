# tests/test_sr_review_gate.py
"""F4 gate (Session 37): a mandatory nondet flag (no_majority / table_shift)
keeps a study OUT of the pooled estimate unless a reviewer overrode every
flagged field in study_overrides.yaml.

Baseline 20261110_120707: Jensen (no_majority x4 + table_shift) and Lami
(no_majority on both means) were pooled with numbers not in the PDFs.
"""
import importlib
import logging
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

JENSEN_FLAG = ("mean_intervention:no_majority|sd_intervention:no_majority|"
               "mean_control:no_majority|sd_control:no_majority|table_shift")
LAMI_FLAG = "mean_intervention:no_majority|mean_control:no_majority"
LAMI_FULL_OVERRIDE = ("n_intervention(38->28); n_control(41->36); "
                      "mean_intervention(4.8->7.35); sd_intervention(2.1->2.08); "
                      "mean_control(6.2->7.4); sd_control(2.3->1.29)")


@pytest.fixture
def gate():
    mod = importlib.import_module("pipelines.sr.src.utils.audit_logger")
    fn = getattr(mod, "review_skip_reason", None)
    assert fn is not None, "audit_logger.review_skip_reason missing (F4 gate)"
    return fn


def test_jensen_like_flag_is_skipped(gate):
    reason = gate(JENSEN_FLAG, None)
    assert reason and reason.startswith("needs review: runs disagree")
    assert "table_shift" in reason


def test_lami_like_flag_without_override_is_skipped(gate):
    reason = gate(LAMI_FLAG, None)
    assert reason and "mean_intervention:no_majority" in reason


def test_majority_only_is_pooled(gate):
    assert gate("sd_control:majority", None) is None


@pytest.mark.parametrize("cell", ["unanimous", "single_run", "not_checked", "", None])
def test_unflagged_cells_are_pooled(gate, cell):
    assert gate(cell, None) is None


def test_full_override_lets_flagged_row_through(gate):
    assert gate(LAMI_FLAG, LAMI_FULL_OVERRIDE) is None
    assert gate(JENSEN_FLAG, LAMI_FULL_OVERRIDE) is None


def test_partial_override_still_skips(gate):
    reason = gate(LAMI_FLAG, "n_intervention(absent->28); n_control(absent->36)")
    assert reason and "mean_intervention:no_majority" in reason


def test_table_shift_needs_all_four_numbers_overridden(gate):
    three = "mean_intervention(confirmed 7.35); sd_intervention(confirmed 2.08); mean_control(confirmed 7.4)"
    assert gate("table_shift", three)
    assert gate("table_shift", three + "; sd_control(confirmed 1.29)") is None


def test_effect_size_loop_calls_gate_before_pooling():
    src = (ROOT / "SOURCE_CODE" / "pipelines" / "sr" / "main.py").read_text(encoding="utf-8")
    loop = src[src.index("meta_audit= []"):src.index("write_results(layout.results_csv")]
    assert "review_skip_reason(" in loop, "effect-size loop never calls the F4 gate"
    assert loop.index("review_skip_reason(") < loop.index("rows.append("), \
        "gate must run before the study is appended to the pooled rows"
    assert '"override_fields"' in loop, "audit_row should carry override_fields"


def test_needs_review_with_missing_n_is_not_reported_as_missing_n(caplog):
    main_mod = None
    for cand in ("pipelines.sr.main", "SOURCE_CODE.pipelines.sr.main"):
        try:
            main_mod = importlib.import_module(cand)
            break
        except ImportError:
            continue
    if main_mod is None:
        pytest.skip("pipelines.sr.main not importable from this cwd")
    gated = {"first_author": "Jensen", "year": 2012, "filename": "j.pdf",
             "mean_intervention": 45.6, "sd_intervention": 20.1,
             "mean_control": 57.8, "sd_control": 21.9,
             "n_intervention": None, "n_control": None, "hedges_g": None,
             "nondet_flag": JENSEN_FLAG, "nondet_runs": 3,
             "included_in_meta": False,
             "skip_reason": "needs review: runs disagree (table_shift)"}
    with caplog.at_level(logging.INFO):
        main_mod._log_stage4_summary([gated], [], "SMD")
    txt = "\n".join(caplog.messages)
    assert "needs review" in txt
    assert "for missing per-arm N" not in txt
