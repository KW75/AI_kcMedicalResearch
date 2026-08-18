"""
Corrected tests for main.py: argument parsing, interactive loop,
helpers, validation, and session management.
"""
import pytest
from pathlib import Path
from unittest.mock import patch

from SOURCE_CODE import main


class TestMainArgumentParsing:
    """Test argument parsing."""

    def test_parse_args_minimal(self):
        with patch('sys.argv', ['main.py', '--mode', 'coding']):
            args = main.parse_args()
            assert args.mode == 'coding'
            assert args.provider == 'deepseek'

    def test_parse_args_with_provider(self):
        with patch('sys.argv', ['main.py', '--mode', 'coding', '--provider', 'openai']):
            args = main.parse_args()
            assert args.mode == 'coding'
            assert args.provider == 'openai'

    def test_parse_args_no_stream(self):
        with patch('sys.argv', ['main.py', '--mode', 'coding', '--no-stream']):
            assert main.parse_args().no_stream is True

    def test_parse_args_resume(self):
        with patch('sys.argv', ['main.py', '--resume']):
            assert main.parse_args().resume is True

    def test_parse_args_dry_run(self):
        with patch('sys.argv', ['main.py', '--mode', 'coding', '--dry-run']):
            assert main.parse_args().dry_run is True

    def test_parse_args_coding_mode(self):
        with patch('sys.argv', ['main.py', '--mode', 'coding']):
            assert main.parse_args().mode == 'coding'

    def test_parse_args_appraisal_mode(self):
        with patch('sys.argv', ['main.py', '--mode', 'appraisal']):
            assert main.parse_args().mode == 'appraisal'

    def test_parse_args_search_mode(self):
        with patch('sys.argv', ['main.py', '--mode', 'search']):
            assert main.parse_args().mode == 'search'

    def test_parse_args_rct_search_mode(self):
        with patch('sys.argv', ['main.py', '--mode', 'rct_search']):
            assert main.parse_args().mode == 'rct_search'

    def test_parse_args_sr_mode(self):
        with patch('sys.argv', ['main.py', '--mode', 'sr']):
            assert main.parse_args().mode == 'sr'

    def test_parse_args_invalid_mode_exits(self):
        with patch('sys.argv', ['main.py', '--mode', 'invalid']):
            with pytest.raises(SystemExit):
                main.parse_args()


class TestMainInteractiveLoop:
    """Test main()'s interactive loop (calls call_ai, not run_* funcs)."""

    def _run_main(self, mode, provider, dry_run,
                  mock_choose_role, role_name, prompt_rel):
        mock_choose_role.return_value = (
            role_name,
            {'prompt': prompt_rel, 'system': 'system prompt'},
        )
        with patch('builtins.input', side_effect=['do the task', KeyboardInterrupt()]), \
             patch('utils.rag.index_uploads', return_value=0), \
             patch('utils.rag.clear_session'), \
             patch('SOURCE_CODE.main.call_ai', return_value='AI response') as mock_call_ai, \
             patch('SOURCE_CODE.main.build_project_context', return_value=''), \
             patch('SOURCE_CODE.main.append_to_transcript'), \
             patch('SOURCE_CODE.main.start_session_transcript',
                   return_value=Path('reports/session_transcript.txt')), \
             patch('SOURCE_CODE.main.print_session_summary'), \
             patch('SOURCE_CODE.main._read_article_files', return_value=[]), \
             patch('SOURCE_CODE.main.Path.exists', return_value=True), \
             patch('SOURCE_CODE.main.Path.read_text', return_value='Prompt content'), \
             patch('sys.argv', ['main.py']):
            main.main(mode=mode, provider=provider, dry_run=dry_run)
        return mock_call_ai

    @patch('SOURCE_CODE.main.choose_role')
    def test_main_coding_mode(self, mock_choose_role):
        m = self._run_main('coding', 'deepseek', False, mock_choose_role,
                           'Builder', 'prompts/builder-prompt.md')
        mock_choose_role.assert_called_once_with('coding')
        m.assert_called_once()

    @patch('SOURCE_CODE.main.choose_role')
    def test_main_writing_mode(self, mock_choose_role):
        m = self._run_main('writing', 'deepseek', False, mock_choose_role,
                           'Editor', 'prompts/editor-prompt.md')
        mock_choose_role.assert_called_once_with('writing')
        m.assert_called_once()

    @patch('SOURCE_CODE.main.choose_role')
    def test_main_appraisal_mode(self, mock_choose_role):
        m = self._run_main('appraisal', 'deepseek', False, mock_choose_role,
                           'Appraiser', 'prompts/appraisal-prompt.md')
        mock_choose_role.assert_called_once_with('appraisal')
        m.assert_called_once()

    @patch('SOURCE_CODE.main.choose_role')
    def test_main_search_mode(self, mock_choose_role):
        m = self._run_main('search', 'deepseek', False, mock_choose_role,
                           'Researcher', 'prompts/researcher-prompt.md')
        mock_choose_role.assert_called_once_with('search')
        m.assert_called_once()

    @patch('SOURCE_CODE.main.choose_role')
    def test_main_rct_search_mode(self, mock_choose_role):
        m = self._run_main('rct_search', 'deepseek', False, mock_choose_role,
                           'Formulator', 'prompts/formulator-prompt.md')
        mock_choose_role.assert_called_once_with('rct_search')
        m.assert_called_once()

    @patch('SOURCE_CODE.main.choose_role')
    def test_main_sr_mode(self, mock_choose_role):
        # NOTE: ALL_MODES in main.py has no "sr" key - SR mode is dispatched
        # straight to run_sr_launcher() at the entry point and never reaches
        # main()/choose_role() for real. This test only passes because
        # choose_role is fully mocked below; with the mock removed,
        # choose_role('sr') would raise KeyError on `ALL_MODES[mode]`.
        # Flagged per README Known Issue #8 - worth deciding whether this
        # test should exist, or be replaced with one that asserts SR mode
        # routes to run_sr_launcher instead.
        m = self._run_main('sr', 'qwen', False, mock_choose_role,
                           'Reviewer', 'prompts/reviewer-prompt.md')
        mock_choose_role.assert_called_once_with('sr')
        m.assert_called_once()

    @patch('SOURCE_CODE.main.choose_role')
    def test_main_dry_run_skips_call_ai(self, mock_choose_role):
        m = self._run_main('coding', 'deepseek', True, mock_choose_role,
                           'Builder', 'prompts/coding/builder.txt')
        mock_choose_role.assert_called_once_with('coding')
        m.assert_not_called()


class TestMainHelpers:
    """Test helper functions."""

    def test_get_input_dir(self):
        d = main.get_input_dir('coding')
        assert 'input' in str(d)
        assert 'coding' in str(d)

    def test_get_output_dir(self):
        d = main.get_output_dir('coding')
        assert 'output' in str(d)
        assert 'coding' in str(d)


class TestMainValidation:
    """Test validation functions."""

    @patch('SOURCE_CODE.main.os.environ')
    def test_validate_api_keys_valid(self, mock_environ):
        mock_environ.get.return_value = 'sk-test123'
        main.validate_api_keys('openai')

    @patch('SOURCE_CODE.main.os.environ')
    def test_validate_api_keys_missing(self, mock_environ):
        mock_environ.get.return_value = ''
        with pytest.raises(OSError):
            main.validate_api_keys('openai')

    @patch('SOURCE_CODE.main.os.environ')
    def test_validate_api_keys_ollama_skip(self, mock_environ):
        mock_environ.get.return_value = ''
        main.validate_api_keys('ollama')


class TestSessionManagement:
    """Test session transcript management functions (file operations)."""

    def _make_session(self, tmp_path, name="session_20260814_120000.md",
                      content="# Session\n\n**Builder**: did a thing\n*note*\n"):
        f = tmp_path / name
        f.write_text(content, encoding="utf-8")
        return f

    def test_list_sessions_with_files(self, tmp_path, capsys):
        self._make_session(tmp_path, "session_20260814_120000.md")
        self._make_session(tmp_path, "session_20260813_090000.md")
        main.list_sessions(reports_dir=str(tmp_path))
        out = capsys.readouterr().out
        assert "session_20260814_120000.md" in out
        assert "session_20260813_090000.md" in out

    def test_list_sessions_empty_folder(self, tmp_path, capsys):
        main.list_sessions(reports_dir=str(tmp_path))
        assert "No session transcripts found." in capsys.readouterr().out

    def test_list_sessions_missing_folder(self, tmp_path, capsys):
        main.list_sessions(reports_dir=str(tmp_path / "nope"))
        assert "No reports folder found." in capsys.readouterr().out

    def test_read_session_existing(self, tmp_path, capsys):
        self._make_session(tmp_path, "session_x.md", content="hello world")
        main.read_session("session_x.md", reports_dir=str(tmp_path))
        out = capsys.readouterr().out
        assert "session_x.md" in out
        assert "hello world" in out

    def test_read_session_missing(self, tmp_path, capsys):
        main.read_session("nope.md", reports_dir=str(tmp_path))
        assert "File not found" in capsys.readouterr().out

    def test_delete_session_confirmed(self, tmp_path, capsys):
        f = self._make_session(tmp_path, "session_del.md")
        with patch('builtins.input', return_value='y'):
            main.delete_session("session_del.md", reports_dir=str(tmp_path))
        assert not f.exists()
        assert "Deleted" in capsys.readouterr().out

    def test_delete_session_cancelled(self, tmp_path, capsys):
        f = self._make_session(tmp_path, "session_keep.md")
        with patch('builtins.input', return_value='n'):
            main.delete_session("session_keep.md", reports_dir=str(tmp_path))
        assert f.exists()
        assert "Cancelled" in capsys.readouterr().out

    def test_delete_session_missing(self, tmp_path, capsys):
        main.delete_session("ghost.md", reports_dir=str(tmp_path))
        assert "File not found" in capsys.readouterr().out

    def test_export_session_strips_markdown(self, tmp_path, capsys):
        self._make_session(tmp_path, "session_exp.md",
                           content="# Title\n\n**bold** and *italic* text\n")
        main.export_session("session_exp.md", reports_dir=str(tmp_path))
        exported = tmp_path / "session_exp.txt"
        assert exported.exists()
        text = exported.read_text(encoding="utf-8")
        assert "Title" in text
        assert "bold and italic text" in text
        assert "**" not in text

    def test_export_session_missing(self, tmp_path, capsys):
        main.export_session("nope.md", reports_dir=str(tmp_path))
        assert "File not found" in capsys.readouterr().out

    def test_rename_session_success(self, tmp_path, capsys):
        f = self._make_session(tmp_path, "session_old.md")
        with patch('builtins.input', return_value='session_new'):
            main.rename_session("session_old.md", reports_dir=str(tmp_path))
        assert not f.exists()
        assert (tmp_path / "session_new.md").exists()
        assert "Renamed" in capsys.readouterr().out

    def test_rename_session_empty_name(self, tmp_path, capsys):
        f = self._make_session(tmp_path, "session_r.md")
        with patch('builtins.input', return_value=''):
            main.rename_session("session_r.md", reports_dir=str(tmp_path))
        assert f.exists()
        assert "Cancelled" in capsys.readouterr().out

    def test_rename_session_target_exists(self, tmp_path, capsys):
        self._make_session(tmp_path, "session_a.md")
        self._make_session(tmp_path, "session_b.md")
        with patch('builtins.input', return_value='session_b'):
            main.rename_session("session_a.md", reports_dir=str(tmp_path))
        assert (tmp_path / "session_a.md").exists()
        assert "already exists" in capsys.readouterr().out

    def test_rename_session_missing(self, tmp_path, capsys):
        main.rename_session("ghost.md", reports_dir=str(tmp_path))
        assert "File not found" in capsys.readouterr().out

    def test_show_stats_runs(self, tmp_path, capsys):
        self._make_session(tmp_path, "session_stats.md")
        main.show_stats(reports_dir=str(tmp_path))
        assert capsys.readouterr().out != ""
