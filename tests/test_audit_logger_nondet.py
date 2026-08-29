# tests/test_audit_logger_nondet.py
"""#11: nondet_flag rendering for meta_analysis_results.csv.

Property pinned: the CSV cell can never be empty for a voted study, so
"checked and unanimous" is distinguishable from "never ran".
"""
import csv
import importlib
import sys
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def al():
    for cand in ("src.utils.audit_logger", "pipelines.sr.src.utils.audit_logger"):
        try:
            return importlib.import_module(cand)
        except ImportError:
            continue
    pytest.skip("audit_logger not importable from this cwd")


@pytest.mark.parametrize("flag,cell", [
    ([], "unanimous"),
    (None, "not_checked"),
    (["single_run"], "single_run"),
    (["mean_control:majority"], "mean_control:majority"),
    (["mean_intervention:no_majority", "table_shift"],
     "mean_intervention:no_majority|table_shift"),
    ("already|a|string", "already|a|string"),
    ("", "unanimous"),
])
def test_nondet_flag_to_cell(al, flag, cell):
    assert al.nondet_flag_to_cell(flag) == cell


@pytest.mark.parametrize("cell,mandatory", [
    ("unanimous", False),
    ("not_checked", False),
    ("single_run", False),
    ("sd_control:majority", False),
    ("mean_control:no_majority", True),
    ("mean_intervention:majority|table_shift", True),
])
def test_nondet_cell_is_mandatory(al, cell, mandatory):
    assert al.nondet_cell_is_mandatory(cell) is mandatory


def test_write_results_carries_nondet_columns(al, tmp_path):
    """Regression for the #47 disease: a key missing from the fixed
    fieldnames list is silently dropped by extrasaction='ignore'."""
    out = tmp_path / "meta.csv"
    al.write_results(out, [{
        "run_id": "r", "first_author": "Ang", "year": 2010, "filename": "a.pdf",
        "nondet_flag": "mean_control:majority|table_shift", "nondet_runs": 3,
    }])
    with open(out, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["nondet_flag"] == "mean_control:majority|table_shift"
    assert rows[0]["nondet_runs"] == "3"
