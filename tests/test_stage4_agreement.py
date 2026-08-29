# tests/test_stage4_agreement.py
"""#11: the [AGREEMENT] line in the Stage-4 summary.

Follows the #66 denominator rule: the count is over VOTED studies
(nondet_runs >= 2). An N=1 run must say "not checked", never "0 flagged".
"""
import importlib
import logging

import pytest


@pytest.fixture(scope="module")
def main_mod():
    for cand in ("pipelines.sr.main", "SOURCE_CODE.pipelines.sr.main"):
        try:
            return importlib.import_module(cand)
        except ImportError:
            continue
    pytest.skip("pipelines.sr.main not importable from this cwd")


def _row(author, flag, runs, mean=1.0):
    return {"first_author": author, "year": 2010, "filename": f"{author}.pdf",
            "mean_intervention": mean, "sd_intervention": 1.0,
            "mean_control": 2.0, "sd_control": 1.0,
            "n_intervention": 10, "n_control": 10, "hedges_g": -0.5,
            "nondet_flag": flag, "nondet_runs": runs}


def _summary(main_mod, caplog, rows):
    with caplog.at_level(logging.INFO):
        main_mod._log_stage4_summary(rows, [], "SMD")
    msgs = caplog.messages
    start = next(i for i, m in enumerate(msgs) if "[AGREEMENT]" in m)
    end = next((i for i, m in enumerate(msgs) if i > start and "[OUTCOME/TIMEPOINT]" in m),
               len(msgs))
    return "\n".join(msgs[start:end])


def test_zero_extraction_prints_0_of_0(main_mod, caplog):
    empty = {"first_author": "X", "year": 2010, "filename": "x.pdf",
             "nondet_flag": "not_checked", "nondet_runs": None}
    txt = _summary(main_mod, caplog, [empty])
    assert "0 flagged of 0 extracted" in txt


def test_single_run_corpus_says_not_checked(main_mod, caplog):
    txt = _summary(main_mod, caplog, [_row("A", "single_run", 1),
                                      _row("B", "single_run", 1)])
    assert "not checked" in txt
    assert "0 flagged" not in txt


def test_unanimous_corpus_prints_zero_with_voted_denominator(main_mod, caplog):
    txt = _summary(main_mod, caplog, [_row("A", "unanimous", 3),
                                      _row("B", "unanimous", 3),
                                      _row("C", "single_run", 1)])
    assert "0 flagged of 2 voted" in txt
    assert "1 extracted studies were not voted" in txt
    assert "not correctness" in txt


def test_flagged_rows_listed_with_mandatory_tag(main_mod, caplog):
    txt = _summary(main_mod, caplog, [
        _row("Ang", "mean_intervention:majority|sd_intervention:majority|"
                    "mean_control:majority|sd_control:majority|table_shift", 3),
        _row("Lami", "sd_control:majority", 3),
        _row("Jensen", "unanimous", 3),
    ])
    assert "2 of 3 voted studies disagreed" in txt
    assert "(1 mandatory" in txt
    assert "Ang (2010) [MANDATORY]" in txt
    assert "Lami (2010) [check]" in txt
    assert "Jensen" not in txt.split("disagreed", 1)[1]
