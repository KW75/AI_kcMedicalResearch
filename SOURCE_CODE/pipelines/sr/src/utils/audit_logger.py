"""
audit_logger.py
---------------
Writes timestamped audit CSVs into the active SRProjectLayout paths.
Each stage calls the relevant write function once after it completes.
"""

import csv
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


# #11: nondet_flag as written by the extractor is a list. The CSV cell must
# distinguish "checked and unanimous" from "never checked" from "flagged"
# without relying on an empty string, because an empty cell also appears on
# error rows and on the Anthropic path where no vote runs.
NONDET_CELL_UNANIMOUS = "unanimous"
NONDET_CELL_NOT_CHECKED = "not_checked"
NONDET_MANDATORY_MARKERS = ("no_majority", "table_shift", "mixed_runs")


def nondet_flag_to_cell(flag) -> str:
    """Render the extractor's nondet_flag for a CSV cell.

    []            -> "unanimous"
    None / absent -> "not_checked"   (extraction error, Anthropic path)
    [..strings..] -> "a|b|c"          (includes "single_run" as-is)
    """
    if flag is None:
        return NONDET_CELL_NOT_CHECKED
    if isinstance(flag, str):
        return flag or NONDET_CELL_UNANIMOUS
    if not flag:
        return NONDET_CELL_UNANIMOUS
    return "|".join(str(x) for x in flag)


def nondet_cell_is_mandatory(cell: str) -> bool:
    """True if a rendered nondet_flag cell requires a source check."""
    return any(m in (cell or "") for m in NONDET_MANDATORY_MARKERS)


# F4 gate (Session 37). The four numbers a table_shift can move.
_REVIEW_NUMERIC_FIELDS = ("mean_intervention", "sd_intervention",
                          "mean_control", "sd_control")


def _overridden_fields(override_fields) -> set:
    """Field names from StudyOverrides.apply's override_fields string,
    e.g. "n_control(41->36); mean_control(confirmed 7.4)" -> {...}."""
    names = set()
    for part in str(override_fields or "").split(";"):
        name = part.strip().split("(", 1)[0].strip()
        if name:
            names.add(name)
    return names


# Session 41 option B (quote gate): page-image numbers whose source quote is
# not in the paper text need review. Run 20261114_202253 pooled Karlsson with
# a misread all N=3 runs agreed on; a vote cannot catch that.
QUOTE_NOT_FOUND_MARKER = "was not found verbatim"
QUOTE_GATE_TOKEN = "quote_not_found"
QUOTE_GATE_REASON = ("needs review: source quote not found (quote_not_found) - "
                     "numbers read from page images; verify all four means/SDs "
                     "against the PDF and enter them in "
                     "input/sr/study_overrides.yaml with a source-page note")


def review_skip_reason(cell, override_fields=None, quote_warning=None,
                       extraction_method=None):
    """F4 gate: None = may be pooled; str = keep OUT of the pooled estimate.

    A mandatory nondet flag (no_majority / table_shift) means the N runs read
    different table cells; baseline 20261110_120707 pooled Jensen and Lami
    with numbers that are not in the PDFs. The row passes only if a reviewer
    overrode every flagged field (table_shift / mixed_runs: all four means/SDs).
    """
    cell = cell or ""
    done = _overridden_fields(override_fields)
    reasons = []
    if nondet_cell_is_mandatory(cell):
        still_open = []
        for tok in (t.strip() for t in cell.split("|")):
            if tok in ("table_shift", "mixed_runs"):
                if not all(f in done for f in _REVIEW_NUMERIC_FIELDS):
                    still_open.append(tok)
            elif tok.endswith(":no_majority"):
                if tok.split(":", 1)[0] not in done:
                    still_open.append(tok)
        if still_open:
            reasons.append(
                "needs review: runs disagree (" + "|".join(still_open) + ") - "
                "verify against the PDF, or enter the values in "
                "input/sr/study_overrides.yaml with a source-page note")
    # Quote gate: text-path studies keep today's behaviour; a missing method
    # counts as page images (safe side). Cleared by all four means/SDs.
    if (QUOTE_NOT_FOUND_MARKER in str(quote_warning or "")
            and not str(extraction_method or "").startswith("text")
            and not all(f in done for f in _REVIEW_NUMERIC_FIELDS)):
        reasons.append(QUOTE_GATE_REASON)
    return "; also: ".join(reasons) or None


def _write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    logger.info(f"Audit CSV written: {path}")


def write_screens(path: Path, screening_results: list[dict]) -> None:
    """Write Stage 2 screening decisions.

    The screener returns pico_match as a NESTED dict; the previous fixed
    fieldnames expected flat pico_* keys that nothing ever wrote, so the
    pico columns were empty in every screening_log.csv ever produced,
    and confidence / is_rct / exclusion_reasons were silently dropped by
    extrasaction="ignore" (Session 14; same disease as #47). Flatten
    here so the CSV carries what the screener actually returned.
    """
    fields = [
        "run_id", "filename", "decision", "confidence", "is_rct",
        "pico_population", "pico_intervention", "pico_comparator",
        "pico_outcome", "pico_study_design",
        "exclusion_reasons", "rationale", "error",
    ]
    rows = []
    for r in screening_results:
        flat = dict(r)
        pico = flat.pop("pico_match", None)
        if isinstance(pico, dict):
            for k, v in pico.items():
                flat[f"pico_{k}"] = v
        reasons = flat.get("exclusion_reasons")
        if isinstance(reasons, list):
            flat["exclusion_reasons"] = "; ".join(str(x) for x in reasons)
        rows.append(flat)
    _write_csv(path, rows, fields)


def write_extracts(path: Path, extraction_results: list[dict]) -> None:
    """Write Stage 3 extraction results (flattened)."""
    import pandas as pd

    if not extraction_results:
        logger.warning("No extraction results to write.")
        return

    rows = []
    for r in extraction_results:
        flat = {}
        for k, v in r.items():
            if isinstance(v, dict):
                for k2, v2 in v.items():
                    flat[f"{k}.{k2}"] = v2
            elif isinstance(v, list):
                flat[k] = str(v)
            else:
                flat[k] = v
        rows.append(flat)

    df = pd.DataFrame(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8")
    logger.info(f"Audit CSV written: {path}")


def write_rob2(path: Path, rob2_results: list[dict]) -> None:
    """Write Stage 3.5 RoB 2.0 assessment results (flattened)."""
    import pandas as pd

    if not rob2_results:
        logger.warning("No RoB2 results to write.")
        return

    rows = []
    for r in rob2_results:
        flat = {}
        for k, v in r.items():
            if isinstance(v, dict):
                for k2, v2 in v.items():
                    flat[f"{k}.{k2}"] = v2
            else:
                flat[k] = v
        rows.append(flat)

    df = pd.DataFrame(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8")
    logger.info(f"Audit CSV written: {path}")


def write_results(path: Path, meta_rows: list[dict]) -> None:
    """Write Stage 4 meta-analysis per-study results."""
    fields = [
        "run_id",  # stamped by sr/main.py; must be listed here or
                   # extrasaction="ignore" silently drops it (#47)
        "first_author", "year", "filename",
        "outcome_match", "effect_measure",
        "hedges_g", "ci_lower", "ci_upper",
        "n_intervention", "n_control",
        "mean_intervention", "sd_intervention",
        "mean_control", "sd_control",
        "included_in_meta", "skip_reason",
        "plausibility_flag", "sd_se_warning", "group_timepoint_warning",
        "source_quote_warning",
        "nondet_flag", "nondet_runs",   # #11; rendered via nondet_flag_to_cell
    ]
    _write_csv(path, meta_rows, fields)


def reviewer_exclusion_reason(result):
    """Session 38 (7k): skip_reason for a study the reviewer excluded via
    study_overrides.yaml exclude_from_meta, or None."""
    if not isinstance(result, dict):
        return None
    reason = str(result.get("reviewer_exclusion") or "").strip()
    return f"excluded by reviewer: {reason}" if reason else None
