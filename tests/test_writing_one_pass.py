"""Tests for one-pass Writing mode: splitting the AI answer into document + review."""

import sys
from pathlib import Path

# Add SOURCE_CODE to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_CODE_DIR = PROJECT_ROOT / "SOURCE_CODE"
sys.path.insert(0, str(SOURCE_CODE_DIR))

from pipelines.writing.writing import REVIEW_MARKER, _split_document_and_review


class TestSplitDocumentAndReview:
    """The single AI answer is cut into (document, review) at the marker line."""

    def test_marker_value(self):
        """The marker is fixed; the prompt and the splitter must use the same text."""
        assert REVIEW_MARKER == "=== REVIEW ==="

    def test_splits_at_marker(self):
        """Text before the marker is the document, text after is the review."""
        text = "# Title\n\nBody text.\n\n=== REVIEW ===\n\n- Point one\n- Point two\n"
        document, review = _split_document_and_review(text)
        assert document == "# Title\n\nBody text."
        assert review == "- Point one\n- Point two"

    def test_marker_line_with_extra_spaces(self):
        """Spaces around the marker line are tolerated."""
        text = "Body.\n   === REVIEW ===   \nReview text."
        document, review = _split_document_and_review(text)
        assert document == "Body."
        assert review == "Review text."

    def test_missing_marker_keeps_all_text_as_document(self):
        """If the model forgets the marker, no text is lost."""
        text = "# Title\n\nBody text with no marker."
        document, review = _split_document_and_review(text)
        assert document == text
        assert "review missing" in review.lower()

    def test_empty_review_after_marker(self):
        """A marker with nothing after it counts as a missing review."""
        text = "Body.\n=== REVIEW ===\n   \n"
        document, review = _split_document_and_review(text)
        assert document == "Body."
        assert "review missing" in review.lower()

    def test_marker_inside_a_sentence_is_not_a_split(self):
        """The marker only counts on a line of its own."""
        text = "We discuss the === REVIEW === marker here.\n\nMore body."
        document, review = _split_document_and_review(text)
        assert document == text
        assert "review missing" in review.lower()



# ---------------------------------------------------------------------------
# One-pass prompts. Imported as a module so a missing function fails each
# test on its own instead of stopping the whole file from loading.
# ---------------------------------------------------------------------------

from pipelines.writing import writing as w


class TestOnePassSystemPrompt:
    """One system prompt that combines the writer, editor and reviewer roles."""

    def test_combines_all_three_personas_topic(self):
        sp = w._one_pass_system_prompt("", w.TRACK_TOPIC)
        assert w._WRITER_PERSONA[w.TRACK_TOPIC] in sp
        assert w._EDITOR_PERSONA[w.TRACK_TOPIC] in sp
        assert w._QA_PERSONA[w.TRACK_TOPIC] in sp

    def test_combines_all_three_personas_article(self):
        sp = w._one_pass_system_prompt("", w.TRACK_ARTICLE)
        assert w._WRITER_PERSONA[w.TRACK_ARTICLE] in sp
        assert w._EDITOR_PERSONA[w.TRACK_ARTICLE] in sp
        assert w._QA_PERSONA[w.TRACK_ARTICLE] in sp

    def test_guidelines_included_when_given(self):
        sp = w._one_pass_system_prompt("Use British spelling.", w.TRACK_TOPIC)
        assert "## Guidelines" in sp
        assert "Use British spelling." in sp

    def test_no_guidelines_heading_when_empty(self):
        sp = w._one_pass_system_prompt("", w.TRACK_TOPIC)
        assert "## Guidelines" not in sp


class TestOnePassUserPrompt:
    """The user prompt asks for the document, the marker line, then the review."""

    def _prompt(self, **kw):
        args = dict(
            direct_instructions=[],
            original_content="",
            is_scratch=True,
            track=w.TRACK_TOPIC,
            word_limit=800,
        )
        args.update(kw)
        return w._one_pass_user_prompt(**args)

    def test_marker_on_its_own_line(self):
        lines = [line.strip() for line in self._prompt().splitlines()]
        assert w.REVIEW_MARKER in lines

    def test_word_limit_used(self):
        assert "650 words" in self._prompt(word_limit=650)

    def test_direct_instructions_listed(self):
        p = self._prompt(direct_instructions=["> Focus on dengue"])
        assert "DIRECT TASK INSTRUCTIONS" in p
        assert "- Focus on dengue" in p

    def test_scratch_has_no_source_section(self):
        p = self._prompt(is_scratch=True)
        assert "No input document" in p
        assert "## Source Document" not in p

    def test_source_document_included(self):
        p = self._prompt(is_scratch=False, original_content="ORIGINAL TEXT 123")
        assert "## Source Document" in p
        assert "ORIGINAL TEXT 123" in p

    def test_track_label(self):
        assert "newspaper editorial" in self._prompt(track=w.TRACK_TOPIC)
        assert "medical journal article" in self._prompt(track=w.TRACK_ARTICLE)

    def test_review_asks_for_recommendation(self):
        assert "RECOMMENDATION" in self._prompt()
