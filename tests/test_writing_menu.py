"""Tests for the Writing mode terminal menu (main.handle_writing_mode).

Flow: track -> (files found? "Use these files? [Y/n]") -> word limit
-> instructions -> one call to run_one_pass (tracks 1-3) or run_synopsis (4).
There is no Writer/Editor/QA sub-mode question any more.
Tracks: 1 Topic (editorial / opinion), 2 Article (medical research articles),
3 Report (abstract / report), 4 Synopsis (all files in input/writing/).

The file list in input/writing/ is faked, so these tests do not depend on
what is in the real folder.
"""

import sys
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_CODE_DIR = PROJECT_ROOT / "SOURCE_CODE"
sys.path.insert(0, str(SOURCE_CODE_DIR))

from SOURCE_CODE import main
from pipelines.writing.writing import TRACK_TOPIC, TRACK_ARTICLE, TRACK_REPORT


def _run_menu(answers, files=None, provider="ollama"):
    """Run handle_writing_mode with typed answers and a fake file list.
    Return (run_one_pass mock, run_writer mock, list of input() prompts,
    run_synopsis mock)."""
    it = iter(answers)
    prompts = []

    def fake_input(prompt=""):
        prompts.append(prompt)
        return next(it, "")  # extra questions get a blank answer

    with patch("builtins.input", side_effect=fake_input), \
         patch("pipelines.writing.writing.list_input_names",
               return_value=list(files or [])), \
         patch("pipelines.writing.writing.run_one_pass") as one_pass, \
         patch("pipelines.writing.writing.run_synopsis") as synopsis, \
         patch("pipelines.writing.writing.run_writer") as writer:
        main.handle_writing_mode(provider=provider, model=None, dry_run=True)
    return one_pass, writer, prompts, synopsis


class TestWritingMenu:

    def test_topic_default_word_limit_calls_run_one_pass(self):
        one_pass, writer, _, _ = _run_menu(["1", "", "Focus on dengue", ""])
        one_pass.assert_called_once()
        kwargs = one_pass.call_args.kwargs
        assert kwargs["track"] == TRACK_TOPIC
        assert kwargs["word_limit"] == 800
        assert "Focus on dengue" in str(kwargs["direct_instructions"])
        writer.assert_not_called()

    def test_article_custom_word_limit(self):
        one_pass, _, _, _ = _run_menu(["2", "1200", "Write about RCT design", ""])
        one_pass.assert_called_once()
        kwargs = one_pass.call_args.kwargs
        assert kwargs["track"] == TRACK_ARTICLE
        assert kwargs["word_limit"] == 1200

    def test_no_sub_mode_question(self):
        _, _, prompts, _ = _run_menu(["1", "", "Focus on dengue", ""])
        assert not any("sub-mode" in p.lower() for p in prompts)

    def test_report_track_default_word_limit(self):
        one_pass, _, _, _ = _run_menu(["3", "", "Summarise dengue cases 2025", ""])
        one_pass.assert_called_once()
        kwargs = one_pass.call_args.kwargs
        assert kwargs["track"] == TRACK_REPORT
        assert kwargs["word_limit"] == 500

    def test_menu_wording_shows_four_tracks(self, capsys):
        _, _, prompts, _ = _run_menu(["0"])
        out = capsys.readouterr().out
        assert "Topic Track" in out and "editorial / opinion" in out
        assert "Article Track" in out and "medical research articles" in out
        assert "Report Track" in out and "abstract / report" in out
        assert "Synopsis Track" in out
        assert any("[0-4]" in p for p in prompts)


class TestUseFilesQuestion:
    """Files in input/writing/ are listed and the user confirms using them."""

    FILES = ["paper_one.pdf"]

    def test_files_found_enter_uses_them(self, capsys):
        one_pass, _, prompts, _ = _run_menu(
            ["1", "", "", "Focus on dengue", ""], files=self.FILES
        )
        assert any("Use these files" in p for p in prompts)
        assert "paper_one.pdf" in capsys.readouterr().out
        one_pass.assert_called_once()
        kwargs = one_pass.call_args.kwargs
        assert kwargs["use_files"] is True
        assert kwargs["word_limit"] == 800

    def test_files_found_n_ignores_them(self, capsys):
        one_pass, _, prompts, _ = _run_menu(
            ["1", "n", "", "Focus on dengue", ""], files=self.FILES
        )
        assert any("Use these files" in p for p in prompts)
        assert "Files ignored" in capsys.readouterr().out
        one_pass.assert_called_once()
        assert one_pass.call_args.kwargs["use_files"] is False

    def test_no_files_no_question_but_says_so(self, capsys):
        one_pass, _, prompts, _ = _run_menu(["1", "", "Focus on dengue", ""])
        assert not any("Use these files" in p for p in prompts)
        assert "No files in input/writing/" in capsys.readouterr().out
        one_pass.assert_called_once()


class TestSynopsisMenu:
    """Option 4: one synopsis of all files; needs files, never from scratch."""

    FILES = ["a.pdf", "b.pdf"]

    def test_synopsis_runs_with_files_default_1500_local(self, capsys):
        one_pass, _, prompts, synopsis = _run_menu(
            ["4", "", "", "Summarise", ""], files=self.FILES
        )
        assert any("Use these files" in p for p in prompts)
        out = capsys.readouterr().out
        assert "a.pdf" in out and "b.pdf" in out
        synopsis.assert_called_once()
        kwargs = synopsis.call_args.kwargs
        assert kwargs["word_limit"] == 1500
        assert kwargs["local"] is True
        assert "Summarise" in str(kwargs["direct_instructions"])
        one_pass.assert_not_called()

    def test_synopsis_cloud_provider_is_not_local(self):
        _, _, _, synopsis = _run_menu(
            ["4", "", "", "Summarise", ""], files=self.FILES, provider="deepseek"
        )
        synopsis.assert_called_once()
        assert synopsis.call_args.kwargs["local"] is False

    def test_synopsis_no_files_stops(self, capsys):
        one_pass, _, prompts, synopsis = _run_menu(["4", "", "Summarise", ""])
        assert "Synopsis needs files in input/writing/" in capsys.readouterr().out
        synopsis.assert_not_called()
        one_pass.assert_not_called()
        assert not any("instruction" in p.lower() for p in prompts)

    def test_synopsis_n_cancels(self, capsys):
        one_pass, _, _, synopsis = _run_menu(["4", "n"], files=self.FILES)
        assert "Synopsis cancelled" in capsys.readouterr().out
        synopsis.assert_not_called()
        one_pass.assert_not_called()
