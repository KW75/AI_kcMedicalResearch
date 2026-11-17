"""Session 45 (item b): a study the reviewer excluded (exclude_from_meta) is
left out of the Stage-4 checks. Run 20261117_155621 still listed Ang under
'before trusting this pooled estimate' although Ang was in no estimate."""
import logging
import pathlib

import SOURCE_CODE.pipelines.sr.main as M

SRC = pathlib.Path(__file__).resolve().parents[1] / "SOURCE_CODE" / "pipelines" / "sr" / "main.py"

ANG = {
    "first_author": "Ang", "year": 2010,
    "skip_reason": "excluded by reviewer: FIQ pain only as Week 6 change scores",
    "plausibility_flag": "|SMD|=9.000 exceeds plausibility bound (1.5)",
    "group_timepoint_warning": "identical intervention/control labels",
    "source_quote_warning": "intervention source quote was not found verbatim",
}
JENSEN = {
    "first_author": "Jensen", "year": 2012, "included_in_meta": True,
    "plausibility_flag": "|SMD|=2.100 exceeds plausibility bound (1.5)",
}


def _msgs(caplog):
    caplog.set_level(logging.INFO)
    M._log_stage4_summary([dict(ANG), dict(JENSEN)], [], "SMD")
    return [r.getMessage() for r in caplog.records]


def test_excluded_study_in_no_check(caplog):
    bad = [m for m in _msgs(caplog) if "Ang (2010)" in m and not m.startswith("[EXCLUDED]")]
    assert bad == []


def test_excluded_line_names_the_study(caplog):
    assert any(m.startswith("[EXCLUDED]") and "Ang (2010)" in m for m in _msgs(caplog))


def test_kept_study_still_listed(caplog):
    assert any("Jensen (2012)" in m for m in _msgs(caplog))


def test_prefix_matches_reviewer_exclusion_reason():
    assert M.reviewer_exclusion_reason({"reviewer_exclusion": "x"}).startswith(M._EXCLUDED_PREFIX)


def test_filter_runs_before_trust_target():
    src = SRC.read_text(encoding="utf-8")
    body = src[src.index("def _log_stage4_summary("):]
    assert body.index("_split_reviewer_excluded(meta_audit)") < body.index("_trust_target(meta_audit)")
