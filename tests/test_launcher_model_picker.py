"""Tests for the Ollama model picker in scripts/launcher.py.

The launcher lives in scripts/, not SOURCE_CODE/, so it is loaded by path.
colorama is replaced with a dummy during import: colorama.init() can wrap
sys.stdout, which would interfere with pytest's output capture.
"""
import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parent.parent

MODELS = [  # what list_ollama_models returns: smallest first, embeddings included
    {"name": "nomic-embed-text:latest", "size_gb": 0.3, "params_b": 0.1},
    {"name": "llama3.2:latest", "size_gb": 2.0, "params_b": 3.2},
    {"name": "gemma4:e4b", "size_gb": 6.6, "params_b": 7.5},
    {"name": "qwen3:8b", "size_gb": 5.2, "params_b": 8.2},
    {"name": "qwen2.5:14b-instruct", "size_gb": 9.0, "params_b": 14.8},
]
CHAT = [m for m in MODELS if "embed" not in m["name"]]
NO_DEFAULT = [m for m in MODELS if m["name"] != "gemma4:e4b"]


@pytest.fixture(scope="module")
def launcher():
    spec = importlib.util.spec_from_file_location(
        "launcher_under_test", ROOT / "scripts" / "launcher.py"
    )
    mod = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {"colorama": MagicMock()}):
        spec.loader.exec_module(mod)
    return mod


@pytest.fixture(autouse=True)
def env_path(launcher, tmp_path, monkeypatch):
    """Every test reads a temp .env (absent unless written), never the real one."""
    path = tmp_path / ".env"
    monkeypatch.setattr(launcher, "ENV_FILE", path)
    return path


def _caps(host, name):
    """Capabilities as Ollama's /api/show reports them."""
    if "embed" in name:
        return {"embedding"}
    return {"completion", "vision"} if name == "gemma4:e4b" else {"completion"}


def _pick(launcher, inputs, models=MODELS):
    with patch.object(launcher, "list_ollama_models", return_value=models), \
         patch.object(launcher, "model_capabilities", side_effect=_caps), \
         patch.object(launcher, "safe_input", side_effect=inputs) as fake_input:
        return launcher.pick_ollama_model(), fake_input


class TestPickOllamaModel:
    """Session 33 rule: default = OLLAMA_MODEL in .env, else gemma4:e4b.
    Only models that can chat (capability 'completion') are offered.
    No ranks, no pull hints, no silent switch to another model."""

    def test_enter_picks_code_default_when_env_unset(self, launcher):
        chosen, _ = _pick(launcher, [""])
        assert chosen == "gemma4:e4b"

    def test_enter_picks_the_env_default(self, launcher, env_path):
        env_path.write_text("OLLAMA_MODEL=qwen3:8b\n", encoding="utf-8")
        chosen, _ = _pick(launcher, [""])
        assert chosen == "qwen3:8b"

    def test_env_default_is_the_one_marked(self, launcher, env_path, capsys):
        env_path.write_text("OLLAMA_MODEL=qwen3:8b\n", encoding="utf-8")
        _pick(launcher, [""])
        marked = [l for l in capsys.readouterr().out.splitlines() if "(default)" in l]
        assert len(marked) == 1 and "qwen3:8b" in marked[0]

    def test_embedding_models_are_hidden(self, launcher, capsys):
        _pick(launcher, [""])
        assert "nomic-embed-text" not in capsys.readouterr().out

    def test_number_picks_that_model(self, launcher):
        chosen, _ = _pick(launcher, ["3"])  # 1 llama3.2, 2 gemma4, 3 qwen3:8b
        assert chosen == "qwen3:8b"

    def test_invalid_choice_asks_again(self, launcher):
        chosen, fake_input = _pick(launcher, ["5", "abc", "2"])  # only 4 chat models
        assert chosen == "gemma4:e4b"
        assert fake_input.call_count == 3

    def test_default_not_pulled_is_not_switched(self, launcher, capsys):
        chosen, _ = _pick(launcher, [""], models=NO_DEFAULT)
        assert chosen == "gemma4:e4b"
        out = capsys.readouterr().out
        assert "not pulled" in out
        assert "ollama pull gemma4:e4b" in out

    def test_ollama_unreachable_returns_empty_without_asking(self, launcher, capsys):
        chosen, fake_input = _pick(launcher, [], models=[])
        assert chosen == ""
        assert fake_input.call_count == 0
        out = capsys.readouterr().out
        assert "Ollama" in out
        assert "will pick one" not in out  # no auto-detection any more
        assert "gemma4:e4b" in out

    def test_only_embedding_models_returns_empty_without_asking(self, launcher, capsys):
        chosen, fake_input = _pick(launcher, [], models=MODELS[:1])
        assert chosen == ""
        assert fake_input.call_count == 0
        assert "no chat model" in capsys.readouterr().out.lower()

    def test_menu_shows_descriptions_and_no_ranks_or_pull_hints(self, launcher, capsys):
        from ollama_models import describe
        _pick(launcher, [""])
        out = capsys.readouterr().out
        for m in CHAT:
            assert describe(m, _caps(None, m["name"])) in out
        assert "(default)" in out
        assert "Ranks:" not in out
        assert "comparison" not in out
        assert "ollama pull" not in out


class TestPickProviderWiring:
    def test_ollama_adds_model_flag(self, launcher):
        with patch.object(launcher, "pick_ollama_model", return_value="qwen3:8b"), \
             patch.object(launcher, "safe_input", side_effect=[""]):
            assert launcher.pick_provider("--mode writing") == "--provider ollama --model qwen3:8b"

    def test_ollama_unreachable_gives_no_model_flag(self, launcher):
        with patch.object(launcher, "pick_ollama_model", return_value=""), \
             patch.object(launcher, "safe_input", side_effect=["1"]):
            assert launcher.pick_provider("--mode writing") == "--provider ollama"

    def test_cloud_provider_unchanged_and_no_model_question(self, launcher):
        with patch.object(launcher, "pick_ollama_model") as fake_pick, \
             patch.object(launcher, "safe_input", side_effect=["4"]):
            assert launcher.pick_provider("--mode writing") == "--provider deepseek"
        fake_pick.assert_not_called()

    def test_sr_blocks_ollama_before_asking_for_a_model(self, launcher):
        # "1" = Ollama (blocked for SR), "" = "Press Enter to choose again", "2" = Qwen
        with patch.object(launcher, "pick_ollama_model") as fake_pick, \
             patch.object(launcher, "safe_input", side_effect=["1", "", "2"]):
            assert launcher.pick_provider("--mode sr") == "--provider qwen"
        fake_pick.assert_not_called()

class TestPickTimeLimit:
    """v2.5: launcher asks the time limit per AI call. Enter = 15 min and adds
    no flag, so the command is unchanged from before."""

    def _ask(self, launcher, inputs):
        with patch.object(launcher, "safe_input", side_effect=inputs) as fake:
            result = launcher.pick_time_limit()
        return result, fake.call_count

    def test_enter_keeps_15_minutes_and_adds_no_flag(self, launcher):
        assert self._ask(launcher, [""]) == ("", 1)

    def test_number_picks_that_limit(self, launcher):
        for choice, flag in [("1", ""), ("2", "--time-limit 30"),
                             ("3", "--time-limit 60"), ("4", "--time-limit none")]:
            assert self._ask(launcher, [choice]) == (flag, 1), choice

    def test_invalid_choice_asks_again(self, launcher):
        assert self._ask(launcher, ["9", "x", "2"]) == ("--time-limit 30", 3)

    def test_menu_lists_every_choice_with_default_marked(self, launcher, capsys):
        import time_limits
        self._ask(launcher, [""])
        out = capsys.readouterr().out
        for label in time_limits.LABELS.values():
            assert label in out
        assert "(default)" in out


class TestTimeLimitFlag:
    def test_dry_run_never_asks(self, launcher):
        with patch.object(launcher, "pick_time_limit",
                          side_effect=AssertionError("asked on --dry-run")):
            assert launcher.time_limit_flag("--dry-run") == ""

    def test_ai_modes_ask(self, launcher):
        with patch.object(launcher, "pick_time_limit", return_value="--time-limit 60"):
            assert launcher.time_limit_flag("--mode writing") == "--time-limit 60"
