"""v2.5 commit 3: the Streamlit UI applies the same cloud gate as the CLI.

Pinned properties:
- The UI lists exactly the destinations main.data_destinations() reports
  (one source of truth, no copied list that can drift).
- --confirm-cloud reaches the CLI only after the user ticks consent, and
  never for Ollama.
- The Render path gives the CLI no keyboard (stdin=DEVNULL), so a cloud job
  can never hang waiting for a [y/N] answer nobody can type.
- --model and --sub reach the CLI on both launch paths (previously dropped).
"""
import subprocess
from unittest.mock import MagicMock, patch

import pytest

import ui.app as app

CHAIN = "deepseek,qwen,groq"


@pytest.fixture(autouse=True)
def _known_chain(monkeypatch):
    monkeypatch.setenv("FALLBACK_PROVIDERS", CHAIN)


def _flag_value(cmd, flag):
    """Value following `flag` in a command list, or None if absent."""
    return cmd[cmd.index(flag) + 1] if flag in cmd else None


class TestBuildCliCmd:
    def test_basic_command(self):
        cmd = app._build_cli_cmd("writing", "ollama", "", "")
        assert cmd[2:] == ["--mode", "writing", "--provider", "ollama"]

    def test_model_is_passed(self):
        cmd = app._build_cli_cmd("writing", "ollama", "qwen3:8b", "")
        assert _flag_value(cmd, "--model") == "qwen3:8b"

    def test_blank_model_is_not_passed(self):
        cmd = app._build_cli_cmd("writing", "ollama", "   ", "")
        assert "--model" not in cmd

    def test_search_submode_is_passed(self):
        cmd = app._build_cli_cmd("search", "ollama", "", "2")
        assert _flag_value(cmd, "--sub") == "2"

    @pytest.mark.parametrize("role", ["Builder", "Reviewer", "Tester"])
    def test_coding_role_is_passed(self, role):
        cmd = app._build_cli_cmd("coding", "ollama", "", f"{role} mode")
        assert _flag_value(cmd, "--role") == role

    def test_confirm_cloud_added_for_cloud_when_ticked(self):
        cmd = app._build_cli_cmd("writing", "deepseek", "", "", confirm_cloud=True)
        assert "--confirm-cloud" in cmd

    def test_confirm_cloud_absent_when_not_ticked(self):
        cmd = app._build_cli_cmd("writing", "deepseek", "", "", confirm_cloud=False)
        assert "--confirm-cloud" not in cmd

    def test_confirm_cloud_never_added_for_ollama(self):
        cmd = app._build_cli_cmd("writing", "ollama", "", "", confirm_cloud=True)
        assert "--confirm-cloud" not in cmd


class TestCloudDestinations:
    def test_local_job_has_no_cloud_destinations(self):
        assert app._cloud_destinations("writing", "ollama") == []

    def test_cloud_job_lists_chosen_then_backups(self):
        assert app._cloud_destinations("writing", "deepseek") == [
            "DeepSeek", "Qwen (Alibaba)", "Groq"]

    def test_sr_lists_only_the_chosen_provider(self):
        assert app._cloud_destinations("sr", "qwen") == ["Qwen (Alibaba)"]

    def test_reads_the_chain_at_call_time(self, monkeypatch):
        monkeypatch.setenv("FALLBACK_PROVIDERS", "deepseek,qwen")
        assert app._cloud_destinations("writing", "deepseek") == [
            "DeepSeek", "Qwen (Alibaba)"]

    def test_matches_main_data_destinations(self):
        from SOURCE_CODE import main as cli
        for provider in ["deepseek", "qwen", "openai", "anthropic", "groq"]:
            expected = [cli.PROVIDER_LABELS[p]
                        for p in cli.data_destinations("writing", provider)
                        if p not in cli.LOCAL_ONLY_PROVIDERS]
            assert app._cloud_destinations("writing", provider) == expected


def _run_cloud(model="", confirm_cloud=False):
    with patch.object(app, "st", MagicMock()), \
         patch.object(app, "_has_api_key", return_value=True), \
         patch.object(app, "_get_env_with_api_keys", return_value={}), \
         patch.object(app.subprocess, "run") as run:
        run.return_value = MagicMock(stdout="", stderr="", returncode=0)
        app._run_cli_cloud("writing", "deepseek", model, "", "",
                           confirm_cloud=confirm_cloud)
    return run.call_args


class TestRunCliCloud:
    def test_cli_gets_no_keyboard(self):
        assert _run_cloud().kwargs.get("stdin") is subprocess.DEVNULL

    def test_confirm_cloud_passed_when_ticked(self):
        assert "--confirm-cloud" in _run_cloud(confirm_cloud=True).args[0]

    def test_confirm_cloud_absent_when_not_ticked(self):
        assert "--confirm-cloud" not in _run_cloud(confirm_cloud=False).args[0]

    def test_model_is_passed(self):
        cmd = _run_cloud(model="deepseek-v4-flash").args[0]
        assert _flag_value(cmd, "--model") == "deepseek-v4-flash"


def _run_local(mode="writing", provider="deepseek", submode="", confirm_cloud=False):
    launchers = {name: MagicMock(return_value="ok")
                 for name in ("_launch_windows", "_launch_macos", "_launch_linux")}
    with patch.object(app, "_get_env_with_api_keys", return_value={}), \
         patch.multiple(app, **launchers):
        app._launch_terminal_local(mode, provider, "", submode,
                                   confirm_cloud=confirm_cloud)
    called = [m for m in launchers.values() if m.called]
    assert len(called) == 1
    return called[0].call_args.args[0]  # cmd_str


class TestLaunchTerminalLocal:
    def test_confirm_cloud_passed_when_ticked(self):
        assert "--confirm-cloud" in _run_local(confirm_cloud=True)

    def test_confirm_cloud_absent_when_not_ticked(self):
        assert "--confirm-cloud" not in _run_local(confirm_cloud=False)

    def test_search_submode_is_passed(self):
        assert "--sub 2" in _run_local(mode="search", provider="ollama", submode="2")


class TestLaunchTerminalForwardsConsent:
    def test_render_path_gets_consent(self):
        with patch.object(app, "_is_cloud_environment", return_value=True), \
             patch.object(app, "_run_cli_cloud", return_value="ok") as cloud:
            app._launch_terminal("writing", "deepseek", "", "", "", confirm_cloud=True)
        assert cloud.call_args.kwargs.get("confirm_cloud") is True

    def test_local_path_gets_consent(self):
        with patch.object(app, "_is_cloud_environment", return_value=False), \
             patch.object(app, "_launch_terminal_local", return_value="ok") as local:
            app._launch_terminal("writing", "deepseek", "", "", "", confirm_cloud=True)
        assert local.call_args.kwargs.get("confirm_cloud") is True
