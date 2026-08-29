# tests/test_extractor_sampling.py
"""#11 mitigation plumbing: temperature/seed must reach every
chat.completions.create call the extractor makes.

Property pinned: the vision call sends the SAME temperature as the text
paths (pre-S26 it silently sent 0.1 while the text paths sent 0), and a
seed is sent when configured and omitted when not. The specific default
values are asserted only because they are the documented contract in
data_extractor.py's module header.
"""
import importlib
import sys
import types

import pytest


# ---------------------------------------------------------------------------
# Import the extractor without needing openai / anthropic / fitz installed
# and without hitting the network. If the real package imports cleanly,
# prefer it; otherwise stub the heavy deps.
# ---------------------------------------------------------------------------
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
        "src.extraction.data_extractor",          # run from SOURCE_CODE/pipelines/sr
        "pipelines.sr.src.extraction.data_extractor",  # run from SOURCE_CODE
    ):
        try:
            return importlib.import_module(candidate)
        except ImportError:
            continue
    pytest.skip("data_extractor not importable from this cwd")


class _FakeCompletions:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        msg = types.SimpleNamespace(content='{"ok": true}')
        return types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)])


class _FakeClient:
    def __init__(self):
        self.chat = types.SimpleNamespace(completions=_FakeCompletions())

    @property
    def calls(self):
        return self.chat.completions.calls


def _make(extractor_module, monkeypatch, **kw):
    monkeypatch.setattr(
        extractor_module, "_openai_compat_creds",
        lambda provider, key: ("k", "http://x"), raising=False)
    # __init__ imports _openai_compat_creds lazily from ..screening.rob2_tool;
    # stub that module so the import resolves regardless of cwd.
    _stub(extractor_module.__name__.rsplit(".", 2)[0] + ".screening.rob2_tool",
          _openai_compat_creds=lambda provider, key: ("k", "http://x"))
    ex = extractor_module.DataExtractor(
        pico_criteria={"outcome": "pain"}, provider="qwen", api_key="k", **kw)
    ex.client = _FakeClient()
    return ex


def _all_three_calls(ex):
    ex._call_vision_api(["aW1n"], "p")
    ex._call_text_api("some text", "f.pdf")
    ex._call_chat_api_with_prompt("q")
    assert len(ex.client.calls) == 3
    return ex.client.calls


def test_defaults_send_temperature_zero_and_seed(extractor_module, monkeypatch):
    monkeypatch.delenv("SR_EXTRACT_TEMPERATURE", raising=False)
    monkeypatch.delenv("SR_EXTRACT_SEED", raising=False)
    ex = _make(extractor_module, monkeypatch)
    calls = _all_three_calls(ex)
    for c in calls:
        assert c["temperature"] == 0
        assert c["seed"] == extractor_module.DEFAULT_EXTRACT_SEED


def test_vision_and_text_paths_share_temperature(extractor_module, monkeypatch):
    """The pre-S26 bug: vision at 0.1, text at 0. Pin that they can't drift."""
    monkeypatch.delenv("SR_EXTRACT_TEMPERATURE", raising=False)
    monkeypatch.delenv("SR_EXTRACT_SEED", raising=False)
    ex = _make(extractor_module, monkeypatch, temperature=0.3)
    calls = _all_three_calls(ex)
    temps = {c["temperature"] for c in calls}
    assert temps == {0.3}


def test_explicit_seed_none_omits_param(extractor_module, monkeypatch):
    monkeypatch.delenv("SR_EXTRACT_SEED", raising=False)
    ex = _make(extractor_module, monkeypatch, seed=None)
    for c in _all_three_calls(ex):
        assert "seed" not in c


def test_env_overrides(extractor_module, monkeypatch):
    monkeypatch.setenv("SR_EXTRACT_TEMPERATURE", "0.7")
    monkeypatch.setenv("SR_EXTRACT_SEED", "1234")
    ex = _make(extractor_module, monkeypatch)
    for c in _all_three_calls(ex):
        assert c["temperature"] == 0.7
        assert c["seed"] == 1234


def test_env_seed_none_omits_param(extractor_module, monkeypatch):
    monkeypatch.setenv("SR_EXTRACT_SEED", "none")
    ex = _make(extractor_module, monkeypatch)
    for c in _all_three_calls(ex):
        assert "seed" not in c


def test_explicit_kwargs_beat_env(extractor_module, monkeypatch):
    monkeypatch.setenv("SR_EXTRACT_TEMPERATURE", "0.7")
    monkeypatch.setenv("SR_EXTRACT_SEED", "1234")
    ex = _make(extractor_module, monkeypatch, temperature=0, seed=7)
    for c in _all_three_calls(ex):
        assert c["temperature"] == 0
        assert c["seed"] == 7


def test_bad_env_values_fall_back_with_warning(extractor_module, monkeypatch, caplog):
    monkeypatch.setenv("SR_EXTRACT_TEMPERATURE", "warm")
    monkeypatch.setenv("SR_EXTRACT_SEED", "lucky")
    with caplog.at_level("WARNING"):
        ex = _make(extractor_module, monkeypatch)
    assert ex.temperature == extractor_module.DEFAULT_EXTRACT_TEMPERATURE
    assert ex.seed == extractor_module.DEFAULT_EXTRACT_SEED
    assert "SR_EXTRACT_TEMPERATURE" in caplog.text
    assert "SR_EXTRACT_SEED" in caplog.text


# ===========================================================================
# N-run agreement (#11)
# ===========================================================================
import json as _json


def _run(mi, sdi, mc, sdc, ni=20, nc=21, ig="CBT", cg="UC", qi="qi", qc="qc"):
    return {"mean_intervention": mi, "sd_intervention": sdi,
            "mean_control": mc, "sd_control": sdc,
            "n_intervention": ni, "n_control": nc,
            "intervention_group": ig, "control_group": cg,
            "source_quote_intervention": qi, "source_quote_control": qc,
            "outcome_match": "pain"}


class _ScriptedCompletions:
    """Returns pre-scripted JSON bodies, one per create() call, in order."""
    def __init__(self, bodies):
        self.bodies = list(bodies)
        self.calls = 0

    def create(self, **kwargs):
        body = self.bodies[self.calls]
        self.calls += 1
        msg = types.SimpleNamespace(content=_json.dumps(body))
        return types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)])


def _agree_ex(extractor_module, monkeypatch, bodies, n=3):
    _stub(extractor_module.__name__.rsplit(".", 2)[0] + ".utils.json_utils",
          extract_json=lambda s: _json.loads(s))
    ex = _make(extractor_module, monkeypatch, n_agreement=n)
    ex.client = types.SimpleNamespace(
        chat=types.SimpleNamespace(completions=_ScriptedCompletions(bodies)))
    return ex


def test_agreement_unanimous_gives_empty_flag(extractor_module, monkeypatch):
    ex = _agree_ex(extractor_module, monkeypatch,
                   [_run(32.5, 15, 37.6, 10)] * 3)
    r, flag, detail, n = ex._extract_vision_with_agreement(["x"], "p", "f")
    assert ex.client.chat.completions.calls == 3
    assert flag == []                       # key present, empty = checked & clean
    assert n == 3
    assert r["mean_intervention"] == 32.5
    assert all(d["kind"] == "unanimous" for d in detail.values())


def test_agreement_majority_picks_majority_and_flags(extractor_module, monkeypatch):
    ex = _agree_ex(extractor_module, monkeypatch, [
        _run(3.88, 0.85, 3.38, 0.92, qi="q1", qc="c1"),
        _run(3.88, 0.85, 3.38, 0.92, qi="q1", qc="c1"),
        _run(3.88, 0.95, 3.37, 0.82, qi="q3", qc="c3"),
    ])
    r, flag, detail, _ = ex._extract_vision_with_agreement(["x"], "p", "f")
    assert set(flag) == {"sd_intervention:majority", "mean_control:majority",
                         "sd_control:majority"}          # 3 of 4 jittered: NOT table_shift
    assert r["sd_intervention"] == 0.85 and r["mean_control"] == 3.38
    assert r["source_quote_intervention"] == "q1"
    assert r["source_quote_control"] == "c1"


def test_agreement_no_majority_flags_and_keeps_first(extractor_module, monkeypatch):
    """The S26 Ang signature: three runs, three different tables."""
    ex = _agree_ex(extractor_module, monkeypatch, [
        _run(37.6, 10.0, 45.3, 24.5, qi="a", qc="a"),
        _run(-0.3, 2.2, -5.4, 13.5, qi="b", qc="b"),
        _run(32.5, 15.0, 37.6, 10.0, qi="c", qc="c"),
    ])
    r, flag, detail, _ = ex._extract_vision_with_agreement(["x"], "p", "f")
    for f in ("mean_intervention", "sd_intervention", "mean_control", "sd_control"):
        assert f"{f}:no_majority" in flag
    assert extractor_module.NONDET_FLAG_TABLE_SHIFT in flag
    assert "n_intervention:no_majority" not in flag       # n agreed
    assert r["mean_intervention"] == 37.6                 # first run kept, visibly flagged
    assert r["source_quote_intervention"] == "a"          # quote matches the kept numbers


def test_agreement_majority_table_shift_is_tagged(extractor_module, monkeypatch):
    """S26 acceptance run: 2-of-3 picked reading A over reading B; both arms'
    mean+SD flipped together. Majority must additionally carry table_shift."""
    ex = _agree_ex(extractor_module, monkeypatch, [
        _run(37.6, 10.0, 45.3, 24.5),
        _run(32.5, 15.0, 37.6, 10.0),
        _run(37.6, 10.0, 45.3, 24.5),
    ])
    r, flag, _, _ = ex._extract_vision_with_agreement(["x"], "p", "f")
    assert extractor_module.NONDET_FLAG_TABLE_SHIFT in flag
    assert "mean_intervention:majority" in flag
    assert r["mean_intervention"] == 37.6


def test_agreement_cross_arm_pair_is_table_shift(extractor_module, monkeypatch):
    """Reading-B majority draw of Ang: B's control pair == A's intervention pair.
    Only one field's majority differs, but the cross-arm match must still tag."""
    ex = _agree_ex(extractor_module, monkeypatch, [
        _run(32.5, 15.0, 37.6, 10.0),
        _run(32.5, 15.0, 37.6, 10.0),
        _run(37.6, 10.0, 45.3, 24.5),
    ])
    r, flag, _, _ = ex._extract_vision_with_agreement(["x"], "p", "f")
    assert r["mean_intervention"] == 32.5
    assert extractor_module.NONDET_FLAG_TABLE_SHIFT in flag


def test_agreement_identical_arms_are_not_table_shift(extractor_module, monkeypatch):
    ex = _agree_ex(extractor_module, monkeypatch, [_run(5, 1, 5, 1)] * 3)
    _, flag, _, _ = ex._extract_vision_with_agreement(["x"], "p", "f")
    assert flag == []


def test_agreement_single_field_majority_is_not_table_shift(extractor_module, monkeypatch):
    ex = _agree_ex(extractor_module, monkeypatch, [
        _run(1, 1, 2, 2.0), _run(1, 1, 2, 2.0), _run(1, 1, 2, 2.1),
    ])
    _, flag, _, _ = ex._extract_vision_with_agreement(["x"], "p", "f")
    assert flag == ["sd_control:majority"]


def test_agreement_quote_follows_chosen_numbers(extractor_module, monkeypatch):
    """Base run may hold a losing value; quote must come from a winning run."""
    ex = _agree_ex(extractor_module, monkeypatch, [
        _run(1.0, 0.1, 9.0, 0.9, qi="q_base", qc="c_lose"),   # control loses
        _run(1.0, 0.1, 5.0, 0.5, qi="q_base", qc="c_win"),
        _run(2.0, 0.2, 5.0, 0.5, qi="q_other", qc="c_win"),   # intervention loses
    ])
    r, flag, _, _ = ex._extract_vision_with_agreement(["x"], "p", "f")
    assert r["mean_intervention"] == 1.0 and r["mean_control"] == 5.0
    assert r["source_quote_intervention"] == "q_base"
    assert r["source_quote_control"] == "c_win"


def test_agreement_labels_compared_normalised(extractor_module, monkeypatch):
    ex = _agree_ex(extractor_module, monkeypatch, [
        _run(1, 1, 1, 1, cg="Wait-list group"),
        _run(1, 1, 1, 1, cg="wait list group"),
        _run(1, 1, 1, 1, cg="WAITLIST GROUP"),
    ])
    _, flag, _, _ = ex._extract_vision_with_agreement(["x"], "p", "f")
    assert flag == []


def test_agreement_unusable_run_is_counted(extractor_module, monkeypatch):
    ex = _agree_ex(extractor_module, monkeypatch, [
        _run(1, 1, 2, 2), {"garbage": True}, _run(1, 1, 2, 2),
    ])
    r, flag, _, n = ex._extract_vision_with_agreement(["x"], "p", "f")
    assert n == 2
    assert "usable_runs:2/3" in flag
    assert r["mean_intervention"] == 1


def test_agreement_all_unusable_returns_none(extractor_module, monkeypatch):
    ex = _agree_ex(extractor_module, monkeypatch, [{"x": 1}] * 3)
    r, flag, _, n = ex._extract_vision_with_agreement(["x"], "p", "f")
    assert r is None and n == 0


def test_agreement_single_run_sets_sentinel(extractor_module, monkeypatch):
    ex = _agree_ex(extractor_module, monkeypatch, [_run(1, 1, 2, 2)], n=1)
    r, flag, _, n = ex._extract_vision_with_agreement(["x"], "p", "f")
    assert ex.client.chat.completions.calls == 1
    assert flag == [extractor_module.NONDET_FLAG_SINGLE_RUN]


def test_agreement_env_override(extractor_module, monkeypatch):
    monkeypatch.setenv("SR_EXTRACT_N_AGREEMENT", "5")
    ex = _make(extractor_module, monkeypatch)
    assert ex.n_agreement == 5
    monkeypatch.setenv("SR_EXTRACT_N_AGREEMENT", "0")
    assert _make(extractor_module, monkeypatch).n_agreement == 1
    monkeypatch.setenv("SR_EXTRACT_N_AGREEMENT", "many")
    assert _make(extractor_module, monkeypatch).n_agreement == \
        extractor_module.DEFAULT_EXTRACT_N_AGREEMENT
    monkeypatch.delenv("SR_EXTRACT_N_AGREEMENT")
    assert _make(extractor_module, monkeypatch).n_agreement == \
        extractor_module.DEFAULT_EXTRACT_N_AGREEMENT


def test_extract_by_pdf_path_writes_nondet_keys(extractor_module, monkeypatch):
    """End-to-end through the strategy loop: keys survive the restructure step."""
    ex = _agree_ex(extractor_module, monkeypatch, [
        _run(32.5, 15, 37.6, 10), _run(32.5, 15, 37.6, 10), _run(32.5, 15, 37.6, 10.1),
    ])
    monkeypatch.setattr(ex, "_get_page_images_smart", lambda p, f: ["img"])
    monkeypatch.setattr(ex, "_apply_known_pdf_corrections", lambda r, *a: r)
    out = ex.extract_by_pdf_path("/nonexistent.pdf", "f.pdf")
    assert out["extraction_error"] is None
    assert out["nondet_flag"] == ["sd_control:majority"]
    assert out["nondet_runs"] == 3 and out["nondet_usable_runs"] == 3
    assert out["primary_outcome"]["sd_control"] == 10
