"""Setup -> Local AI (Ollama) screen in scripts/launcher.py (Session 33 commit 5).

Nothing here touches the real Ollama, the network or the real .env: the
ollama executable lookup, /api/version, the model list, capabilities,
subprocess.run (ollama pull) and input are all patched, and ENV_FILE /
ENV_TEMPLATE point at a temp folder.
"""
import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import env_file

ROOT = Path(__file__).resolve().parent.parent
EXE = r"C:\Ollama\ollama.exe"
MODELS = [  # list_ollama_models: every pulled model, smallest first
    {"name": "nomic-embed-text:latest", "size_gb": 0.3, "params_b": 0.1},
    {"name": "llama3.2:latest", "size_gb": 2.0, "params_b": 3.2},
    {"name": "gemma4:e4b", "size_gb": 6.6, "params_b": 7.5},
    {"name": "qwen3:8b", "size_gb": 5.2, "params_b": 8.2},
]


@pytest.fixture(scope="module")
def launcher():
    spec = importlib.util.spec_from_file_location(
        "launcher_local_ai_under_test", ROOT / "scripts" / "launcher.py"
    )
    mod = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {"colorama": MagicMock()}):
        spec.loader.exec_module(mod)
    return mod


@pytest.fixture(autouse=True)
def env_path(launcher, tmp_path, monkeypatch):
    """Temp .env (absent until saved) and template; no Windows variable."""
    template = tmp_path / ".env.example"
    template.write_text("OLLAMA_MODEL=gemma4:e4b\n", encoding="utf-8")
    path = tmp_path / ".env"
    monkeypatch.setattr(launcher, "ENV_FILE", path)
    monkeypatch.setattr(launcher, "ENV_TEMPLATE", template)
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    return path


def _caps(host, name):
    if "embed" in name:
        return {"embedding"}
    return {"completion", "vision"} if name == "gemma4:e4b" else {"completion"}


def _run(launcher, inputs, *, exe=EXE, version="0.40.11", rc=0, run_exc=None):
    result = MagicMock(returncode=rc)
    with patch.object(launcher, "_ollama_exe", return_value=exe), \
         patch.object(launcher, "ollama_version", return_value=version), \
         patch.object(launcher, "list_ollama_models", return_value=MODELS), \
         patch.object(launcher, "model_capabilities", side_effect=_caps), \
         patch.object(launcher, "safe_input", side_effect=inputs) as fake_input, \
         patch.object(launcher.subprocess, "run", return_value=result,
                      side_effect=run_exc) as fake_run:
        launcher.local_ai_menu()
    return fake_input, fake_run


def _default(path):
    return env_file.read_values(path).get("OLLAMA_MODEL") if path.exists() else None


def _prompts(fake_input):
    return " ".join(str(c.args[0]) for c in fake_input.call_args_list)


# --- reaching the screen and status -----------------------------------------

def test_setup_item_2_opens_local_ai(launcher):
    with patch.object(launcher, "local_ai_menu") as fake_menu, \
         patch.object(launcher, "safe_input", side_effect=["2", "0"]):
        launcher.setup_menu()
    fake_menu.assert_called_once()


def test_not_installed_points_to_download_and_offers_nothing(launcher, capsys):
    fake_input, fake_run = _run(launcher, [""], exe="", version="")
    out = capsys.readouterr().out
    assert "not installed" in out.lower()
    assert "https://ollama.com/download" in out
    assert "Change default" not in out
    assert fake_input.call_count == 1
    fake_run.assert_not_called()


def test_not_running_says_so_and_offers_nothing(launcher, capsys):
    fake_input, fake_run = _run(launcher, [""], version="")
    out = capsys.readouterr().out
    assert "not running" in out.lower()
    assert "Change default" not in out
    assert fake_input.call_count == 1
    fake_run.assert_not_called()


def test_status_shows_version_and_env_default(launcher, env_path, capsys):
    env_path.write_text("OLLAMA_MODEL=qwen3:8b\n", encoding="utf-8")
    _run(launcher, ["0"])
    out = capsys.readouterr().out
    assert "0.40.11" in out
    assert "qwen3:8b" in out
    assert "Change default model" in out
    assert "Pull a new model" in out


def test_status_shows_code_default_when_env_unset(launcher, capsys):
    _run(launcher, ["0"])
    assert "gemma4:e4b" in capsys.readouterr().out


def test_invalid_choice_says_so(launcher, capsys):
    _run(launcher, ["9", "0"])
    assert "invalid choice" in capsys.readouterr().out.lower()


# --- 1 Change default model --------------------------------------------------

def test_change_default_saves_to_env(launcher, env_path):
    _run(launcher, ["1", "3", "0"])  # 1 llama3.2, 2 gemma4, 3 qwen3:8b
    assert _default(env_path) == "qwen3:8b"


def test_change_default_lists_chat_models_only_and_enter_cancels(launcher, env_path, capsys):
    _run(launcher, ["1", "", "0"])
    assert "nomic-embed-text" not in capsys.readouterr().out
    assert not env_path.exists()


def test_warns_when_windows_variable_overrides(launcher, env_path, monkeypatch, capsys):
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.2:latest")
    _run(launcher, ["1", "3", "0"])
    out = capsys.readouterr().out
    assert _default(env_path) == "qwen3:8b"
    assert "windows" in out.lower() and "OLLAMA_MODEL" in out


# --- 2 Pull a new model ------------------------------------------------------

def test_pull_runs_ollama_after_warning_and_yes(launcher, env_path, capsys):
    fake_input, fake_run = _run(launcher, ["2", "qwen3:4b", "y", "", "0"])
    fake_run.assert_called_once()
    assert fake_run.call_args.args[0] == [EXE, "pull", "qwen3:4b"]
    assert "GB" in capsys.readouterr().out
    assert "[y/N]" in _prompts(fake_input)
    assert not env_path.exists()  # Enter at "make it the default?" = no


def test_pull_enter_at_confirm_downloads_nothing(launcher, capsys):
    _, fake_run = _run(launcher, ["2", "qwen3:4b", "", "0"])
    fake_run.assert_not_called()
    assert "cancel" in capsys.readouterr().out.lower()


def test_pull_then_make_it_the_default(launcher, env_path):
    _run(launcher, ["2", "qwen3:4b", "y", "y", "0"])
    assert _default(env_path) == "qwen3:4b"


def test_failed_pull_says_so_and_does_not_offer_default(launcher, env_path, capsys):
    fake_input, _ = _run(launcher, ["2", "nosuch:model", "y", "0"], rc=1)
    assert "failed" in capsys.readouterr().out.lower()
    assert fake_input.call_count == 4
    assert not env_path.exists()


def test_bad_model_name_is_rejected(launcher, capsys):
    _, fake_run = _run(launcher, ["2", "rm -rf /", "0"])
    fake_run.assert_not_called()
    assert "invalid model name" in capsys.readouterr().out.lower()


def test_ctrl_c_during_download_is_handled(launcher, env_path, capsys):
    fake_input, _ = _run(launcher, ["2", "qwen3:4b", "y", "0"], run_exc=KeyboardInterrupt)
    assert "stopped" in capsys.readouterr().out.lower()
    assert fake_input.call_count == 4
    assert not env_path.exists()
