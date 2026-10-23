"""
Where does this job's data go? (v2.5 local-first)

Pinned properties:
- Local AI (Ollama) never prompts and never lists a cloud company.
- Search modes name the search services that receive the query, even on
  local AI, so "LOCAL" is never claimed for data that leaves the machine.
- A cloud job lists every provider it may reach, in the order
  call_ai_with_fallback actually tries them. SR lists only the chosen
  provider (it never uses the fallback chain).
- A cloud job needs consent: --confirm-cloud, or "y" typed at a keyboard.
  Enter, "n", anything else, or no keyboard at all means the job does
  not run. It never hangs and never proceeds silently.
"""
import io
from unittest.mock import patch, MagicMock

import pytest

from SOURCE_CODE import main

CHAIN = "deepseek,qwen,groq"


# ---------------------------------------------------------------------------
# One ordering rule, shared by the fallback code and the warning
# ---------------------------------------------------------------------------
class TestProviderAttemptOrder:

    def test_local_provider_never_falls_back(self):
        from providers import provider_attempt_order
        assert provider_attempt_order("ollama", ["deepseek", "qwen"]) == ["ollama"]

    def test_cloud_provider_lists_chosen_then_backups_without_duplicates(self):
        from providers import provider_attempt_order
        assert provider_attempt_order("openai", ["deepseek", "openai", "qwen"]) == [
            "openai", "deepseek", "qwen"]

    def test_empty_chain_means_chosen_provider_only(self):
        from providers import provider_attempt_order
        assert provider_attempt_order("openai", []) == ["openai"]

    def test_order_matches_what_call_ai_with_fallback_really_tries(self):
        import providers
        tried = []

        def fake_call_ai(prompt, provider=None, model=None):
            tried.append(provider)
            raise RuntimeError("simulated transient failure")

        chain = ["deepseek", "qwen", "groq"]
        with patch.object(providers, "call_ai", side_effect=fake_call_ai), \
             patch.object(providers, "_is_transient_error", return_value=True):
            with pytest.raises(RuntimeError):
                providers.call_ai_with_fallback(
                    "p", provider="openai", fallback_chain=chain)
        assert tried == providers.provider_attempt_order("openai", chain)


# ---------------------------------------------------------------------------
# Which providers a job may reach
# ---------------------------------------------------------------------------
class TestDataDestinations:

    def test_cloud_job_lists_chosen_then_env_backups(self, monkeypatch):
        monkeypatch.setenv("FALLBACK_PROVIDERS", CHAIN)
        assert main.data_destinations("coding", "openai") == [
            "openai", "deepseek", "qwen", "groq"]

    def test_sr_lists_only_the_chosen_provider(self, monkeypatch):
        monkeypatch.setenv("FALLBACK_PROVIDERS", CHAIN)
        assert main.data_destinations("sr", "openai") == ["openai"]

    def test_local_job_lists_only_ollama(self, monkeypatch):
        monkeypatch.setenv("FALLBACK_PROVIDERS", CHAIN)
        assert main.data_destinations("writing", "ollama") == ["ollama"]

    def test_matches_the_chain_main_call_ai_really_uses(self, monkeypatch):
        import providers
        monkeypatch.setenv("FALLBACK_PROVIDERS", CHAIN)
        with patch.object(main, "call_ai_with_fallback", return_value="ok") as m:
            main.call_ai("p", provider="openai")
        used_chain = m.call_args.kwargs["fallback_chain"]
        assert providers.provider_attempt_order("openai", used_chain) == \
            main.data_destinations("coding", "openai")


# ---------------------------------------------------------------------------
# The banner and the consent gate
# ---------------------------------------------------------------------------
def _ask(mode, provider, *, confirm_cloud=False, tty=False, answer=""):
    input_fn = MagicMock(return_value=answer)
    ok = main.confirm_data_destinations(
        mode, provider, None,
        confirm_cloud=confirm_cloud, stdin_is_tty=tty, input_fn=input_fn)
    return ok, input_fn


class TestConfirmDataDestinations:

    @pytest.fixture(autouse=True)
    def _chain(self, monkeypatch):
        monkeypatch.setenv("FALLBACK_PROVIDERS", CHAIN)

    def test_local_job_runs_without_prompt_and_names_no_cloud(self, capsys):
        ok, asked = _ask("coding", "ollama")
        out = capsys.readouterr().out.lower()
        assert ok is True
        asked.assert_not_called()
        assert "local" in out
        for cloud in ("deepseek", "qwen", "groq", "openai", "anthropic"):
            assert cloud not in out, f"local banner mentions {cloud}"

    def test_local_search_names_every_search_service(self, capsys):
        ok, _ = _ask("search", "ollama")
        out = capsys.readouterr().out.lower()
        assert ok is True
        for service in ("pubmed", "europe pmc", "duckduckgo"):
            assert service in out

    def test_local_rct_search_names_its_search_services_only(self, capsys):
        ok, _ = _ask("rct_search", "ollama")
        out = capsys.readouterr().out.lower()
        assert ok is True
        assert "pubmed" in out and "europe pmc" in out
        assert "duckduckgo" not in out

    def test_cloud_job_with_confirm_flag_runs_and_lists_every_provider(self, capsys):
        ok, asked = _ask("coding", "openai", confirm_cloud=True)
        out = capsys.readouterr().out.lower()
        assert ok is True
        asked.assert_not_called()
        for name in ("openai", "deepseek", "qwen", "groq"):
            assert name in out
        assert "patient" in out

    @pytest.mark.parametrize("answer", ["y", "Y", "yes"])
    def test_cloud_job_runs_when_user_types_yes(self, answer):
        ok, asked = _ask("coding", "openai", tty=True, answer=answer)
        assert ok is True
        asked.assert_called_once()

    @pytest.mark.parametrize("answer", ["", "n", "no", "maybe"])
    def test_cloud_job_stops_unless_user_types_yes(self, answer):
        ok, _ = _ask("coding", "openai", tty=True, answer=answer)
        assert ok is False

    def test_cloud_job_with_no_keyboard_and_no_flag_is_refused(self, capsys):
        ok, asked = _ask("coding", "openai", tty=False)
        out = capsys.readouterr().out
        assert ok is False
        asked.assert_not_called()
        assert "--confirm-cloud" in out

    def test_sr_cloud_warning_lists_only_the_chosen_provider(self, capsys):
        ok, _ = _ask("sr", "openai", confirm_cloud=True)
        out = capsys.readouterr().out.lower()
        assert ok is True
        assert "openai" in out
        assert "deepseek" not in out and "groq" not in out


# ---------------------------------------------------------------------------
# The gate is wired into run_cli
# ---------------------------------------------------------------------------
class TestRunCliGate:

    def test_parse_args_confirm_cloud_defaults_off(self):
        assert main.parse_args([]).confirm_cloud is False

    @patch('SOURCE_CODE.main.validate_api_keys')
    @patch('SOURCE_CODE.main.handle_coding_mode')
    def test_cloud_job_without_consent_does_not_run(self, mock_handler, _keys, monkeypatch):
        monkeypatch.setattr(main.sys, "stdin", io.StringIO(""))
        with pytest.raises(SystemExit):
            main.run_cli(main.parse_args(["--mode", "coding", "--provider", "openai"]))
        mock_handler.assert_not_called()

    @patch('SOURCE_CODE.main.validate_api_keys')
    @patch('SOURCE_CODE.main.handle_coding_mode')
    def test_cloud_job_with_confirm_cloud_runs(self, mock_handler, _keys, monkeypatch):
        monkeypatch.setattr(main.sys, "stdin", io.StringIO(""))
        main.run_cli(main.parse_args(
            ["--mode", "coding", "--provider", "openai", "--confirm-cloud"]))
        mock_handler.assert_called_once()

    @patch('SOURCE_CODE.main.validate_api_keys')
    @patch('SOURCE_CODE.main.handle_coding_mode')
    def test_local_job_runs_without_any_prompt(self, mock_handler, _keys, monkeypatch):
        monkeypatch.setattr(main.sys, "stdin", io.StringIO(""))
        main.run_cli(main.parse_args(["--mode", "coding", "--provider", "ollama"]))
        mock_handler.assert_called_once()
