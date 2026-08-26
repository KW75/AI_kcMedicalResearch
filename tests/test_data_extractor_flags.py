"""
Regression tests for the deterministic extraction tripwires in
data_extractor.py.

Covers three related fixes:
  - _flag_possible_se_as_sd            (Known Issue #9)
  - _flag_group_timepoint_confusion    (Known Issue #10)
  - _collect_candidate_group_names /
    _infer_group_timepoint_from_text   (removed hardcoded trial-specific
                                         literals, generalized to any trial)

None of these need network access or real API credentials - they're pure
data-transformation logic. DataExtractor's __init__ still builds a
provider client, so tests pass a dummy api_key explicitly to avoid needing
a real DASHSCOPE_API_KEY in the environment.

Run with: python -m pytest test_data_extractor_flags.py -v
"""
import pytest

from pipelines.sr.src.extraction.data_extractor import DataExtractor


@pytest.fixture
def extractor():
    return DataExtractor(
        pico_criteria={"outcome": "pain"},
        provider="qwen",
        api_key="dummy-not-a-real-key",
    )


# ---------------------------------------------------------------------------
# #9: SD/SE confusion tripwire
# ---------------------------------------------------------------------------

def test_se_flag_fires_on_documented_zsy234_pattern(extractor):
    """The exact failure pattern from Session 8: SE values copied into SD fields."""
    zsy234_text = (
        "Regardless of treatment condition, participants reported less "
        "morning pain at posttreatment (M = 47.14, SE = 2.36) relative to "
        "baseline (M = 52.67, SE = 2.27)."
    )
    result = {
        "primary_outcome": {
            "mean_intervention": 47.14, "sd_intervention": 2.36,
            "mean_control": 52.67, "sd_control": 2.27,
        }
    }
    out = extractor._flag_possible_se_as_sd(result, zsy234_text)
    assert "sd_se_warning" in out
    assert "intervention" in out["sd_se_warning"]
    assert "control" in out["sd_se_warning"]


def test_se_flag_silent_on_genuine_sd(extractor):
    """A real SD extraction with no SE mentioned nearby must not be flagged."""
    clean_text = "Group A: mean 7.35, SD 2.08 at 12 weeks."
    result = {"primary_outcome": {"sd_intervention": 2.08}}
    out = extractor._flag_possible_se_as_sd(result, clean_text)
    assert "sd_se_warning" in out and out["sd_se_warning"] is None


def test_se_flag_noop_without_text(extractor):
    """No source text (e.g. vision path) - must not crash, must not flag."""
    result = {"primary_outcome": {"sd_intervention": 2.08}}
    out = extractor._flag_possible_se_as_sd(result, "")
    assert "sd_se_warning" not in out


# ---------------------------------------------------------------------------
# #10: within/between-group confusion tripwire
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("intervention_group,control_group,should_flag", [
    ("baseline", "posttreatment", True),           # zsy234-style
    ("Baseline", "Follow-up", True),                # different wording/casing
    ("CBT", "CBT", True),                           # same group named twice
    ("Week 12", "Usual Care", True),                # one side is a timepoint
    ("CBT-IP", "UMC", False),                       # genuine two-arm trial
    ("Metformin", "Placebo", False),                # different genuine trial
    ("Exercise Therapy", "Waitlist Control", False),# "Control" alone must not trip it
    (None, None, False),                            # nothing extracted
])
def test_group_timepoint_confusion(extractor, intervention_group, control_group, should_flag):
    result = {"intervention_group": intervention_group, "control_group": control_group}
    extractor._flag_group_timepoint_confusion(result)
    if should_flag:
        assert "group_timepoint_warning" in result, (
            f"expected a flag for intervention={intervention_group!r} "
            f"control={control_group!r}, got none"
        )
    else:
        assert ("group_timepoint_warning" in result
            and result["group_timepoint_warning"] is None), (    
            f"unexpected flag for intervention={intervention_group!r} "
            f"control={control_group!r}: {result.get('group_timepoint_warning')}"
        )


def test_group_timepoint_confusion_wired_into_coerce(extractor):
    """The check must actually run as part of normal result coercion, not
    just be callable in isolation - this guards the wiring, not just the
    logic."""
    result = {"intervention_group": "baseline", "control_group": "posttreatment"}
    out = extractor._coerce_extraction_result(result)
    assert "group_timepoint_warning" in out


# ---------------------------------------------------------------------------
# Generalized group-name matching (replaced hardcoded CBT-IP/CBT-P/UMC)
# ---------------------------------------------------------------------------

def test_infer_group_timepoint_still_works_for_original_trial(extractor):
    """The trial the old hardcoded literals were written for must still work,
    now driven by data instead of hardcoded strings."""
    ang_text = (
        "CBT-IP 7.58 (1.75) 7.35 (2.08) 7.21 (1.79)\n"
        "UMC 8.10 (1.90) 7.95 (1.85) 7.80 (1.70)"
    )
    group, timepoint = extractor._infer_group_timepoint_from_text(
        ang_text, mean_value=7.35, sd_value=2.08,
        candidate_groups=["CBT-IP", "UMC"],
    )
    assert group == "CBT-IP"
    assert timepoint == "post-treatment"


def test_infer_group_timepoint_generalizes_to_different_trial(extractor):
    """A completely different trial's arm names, previously impossible to
    match at all since the old code only recognized three hardcoded
    literals from one specific paper."""
    metformin_text = (
        "Metformin 5.2 (0.8) 4.9 (0.7) 4.5 (0.6)\n"
        "Placebo 5.3 (0.9) 5.1 (0.8) 5.0 (0.7)"
    )
    group, timepoint = extractor._infer_group_timepoint_from_text(
        metformin_text, mean_value=4.9, sd_value=0.7,
        candidate_groups=["Metformin", "Placebo"],
    )
    assert group == "Metformin"
    assert timepoint == "post-treatment"


def test_infer_group_timepoint_no_candidates_returns_none(extractor):
    """No candidates supplied (model gave no group names at all) - must
    degrade safely, not crash or guess."""
    group, timepoint = extractor._infer_group_timepoint_from_text(
        "some text", mean_value=1.0, sd_value=0.5, candidate_groups=[],
    )
    assert group is None
    assert timepoint is None


def test_collect_candidate_group_names_from_top_level_fields(extractor):
    result = {
        "intervention_group": "Exercise Therapy",
        "control_group": "Waitlist Control",
    }
    names = extractor._collect_candidate_group_names(result)
    assert "Exercise Therapy" in names
    assert "Waitlist Control" in names


def test_collect_candidate_group_names_from_sample_size_rows(extractor):
    result = {
        "groups_n_by_timepoint": [
            {"group": "Drug A", "post_n": 30},
            {"arm": "Drug B", "post_n": 28},
        ]
    }
    names = extractor._collect_candidate_group_names(result)
    assert "Drug A" in names
    assert "Drug B" in names


def test_collect_candidate_group_names_dedupes(extractor):
    result = {
        "intervention_group": "CBT",
        "groups_n_by_timepoint": [{"group": "CBT", "post_n": 20}],
    }
    names = extractor._collect_candidate_group_names(result)
    assert names.count("CBT") == 1
