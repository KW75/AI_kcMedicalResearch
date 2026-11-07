"""Tests for Setup -> 1 API keys in scripts/launcher.py (Session 33 commit 2).

Every test points the launcher at a temp .env, so the real .env is never
read or written. Key values must never appear on screen, only the mask.
"""
import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

ROOT = Path(__file__).resolve().parent.parent
KEY_VARS = ["DASHSCOPE_API_KEY", "GROQ_API_KEY", "DEEPSEEK_API_KEY",
            "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]


def _load(monkeypatch):
    # colorama.init() can wrap sys.stdout and break pytest's capture.
    monkeypatch.setitem(sys.modules, "colorama", MagicMock())
    spec = importlib.util.spec_from_file_location(
        "launcher_keys_under_test", ROOT / "scripts" / "launcher.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def launcher(monkeypatch, tmp_path):
    mod = _load(monkeypatch)
    monkeypatch.setattr(mod, "ENV_FILE", tmp_path / ".env", raising=False)
    monkeypatch.setattr(mod, "ENV_TEMPLATE", tmp_path / ".env.example", raising=False)
    monkeypatch.setattr(mod, "clear", lambda: None)
    for var in KEY_VARS:
        monkeypatch.delenv(var, raising=False)
    return mod


def _drive(mod, monkeypatch, choices, secret=""):
    """Feed menu answers to safe_input and one hidden answer to getpass."""
    answers = iter(choices)
    monkeypatch.setattr(mod, "safe_input",
                        lambda prompt="", default="": next(answers, default))

    def fake_getpass(prompt=""):
        if isinstance(secret, BaseException):
            raise secret
        return secret

    monkeypatch.setattr(mod.getpass, "getpass", fake_getpass)


def test_env_paths_point_at_project_root(monkeypatch):
    mod = _load(monkeypatch)
    assert mod.ENV_FILE == ROOT / ".env"
    assert mod.ENV_TEMPLATE == ROOT / ".env.example"


def test_setup_item_1_opens_the_api_keys_screen(launcher, monkeypatch, capsys):
    _drive(launcher, monkeypatch, ["1", "0", "0"])
    launcher.setup_menu()
    out = capsys.readouterr().out
    assert "DASHSCOPE_API_KEY" in out
    assert "coming soon" not in out.lower()


def test_screen_lists_the_five_keys_masked(launcher, monkeypatch, capsys, tmp_path):
    (tmp_path / ".env").write_bytes(b"DEEPSEEK_API_KEY=sk-abcdef1234\n")
    _drive(launcher, monkeypatch, ["0"])
    launcher.api_keys_menu()
    out = capsys.readouterr().out
    for var in KEY_VARS:
        assert var in out
    assert "****1234" in out
    assert "(not set)" in out
    assert "sk-abcdef1234" not in out
    assert "OLLAMA" not in out.upper().replace("OLLAMA)", "")  # no Ollama key row


def test_saving_changes_only_that_line_and_shows_the_mask(launcher, monkeypatch, capsys, tmp_path):
    env = tmp_path / ".env"
    env.write_bytes(b"A=1\r\nDEEPSEEK_API_KEY=old\r\n")
    _drive(launcher, monkeypatch, ["3", "", "0"], secret="sk-new99991234")
    launcher.api_keys_menu()
    out = capsys.readouterr().out
    assert env.read_bytes() == b"A=1\r\nDEEPSEEK_API_KEY=sk-new99991234\r\n"
    assert "****1234" in out
    assert "sk-new99991234" not in out
    assert "environment variable" not in out.lower()


def test_empty_answer_keeps_the_old_key(launcher, monkeypatch, capsys, tmp_path):
    env = tmp_path / ".env"
    env.write_bytes(b"DEEPSEEK_API_KEY=old\n")
    _drive(launcher, monkeypatch, ["3", "", "0"], secret="")
    launcher.api_keys_menu()
    assert env.read_bytes() == b"DEEPSEEK_API_KEY=old\n"
    assert "no change" in capsys.readouterr().out.lower()


def test_missing_env_is_created_from_the_template(launcher, monkeypatch, tmp_path):
    (tmp_path / ".env.example").write_bytes(b"# t\nGROQ_API_KEY=\n")
    _drive(launcher, monkeypatch, ["2", "", "0"], secret="gsk_abcdefgh")
    launcher.api_keys_menu()
    assert (tmp_path / ".env").read_bytes() == b"# t\nGROQ_API_KEY=gsk_abcdefgh\n"
    assert (tmp_path / ".env.example").read_bytes() == b"# t\nGROQ_API_KEY=\n"


def test_bad_value_is_rejected_and_not_echoed(launcher, monkeypatch, capsys, tmp_path):
    env = tmp_path / ".env"
    env.write_bytes(b"DEEPSEEK_API_KEY=old\n")
    _drive(launcher, monkeypatch, ["3", "", "0"], secret="has space99")
    launcher.api_keys_menu()
    out = capsys.readouterr().out
    assert env.read_bytes() == b"DEEPSEEK_API_KEY=old\n"
    assert "space" in out.lower()
    assert "has space99" not in out


def test_ctrl_c_at_the_key_prompt_changes_nothing(launcher, monkeypatch, tmp_path):
    env = tmp_path / ".env"
    env.write_bytes(b"DEEPSEEK_API_KEY=old\n")
    _drive(launcher, monkeypatch, ["3", "", "0"], secret=KeyboardInterrupt())
    launcher.api_keys_menu()
    assert env.read_bytes() == b"DEEPSEEK_API_KEY=old\n"


def test_warns_when_a_windows_variable_would_override(launcher, monkeypatch, capsys):
    monkeypatch.setenv("OPENAI_API_KEY", "set-elsewhere")
    _drive(launcher, monkeypatch, ["4", "", "0"], secret="sk-openai1234")
    launcher.api_keys_menu()
    out = capsys.readouterr().out
    assert "environment variable" in out.lower()
    assert "set-elsewhere" not in out


def test_invalid_choice_says_so(launcher, monkeypatch, capsys):
    _drive(launcher, monkeypatch, ["9", "", "0"])
    launcher.api_keys_menu()
    assert "invalid choice" in capsys.readouterr().out.lower()
