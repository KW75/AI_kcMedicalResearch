"""Session 46 (item g): [OUTCOME/TIMEPOINT] says when the line is only the AI's
reading because a reviewer entered all four means/SDs.

Run 20261117_201642 printed 'Jensen (2012): ... | timepoint=baseline' although
the pooled numbers were the reviewer's post-treatment values.
Rule: means_sds_overridden(override_fields), same as [SOURCE QUOTE CHECK].
"""
import importlib
import logging

import pytest

NOTE = "(AI reading; means/SDs entered by reviewer - see override note)"
ALL_SIX = ("n_intervention(25->19); n_control(18->15); "
           "mean_intervention(60.5->49); sd_intervention(4->19); "
           "mean_control(65->59); sd_control(2.7->26)")


@pytest.fixture(scope="module")
def main_mod():
    for cand in ("pipelines.sr.main", "SOURCE_CODE.pipelines.sr.main"):
        try:
            return importlib.import_module(cand)
        except ImportError:
            continue
    pytest.skip("pipelines.sr.main not importable from this cwd")


def _er(author, year, timepoint, overrides=None):
    return {"filename": f"{author}.pdf",
            "study_metadata": {"first_author": author, "year": year},
            "primary_outcome": {"outcome_selected": "Average weekly FM pain",
                                "timepoint_selected": timepoint},
            "override_fields": overrides}


def _lines(main_mod, caplog, er):
    with caplog.at_level(logging.INFO):
        main_mod._log_stage4_summary([], er, "SMD")
    return [m for m in caplog.messages if "[OUTCOME/TIMEPOINT]" in m]


def test_overridden_line_says_ai_reading(main_mod, caplog):
    lines = _lines(main_mod, caplog, [_er("Jensen", 2012, "baseline", ALL_SIX)])
    j = [l for l in lines if "Jensen (2012):" in l]
    assert len(j) == 1
    assert j[0].endswith("timepoint=baseline " + NOTE), j[0]


def test_plain_line_unchanged(main_mod, caplog):
    lines = _lines(main_mod, caplog, [_er("Karlsson", 2015, "After treatment")])
    k = [l for l in lines if "Karlsson (2015):" in l]
    assert k[0].endswith("timepoint=After treatment"), k[0]


def test_partial_override_gets_no_note(main_mod, caplog):
    lines = _lines(main_mod, caplog,
                   [_er("Lami", 2018, "Post-treatment", "mean_intervention(13.68->7.35)")])
    assert not any(NOTE in l for l in lines)


def test_header_still_printed_once(main_mod, caplog):
    lines = _lines(main_mod, caplog, [_er("Jensen", 2012, "baseline", ALL_SIX),
                                      _er("Karlsson", 2015, "After treatment")])
    assert sum("recorded outcome_selected" in l for l in lines) == 1
