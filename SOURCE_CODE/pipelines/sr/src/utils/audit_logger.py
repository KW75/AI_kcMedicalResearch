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


def _write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    logger.info(f"Audit CSV written: {path}")


def write_screens(path: Path, screening_results: list[dict]) -> None:
    """Write Stage 2 screening decisions."""
    fields = [
        "filename", "decision", "rationale",
        "pico_population", "pico_intervention",
        "pico_comparator", "pico_outcome", "error"
    ]
    _write_csv(path, screening_results, fields)


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
        "first_author", "year", "filename",
        "outcome_match", "effect_measure",
        "hedges_g", "ci_lower", "ci_upper",
        "n_intervention", "n_control",
        "mean_intervention", "sd_intervention",
        "mean_control", "sd_control",
        "included_in_meta", "skip_reason",
        "plausibility_flag", "sd_se_warning", "group_timepoint_warning",
    ]
    _write_csv(path, meta_rows, fields)
