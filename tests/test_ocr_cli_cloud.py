"""OCR cloud step 3: cli.run sends page images to Qwen/OpenAI only with consent.

Fakes only: no Ollama, no network. Covers --provider qwen/openai, and the
offer of a cloud provider when no local vision model is pulled.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "SOURCE_CODE"))

from pipelines.ocr import cli, engine  # noqa: E402


class FakeEngine:
    def __init__(self):
        self.calls = []

    def _record(self, src, out_dir, name, model, log=print,
                records_root=None, call=None):
        self.calls.append({"model": model, "call": call})
        return {"header": "H", "records": [], "failed": [], "summary": []}

    run_single = _record
    run_set = _record


def _boom(*args, **kwargs):
    raise AssertionError("must not be called")


def _answers(*items):
    it = iter(items)
    return lambda prompt="": next(it)


def _one_file(tmp_path):
    folder = tmp_path / "input" / "ocr"
    folder.mkdir(parents=True)
    (folder / "a.txt").write_text("BP 140/90 mmHg", encoding="utf-8")


def _run(tmp_path, eng, **kw):
    logs = []
    kw.setdefault("list_fn", lambda host=None: [])
    kw.setdefault("caps_fn", lambda host, name: set())
    result = cli.run(tmp_path, run_single=eng.run_single,
                     run_set=eng.run_set, log=logs.append, **kw)
    return result, "\n".join(logs)


def test_cloud_provider_does_not_ask_ollama(tmp_path):
    _one_file(tmp_path)
    eng = FakeEngine()
    _run(tmp_path, eng, provider="qwen", list_fn=_boom, caps_fn=_boom,
         input_fn=_answers("Scan"))
    assert len(eng.calls) == 1
    assert eng.calls[0]["call"] is not None
    assert eng.calls[0]["model"].endswith("(qwen, cloud)")


def test_chosen_cloud_model_is_named_in_the_output(tmp_path):
    _one_file(tmp_path)
    eng = FakeEngine()
    _run(tmp_path, eng, provider="openai", model="gpt-4o",
         input_fn=_answers("Scan"))
    assert eng.calls[0]["model"] == "gpt-4o (openai, cloud)"


def test_no_local_model_offers_cloud_and_runs_after_yes(tmp_path, monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "k")
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    _one_file(tmp_path)
    eng = FakeEngine()
    asked = []

    def confirm(provider):
        asked.append(provider)
        return True

    _run(tmp_path, eng, confirm=confirm, input_fn=_answers("1", "Scan"))
    assert asked == ["qwen"]
    assert eng.calls[0]["model"].endswith("(qwen, cloud)")


def test_cloud_not_confirmed_means_job_not_run(tmp_path, monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "k")
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    _one_file(tmp_path)
    eng = FakeEngine()
    result, log = _run(tmp_path, eng, confirm=lambda p: False,
                       input_fn=_answers("2"))
    assert result is None
    assert eng.calls == []
    assert "Job not run" in log


def test_enter_at_cloud_offer_cancels(tmp_path, monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "k")
    _one_file(tmp_path)
    eng = FakeEngine()
    result, _ = _run(tmp_path, eng, confirm=_boom, input_fn=_answers(""))
    assert result is None
    assert eng.calls == []


def test_no_cloud_key_keeps_the_pull_message(tmp_path, monkeypatch):
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _one_file(tmp_path)
    eng = FakeEngine()
    result, log = _run(tmp_path, eng, confirm=_boom, input_fn=_boom)
    assert result is None
    assert "ollama pull" in log


def test_cloud_call_sends_images_to_the_chosen_provider(monkeypatch):
    import providers
    seen = {}

    def fake(prompt, model=None, images=None):
        seen.update(prompt=prompt, model=model, images=images)
        return "TEXT"

    monkeypatch.setattr(providers, "call_qwen_provider", fake)
    call = engine.cloud_call("qwen", None)
    assert call("read this", images=[b"png"]) == "TEXT"
    assert seen == {"prompt": "read this", "model": None, "images": [b"png"]}
