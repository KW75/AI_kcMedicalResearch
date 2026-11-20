"""Session 49 PR E: SaMD steps 2-3 (AI); no browser output yet.

Pinned:
- One AI call per image page, then one reasoning call (images + 1).
- Text layers (.txt/.docx/PDF text) need no AI call.
- Step files in reports/samd/<run_id>/: step2_<nn>_<file>.txt, case.md,
  reasoning.md (intended use on top).
- A failed or empty AI reply, an unreadable file or a case too long for
  the model's context stops the job: no reasoning.md (no half answer).
- No model -> stops after step 1 (the doctor's text is kept).
- confirm is used only for the cloud offer when no local vision model is
  pulled; run_cli already asked for --provider qwen/openai (one banner).
"""
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from SOURCE_CODE.pipelines.ocr import cli as ocr_cli
from SOURCE_CODE.pipelines.samd import cli

NOW = datetime(2026, 11, 20, 16, 0, 0)
RUN = "20261120_160000"


@pytest.fixture(autouse=True)
def _no_browser(monkeypatch):
    # PR F: run() opens the report in the browser; never in tests.
    monkeypatch.setattr(cli, "open_browser", lambda p, log=print: None, raising=False)

def _full():
    return "\n".join(f"{h}\nx" for h in cli.HEADINGS)


def _answers(*items):
    it = iter(items)
    return lambda _p="": next(it)


def _fake_pages(path):
    if path.suffix.lower() in (".png", ".jpg"):
        return [{"number": 1, "text": None, "png": b"PNG-" + path.name.encode()}]
    return [{"number": 1, "text": "note text from " + path.name, "png": None}]


class Fake:
    def __init__(self, *replies):
        self.replies = list(replies)
        self.calls = []

    def __call__(self, prompt, images=None):
        self.calls.append((prompt, images))
        r = self.replies.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


@pytest.fixture
def case(tmp_path, monkeypatch):
    d = tmp_path / "input" / "samd"
    d.mkdir(parents=True)
    for n in ("labs.png", "notes.txt", "rash.jpg"):
        (d / n).write_bytes(b"abc")
    monkeypatch.setattr(cli, "read_pages", _fake_pages)
    return tmp_path


def _run(base, fake, monkeypatch, answers=("", "55F, rash and anaemia", "")):
    monkeypatch.setattr(cli, "choose_call", lambda *a, **k: fake)
    lines = []
    res = cli.run(base, input_fn=_answers(*answers), log=lines.append, now=NOW)
    return res, "\n".join(lines)


# --- steps 2-3 ---------------------------------------------------------------

def test_one_call_per_image_then_reasoning(case, monkeypatch):
    fake = Fake("TYPE: TEXT\nHb 9.1 g/dL", "TYPE: PHOTO\nred scaly plaque", _full())
    res, _ = _run(case, fake, monkeypatch)
    assert len(fake.calls) == 3
    assert fake.calls[0][1] == [b"PNG-labs.png"]
    assert fake.calls[1][1] == [b"PNG-rash.jpg"]
    prompt, images = fake.calls[2]
    assert images is None
    for s in ("Hb 9.1 g/dL", "red scaly plaque", "note text from notes.txt",
              "55F, rash and anaemia"):
        assert s in prompt
    assert "TYPE:" not in prompt
    assert res["ai_called"] is True


def test_step_files(case, monkeypatch):
    fake = Fake("TYPE: TEXT\nHb 9.1 g/dL", "TYPE: PHOTO\nred scaly plaque", _full())
    res, _ = _run(case, fake, monkeypatch)
    d = case / "reports" / "samd" / RUN
    lab = (d / "step2_01_labs.png.txt").read_text(encoding="utf-8")
    assert "transcription" in lab and "Hb 9.1 g/dL" in lab
    assert "text layer" in (d / "step2_02_notes.txt.txt").read_text(encoding="utf-8")
    assert "photo description" in (d / "step2_03_rash.jpg.txt").read_text(encoding="utf-8")
    assert "Hb 9.1 g/dL" in (d / "case.md").read_text(encoding="utf-8")
    answer = (d / "reasoning.md").read_text(encoding="utf-8")
    assert answer.startswith(cli.INTENDED_USE)
    assert _full() in answer
    assert res["answer"] == d / "reasoning.md"
    log = (d / "run.log").read_text(encoding="utf-8")
    assert "Step 3" in log and cli.INTENDED_USE in log
    assert (case / "output" / "samd" / RUN / "report.html").exists()


def test_text_file_needs_no_ai_call(case, monkeypatch):
    fake = Fake(_full())
    _run(case, fake, monkeypatch, answers=("2", ""))
    assert len(fake.calls) == 1 and fake.calls[0][1] is None


def test_reply_without_type_line_is_kept(case, monkeypatch):
    fake = Fake("Hb 9.1 g/dL", "TYPE: PHOTO\nplaque", _full())
    _run(case, fake, monkeypatch)
    lab = (case / "reports" / "samd" / RUN / "step2_01_labs.png.txt").read_text(encoding="utf-8")
    assert "image (type not stated)" in lab and "Hb 9.1 g/dL" in lab


@pytest.mark.parametrize("replies, n_calls", [
    ((RuntimeError("HTTP 500"),), 1),
    (("   ",), 1),
    (("TYPE: TEXT\nHb", "TYPE: PHOTO\np", RuntimeError("timeout")), 3),
    (("TYPE: TEXT\nHb", "TYPE: PHOTO\np", ""), 3),
])
def test_failed_or_empty_reply_writes_no_answer(case, monkeypatch, replies, n_calls):
    fake = Fake(*replies)
    res, out = _run(case, fake, monkeypatch)
    assert len(fake.calls) == n_calls
    assert res["answer"] is None
    assert not (case / "reports" / "samd" / RUN / "reasoning.md").exists()
    assert "No answer written" in out


def test_missing_headings_are_named(case, monkeypatch):
    partial = "\n".join(f"{h}\nx" for h in cli.HEADINGS if h != "## Red flags")
    fake = Fake("TYPE: TEXT\nHb", "TYPE: PHOTO\np", partial)
    res, out = _run(case, fake, monkeypatch)
    assert res["answer"] is not None
    assert "Red flags" in out and "missing" in out.lower()


def test_case_too_long_stops_before_reasoning(case, monkeypatch):
    monkeypatch.setattr(cli, "_case_limit", lambda: 10)
    fake = Fake("TYPE: TEXT\nHb", "TYPE: PHOTO\np", _full())
    res, out = _run(case, fake, monkeypatch)
    assert len(fake.calls) == 2
    assert res["answer"] is None
    assert "too long" in out


def test_unreadable_file_stops_before_any_ai_call(case, monkeypatch):
    def bad(path):
        raise ValueError("broken file")
    monkeypatch.setattr(cli, "read_pages", bad)
    fake = Fake(_full())
    res, out = _run(case, fake, monkeypatch)
    assert fake.calls == []
    assert res["answer"] is None
    assert "Could not read labs.png" in out


def test_no_model_stops_after_step1(case, monkeypatch):
    monkeypatch.setattr(cli, "choose_call", lambda *a, **k: None)
    res = cli.run(case, input_fn=_answers("", "55F", ""), log=lambda m: None, now=NOW)
    d = case / "reports" / "samd" / RUN
    assert res["ai_called"] is False and res["answer"] is None
    assert (d / "clinician_input.txt").exists()
    assert not (d / "case.md").exists()


# --- choose_call: one cloud banner only --------------------------------------

def test_cloud_provider_does_not_ask_again():
    confirm = MagicMock()
    assert callable(cli.choose_call("qwen", None, confirm=confirm, log=lambda m: None))
    confirm.assert_not_called()


def test_local_model_with_vision():
    confirm = MagicMock()
    call = cli.choose_call("ollama", "m:1", confirm=confirm, log=lambda m: None,
                           caps_fn=lambda host, name: ["completion", "vision"])
    assert callable(call)
    confirm.assert_not_called()


def test_local_model_without_vision():
    msgs = []
    assert cli.choose_call("ollama", "m:1", log=msgs.append,
                           caps_fn=lambda h, n: ["completion"]) is None
    assert "cannot read images" in msgs[-1]


def test_pulled_vision_model_is_picked():
    confirm = MagicMock()
    pick = MagicMock(return_value="qwen3-vl:8b")
    call = cli.choose_call("ollama", None, confirm=confirm, log=lambda m: None,
                           models_fn=lambda: [{"name": "qwen3-vl:8b"}], pick_fn=pick)
    assert callable(call)
    pick.assert_called_once()
    confirm.assert_not_called()


def test_no_model_picked():
    assert cli.choose_call("ollama", None, log=lambda m: None,
                           models_fn=lambda: [{"name": "a"}],
                           pick_fn=lambda *a, **k: None) is None


def test_no_local_vision_offers_cloud_once(monkeypatch):
    monkeypatch.setattr(ocr_cli, "_cloud_choices", lambda: ["qwen"])
    confirm = MagicMock(return_value=True)
    msgs = []
    call = cli.choose_call("ollama", None, confirm=confirm, input_fn=_answers("1"),
                           log=msgs.append, models_fn=lambda: [])
    assert callable(call)
    confirm.assert_called_once_with("qwen")
    assert any("clinical photos" in m for m in msgs)


def test_cloud_offer_enter_cancels(monkeypatch):
    monkeypatch.setattr(ocr_cli, "_cloud_choices", lambda: ["qwen"])
    confirm = MagicMock()
    assert cli.choose_call("ollama", None, confirm=confirm, input_fn=_answers(""),
                           log=lambda m: None, models_fn=lambda: []) is None
    confirm.assert_not_called()


def test_no_vision_model_and_no_key(monkeypatch):
    monkeypatch.setattr(ocr_cli, "_cloud_choices", lambda: [])
    msgs = []
    assert cli.choose_call("ollama", None, confirm=MagicMock(), log=msgs.append,
                           models_fn=lambda: []) is None
    assert "ollama pull" in " ".join(msgs)

@pytest.mark.parametrize("rule", [
    "compare it with its reference",
    "a value inside its range is normal",
    "do not support the premise",
    "state both",
    "Address every finding the doctor typed",
    "unless the case says so",
    "explain the doctor's main complaint",
    "why a test was ordered",
])
def test_reasoning_prompt_rules(rule):
    # First real run (20261120_142307): Hb 13.7 (13.5-17.3) called anaemia,
    # typed age 62 replaced by 71, typed rash ignored, absent signs invented.
    assert rule in cli.REASONING_PROMPT
