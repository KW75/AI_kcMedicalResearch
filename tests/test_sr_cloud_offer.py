"""
Session 40, commit 3b (item 12): when the local Ollama model cannot read
page images, SR offers a cloud provider (qwen/openai with an API key set),
like OCR: pick a number, then confirm ([CLOUD] + y). Enter, a wrong number
or no consent -> SR not run, no AI call. A typed --model gets no offer.
A direct run of pipelines/sr/main.py --provider ollama runs the same
vision check before any AI call. No network: capabilities, input and
consent are faked.
"""
import inspect
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "SOURCE_CODE"))

import main  # noqa: E402
import ollama_models  # noqa: E402

KEYS = ("DASHSCOPE_API_KEY", "OPENAI_API_KEY")


def _keys(monkeypatch, *present):
    """CI sets dummy keys for every provider: clear them, then set some."""
    for k in KEYS:
        monkeypatch.delenv(k, raising=False)
    for k in present:
        monkeypatch.setenv(k, "test-key")


def _answers(*answers):
    it = iter(answers)
    return lambda prompt="": next(it)


def _boom(*a, **k):
    raise AssertionError("must not be called")


class _Confirm:
    def __init__(self, answer):
        self.answer, self.asked = answer, []

    def __call__(self, provider):
        self.asked.append(provider)
        return self.answer


def _offer(confirm, input_fn):
    log = []
    return main.sr_offer_cloud(confirm, input_fn=input_fn, log=log.append), log


# ---------- the offer ----------

def test_no_cloud_key_means_no_offer(monkeypatch):
    _keys(monkeypatch)
    result, _ = _offer(_boom, _boom)
    assert result is None


def test_no_consent_function_means_no_offer(monkeypatch):
    _keys(monkeypatch, "DASHSCOPE_API_KEY")
    result, _ = _offer(None, _boom)
    assert result is None


def test_pick_qwen_and_confirm(monkeypatch):
    _keys(monkeypatch, "DASHSCOPE_API_KEY")
    c = _Confirm(True)
    result, log = _offer(c, _answers("1"))
    assert result == "qwen"
    assert c.asked == ["qwen"]
    assert any("leave this machine" in line for line in log)


def test_both_keys_pick_openai(monkeypatch):
    _keys(monkeypatch, *KEYS)
    result, _ = _offer(_Confirm(True), _answers("2"))
    assert result == "openai"


def test_enter_cancels_without_asking_consent(monkeypatch):
    _keys(monkeypatch, "DASHSCOPE_API_KEY")
    result, log = _offer(_boom, _answers(""))
    assert result is None
    assert any("not run" in line.lower() for line in log)


def test_wrong_number_stops(monkeypatch):
    _keys(monkeypatch, "DASHSCOPE_API_KEY")
    result, _ = _offer(_boom, _answers("9"))
    assert result is None


def test_no_consent_stops(monkeypatch):
    _keys(monkeypatch, "DASHSCOPE_API_KEY")
    c = _Confirm(False)
    result, _ = _offer(c, _answers("1"))
    assert result is None
    assert c.asked == ["qwen"]


def test_sr_cloud_keys_match_ocr():
    from pipelines.ocr import cli as ocr_cli
    assert main.SR_CLOUD_KEYS == ocr_cli.CLOUD_KEYS


def test_launcher_has_consent_hook_and_offer():
    assert "confirm" in inspect.signature(main.run_sr_launcher).parameters
    assert "sr_offer_cloud(" in inspect.getsource(main.run_sr_launcher)


# ---------- one vision check for both routes ----------

def test_one_vision_check_for_launcher_and_direct_run():
    no = lambda h, n: {"completion"}
    msg = ollama_models.sr_vision_error("qwen3:8b", caps_fn=no)
    assert "cannot read page images" in msg
    assert main.sr_ollama_vision_error("qwen3:8b", caps_fn=no) == msg
    assert ollama_models.sr_vision_error(
        "gemma4:e4b", caps_fn=lambda h, n: {"vision"}) is None


# ---------- direct run of pipelines/sr/main.py ----------

class _Stop(Exception):
    pass


def _direct(monkeypatch, caps):
    from pipelines.sr import main as sr_main

    def stop(*a, **k):
        raise _Stop

    monkeypatch.setattr(sys, "argv",
                        ["sr", "--provider", "ollama", "--model", "qwen3:8b"])
    monkeypatch.setattr(sr_main, "resolve_model", lambda p, m: m)
    monkeypatch.setattr(ollama_models, "model_capabilities",
                        lambda h, n: caps)
    monkeypatch.setattr(sr_main, "load_config", stop)  # first step after the check
    return sr_main


def test_direct_run_stops_without_vision(monkeypatch):
    sr_main = _direct(monkeypatch, {"completion"})
    with pytest.raises(SystemExit) as e:
        sr_main.main()
    assert "cannot read page images" in str(e.value.code)


def test_direct_run_continues_with_vision(monkeypatch):
    sr_main = _direct(monkeypatch, {"completion", "vision"})
    with pytest.raises(_Stop):
        sr_main.main()
