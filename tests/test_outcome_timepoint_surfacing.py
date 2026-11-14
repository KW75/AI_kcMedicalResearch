"""
Regression test for the [OUTCOME/TIMEPOINT] provenance surfacing block in
sr/main.py (Session 19, #22 / #51).

Background
----------
Extraction is non-deterministic (#11): the same paper can draw its numbers
from different outcomes or timepoints across runs (Ang's bimodal
g=+0.075 vs -0.248 was the motivating case). v2.4.13 added
outcome_selected / timepoint_selected fields to the schema (#51) but
they were only reviewer-inspectable via extracted_data.csv - a run whose
numbers changed silently in the pooled estimate did not visibly change
in the Stage 4 console output.

Session 19 added an [OUTCOME/TIMEPOINT] block after the existing check
summaries in main(). This test pins its behaviour so a future refactor
that drops the block, drops a study's line, or silently changes how
None is displayed will fail CI.

Approach
--------
The block is inline in main() rather than a factored function. Rather
than run main() end-to-end (which would need ~20 mocks and slow the
suite significantly), we extract the block's source from sr/main.py by
string markers, exec it with a synthesized `er` list and a captured
logger, and assert the emitted log lines.

This does NOT guarantee the block is called during a real run - the
surrounding structure (that it sits inside main() after the source-quote
check and before the < 2 studies abort) is separately covered by the
syntactic well-formedness the whole test suite implicitly checks (a
broken main() fails to import in test_sr.py).
"""
from __future__ import annotations

import logging
import textwrap
from pathlib import Path


SR_MAIN = (
    Path(__file__).resolve().parent.parent
    / "SOURCE_CODE" / "pipelines" / "sr" / "main.py"
)

# Session 41 (bug b): the inline copy of the [OUTCOME/TIMEPOINT] block in
# main() was deleted - it printed the block a second time. These tests now
# drive the one remaining copy in _log_stage4_summary (meta_audit=[]).


def _main_module():
    import importlib
    import sys
    for cand in ("pipelines.sr.main", "SOURCE_CODE.pipelines.sr.main"):
        if cand in sys.modules:
            return sys.modules[cand]
    for stub in ("pipelines.sr.src.screening.rob2_tool",
                 "SOURCE_CODE.pipelines.sr.src.screening.rob2_tool"):
        m = sys.modules.get(stub)
        if m is not None and not hasattr(m, "RoB2Assessor"):
            del sys.modules[stub]
    err = None
    for cand in ("pipelines.sr.main", "SOURCE_CODE.pipelines.sr.main"):
        try:
            return importlib.import_module(cand)
        except ImportError as e:
            err = e
    raise err


def _run_block(er, logger):
    """Run _log_stage4_summary with no meta rows; capture its log lines."""
    mod = _main_module()
    old = mod.logger
    mod.logger = logger
    try:
        mod._log_stage4_summary([], er, "SMD")
    finally:
        mod.logger = old


class _CaptureLogger:
    """Minimal logger stand-in that records every call."""
    def __init__(self):
        self.messages = []
    def _rec(self, lvl, msg, *args):
        self.messages.append((lvl, msg % args if args else msg))
    def info(self, msg, *args):
        self._rec("INFO", msg, *args)
    def warning(self, msg, *args):
        self._rec("WARNING", msg, *args)
    def error(self, msg, *args):
        self._rec("ERROR", msg, *args)
    def debug(self, msg, *args):
        self._rec("DEBUG", msg, *args)


def _study(author, year, filename, outcome=None, timepoint=None):
    return {
        "filename": filename,
        "study_metadata": {"first_author": author, "year": year},
        "primary_outcome": {
            "outcome_selected": outcome,
            "timepoint_selected": timepoint,
        },
    }


def test_summary_reports_zero_of_zero_on_empty_extraction():
    """No studies -> block still emits its header (silence-ambiguity contract)."""
    logger = _CaptureLogger()
    _run_block(er=[], logger=logger)
    infos = [m for lvl, m in logger.messages if lvl == "INFO"]
    assert any("[OUTCOME/TIMEPOINT] 0 of 0 studies" in m for m in infos), (
        f"expected header line; got {infos!r}"
    )


def test_summary_counts_studies_with_at_least_one_field_recorded():
    """Recorded count = studies with at least one of the two fields non-null."""
    er = [
        _study("Ang",     2020, "ang.pdf",     outcome="NFR threshold",   timepoint="post"),
        _study("Jensen",  2019, "jensen.pdf",  outcome=None,              timepoint="week 12"),
        _study("Karlsson",2021, "karlsson.pdf",outcome=None,              timepoint=None),
        _study("Lami",    2018, "lami.pdf",    outcome="FIQ pain score",  timepoint=None),
    ]
    logger = _CaptureLogger()
    _run_block(er=er, logger=logger)
    infos = [m for lvl, m in logger.messages if lvl == "INFO"]
    header = [m for m in infos if "of 4 studies" in m]
    assert header, f"expected 'of 4 studies' header; got {infos!r}"
    # Ang, Jensen, Lami have at least one field; Karlsson has neither.
    assert "3 of 4 studies" in header[0]


def test_per_study_lines_show_outcome_and_timepoint():
    """Every study emits a line with both fields, and None is rendered readably."""
    er = [
        _study("Ang", 2020, "ang.pdf", outcome="NFR threshold", timepoint="post"),
        _study("Karlsson", 2021, "k.pdf", outcome=None, timepoint=None),
    ]
    logger = _CaptureLogger()
    _run_block(er=er, logger=logger)
    infos = [m for lvl, m in logger.messages if lvl == "INFO"]
    ang_line = [m for m in infos if "Ang" in m and "outcome=" in m]
    kar_line = [m for m in infos if "Karlsson" in m and "outcome=" in m]
    assert ang_line, f"missing Ang per-study line; got {infos!r}"
    assert kar_line, f"missing Karlsson per-study line; got {infos!r}"
    assert "outcome=NFR threshold" in ang_line[0]
    assert "timepoint=post" in ang_line[0]
    # Null renders as '(not recorded)', not the string 'None' or a bare blank.
    assert "outcome=(not recorded)" in kar_line[0]
    assert "timepoint=(not recorded)" in kar_line[0]


def test_bimodal_flip_would_be_visible():
    """
    The motivating case for #22: Ang's bimodal outcome flip (#11).
    Two runs pick different outcomes; the log must distinguish them,
    so a reviewer comparing two run logs can see which outcome each
    pooled estimate was keyed to without opening the CSV.
    """
    run_a = _study("Ang", 2020, "ang.pdf", outcome="pain change", timepoint="post")
    run_b = _study("Ang", 2020, "ang.pdf", outcome="NFR threshold", timepoint="post")

    log_a = _CaptureLogger()
    _run_block(er=[run_a], logger=log_a)
    log_b = _CaptureLogger()
    _run_block(er=[run_b], logger=log_b)

    a_lines = [m for lvl, m in log_a.messages if "Ang" in m]
    b_lines = [m for lvl, m in log_b.messages if "Ang" in m]
    assert a_lines and b_lines
    assert "pain change" in a_lines[0]
    assert "NFR threshold" in b_lines[0]
    # And the two run-logs must not be textually identical on Ang's line.
    assert a_lines[0] != b_lines[0]


def test_non_dict_entries_in_er_are_skipped_not_crashed():
    """Extraction can emit non-dict entries in edge cases; block must tolerate."""
    er = [
        _study("Ang", 2020, "ang.pdf", outcome="x", timepoint="y"),
        None,                     # e.g. an upstream failure
        "some string",            # defensive
    ]
    logger = _CaptureLogger()
    _run_block(er=er, logger=logger)   # must not raise
    infos = [m for lvl, m in logger.messages if lvl == "INFO"]
    # Only the one real study is counted.
    assert any("1 of 1 studies" in m for m in infos), (
        f"non-dict entries should be filtered; got {infos!r}"
    )
