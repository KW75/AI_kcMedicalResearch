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


# ---------------------------------------------------------------------------
# run_one_pass: one AI call per input, then document (.docx + .md) + review.
# Folders are redirected to tmp_path, as in test_writing.py.
# ---------------------------------------------------------------------------

from unittest.mock import patch

FAKE_ANSWER = (
    "# Dengue Update\n\nDocument body text.\n\n"
    "=== REVIEW ===\n\nPASS: clear structure.\nRECOMMENDATION: APPROVE\n"
)


def _make_paths(tmp_path):
    paths = {
        "doc_root": tmp_path / "docs",
        "input": tmp_path / "input",
        "output": tmp_path / "output",
        "reports": tmp_path / "reports",
    }
    for p in paths.values():
        p.mkdir(parents=True)
    return paths


def _outputs(output_dir):
    docx = sorted(output_dir.glob("WRITING_*.docx"))
    reviews = sorted(output_dir.glob("WRITING_*_REVIEW.md"))
    docs_md = sorted(
        p for p in output_dir.glob("WRITING_*.md") if not p.name.endswith("_REVIEW.md")
    )
    return docx, docs_md, reviews


class TestRunOnePass:
    """run_one_pass makes one AI call per input and saves document + review."""

    def _run(self, tmp_path, answer=FAKE_ANSWER, track=w.TRACK_TOPIC, files=None):
        paths = _make_paths(tmp_path)
        for name, text in (files or {}).items():
            (paths["input"] / name).write_text(text, encoding="utf-8")
        calls = []

        def fake_llm(system_prompt, user_prompt):
            calls.append((system_prompt, user_prompt))
            return answer

        with patch.object(w, "_paths", return_value=paths):
            w.run_one_pass(
                direct_instructions=[],
                call_llm_fn=fake_llm,
                track=track,
                verbose=False,
            )
        return paths, calls

    def test_scratch_makes_one_ai_call(self, tmp_path):
        _, calls = self._run(tmp_path)
        assert len(calls) == 1

    def test_scratch_creates_docx_md_and_review(self, tmp_path):
        paths, _ = self._run(tmp_path)
        docx, docs_md, reviews = _outputs(paths["output"])
        assert len(docx) == 1
        assert len(docs_md) == 1
        assert len(reviews) == 1

    def test_document_and_review_are_separated(self, tmp_path):
        paths, _ = self._run(tmp_path)
        _, docs_md, reviews = _outputs(paths["output"])
        doc_text = docs_md[0].read_text(encoding="utf-8")
        review_text = reviews[0].read_text(encoding="utf-8")
        assert "Document body text." in doc_text
        assert "RECOMMENDATION" not in doc_text
        assert w.REVIEW_MARKER not in doc_text
        assert "RECOMMENDATION: APPROVE" in review_text

    def test_missing_marker_keeps_text_and_flags_review(self, tmp_path):
        paths, _ = self._run(tmp_path, answer="# Title\n\nOnly a document, no marker.")
        _, docs_md, reviews = _outputs(paths["output"])
        assert "Only a document, no marker." in docs_md[0].read_text(encoding="utf-8")
        assert "review missing" in reviews[0].read_text(encoding="utf-8").lower()

    def test_input_file_text_goes_into_prompt(self, tmp_path):
        paths, calls = self._run(
            tmp_path, files={"dengue_note.txt": "SOURCE TEXT ABC 123"}
        )
        assert len(calls) == 1
        assert "SOURCE TEXT ABC 123" in calls[0][1]
        docx, _, _ = _outputs(paths["output"])
        assert "dengue_note" in docx[0].name

    def test_one_call_and_one_document_per_input_file(self, tmp_path):
        paths, calls = self._run(
            tmp_path, files={"a.txt": "First text.", "b.txt": "Second text."}
        )
        assert len(calls) == 2
        docx, docs_md, reviews = _outputs(paths["output"])
        assert len(docx) == 2
        assert len(docs_md) == 2
        assert len(reviews) == 2

    def test_nothing_written_to_reports(self, tmp_path):
        paths, _ = self._run(tmp_path)
        assert list(paths["reports"].iterdir()) == []

    def test_article_track_in_file_names(self, tmp_path):
        paths, _ = self._run(tmp_path, track=w.TRACK_ARTICLE)
        docx, _, reviews = _outputs(paths["output"])
        assert docx[0].name.startswith("WRITING_ARTICLE_")
        assert reviews[0].name.startswith("WRITING_ARTICLE_")


class TestRunOnePassFencedAnswer:
    """Models sometimes wrap their reply in code fences; the split must survive."""

    def test_whole_answer_in_markdown_fence(self, tmp_path):
        answer = "```markdown\n" + FAKE_ANSWER + "```"
        paths, _ = TestRunOnePass()._run(tmp_path, answer=answer)
        _, docs_md, reviews = _outputs(paths["output"])
        doc_text = docs_md[0].read_text(encoding="utf-8")
        review_text = reviews[0].read_text(encoding="utf-8")
        assert "Document body text." in doc_text
        assert "```" not in doc_text
        assert "RECOMMENDATION: APPROVE" in review_text
        assert "```" not in review_text

    def test_document_and_review_fenced_separately(self, tmp_path):
        answer = (
            "```markdown\n# Title\n\nBody.\n```\n"
            "=== REVIEW ===\n"
            "```\nPASS: ok.\nRECOMMENDATION: APPROVE\n```"
        )
        paths, _ = TestRunOnePass()._run(tmp_path, answer=answer)
        _, docs_md, reviews = _outputs(paths["output"])
        doc_text = docs_md[0].read_text(encoding="utf-8")
        review_text = reviews[0].read_text(encoding="utf-8")
        assert "Body." in doc_text
        assert "```" not in doc_text
        assert "RECOMMENDATION: APPROVE" in review_text
        assert "```" not in review_text


class TestReportTrack:
    """Third track: Report (abstract / report), default 500 words."""

    def test_track_constant(self):
        assert w.TRACK_REPORT == "report"

    def test_default_words(self):
        assert w.DEFAULT_WORDS[w.TRACK_REPORT] == 500

    def test_has_writer_editor_and_reviewer_texts(self):
        for table in (w._WRITER_PERSONA, w._EDITOR_PERSONA, w._QA_PERSONA):
            assert table[w.TRACK_REPORT].strip()

    def test_role_texts_differ_from_other_tracks(self):
        for table in (w._WRITER_PERSONA, w._EDITOR_PERSONA, w._QA_PERSONA):
            assert table[w.TRACK_REPORT] != table[w.TRACK_TOPIC]
            assert table[w.TRACK_REPORT] != table[w.TRACK_ARTICLE]

    def test_system_prompt_uses_report_texts(self):
        sp = w._one_pass_system_prompt("", w.TRACK_REPORT)
        assert w._WRITER_PERSONA[w.TRACK_REPORT] in sp
        assert w._EDITOR_PERSONA[w.TRACK_REPORT] in sp
        assert w._QA_PERSONA[w.TRACK_REPORT] in sp

    def test_user_prompt_says_abstract_report_not_journal_article(self):
        p = w._one_pass_user_prompt([], "", True, w.TRACK_REPORT, 500)
        assert "abstract / report" in p
        assert "journal article" not in p

    def test_run_one_pass_report_file_names(self, tmp_path):
        paths, _ = TestRunOnePass()._run(tmp_path, track=w.TRACK_REPORT)
        docx, _, reviews = _outputs(paths["output"])
        assert docx[0].name.startswith("WRITING_REPORT_")
        assert reviews[0].name.startswith("WRITING_REPORT_")
        
# ---------------------------------------------------------------------------
# Use files in input/writing/ or ignore them (user choice)
# ---------------------------------------------------------------------------
from unittest.mock import patch as _patch


class TestUseFilesChoice:
    """Writing mode lists input files and can ignore them on request."""

    @staticmethod
    def _paths(tmp_path):
        paths = {
            "doc_root": tmp_path / "docs",
            "input": tmp_path / "input",
            "output": tmp_path / "output",
            "reports": tmp_path / "reports",
        }
        for p in paths.values():
            p.mkdir(parents=True, exist_ok=True)
        return paths

    def test_list_input_names_supported_only_sorted(self, tmp_path):
        (tmp_path / "b.pdf").write_bytes(b"%PDF-1.4")
        (tmp_path / "a.txt").write_text("x", encoding="utf-8")
        (tmp_path / "notes.xyz").write_text("x", encoding="utf-8")
        (tmp_path / "sub").mkdir()
        assert w.list_input_names(tmp_path) == ["a.txt", "b.pdf"]

    def test_list_input_names_missing_folder(self, tmp_path):
        assert w.list_input_names(tmp_path / "nope") == []

    def test_use_files_false_writes_from_scratch(self, tmp_path):
        paths = self._paths(tmp_path)
        (paths["input"] / "source.txt").write_text(
            "SECRET SOURCE TEXT", encoding="utf-8"
        )
        calls = []

        def fake_llm(system_prompt, user_prompt):
            calls.append(user_prompt)
            return "Doc text\n=== REVIEW ===\nRECOMMENDATION: APPROVE"

        with _patch("pipelines.writing.writing._paths", return_value=paths):
            w.run_one_pass(
                direct_instructions=["Write about dengue"],
                call_llm_fn=fake_llm,
                track=w.TRACK_TOPIC,
                verbose=False,
                use_files=False,
            )

        assert len(calls) == 1
        assert "SECRET SOURCE TEXT" not in calls[0]
        names = [p.name for p in paths["output"].iterdir()]
        assert names, "documents should be written"
        assert all("new_doc" in n for n in names)
        assert not any("source" in n for n in names)
        assert (paths["input"] / "source.txt").exists(), "file must never be deleted"

# ---------------------------------------------------------------------------
# Fallback split: model wrote "Stage" headings instead of the marker
# ---------------------------------------------------------------------------
STAGED_ANSWER = (
    "## Stage 1 - Writer Draft\n\n# Title\n\nDRAFT TEXT\n\n"
    "## Stage 2 - Editor Polish\n\n# Title\n\nPOLISHED TEXT\n\n"
    "## Stage 3 - Reviewer QA Report\n\n| Item | PASS |\n\n"
    "**RECOMMENDATION:** APPROVE\n"
)


class TestStageHeadingFallback:

    def test_stage_headings_split_into_polished_doc_and_review(self):
        doc, review = w._split_document_and_review(STAGED_ANSWER)
        assert "POLISHED TEXT" in doc
        assert "DRAFT TEXT" not in doc
        assert "Stage" not in doc
        assert "RECOMMENDATION" not in doc
        assert "RECOMMENDATION" in review
        assert review != w.REVIEW_MISSING

    def test_stage_3_only_doc_is_text_before_it(self):
        text = "# Title\n\nBODY\n\n## Stage 3 - Reviewer QA Report\n\nRECOMMENDATION: APPROVE"
        doc, review = w._split_document_and_review(text)
        assert "BODY" in doc and "Stage" not in doc
        assert "RECOMMENDATION: APPROVE" in review

    def test_qa_report_heading_also_splits(self):
        text = "# Title\n\nBODY\n\n## QA Report\n\nRECOMMENDATION: REVISE MINOR"
        doc, review = w._split_document_and_review(text)
        assert "BODY" in doc and "QA Report" not in doc
        assert "REVISE MINOR" in review

    def test_ordinary_review_heading_does_not_split(self):
        text = "# Title\n\n## Review of the literature\n\nBODY"
        doc, review = w._split_document_and_review(text)
        assert "Review of the literature" in doc
        assert review == w.REVIEW_MISSING

    def test_marker_still_wins_over_stage_headings(self):
        text = "## Stage 3 - x\n\nDOC\n=== REVIEW ===\nREAL REVIEW"
        doc, review = w._split_document_and_review(text)
        assert "REAL REVIEW" in review and "REAL REVIEW" not in doc

    def test_system_prompt_forbids_stage_headings(self):
        p = w._one_pass_system_prompt("", w.TRACK_REPORT).lower()
        assert "stage headings" in p
