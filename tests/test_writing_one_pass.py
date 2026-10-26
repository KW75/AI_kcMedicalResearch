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
