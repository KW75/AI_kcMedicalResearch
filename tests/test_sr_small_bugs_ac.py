"""Session 41 small bugs a-c (tests first).

a) A vision run with no mean/SD (only outcome_match, Ns, labels) counted as
   usable and its Nones broke the vote. Run 20261114_202253, Lami:
   [13.68, None, None] -> no_majority + table_shift, nondet_usable_runs 3.
   Rule: only runs with at least one mean/SD are voted and counted. If only
   one run has numbers (n_agreement >= 2) the flag too_few_runs is added; it
   is mandatory (not pooled) and cleared like table_shift (all four
   means/SDs overridden). If no run has numbers, behaviour is unchanged.
b) [OUTCOME/TIMEPOINT] was printed twice (inline copy in main() after
   _log_stage4_summary). Only the function copy stays.
c) "Skip study:" log lines name the study (author and year).
"""
import importlib
import json
import logging
import sys
import types
from pathlib import Path

import pytest

from pipelines.sr.src.utils import audit_logger as audit

MAIN = (Path(__file__).resolve().parents[1]
        / "SOURCE_CODE" / "pipelines" / "sr" / "main.py")
ALL_FOUR = ("mean_intervention(13.68->7.35); sd_intervention(4.61->2.08); "
            "mean_control(13.79->7.4); sd_control(4.22->1.29)")
TOO_FEW_REASON = ("needs review: runs disagree (too_few_runs) - verify against "
                  "the PDF, or enter the values in input/sr/study_overrides.yaml "
                  "with a source-page note")


def _stub(name, **attrs):
    if name in sys.modules:
        return sys.modules[name]
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules[name] = m
    return m


@pytest.fixture(scope="module")
def ex_mod():
    _stub("anthropic", Anthropic=lambda **kw: object())
    _stub("fitz")
    openai_mod = _stub("openai")
    if not hasattr(openai_mod, "OpenAI"):
        openai_mod.OpenAI = lambda **kw: object()
    for cand in ("src.extraction.data_extractor",
                 "pipelines.sr.src.extraction.data_extractor"):
        try:
            return importlib.import_module(cand)
        except ImportError:
            continue
    pytest.skip("data_extractor not importable from this cwd")


class _Scripted:
    def __init__(self, bodies):
        self.bodies, self.calls = list(bodies), 0

    def create(self, **kwargs):
        body = self.bodies[self.calls]
        self.calls += 1
        msg = types.SimpleNamespace(content=json.dumps(body))
        return types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)])


def _agree(ex_mod, monkeypatch, bodies, n=3):
    """Like test_extractor_sampling._agree_ex, but stubs are undone after."""
    creds = lambda provider, key: ("k", "http://x")
    monkeypatch.setattr(ex_mod, "_openai_compat_creds", creds, raising=False)
    pkg = ex_mod.__name__.rsplit(".", 2)[0]
    rob, js = pkg + ".screening.rob2_tool", pkg + ".utils.json_utils"
    if rob in sys.modules:
        monkeypatch.setattr(sys.modules[rob], "_openai_compat_creds", creds,
                            raising=False)
    else:
        m = types.ModuleType(rob)
        m._openai_compat_creds = creds
        monkeypatch.setitem(sys.modules, rob, m)
    if js not in sys.modules:
        j = types.ModuleType(js)
        j.extract_json = json.loads
        monkeypatch.setitem(sys.modules, js, j)
    ex = ex_mod.DataExtractor(pico_criteria={"outcome": "pain"},
                              provider="qwen", api_key="k", n_agreement=n)
    ex.client = types.SimpleNamespace(
        chat=types.SimpleNamespace(completions=_Scripted(bodies)))
    return ex


def _run(mi, sdi, mc, sdc, ni=24, nc=24):
    return {"mean_intervention": mi, "sd_intervention": sdi,
            "mean_control": mc, "sd_control": sdc,
            "n_intervention": ni, "n_control": nc,
            "intervention_group": "CBT", "control_group": "WLC",
            "source_quote_intervention": "qi", "source_quote_control": "qc",
            "outcome_match": "pain"}


def _empty(ni=24, nc=24):
    r = _run(None, None, None, None, ni, nc)
    r["source_quote_intervention"] = r["source_quote_control"] = None
    return r


def _main():
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


def _stage4(caplog, flag):
    row = {"first_author": "Lami", "year": 2017, "filename": "lami.pdf",
           "mean_intervention": 13.68, "sd_intervention": 4.61,
           "mean_control": 13.79, "sd_control": 4.22,
           "n_intervention": 34, "n_control": 41, "hedges_g": -0.02,
           "nondet_flag": flag, "nondet_runs": 3}
    mod = _main()
    with caplog.at_level(logging.INFO):
        mod._log_stage4_summary([row], [], "SMD")
    return caplog.messages


# --- bug a: vote only runs that have numbers ------------------------------

def test_a_lami_one_numeric_run_is_too_few(ex_mod, monkeypatch):
    ex = _agree(ex_mod, monkeypatch,
                [_run(13.68, 4.61, 13.79, 4.22, 34, 41), _empty(34, 41), _empty(34, 41)])
    r, flag, _, n = ex._extract_vision_with_agreement(["x"], "p", "lami.pdf")
    assert n == 1
    assert "usable_runs:1/3" in flag and "too_few_runs" in flag
    assert not any("no_majority" in f or f == "table_shift" for f in flag)
    assert r["mean_intervention"] == 13.68
    assert getattr(ex_mod, "NONDET_FLAG_TOO_FEW_RUNS", None) == "too_few_runs"


def test_a_two_numeric_runs_vote_normally(ex_mod, monkeypatch):
    ex = _agree(ex_mod, monkeypatch,
                [_run(3.88, 1.05, 3.67, 0.75), _empty(), _run(3.88, 1.05, 3.67, 0.75)])
    r, flag, _, n = ex._extract_vision_with_agreement(["x"], "p", "k.pdf")
    assert n == 2
    assert flag == ["usable_runs:2/3"]
    assert r["sd_control"] == 0.75


def test_a_three_numeric_runs_unchanged(ex_mod, monkeypatch):
    ex = _agree(ex_mod, monkeypatch, [_run(48.3, 11.5, 48.8, 6.5),
                                      _run(3.61, 0.85, 3.7, 0.92),
                                      _run(3.61, 0.85, 4.2, 0.92)])
    _, flag, _, n = ex._extract_vision_with_agreement(["x"], "p", "k.pdf")
    assert n == 3
    assert "too_few_runs" not in flag
    assert not any(f.startswith("usable_runs") for f in flag)


def test_a_no_numbers_anywhere_keeps_old_behaviour(ex_mod, monkeypatch):
    ex = _agree(ex_mod, monkeypatch, [_empty()] * 3)
    r, flag, _, n = ex._extract_vision_with_agreement(["x"], "p", "e.pdf")
    assert r is not None and n == 3
    assert "too_few_runs" not in flag


def test_a_gate_blocks_too_few_runs():
    assert audit.review_skip_reason("usable_runs:1/3|too_few_runs") == TOO_FEW_REASON


def test_a_gate_too_few_runs_cleared_by_all_four():
    assert audit.review_skip_reason("usable_runs:1/3|too_few_runs", ALL_FOUR) is None


def test_a_plain_wording_too_few_runs():
    hr = importlib.import_module("pipelines.sr.src.reporting.html_report")
    s = hr.plain_skip_reason(TOO_FEW_REASON).lower()
    assert "only one of the repeated readings" in s
    assert "different values" not in s


def test_a_stage4_too_few_runs_is_mandatory(caplog):
    msgs = _stage4(caplog, "usable_runs:1/3|too_few_runs")
    assert any("Lami (2017)" in m and "MANDATORY" in m for m in msgs), msgs


def test_a_stage4_header_names_too_few_runs(caplog):
    msgs = _stage4(caplog, "usable_runs:1/3|too_few_runs")
    hdr = [m for m in msgs if "mandatory: " in m]
    assert hdr and "too_few_runs" in hdr[0], msgs


# --- bug b: block printed once ---------------------------------------------

def test_b_outcome_timepoint_block_only_once_in_main():
    src = MAIN.read_text(encoding="utf-8")
    assert src.count('f"[OUTCOME/TIMEPOINT] {_op_recorded} of') == 1


# --- bug c: skip lines name the study ---------------------------------------

def test_c_skip_study_lines_name_the_study():
    lines = [l.strip() for l in MAIN.read_text(encoding="utf-8").splitlines()
             if 'logger.warning(f"Skip study:' in l]
    assert len(lines) == 2, lines
    for l in lines:
        assert "first_author" in l and "year" in l, l