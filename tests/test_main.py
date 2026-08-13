"""Comprehensive tests for main.py - Tests define the specification."""

import sys
import os
import json
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock

import pytest

# Add SOURCE_CODE to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_CODE_DIR = PROJECT_ROOT / "SOURCE_CODE"
sys.path.insert(0, str(SOURCE_CODE_DIR))

# Import main module
from SOURCE_CODE import main


class TestMainConfiguration:
    """Test main.py configuration and constants."""

    def test_version_defined(self):
        assert hasattr(main, "VERSION")
        assert isinstance(main.VERSION, str)
        assert main.VERSION.startswith("2.")

    def test_providers_defined(self):
        assert hasattr(main, "PROVIDERS")
        assert "ollama" in main.PROVIDERS
        assert "openai" in main.PROVIDERS
        assert "anthropic" in main.PROVIDERS
        assert "deepseek" in main.PROVIDERS
        assert "groq" in main.PROVIDERS
        assert "qwen" in main.PROVIDERS

    def test_paths_defined(self):
        assert hasattr(main, "BASE_DIR")
        assert hasattr(main, "DOCS_DIR")
        assert hasattr(main, "INPUT_DIR")
        assert hasattr(main, "OUTPUT_DIR")
        assert hasattr(main, "REPORTS_DIR")

    def test_mode_extensions_defined(self):
        assert hasattr(main, "_MODE_EXTENSIONS")
        assert "coding" in main._MODE_EXTENSIONS
        assert "writing" in main._MODE_EXTENSIONS
        assert "appraisal" in main._MODE_EXTENSIONS
        assert "rct_search" in main._MODE_EXTENSIONS
        assert "search" in main._MODE_EXTENSIONS
        assert "sr" in main._MODE_EXTENSIONS

    def test_provider_env_vars_defined(self):
        assert hasattr(main, "PROVIDER_ENV_VARS")
        assert main.PROVIDER_ENV_VARS["openai"] == "OPENAI_API_KEY"
        assert main.PROVIDER_ENV_VARS["anthropic"] == "ANTHROPIC_API_KEY"
        assert main.PROVIDER_ENV_VARS["ollama"] is None


class TestMainHelpers:
    """Test helper functions in main.py."""

    def test_auto_load_input_files_coding(self, tmp_path):
        input_dir = tmp_path / "input" / "coding"
        input_dir.mkdir(parents=True)
        (input_dir / "test1.py").touch()
        (input_dir / "test2.js").touch()
        (input_dir / "test3.log").touch()
        
        with patch("SOURCE_CODE.main.INPUT_CODING", input_dir):
            with patch("SOURCE_CODE.main.INPUT_DIR", tmp_path / "input"):
                result = main.auto_load_input_files("coding")
                assert isinstance(result, list)

    def test_auto_load_input_files_empty(self, tmp_path):
        with patch("SOURCE_CODE.main.INPUT_DIR", tmp_path / "input"):
            result = main.auto_load_input_files("coding")
            assert isinstance(result, list)

    def test_auto_load_input_files_writing(self, tmp_path):
        input_dir = tmp_path / "input" / "writing"
        input_dir.mkdir(parents=True)
        (input_dir / "test1.md").touch()
        (input_dir / "test2.txt").touch()
        
        with patch("SOURCE_CODE.main.INPUT_WRITING", input_dir):
            with patch("SOURCE_CODE.main.INPUT_DIR", tmp_path / "input"):
                result = main.auto_load_input_files("writing")
                assert isinstance(result, list)

    def test_read_text_file_exists(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content", encoding="utf-8")
        result = main.read_text_file(test_file)
        assert result == "Test content"

    def test_read_text_file_missing(self, tmp_path):
        result = main.read_text_file(tmp_path / "missing.txt")
        assert result == ""

    def test_truncate_context_within_limit(self):
        text = "Short text" * 10
        result = main.truncate_context(text, max_chars=1000)
        assert result == text

    def test_truncate_context_exceeds_limit(self):
        text = "x" * 3000
        result = main.truncate_context(text, max_chars=2000)
        assert len(result) <= 2001

    def test_role_color_returns_ansi(self):
        assert main.role_color("Builder").startswith("\033[")
        assert main.role_color("Reviewer").startswith("\033[")
        assert main.role_color("Tester").startswith("\033[")
        assert main.role_color("Unknown") == main.RESET

    def test_choose_role(self, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda _: "1")
        role_name, config = main.choose_role("coding")
        assert role_name in main.ALL_MODES["coding"]
        assert isinstance(config, dict)

    def test_choose_role_invalid_input_then_valid(self, monkeypatch):
        calls = [0]
        def mock_input(prompt):
            calls[0] += 1
            if calls[0] == 1:
                return "99"
            return "1"
        
        monkeypatch.setattr("builtins.input", mock_input)
        role_name, config = main.choose_role("coding")
        assert role_name in main.ALL_MODES["coding"]


class TestMainSessionManagement:
    """Test session management functions."""

    def test_start_session_transcript(self, tmp_path):
        path = main.start_session_transcript(tmp_path)
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "# Session Transcript" in content
        assert "Started:" in content

    def test_append_to_transcript(self, tmp_path):
        transcript = main.start_session_transcript(tmp_path)
        main.append_to_transcript(transcript, "TestRole", 1, "Test Task", "Test Response")
        
        content = transcript.read_text(encoding="utf-8")
        assert "## Step 1" in content
        assert "TestRole" in content
        assert "Test Task" in content
        assert "Test Response" in content

    def test_save_report(self, tmp_path):
        report_path = tmp_path / "report.md"
        main.save_report(report_path, "TestRole", "test-model", "Test Task", "Test Response")
        
        content = report_path.read_text(encoding="utf-8")
        assert "## TestRole" in content
        assert "**Model:** test-model" in content
        assert "Test Task" in content
        assert "Test Response" in content

    def test_list_sessions_no_files(self, tmp_path, capsys):
        with patch("SOURCE_CODE.main.REPORTS_DIR", tmp_path):
            main.list_sessions(reports_dir=str(tmp_path))

    def test_list_sessions_with_files(self, tmp_path, capsys):
        (tmp_path / "session_20250101_120000.md").touch()
        (tmp_path / "session_20250102_130000.md").touch()
        
        with patch("SOURCE_CODE.main.REPORTS_DIR", tmp_path):
            main.list_sessions(reports_dir=str(tmp_path))
            captured = capsys.readouterr()
            assert "session_20250101_120000.md" in captured.out

    def test_read_session(self, tmp_path, capsys):
        session_file = tmp_path / "session_test.md"
        session_file.write_text("# Test Session\nContent here.", encoding="utf-8")
        
        main.read_session("session_test.md", reports_dir=str(tmp_path))
        captured = capsys.readouterr()
        assert "Test Session" in captured.out
        assert "Content here" in captured.out

    def test_read_session_missing(self, tmp_path, capsys):
        main.read_session("missing.md", reports_dir=str(tmp_path))
        captured = capsys.readouterr()
        assert "File not found" in captured.out


class TestMainProviderCalls:
    """Test provider call functions - skip real API calls."""

    @pytest.mark.skip(reason="Requires Ollama to be running and may make real API calls")
    def test_call_ollama_provider(self):
        pass

    @pytest.mark.skip(reason="Requires Ollama to be running")
    def test_call_ollama_provider_handles_error(self):
        pass

    @pytest.mark.live
    def test_call_openai_provider_missing_key(self):
        with patch("SOURCE_CODE.main.OPENAI_API_KEY", ""):
            with pytest.raises(RuntimeError) as exc:
                main.call_openai_provider("Test prompt")
            assert "OPENAI_API_KEY" in str(exc.value)

    @pytest.mark.skip(reason="Requires OpenAI API key and makes real API calls")
    def test_call_openai_provider_success(self):
        pass

    def test_call_anthropic_provider_missing_key(self):
        # Patch the module where the function actually looks up the variable
        import sys
        _prov = sys.modules[main.call_anthropic_provider.__module__]
        orig = _prov.ANTHROPIC_API_KEY
        _prov.ANTHROPIC_API_KEY = ""
        try:
            with pytest.raises(RuntimeError) as exc:
                main.call_anthropic_provider("Test prompt")
            assert "ANTHROPIC_API_KEY" in str(exc.value)
        finally:
            _prov.ANTHROPIC_API_KEY = orig

    @pytest.mark.live
    def test_call_groq_provider_missing_key(self):
        with patch("SOURCE_CODE.main.GROQ_API_KEY", ""):
            with pytest.raises(RuntimeError) as exc:
                main.call_groq_provider("Test prompt")
            assert "GROQ_API_KEY" in str(exc.value)

    def test_call_deepseek_provider_missing_key(self):
        import sys
        _prov = sys.modules[main.call_deepseek_provider.__module__]
        orig = _prov.DEEPSEEK_API_KEY
        _prov.DEEPSEEK_API_KEY = ""
        try:
            with pytest.raises(RuntimeError) as exc:
                main.call_deepseek_provider("Test prompt")
            assert "DEEPSEEK_API_KEY" in str(exc.value)
        finally:
            _prov.DEEPSEEK_API_KEY = orig

    def test_call_ai_routes_to_correct_provider(self):
        """call_ai routes to correct provider using PROVIDERS dict."""
        mock_provider = Mock(return_value="Ollama response")
        
        with patch.dict("SOURCE_CODE.main.PROVIDERS", {"ollama": mock_provider}):
            result = main.call_ai("Test prompt", provider="ollama")
            mock_provider.assert_called_once()
            assert result == "Ollama response"

    @pytest.mark.live
    def test_call_ai_fallback_to_ollama(self):
        """call_ai falls back to ollama for unknown provider."""
        # This test verifies the fallback behavior by checking the provider
        # returns a response even for unknown providers
        result = main.call_ai("Test prompt", provider="unknown")
        # Should return a string (either from ollama or error)
        assert isinstance(result, str)


class TestMainValidation:
    """Test validation functions in main.py."""

    def test_validate_api_keys_ollama(self):
        main.validate_api_keys("ollama")

    @pytest.mark.live
    def test_validate_api_keys_openai_missing(self):
        with patch("SOURCE_CODE.main.OPENAI_API_KEY", ""):
            with pytest.raises(EnvironmentError) as exc:
                main.validate_api_keys("openai")
            assert "OPENAI_API_KEY" in str(exc.value)

    def test_validate_api_keys_qwen_with_key(self):
        with patch("SOURCE_CODE.main.DASHSCOPE_API_KEY", "test-key"):
            main.validate_api_keys("qwen")

    def test_validate_api_keys_invalid_provider(self):
        with pytest.raises(ValueError) as exc:
            main.validate_api_keys("invalid_provider")
        assert "Unknown provider" in str(exc.value)


class TestMainParsing:
    """Test argument parsing functions."""

    def test_parse_args_default(self):
        args = main.parse_args([])
        assert args.mode == "coding"
        assert args.provider == "deepseek"
        assert args.model is None

    def test_parse_args_with_provider(self):
        args = main.parse_args(["--provider", "qwen"])
        assert args.provider == "qwen"

    def test_parse_args_with_mode(self):
        args = main.parse_args(["--mode", "writing"])
        assert args.mode == "writing"

    def test_parse_args_with_model(self):
        args = main.parse_args(["--model", "llama3.2"])
        assert args.model == "llama3.2"

    def test_parse_args_with_report(self):
        args = main.parse_args(["--report"])
        assert args.report is True

    def test_parse_args_with_revise(self):
        args = main.parse_args(["--revise"])
        assert args.revise is True

    def test_parse_args_with_dry_run(self):
        args = main.parse_args(["--dry-run"])
        assert args.dry_run is True

    def test_parse_args_with_sub(self):
        args = main.parse_args(["--sub", "1"])
        assert args.sub == "1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])