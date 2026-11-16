"""Domain 4 is flagged for the reviewer (item 8, decision 8c, Session 43).

The Domain 4 label and the overall rule stay. The report marks each judged
D4 cell 'reviewer to confirm' and explains why under the table;
REVIEWER_GUIDE 3.6 and 7 name it as a reviewer task.
"""
from __future__ import annotations

import importlib
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GUIDE = REPO / "docs" / "sr" / "REVIEWER_GUIDE.md"
MARK = "reviewer to confirm"


def _hr():
    return importlib.import_module("pipelines.sr.src.reporting.html_report")


def _rows(d4):
    doms = {"randomisation": "Low", "deviations": "Low", "missing_data": "Low",
            "reported_result": "Low"}
    if d4 is not None:
        doms["outcome_measurement"] = d4
    return _hr().HTMLReportGenerator()._rob_rows(
        [{"study": "Ang (2010)", "domains": doms, "overall_judgment": "High"}])


def _section(start, stop):
    body = GUIDE.read_text(encoding="utf-8").split(start, 1)[1]
    return re.split(stop, body, maxsplit=1)[0]


def test_judged_d4_cell_is_marked():
    for j in ("High", "Some concerns", "Low"):
        assert MARK in _rows(j)


def test_only_d4_is_marked():
    assert _rows("High").count(MARK) == 1


def test_missing_d4_not_marked():
    assert MARK not in _rows(None)


def test_not_assessed_d4_not_marked():
    assert MARK not in _rows("Not assessed")


def test_note_under_rob_table():
    src = Path(_hr().__file__).read_text(encoding="utf-8")
    i = src.index("{rob_rows}")
    assert "reviewer judgement" in src[i:i + 800]


def test_guide_36_names_domain4_as_reviewer_task():
    sec = _section("### 3.6", r"\n#{2,3} ")
    assert "Confirm Domain 4" in sec


def test_guide_7_no_fixed_domain4_high():
    sec = _section("## 7.", r"\n## ")
    assert "Domain 4 was judged High." not in sec
    assert "by the reviewers" in sec
