"""Comprehensive tests for the Streamlit UI (app.py)."""

import sys
import os
import json
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock, mock_open

import pytest

# Add SOURCE_CODE to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_CODE_DIR = PROJECT_ROOT / "SOURCE_CODE"
sys.path.insert(0, str(SOURCE_CODE_DIR))

# Mock streamlit before importing app
import streamlit as st

# Import the app module - use ui.app not app
from ui import app


class TestAppConfiguration:
    """Test app configuration and constants."""

    def test_modes_defined(self):
        """Test that all modes are defined in MODES."""
        expected_modes = ["coding", "writing", "rct_search", "appraisal", "search", "sr"]
        for mode in expected_modes:
            assert mode in app.MODES, f"Mode '{mode}' should be in MODES"

    def test_mode_has_required_keys(self):
        """Test that each mode has required configuration keys."""
        required_keys = ["label", "icon", "accent", "bg", "description", "extensions", "instructions"]
        for mode_key, mode_config in app.MODES.items():
            for key in required_keys:
                assert key in mode_config, f"Mode '{mode_key}' missing '{key}'"

    def test_providers_defined(self):
        """Test that all providers are defined."""
        expected_providers = ["ollama", "openai", "anthropic", "deepseek", "groq", "qwen"]
        assert len(app.PROVIDERS) >= 6
        for provider in expected_providers:
            assert provider in app.PROVIDERS, f"Provider '{provider}' should be in PROVIDERS"

    def test_paths_defined(self):
        """Test that all paths are defined."""
        assert app.PROJECT_ROOT.exists(), "PROJECT_ROOT should exist"
        assert app.SOURCE_CODE_DIR.exists(), "SOURCE_CODE_DIR should exist"
        assert app.INPUT_DIR is not None, "INPUT_DIR should be defined"
        assert app.OUTPUT_DIR is not None, "OUTPUT_DIR should be defined"
        assert app.REPORTS_DIR is not None, "REPORTS_DIR should be defined"


class TestAppHelpers:
    """Test helper functions in app.py."""

    def test_icon_b64_with_valid_image(self, tmp_path):
        """Test _icon_b64 with a valid image file."""
        img_path = tmp_path / "test.png"
        try:
            from PIL import Image
            img = Image.new("RGB", (1, 1), color="red")
            img.save(img_path, format="PNG")
            result = app._icon_b64(img_path)
            assert result is not None
            assert result.startswith("data:image/png;base64,")
        except ImportError:
            pytest.skip("PIL not installed")

    def test_icon_b64_with_missing_file(self):
        """Test _icon_b64 with a missing file."""
        result = app._icon_b64(Path("/nonexistent/file.png"))
        assert result is None

    def test_logo_b64(self):
        """Test _logo_b64 returns a valid data URI or None."""
        result = app._logo_b64()
        if result:
            assert result.startswith("data:image/")

    def test_count_files_empty(self, tmp_path):
        """Test _count_files with empty directory."""
        result = app._count_files(tmp_path, [".txt"])
        assert result == 0

    def test_count_files_with_files(self, tmp_path):
        """Test _count_files with files."""
        (tmp_path / "test1.txt").touch()
        (tmp_path / "test2.txt").touch()
        (tmp_path / "test3.pdf").touch()
        result = app._count_files(tmp_path, [".txt"])
        assert result == 2

    def test_latest_outputs_empty(self, tmp_path):
        """Test _latest_outputs with empty directory."""
        result = app._latest_outputs(tmp_path)
        assert result == []

    def test_latest_outputs_with_files(self, tmp_path):
        """Test _latest_outputs returns latest files."""
        (tmp_path / "file1.md").touch()
        (tmp_path / "file2.docx").touch()
        (tmp_path / "file3.md").touch()
        result = app._latest_outputs(tmp_path)
        assert len(result) <= 4

    def test_get_env_with_api_keys(self):
        """Test _get_env_with_api_keys merges session keys."""
        mock_session = {"api_keys": {"openai": "test-key"}}
        with patch("streamlit.session_state", mock_session):
            env = app._get_env_with_api_keys()
            assert env.get("OPENAI_API_KEY") == "test-key"

    def test_exit_to_launcher(self):
        """Test _exit_to_launcher clears session state."""
        with patch("streamlit.session_state", {}) as mock_state:
            with patch("streamlit.stop") as mock_stop:
                app._exit_to_launcher()
                assert mock_state["page"] == "home"


class TestAppApiKeys:
    """Test API key management in the UI."""

    def test_api_key_sidebar_renders(self):
        """Test that _api_key_sidebar renders inputs."""
        mock_session = MagicMock()
        mock_session.api_keys = {}
        
        with patch("streamlit.session_state", mock_session):
            with patch("streamlit.sidebar") as mock_sidebar:
                with patch("streamlit.text_input", return_value=""):
                    mock_sidebar.__enter__ = Mock(return_value=mock_sidebar)
                    mock_sidebar.__exit__ = Mock(return_value=False)
                    app._api_key_sidebar()

    def test_api_key_storage(self):
        """Test that API keys are stored in session state."""
        mock_session = MagicMock()
        mock_session.api_keys = {}
        
        with patch("streamlit.session_state", mock_session):
            with patch("streamlit.sidebar") as mock_sidebar:
                mock_sidebar.__enter__ = Mock(return_value=mock_sidebar)
                mock_sidebar.__exit__ = Mock(return_value=False)
                with patch("streamlit.text_input", return_value="test-key"):
                    app._api_key_sidebar()

    def test_env_api_keys_detection(self):
        """Test that environment API keys are detected."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "env-key"}):
            mock_session = MagicMock()
            mock_session.api_keys = {}
            
            with patch("streamlit.session_state", mock_session):
                with patch("streamlit.sidebar") as mock_sidebar:
                    mock_sidebar.__enter__ = Mock(return_value=mock_sidebar)
                    mock_sidebar.__exit__ = Mock(return_value=False)
                    with patch("streamlit.success") as mock_success:
                        app._api_key_sidebar()


class TestAppTerminal:
    """Test terminal launching functions."""

    def test_launch_terminal_cloud_detection(self):
        """Test that cloud environment is detected."""
        with patch.dict(os.environ, {"RENDER": "true"}):
            with patch("ui.app._run_cli_cloud", return_value="ok") as mock_cloud:
                result = app._launch_terminal("coding", "ollama", "", "")
                mock_cloud.assert_called_once()
                assert result == "ok"

    def test_launch_terminal_local(self):
        """Test local terminal launch."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("ui.app._launch_terminal_local", return_value="ok") as mock_local:
                result = app._launch_terminal("coding", "ollama", "", "")
                mock_local.assert_called_once()
                assert result == "ok"

    def test_run_cli_cloud_with_submode(self):
        """Test _run_cli_cloud with sub-mode parameter."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="Success", stderr="")
            with patch("streamlit.session_state", {"api_keys": {}}):
                with patch("streamlit.code") as mock_code:
                    with patch("streamlit.success") as mock_success:
                        result = app._run_cli_cloud(
                            mode="search",
                            provider="ollama",
                            model="",
                            submode="1",
                            prompt=""
                        )
                        call_args = mock_run.call_args[0][0]
                        assert "--sub" in call_args
                        assert "1" in call_args

    def test_run_cli_cloud_with_api_keys(self):
        """Test _run_cli_cloud uses API keys from session."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="Success", stderr="")
            with patch("streamlit.session_state", {"api_keys": {"openai": "test-key"}}):
                with patch("streamlit.success") as mock_success:
                    result = app._run_cli_cloud(
                        mode="coding",
                        provider="openai",
                        model="gpt-4",
                        submode="",
                        prompt=""
                    )
                    call_env = mock_run.call_args[1].get("env", {})
                    assert call_env.get("OPENAI_API_KEY") == "test-key"

    def test_run_cli_cloud_missing_api_key(self):
        """Test _run_cli_cloud shows warning for missing API key."""
        with patch("streamlit.session_state", {"api_keys": {}}):
            with patch("streamlit.warning") as mock_warning:
                result = app._run_cli_cloud(
                    mode="coding",
                    provider="openai",
                    model="",
                    submode="",
                    prompt=""
                )
                assert result == "error: missing API key"
                mock_warning.assert_called()


class TestAppUIComponents:
    """Test UI component rendering."""

    def test_inject_css(self):
        """Test CSS injection."""
        with patch("streamlit.markdown") as mock_markdown:
            app._inject_css()
            mock_markdown.assert_called_once()

    def test_render_header(self):
        """Test header rendering."""
        with patch("ui.app._logo_b64", return_value="data:image/png;base64,test"):
            with patch("streamlit.markdown") as mock_markdown:
                app._render_header("Test subtitle")
                mock_markdown.assert_called()

    def test_show_folder_contents_empty(self, tmp_path):
        """Test _show_folder_contents with empty folder."""
        test_path = app.PROJECT_ROOT / "test_temp"
        test_path.mkdir(exist_ok=True)
        try:
            with patch("streamlit.expander") as mock_expander:
                mock_expander.return_value.__enter__ = Mock(return_value=mock_expander)
                mock_expander.return_value.__exit__ = Mock(return_value=False)
                with patch("streamlit.info") as mock_info:
                    app._show_folder_contents(test_path, [".txt"], "Test Label")
        finally:
            import shutil
            shutil.rmtree(test_path, ignore_errors=True)

    def test_show_folder_contents_with_files(self, tmp_path):
        """Test _show_folder_contents with files."""
        test_path = app.PROJECT_ROOT / "test_temp"
        test_path.mkdir(exist_ok=True)
        (test_path / "test.txt").touch()
        try:
            with patch("streamlit.expander") as mock_expander:
                mock_expander.return_value.__enter__ = Mock(return_value=mock_expander)
                mock_expander.return_value.__exit__ = Mock(return_value=False)
                with patch("streamlit.columns") as mock_columns:
                    mock_col1 = MagicMock()
                    mock_col2 = MagicMock()
                    mock_col1.__enter__ = Mock(return_value=mock_col1)
                    mock_col1.__exit__ = Mock(return_value=False)
                    mock_col2.__enter__ = Mock(return_value=mock_col2)
                    mock_col2.__exit__ = Mock(return_value=False)
                    mock_columns.return_value = [mock_col1, mock_col2]
                    app._show_folder_contents(test_path, [".txt"], "Test Label")
        finally:
            import shutil
            shutil.rmtree(test_path, ignore_errors=True)


class TestAppPages:
    """Test page rendering functions."""

    def test_home_page_renders(self):
        """Test that home page renders."""
        mock_session = MagicMock()
        mock_session.api_keys = {}
        
        with patch("streamlit.session_state", mock_session):
            with patch("ui.app._api_key_sidebar"):
                with patch("ui.app._render_header"):
                    with patch("streamlit.columns") as mock_columns:
                        mock_col1 = MagicMock()
                        mock_col2 = MagicMock()
                        mock_col1.__enter__ = Mock(return_value=mock_col1)
                        mock_col1.__exit__ = Mock(return_value=False)
                        mock_col2.__enter__ = Mock(return_value=mock_col2)
                        mock_col2.__exit__ = Mock(return_value=False)
                        mock_columns.return_value = [mock_col1, mock_col2]
                        with patch("streamlit.button", return_value=False):
                            with patch("streamlit.rerun"):
                                app._home_page()

    def test_mode_page_renders(self):
        """Test that mode page renders."""
        mock_session = MagicMock()
        mock_session.api_keys = {}
        
        with patch("streamlit.session_state", mock_session):
            with patch("ui.app._api_key_sidebar"):
                with patch("ui.app._render_header"):
                    with patch("streamlit.columns") as mock_columns:
                        # Handle both list and integer arguments
                        def columns_side_effect(*args, **kwargs):
                            # Determine number of columns needed
                            if args and isinstance(args[0], (list, tuple)):
                                num_cols = len(args[0])
                            elif args and isinstance(args[0], int):
                                num_cols = args[0]
                            else:
                                # Default to 2 columns
                                num_cols = 2
                            
                            # Create the requested number of mock columns
                            result = []
                            for _ in range(num_cols):
                                mock_col = MagicMock()
                                mock_col.__enter__ = Mock(return_value=mock_col)
                                mock_col.__exit__ = Mock(return_value=False)
                                result.append(mock_col)
                            return result
                        
                        mock_columns.side_effect = columns_side_effect
                        with patch("streamlit.button", return_value=False):
                            with patch("streamlit.selectbox", return_value="Builder (pipeline)"):
                                with patch("streamlit.text_input", return_value=""):
                                    with patch("streamlit.file_uploader", return_value=[]):
                                        with patch("streamlit.expander"):
                                            with patch("streamlit.divider"):
                                                with patch("streamlit.rerun"):
                                                    app._mode_page("coding")

    def test_main_router_home(self):
        """Test main router goes to home page."""
        with patch("streamlit.set_page_config"):
            with patch("ui.app._inject_css"):
                with patch("streamlit.session_state", {"page": "home"}):
                    with patch("ui.app._home_page") as mock_home:
                        app.main()
                        mock_home.assert_called_once()

    def test_main_router_mode(self):
        """Test main router goes to mode page."""
        with patch("streamlit.set_page_config"):
            with patch("ui.app._inject_css"):
                with patch("streamlit.session_state", {"page": "coding"}):
                    with patch("ui.app._mode_page") as mock_mode:
                        app.main()
                        mock_mode.assert_called_once_with("coding")


class TestAppSRMode:
    """Test SR mode specific features."""

    def test_sr_mode_pico_import(self):
        """Test PICO import in SR mode."""
        mock_session = MagicMock()
        mock_session.api_keys = {}
        
        with patch("streamlit.session_state", mock_session):
            with patch("ui.app._api_key_sidebar"):
                with patch("ui.app._render_header"):
                    with patch("streamlit.columns") as mock_columns:
                        # Handle both list and integer arguments
                        def columns_side_effect(*args, **kwargs):
                            # Determine number of columns needed
                            if args and isinstance(args[0], (list, tuple)):
                                num_cols = len(args[0])
                            elif args and isinstance(args[0], int):
                                num_cols = args[0]
                            else:
                                # Default to 2 columns
                                num_cols = 2
                            
                            # Create the requested number of mock columns
                            result = []
                            for _ in range(num_cols):
                                mock_col = MagicMock()
                                mock_col.__enter__ = Mock(return_value=mock_col)
                                mock_col.__exit__ = Mock(return_value=False)
                                result.append(mock_col)
                            return result
                        
                        mock_columns.side_effect = columns_side_effect
                        with patch("streamlit.button", return_value=False):
                            with patch("streamlit.file_uploader", return_value=[]):
                                with patch("streamlit.expander"):
                                    with patch("streamlit.selectbox", return_value="pico_test.json"):
                                        with patch("pathlib.Path.exists", return_value=True):
                                            with patch("pathlib.Path.read_text", return_value='{"population": "test"}'):
                                                with patch("json.loads", return_value={"population": "test"}):
                                                    with patch("streamlit.text_input", return_value="test"):
                                                        with patch("streamlit.selectbox", return_value="SMD"):
                                                            with patch("ui.app._show_folder_contents"):
                                                                with patch("streamlit.divider"):
                                                                    app._mode_page("sr")


class TestAppEdgeCases:
    """Test edge cases and error handling."""

    def test_invalid_mode(self):
        """Test invalid mode handling."""
        with patch("streamlit.session_state", {"page": "invalid"}):
            with patch("streamlit.set_page_config"):
                with patch("ui.app._inject_css"):
                    with patch("streamlit.rerun") as mock_rerun:
                        app.main()
                        assert mock_rerun.called

    def test_no_session_state(self):
        """Test when session state is empty."""
        with patch("streamlit.session_state", {}):
            with patch("streamlit.set_page_config"):
                with patch("ui.app._inject_css"):
                    with patch("ui.app._home_page") as mock_home:
                        app.main()
                        mock_home.assert_called_once()

    def test_file_upload_with_duplicate(self, tmp_path):
        """Test file upload with duplicate files."""
        dest = tmp_path / "input" / "coding"
        dest.mkdir(parents=True)
        (dest / "test.txt").touch()
        assert dest.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
