"""Session 46 (item h): the Stage-4 [AGREEMENT] summary clears a study whose
flagged fields were all overridden.

Run 20261117_201642: the pooling gate pooled Lami (2018) with reviewer values
('every flagged field was overridden'), but the summary still listed it as
[MANDATORY] 'before trusting this pooled estimate'. Same rule as the gate:
review_skip_reason(flag, override_fields) is None.
"""
import importlib
import logging
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
LAMI_FLAG = ("mean_intervention:no_majority|sd_intervention:no_majority|"
             "mean_control:no_majority|sd_control:no_majority|table_shift")
ALL_SIX = ("n_intervention(34->28); n_control(41->36); "
           "mean_intervention(13.68->7.35); sd_intervention(4.61->2.08); "
           "mean_control(12.88->7.4); sd_control(5.01->1.29)")


def _import(*names):
    for cand in names:
        try:
            return importlib.import_module(cand)
        except ImportError:
            continue
    pytest.skip(f"none importable: {names}")


@pytest.fixture(scope="module")
def main_mod():
    return _import("pipelines.sr.main", "SOURCE_CODE.pipelines.sr.main")


def _row(author, year, flag, overrides=None):
    return {"first_author": author, "year": year, "filename": f"{author}.pdf",
            "mean_intervention": 1.0, "sd_intervention": 1.0,
            "mean_control": 2.0, "sd_control": 1.0,
            "n_intervention": 10, "n_control": 10, "hedges_g": -0.5,
            "nondet_flag": flag, "nondet_runs": 3,
            "override_fields": overrides}


def _summary(main_mod, caplog, rows):
    with caplog.at_level(logging.INFO):
        main_mod._log_stage4_summary(rows, [], "SMD")
    msgs = caplog.messages
    start = next(i for i, m in enumerate(msgs) if "[AGREEMENT]" in m)
    end = next((i for i, m in enumerate(msgs) if i > start and "[OUTCOME/TIMEPOINT]" in m),
               len(msgs))
    return "\n".join(msgs[start:end])


def test_overridden_study_is_not_mandatory(main_mod, caplog):
    txt = _summary(main_mod, caplog, [_row("Lami", 2018, LAMI_FLAG, ALL_SIX),
                                      _row("Jensen", 2012, "unanimous")])
    assert "Lami (2018) [MANDATORY]" not in txt
    assert "Lami (2018): runs disagreed; cleared by reviewer override" in txt


def test_header_counts_only_studies_still_flagged(main_mod, caplog):
    txt = _summary(main_mod, caplog, [_row("Lami", 2018, LAMI_FLAG, ALL_SIX),
                                      _row("Jensen", 2012, "unanimous")])
    assert "0 still flagged of 2 voted studies" in txt
    assert "1 cleared by reviewer override" in txt
    assert "all N runs agreed" not in txt


def test_not_overridden_stays_mandatory(main_mod, caplog):
    txt = _summary(main_mod, caplog, [_row("Lami", 2018, LAMI_FLAG)])
    assert "Lami (2018) [MANDATORY]" in txt
    assert "cleared by reviewer override" not in txt


def test_partial_override_stays_mandatory(main_mod, caplog):
    txt = _summary(main_mod, caplog,
                   [_row("Lami", 2018, LAMI_FLAG, "mean_intervention(13.68->7.35)")])
    assert "Lami (2018) [MANDATORY]" in txt


def test_cleared_and_open_studies_counted_apart(main_mod, caplog):
    txt = _summary(main_mod, caplog, [_row("Lami", 2018, LAMI_FLAG, ALL_SIX),
                                      _row("Ang", 2010, "table_shift")])
    assert "1 of 2 voted studies disagreed" in txt
    assert "(1 mandatory" in txt
    assert "Ang (2010) [MANDATORY]" in txt
    assert "Lami (2018) [MANDATORY]" not in txt


def test_helper_uses_the_gate_rule():
    al = _import("pipelines.sr.src.utils.audit_logger",
                 "SOURCE_CODE.pipelines.sr.src.utils.audit_logger")
    lami = _row("Lami", 2018, LAMI_FLAG, ALL_SIX)
    ang = _row("Ang", 2010, "table_shift")
    kar = _row("Karlsson", 2015, "sd_control:majority", ALL_SIX)
    still, cleared = al.split_agreement_cleared([lami, ang, kar])
    assert still == [ang]
    assert cleared == [lami]


def test_per_study_line_names_the_year():
    src = (ROOT / "SOURCE_CODE" / "pipelines" / "sr" / "main.py").read_text(encoding="utf-8")
    assert "[AGREEMENT] {skip_label(audit_row)}: runs disagreed but " in src
    assert "[AGREEMENT] {m.get('first_author','?')}: runs disagreed but " not in src
