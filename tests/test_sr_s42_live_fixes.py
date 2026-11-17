"""Session 42, item 1b live run 20261115_230933 (qwen3-vl:30b, CPU).

1. The launcher's time limit never reached the SR subprocess: _build_sr_cmd
   passed no --time-limit and pipelines/sr/main.py had no such flag, so every
   SR call used the 900 s default (all timeouts stopped at 15 min 3 s, even
   with "Until finished"). time_limits keeps the limit in a module variable,
   so a child process must be told it on the command line.
2. A thinking model ignores "think": false (probe: done_reason=length,
   1186 chars of thinking, empty content). call_ollama_provider then said
   only "Ollama returned an empty response." and every run was "unusable".
   The error must name the cause and the fix (an -instruct vision model).
"""
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import time_limits

SRC = Path(__file__).resolve().parent.parent / "SOURCE_CODE"


@pytest.fixture(autouse=True)
def _reset_limit():
    yield
    time_limits.set_limit(time_limits.parse(time_limits.DEFAULT))


# 1. time limit reaches the SR subprocess

@pytest.mark.parametrize("key", ["15", "30", "60", "none"])
def test_key_for_round_trips(key):
    assert time_limits.key_for(time_limits.parse(key)) == key


def test_key_for_unknown_seconds_is_rejected():
    with pytest.raises(ValueError):
        time_limits.key_for(123)


@pytest.mark.parametrize("seconds,key", [(900, "15"), (1800, "30"),
                                         (3600, "60"), (None, "none")])
def test_build_sr_cmd_passes_the_current_limit(seconds, key):
    import main
    time_limits.set_limit(seconds)
    cmd = main._build_sr_cmd("ollama", "any-model", "SMD", None, "20261116_000000")
    assert cmd[cmd.index("--time-limit") + 1] == key


def test_sr_main_accepts_time_limit_and_sets_it():
    text = (SRC / "pipelines" / "sr" / "main.py").read_text(encoding="utf-8")
    assert '"--time-limit"' in text
    assert "time_limits.set_limit(time_limits.parse(args.time_limit))" in text


# 2. thinking model: say why the answer is empty

def _fake_urlopen(payload):
    def fake(req, timeout=...):
        resp = MagicMock()
        resp.read.return_value = json.dumps(payload).encode()
        resp.__enter__.return_value = resp
        resp.__exit__.return_value = False
        return resp
    return fake


def test_empty_answer_after_thinking_names_cause_and_fix(monkeypatch):
    import providers
    monkeypatch.setattr(providers, "urlopen", _fake_urlopen(
        {"response": "", "thinking": "x" * 1186, "done_reason": "length"}))
    with pytest.raises(RuntimeError) as exc:
        providers.call_ollama_provider("hello", model="some-vl:30b")
    msg = str(exc.value)
    assert "some-vl:30b" in msg
    assert "thinking" in msg
    assert "-instruct" in msg


def test_empty_answer_without_thinking_keeps_old_message(monkeypatch):
    import providers
    monkeypatch.setattr(providers, "urlopen", _fake_urlopen({"response": ""}))
    with pytest.raises(RuntimeError) as exc:
        providers.call_ollama_provider("hello", model="some-vl:30b")
    assert str(exc.value) == "Ollama returned an empty response."

# 3. thinking model cut off mid-answer (done_reason=length): same plain error

def test_cut_off_answer_after_thinking_is_an_error(monkeypatch):
    import providers
    monkeypatch.setattr(providers, "urlopen", _fake_urlopen(
        {"response": '{"mean_intervention": 3.', "thinking": "x" * 3000,
         "done_reason": "length"}))
    with pytest.raises(RuntimeError) as exc:
        providers.call_ollama_provider("hello", model="some-vl:30b")
    assert "some-vl:30b" in str(exc.value)
    assert "-instruct" in str(exc.value)


def test_thinking_model_that_finishes_is_accepted(monkeypatch):
    import providers
    monkeypatch.setattr(providers, "urlopen", _fake_urlopen(
        {"response": '{"ok": 1}', "thinking": "short", "done_reason": "stop"}))
    assert providers.call_ollama_provider("hello", model="m") == '{"ok": 1}'


def test_cut_off_without_thinking_is_returned_as_before(monkeypatch):
    import providers
    monkeypatch.setattr(providers, "urlopen", _fake_urlopen(
        {"response": '{"a": 1', "done_reason": "length"}))
    assert providers.call_ollama_provider("hello", model="m") == '{"a": 1'


# 4. "Skip study:" names the file when author/year are missing (was None (None))

def _audit():
    import pipelines.sr.src.utils.audit_logger as audit
    return audit


def test_skip_label_uses_author_and_year():
    row = {"first_author": "Lami", "year": 2017, "filename": "x.pdf"}
    assert _audit().skip_label(row) == "Lami (2017)"


def test_skip_label_falls_back_to_filename():
    row = {"first_author": None, "year": None,
           "filename": "s10608-017-9875-4.pdf"}
    assert _audit().skip_label(row) == "s10608-017-9875-4.pdf"


def test_skip_label_never_says_none():
    assert "None" not in _audit().skip_label({})


def test_sr_main_skip_lines_use_skip_label():
    text = (SRC / "pipelines" / "sr" / "main.py").read_text(encoding="utf-8")
    assert text.count("Skip study: {skip_label(audit_row)}") == 2
    assert "Skip study: {audit_row['first_author']}" not in text


# 5. the "unusable" line shows what the model answered

@pytest.fixture
def dx():
    try:
        import pipelines.sr.src.extraction.data_extractor as m
    except ImportError as e:
        pytest.skip(f"data_extractor not importable: {e}")
    return m


def test_answer_snippet_shows_length_and_start(dx):
    s = dx.answer_snippet("x" * 500)
    assert "500 chars" in s
    assert "x" * 200 in s and "x" * 201 not in s


def test_answer_snippet_handles_none_and_empty(dx):
    assert "0 chars" in dx.answer_snippet(None)
    assert "0 chars" in dx.answer_snippet("")


def test_unusable_line_logs_the_answer():
    text = (SRC / "pipelines" / "sr" / "src" / "extraction"
            / "data_extractor.py").read_text(encoding="utf-8")
    assert "answer_snippet(raw)" in text
