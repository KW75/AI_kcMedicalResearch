"""Tests for the Writing mode terminal menu (main.handle_writing_mode).

New flow: track -> word limit -> instructions -> one call to run_one_pass.
There is no Writer/Editor/QA sub-mode question any more.
Tracks: 1 Topic (editorial / opinion), 2 Article (medical research articles),
3 Report (abstract / report).
"""

import sys
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_CODE_DIR = PROJECT_ROOT / "SOURCE_CODE"
sys.path.insert(0, str(SOURCE_CODE_DIR))

from SOURCE_CODE import main
from pipelines.writing.writing import TRACK_TOPIC, TRACK_ARTICLE, TRACK_REPORT


def _run_menu(answers):
    """Run handle_writing_mode with typed answers; return (run_one_pass mock,
    run_writer mock, list of input() prompts shown)."""
    it = iter(answers)
    prompts = []

    def fake_input(prompt=""):
        prompts.append(prompt)
        return next(it, "")  # extra questions get a blank answer

    with patch("builtins.input", side_effect=fake_input), \
         patch("pipelines.writing.writing.run_one_pass") as one_pass, \
         patch("pipelines.writing.writing.run_writer") as writer:
        main.handle_writing_mode(provider="ollama", model=None, dry_run=True)
    return one_pass, writer, prompts


class TestWritingMenu:

    def test_topic_default_word_limit_calls_run_one_pass(self):
        one_pass, writer, _ = _run_menu(["1", "", "Focus on dengue", ""])
        one_pass.assert_called_once()
        kwargs = one_pass.call_args.kwargs
        assert kwargs["track"] == TRACK_TOPIC
        assert kwargs["word_limit"] == 800
        assert "Focus on dengue" in str(kwargs["direct_instructions"])
        writer.assert_not_called()

    def test_article_custom_word_limit(self):
        one_pass, _, _ = _run_menu(["2", "1200", "Write about RCT design", ""])
        one_pass.assert_called_once()
        kwargs = one_pass.call_args.kwargs
        assert kwargs["track"] == TRACK_ARTICLE
        assert kwargs["word_limit"] == 1200

    def test_no_sub_mode_question(self):
        _, _, prompts = _run_menu(["1", "", "Focus on dengue", ""])
        assert not any("sub-mode" in p.lower() for p in prompts)

    def test_report_track_default_word_limit(self):
        one_pass, _, _ = _run_menu(["3", "", "Summarise dengue cases 2025", ""])
        one_pass.assert_called_once()
        kwargs = one_pass.call_args.kwargs
        assert kwargs["track"] == TRACK_REPORT
        assert kwargs["word_limit"] == 500

    def test_menu_wording_shows_three_tracks(self, capsys):
        _, _, prompts = _run_menu(["0"])
        out = capsys.readouterr().out
        assert "Topic Track" in out and "editorial / opinion" in out
        assert "Article Track" in out and "medical research articles" in out
        assert "Report Track" in out and "abstract / report" in out
        assert any("[0-3]" in p for p in prompts)
