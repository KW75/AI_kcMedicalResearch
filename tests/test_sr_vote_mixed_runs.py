"""Session 41: vote mixing (mixed_runs).

_vote_runs votes each AGREEMENT_* field on its own and writes every chosen
value into one result. If the majorities come from different pairs of runs,
the chosen set can be one that no single run read. Run 20261114_184026
(Karlsson) combined mean_control 48.8 from run 1 with ~3.6 values from
runs 2-3 (g = -50.2); table_shift caught that one. A set with only
':majority' flags and no table_shift signature passes the F4 gate
(test_majority_only_is_pooled), so it reached the pooled estimate unflagged.

Rule pinned here: if no single run holds every chosen numeric value, the
vote adds the flag 'mixed_runs'; the F4 gate treats it like table_shift
(not pooled until a reviewer overrides all four means/SDs).
Unchanged: no_majority keeps run 1's value; ':majority' alone is pooled.
"""
import importlib
import json as _json
import sys
import types

import pytest


def _stub(name, **attrs):
    if name in sys.modules:
        return sys.modules[name]
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules[name] = m
    return m


@pytest.fixture(scope="module")
def extractor_module():
    _stub("anthropic", Anthropic=lambda **kw: object())
    _stub("fitz")
    openai_mod = _stub("openai")
    if not hasattr(openai_mod, "OpenAI"):
        openai_mod.OpenAI = lambda **kw: object()
    for candidate in (
        "src.extraction.data_extractor",
        "pipelines.sr.src.extraction.data_extractor",
    ):
        try:
            return importlib.import_module(candidate)
        except ImportError:
            continue
    pytest.skip("data_extractor not importable from this cwd")


@pytest.fixture
def audit():
    return importlib.import_module("pipelines.sr.src.utils.audit_logger")


def _make(extractor_module, monkeypatch, **kw):
    monkeypatch.setattr(
        extractor_module, "_openai_compat_creds",
        lambda provider, key: ("k", "http://x"), raising=False)
    _stub(extractor_module.__name__.rsplit(".", 2)[0] + ".screening.rob2_tool",
          _openai_compat_creds=lambda provider, key: ("k", "http://x"))
    return extractor_module.DataExtractor(
        pico_criteria={"outcome": "pain"}, provider="qwen", api_key="k", **kw)


def _run(mi, sdi, mc, sdc, ni=20, nc=21, ig="CBT", cg="UC", qi="qi", qc="qc"):
    return {"mean_intervention": mi, "sd_intervention": sdi,
            "mean_control": mc, "sd_control": sdc,
            "n_intervention": ni, "n_control": nc,
            "intervention_group": ig, "control_group": cg,
            "source_quote_intervention": qi, "source_quote_control": qc,
            "outcome_match": "pain"}


class _ScriptedCompletions:
    def __init__(self, bodies):
        self.bodies = list(bodies)
        self.calls = 0

    def create(self, **kwargs):
        body = self.bodies[self.calls]
        self.calls += 1
        msg = types.SimpleNamespace(content=_json.dumps(body))
        return types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)])


def _vote(extractor_module, monkeypatch, bodies):
    _stub(extractor_module.__name__.rsplit(".", 2)[0] + ".utils.json_utils",
          extract_json=lambda s: _json.loads(s))
    ex = _make(extractor_module, monkeypatch, n_agreement=3)
    ex.client = types.SimpleNamespace(
        chat=types.SimpleNamespace(completions=_ScriptedCompletions(bodies)))
    r, flag, detail, _ = ex._extract_vision_with_agreement(["x"], "p", "f")
    return r, flag, detail


CORE = ("mean_intervention", "sd_intervention", "mean_control", "sd_control")

# Majorities from runs 1+2, 1+3, 2+3; sd_control unanimous -> no table_shift.
MIXED = [
    _run(3.88, 1.05, 3.70, 0.75),
    _run(3.88, 0.85, 3.67, 0.75),
    _run(3.61, 1.05, 3.67, 0.75),
]
# Reproduces the chosen set of run 20261114_184026 (3.61/0.85/48.8/0.92);
# per-run values are illustrative.
KARLSSON = [
    _run(48.3, 0.85, 48.8, 0.92, ni=24, nc=24),
    _run(3.61, 0.85, 3.70, 0.92, ni=24, nc=24),
    _run(3.61, 0.95, 3.67, 0.82, ni=24, nc=24),
]


def test_majorities_from_different_runs_are_flagged_mixed(extractor_module, monkeypatch):
    r, flag, _ = _vote(extractor_module, monkeypatch, MIXED)
    chosen = tuple(r[f] for f in CORE)
    assert chosen == (3.88, 1.05, 3.67, 0.75)
    assert all(tuple(run[f] for f in CORE) != chosen for run in MIXED)
    assert extractor_module.NONDET_FLAG_TABLE_SHIFT not in flag   # the gap
    assert "mixed_runs" in flag, f"flag={flag}"


def test_karlsson_like_vote_is_flagged_mixed(extractor_module, monkeypatch):
    r, flag, detail = _vote(extractor_module, monkeypatch, KARLSSON)
    assert r["mean_intervention"] == 3.61 and r["mean_control"] == 48.8
    assert detail["mean_control"]["kind"] == "no_majority"
    assert extractor_module.NONDET_FLAG_TABLE_SHIFT in flag
    assert "mixed_runs" in flag, f"flag={flag}"


def test_mixed_vote_is_kept_out_of_the_pool(extractor_module, monkeypatch, audit):
    _, flag, _ = _vote(extractor_module, monkeypatch, MIXED)
    cell = audit.nondet_flag_to_cell(flag)
    reason = audit.review_skip_reason(cell, None)
    assert reason and "mixed_runs" in reason, f"cell={cell!r} would be pooled"


def test_unanimous_is_not_mixed(extractor_module, monkeypatch):
    _, flag, _ = _vote(extractor_module, monkeypatch, [_run(32.5, 15, 37.6, 10)] * 3)
    assert flag == []


def test_majority_from_one_pair_is_not_mixed(extractor_module, monkeypatch):
    _, flag, _ = _vote(extractor_module, monkeypatch, [
        _run(3.88, 0.85, 3.38, 0.92),
        _run(3.88, 0.85, 3.38, 0.92),
        _run(3.88, 0.95, 3.37, 0.82),
    ])
    assert set(flag) == {"sd_intervention:majority", "mean_control:majority",
                         "sd_control:majority"}


def test_no_majority_keeps_first_run_and_is_not_mixed(extractor_module, monkeypatch):
    r, flag, _ = _vote(extractor_module, monkeypatch, [
        _run(37.6, 10.0, 45.3, 24.5),
        _run(-0.3, 2.2, -5.4, 13.5),
        _run(32.5, 15.0, 37.6, 10.0),
    ])
    assert r["mean_intervention"] == 37.6
    assert extractor_module.NONDET_FLAG_TABLE_SHIFT in flag
    assert "mixed_runs" not in flag


def test_gate_skips_mixed_runs(audit):
    reason = audit.review_skip_reason("mixed_runs", None)
    assert reason and "mixed_runs" in reason


def test_gate_mixed_runs_needs_all_four_numbers_overridden(audit):
    three = ("mean_intervention(confirmed 3.88); sd_intervention(confirmed 1.05); "
             "mean_control(confirmed 3.67)")
    assert audit.review_skip_reason("mixed_runs", three)
    assert audit.review_skip_reason("mixed_runs", three + "; sd_control(confirmed 0.75)") is None


def test_gate_majority_only_still_pooled(audit):
    cell = "mean_intervention:majority|sd_intervention:majority|mean_control:majority"
    assert audit.review_skip_reason(cell, None) is None


# --- Report wording and Stage 4 header for mixed_runs ----------------------
@pytest.fixture
def hr():
    return importlib.import_module("pipelines.sr.src.reporting.html_report")


@pytest.fixture
def main_mod():
    # _make stubs rob2_tool (only _openai_compat_creds). main needs the real
    # module (RoB2Assessor); drop our stub so the result does not depend on
    # test order. No-op when the real module is already loaded.
    name = "pipelines.sr.src.screening.rob2_tool"
    if name in sys.modules and not hasattr(sys.modules[name], "RoB2Assessor"):
        del sys.modules[name]
    return importlib.import_module("pipelines.sr.main")


_TAIL = (" - verify against the PDF, or enter the values in "
         "input/sr/study_overrides.yaml with a source-page note")


def test_report_wording_mixed_runs(hr):
    out = hr.plain_skip_reason("needs review: runs disagree (mixed_runs)" + _TAIL)
    assert "no single reading" in out, out
    assert "mixed_runs" not in out          # flag names are reworded (7n e)


def test_report_wording_shift_plus_mixed(hr):
    out = hr.plain_skip_reason("needs review: runs disagree (table_shift|mixed_runs)" + _TAIL)
    assert "neighbouring table row" in out and "no single reading" in out, out


def test_report_wording_table_shift_unchanged(hr):
    out = hr.plain_skip_reason("needs review: runs disagree (table_shift)" + _TAIL)
    assert "neighbouring table row" in out
    assert "no single reading" not in out


def _stage4(main_mod, caplog, flag):
    import logging
    row = {"first_author": "Karlsson", "year": 2015, "filename": "k.pdf",
           "mean_intervention": 3.88, "sd_intervention": 1.05,
           "mean_control": 3.67, "sd_control": 0.75,
           "n_intervention": 24, "n_control": 24, "hedges_g": 0.2,
           "nondet_flag": flag, "nondet_runs": 3}
    with caplog.at_level(logging.INFO):
        main_mod._log_stage4_summary([row], [], "SMD")
    return [m for m in caplog.messages if "[AGREEMENT]" in m or "Karlsson" in m]


MIXED_CELL = ("mean_intervention:majority|sd_intervention:majority|"
              "mean_control:majority|mixed_runs")


def test_stage4_mixed_runs_row_is_mandatory(main_mod, caplog):
    msgs = _stage4(main_mod, caplog, MIXED_CELL)
    assert any("Karlsson (2015) [MANDATORY]" in m for m in msgs), msgs


def test_stage4_header_names_mixed_runs(main_mod, caplog):
    msgs = _stage4(main_mod, caplog, MIXED_CELL)
    header = next(m for m in msgs if "voted studies disagreed" in m)
    assert "mixed_runs" in header, header
