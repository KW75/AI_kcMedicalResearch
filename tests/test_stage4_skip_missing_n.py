"""#69: text-fallback studies with usable means/SDs but no per-arm N must
appear in the Stage-4 [SKIP] block, not just as a mid-run WARNING that
the reviewer might miss."""

import logging
from SOURCE_CODE.pipelines.sr.main import _log_stage4_summary


def _meta_row(**overrides):
    """Minimal meta_audit row with the fields _log_stage4_summary reads."""
    row = {
        "first_author": "Lami",
        "year": 2017,
        "filename": "s10608-017-9875-4.pdf",
        "mean_intervention": 7.35,
        "sd_intervention": 2.08,
        "mean_control": 7.4,
        "sd_control": 1.29,
        "n_intervention": None,
        "n_control": None,
        "hedges_g": None,
        "included_in_meta": False,
        "skip_reason": "insufficient mean/SD/N to derive effect size",
        "plausibility_flag": None,
        "sd_se_warning": None,
        "group_timepoint_warning": None,
        "source_quote_warning": None,
        "nondet_flag": "single_run",
        "nondet_runs": 1,
    }
    row.update(overrides)
    return row


def _extraction_row(**overrides):
    row = {
        "study_metadata": {"first_author": "Lami", "year": 2017},
        "primary_outcome": {},
        "filename": "s10608-017-9875-4.pdf",
        "extraction_method": "text_fallback",
    }
    row.update(overrides)
    return row


def test_skip_block_flags_missing_ns_on_text_fallback(caplog):
    """The Lami-shaped failure: means/SDs present, per-arm N missing."""
    caplog.set_level(logging.WARNING, logger="sr.main")
    _log_stage4_summary(
        meta_audit=[_meta_row()],
        er=[_extraction_row()],
        effect_measure="SMD",
    )
    messages = [r.getMessage() for r in caplog.records]
    skip_lines = [m for m in messages
                    if m.startswith("[SKIP]") or m.lstrip().startswith("- ")]
    assert skip_lines, (
        f"expected a [SKIP] warning for missing-N drop; got: {messages}")
    header = skip_lines[0]
    assert "1 of 1 extracted studies" in header
    assert "missing per-arm N" in header
    assert any("Lami" in m for m in skip_lines), (
        f"Lami must be named in the [SKIP] block; got: {skip_lines}")


def test_skip_block_reports_zero_when_nothing_was_dropped(caplog):
    """Clean run: every extracted study made it into the pooled estimate."""
    caplog.set_level(logging.INFO, logger="sr.main")
    clean = _meta_row(
        first_author="Jensen",
        n_intervention=25,
        n_control=18,
        hedges_g=-0.42,
        included_in_meta=True,
        skip_reason=None,
    )
    _log_stage4_summary(
        meta_audit=[clean],
        er=[_extraction_row(study_metadata={"first_author": "Jensen", "year": 2012},
                             extraction_method="vision_smart")],
        effect_measure="SMD",
    )
    messages = [r.getMessage() for r in caplog.records]
    skip_lines = [m for m in messages if m.startswith("[SKIP]")]
    assert skip_lines, f"expected [SKIP] line even on clean run; got: {messages}"
    assert "0 of 1 extracted studies were dropped" in skip_lines[0]


def test_skip_block_separates_missing_n_from_other_reasons(caplog):
    """A missing-N drop and a different drop must not be conflated."""
    caplog.set_level(logging.WARNING, logger="sr.main")
    missing_n = _meta_row()   # Lami
    other = _meta_row(
        first_author="OtherStudy",
        year=2020,
        filename="other.pdf",
        n_intervention=20,
        n_control=20,
        skip_reason="outcome_match=False: primary outcome not reported",
    )
    _log_stage4_summary(
        meta_audit=[missing_n, other],
        er=[_extraction_row(),
            _extraction_row(study_metadata={"first_author": "OtherStudy", "year": 2020},
                             filename="other.pdf")],
        effect_measure="SMD",
    )
    messages = [r.getMessage() for r in caplog.records]
    missing_n_header = next(
        (m for m in messages if m.startswith("[SKIP]") and "missing per-arm N" in m), None)
    other_header = next(
        (m for m in messages if m.startswith("[SKIP]") and "reasons other than" in m), None)
    assert missing_n_header, f"missing-N header absent from: {messages}"
    assert other_header, f"other-reasons header absent from: {messages}"
    assert "1 of 2 extracted" in missing_n_header
    assert "1 other studies" in other_header
