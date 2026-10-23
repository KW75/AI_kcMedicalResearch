"""v2.5: --time-limit reaches every place that used the hard-coded 900 s
(coding/writing watchdogs, Ollama call, Ollama streaming)."""
import importlib
import json
import re
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import time_limits

SRC = Path(__file__).resolve().parent.parent / "SOURCE_CODE"


@pytest.fixture(autouse=True)
def _reset_limit():
    yield
    time_limits.set_limit(time_limits.parse(time_limits.DEFAULT))


class TestCommandLine:
    @pytest.mark.parametrize("flag,stored,seconds", [
        ([], "15", 900),
        (["--time-limit", "30"], "30", 1800),
        (["--time-limit", "60"], "60", 3600),
        (["--time-limit", "none"], "none", None),
        (["--time-limit", "NONE"], "none", None),
    ])
    def test_parse_args_sets_the_limit(self, flag, stored, seconds):
        import main
        time_limits.set_limit(123)  # prove parse_args overwrites it
        args = main.parse_args(["--mode", "writing"] + flag)
        assert args.time_limit == stored
        assert time_limits.get_limit() == seconds

    def test_other_values_are_rejected(self):
        import main
        with pytest.raises(SystemExit):
            main.parse_args(["--time-limit", "10"])


@pytest.mark.parametrize("modname", ["pipelines.coding.coding",
                                     "pipelines.writing.writing"])
class TestWatchdog:
    def test_uses_the_current_limit(self, modname, monkeypatch):
        mod = importlib.import_module(modname)
        seen = []

        def fake_wait(thread, seconds):
            seen.append(seconds)
            thread.join(5)
            return True

        monkeypatch.setattr(time_limits, "wait_for", fake_wait)
        time_limits.set_limit(3600)
        out = mod._call_llm("sys", "user",
                            lambda system_prompt, user_prompt: "ok")
        assert seen == [3600]
        assert "ok" in out

    def test_timeout_message_names_the_limit(self, modname, monkeypatch):
        mod = importlib.import_module(modname)
        release = threading.Event()
        monkeypatch.setattr(time_limits, "wait_for", lambda t, s: False)
        time_limits.set_limit(1800)
        out = mod._call_llm("sys", "user",
                            lambda system_prompt, user_prompt: release.wait(5) and "late")
        release.set()
        assert out.startswith("[ERROR] LLM call timed out after 30 minutes")


class TestOllamaTimeouts:
    @pytest.mark.parametrize("seconds", [1800, None])
    def test_call_ollama_provider(self, seconds, monkeypatch):
        import providers
        seen = {}

        def fake_urlopen(req, timeout=...):
            seen["timeout"] = timeout
            resp = MagicMock()
            resp.read.return_value = json.dumps({"response": "hi"}).encode()
            resp.__enter__.return_value = resp
            resp.__exit__.return_value = False
            return resp

        monkeypatch.setattr(providers, "urlopen", fake_urlopen)
        time_limits.set_limit(seconds)
        providers.call_ollama_provider("hello", model="gemma4:e4b")
        assert seen["timeout"] == seconds

    @pytest.mark.parametrize("seconds", [3600, None])
    def test_stream_ollama(self, seconds):
        import streaming
        seen = {}
        lines = [json.dumps({"response": "a", "done": True}).encode() + b"\n"]

        def fake_urlopen(req, timeout=...):
            seen["timeout"] = timeout
            resp = MagicMock()
            resp.__iter__.return_value = iter(lines)
            return resp

        time_limits.set_limit(seconds)
        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            list(streaming._stream_ollama("hello", model="gemma4:e4b"))
        assert seen["timeout"] == seconds


@pytest.mark.parametrize("rel", ["pipelines/coding/coding.py",
                                 "pipelines/writing/writing.py",
                                 "providers.py", "streaming.py"])
def test_no_hard_coded_15_minutes_left(rel):
    text = (SRC / rel).read_text(encoding="utf-8")
    assert not re.search(r"timeout\s*=\s*900\b", text)
    assert "15 minutes" not in text
