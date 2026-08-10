"""Tests for the writing pipeline module - Standard Way: Tests define the specification."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock

import pytest

# Add SOURCE_CODE to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_CODE_DIR = PROJECT_ROOT / "SOURCE_CODE"
sys.path.insert(0, str(SOURCE_CODE_DIR))

# Import the writing module
from pipelines.writing.writing import (
    _project_root,
    _ts,
    _paths,
    _load_guidelines,
    _load_input_files,
    _write_text,
    _strip_fences,
    _strip_boilerplate,
    _system_prompt,
    _writer_user_prompt,
    _editor_user_prompt,
    _qa_user_prompt,
    run_writer,
    run_editor,
    run_qa,
    parse_direct_instructions,
    TRACK_TOPIC,
    TRACK_ARTICLE,
    DEFAULT_WORDS,
    DISCLOSURE,
)


class TestWritingHelpers:
    """Test helper functions in writing.py."""

    def test_project_root(self):
        """_project_root returns a Path object."""
        root = _project_root()
        assert isinstance(root, Path)
        assert root.exists()

    def test_ts(self):
        """_ts returns a timestamp string in YYYYMMDD_HHMMSS format."""
        ts = _ts()
        assert isinstance(ts, str)
        assert len(ts) == 15  # YYYYMMDD_HHMMSS
        assert ts[8] == "_"  # Underscore between date and time

    def test_paths(self):
        """_paths returns expected directory structure with doc_root key."""
        root = _project_root()
        paths = _paths(root)
        
        expected_keys = ["doc_root", "input", "output", "reports"]
        for key in expected_keys:
            assert key in paths
            assert isinstance(paths[key], Path)

    def test_load_guidelines_empty(self, tmp_path):
        """_load_guidelines returns empty string when no guidelines exist."""
        result = _load_guidelines(tmp_path, tmp_path)
        assert result == ""

    def test_load_guidelines_with_files(self, tmp_path):
        """_load_guidelines loads and concatenates .md files."""
        track_path = tmp_path / "topic"
        track_path.mkdir()
        shared_path = tmp_path / "shared"
        shared_path.mkdir()
        
        guideline_file = track_path / "style-guide.md"
        guideline_file.write_text("# Style Guide\n\nThis is a test style guide.", encoding="utf-8")
        
        (shared_path / "project-brief.md").write_text(
            "# Project Brief\n\nThis is the project brief.",
            encoding="utf-8"
        )
        
        result = _load_guidelines(track_path, shared_path)
        assert "Style Guide" in result
        assert "This is a test style guide" in result

    def test_load_input_files_empty(self, tmp_path):
        """_load_input_files returns empty list when no files exist."""
        result = _load_input_files(tmp_path)
        assert result == []

    def test_load_input_files_with_supported_files(self, tmp_path):
        """_load_input_files loads supported file types (.txt, .md, .docx, .pdf)."""
        (tmp_path / "test1.txt").write_text("Text content", encoding="utf-8")
        (tmp_path / "test2.md").write_text("# Markdown content", encoding="utf-8")
        (tmp_path / "test3.pdf").write_text("PDF content", encoding="utf-8")
        (tmp_path / "test4.docx").write_text("DOCX content", encoding="utf-8")
        (tmp_path / "test5.log").write_text("Log file", encoding="utf-8")
        
        result = _load_input_files(tmp_path)
        assert len(result) >= 4
        stems = [f[0] for f in result]
        assert "test1" in stems
        assert "test2" in stems

    def test_write_text(self, tmp_path):
        """_write_text creates file with content."""
        test_file = tmp_path / "test.txt"
        content = "Test content"
        
        _write_text(test_file, content)
        assert test_file.exists()
        assert test_file.read_text(encoding="utf-8") == content

    def test_strip_fences_no_fences(self):
        """_strip_fences returns text unchanged when no fences present."""
        text = "This is plain text without fences."
        assert _strip_fences(text) == text.strip()

    def test_strip_fences_with_code_fence(self):
        """_strip_fences removes ``` fences."""
        text = "```\nSome code\n```"
        expected = "Some code"
        assert _strip_fences(text) == expected

    def test_strip_fences_with_python_fence(self):
        """_strip_fences removes ```python fences."""
        text = "```python\nprint('Hello')\n```"
        expected = "print('Hello')"
        assert _strip_fences(text) == expected

    def test_strip_boilerplate_no_marker(self):
        """_strip_boilerplate returns text unchanged when no boilerplate markers found."""
        text = "This is clean content without boilerplate."
        assert _strip_boilerplate(text) == text

    def test_strip_boilerplate_with_marker(self):
        """_strip_boilerplate removes content after boilerplate markers."""
        text = "Document content.\n\n## QA Checklist\nThis should be removed."
        result = _strip_boilerplate(text)
        assert "Document content." in result
        assert "QA Checklist" not in result

    def test_system_prompt_writer_topic(self):
        """_system_prompt returns writer persona for topic track."""
        guidelines = "Test guidelines"
        result = _system_prompt(guidelines, "Writer", TRACK_TOPIC)
        assert isinstance(result, str)
        assert "newspaper columnist" in result or "editorial" in result.lower()
        if guidelines:
            assert guidelines in result

    def test_system_prompt_writer_article(self):
        """_system_prompt returns writer persona for article track."""
        guidelines = "Test guidelines"
        result = _system_prompt(guidelines, "Writer", TRACK_ARTICLE)
        assert isinstance(result, str)
        assert "medical academic writer" in result or "IMRAD" in result
        if guidelines:
            assert guidelines in result

    def test_system_prompt_editor_topic(self):
        """_system_prompt returns editor persona for topic track."""
        guidelines = "Test guidelines"
        result = _system_prompt(guidelines, "Editor", TRACK_TOPIC)
        assert isinstance(result, str)
        assert "newspaper" in result.lower() or "editor" in result.lower()

    def test_system_prompt_qa_topic(self):
        """_system_prompt returns QA persona for topic track."""
        guidelines = "Test guidelines"
        result = _system_prompt(guidelines, "QA", TRACK_TOPIC)
        assert isinstance(result, str)
        assert "quality assurance" in result.lower() or "QA" in result

    def test_writer_user_prompt_scratch(self):
        """_writer_user_prompt handles scratch mode (no input files)."""
        direct = ["Write about topic X"]
        original_content = ""
        is_scratch = True
        track = TRACK_TOPIC
        word_limit = 800
        
        result = _writer_user_prompt(direct, original_content, is_scratch, track, word_limit)
        assert "DIRECT TASK INSTRUCTIONS" in result
        assert "Write about topic X" in result
        assert "800" in result

    def test_writer_user_prompt_with_content(self):
        """_writer_user_prompt includes original content when available."""
        direct = ["Improve this document"]
        original_content = "This is the original content."
        is_scratch = False
        track = TRACK_ARTICLE
        word_limit = 3500
        
        result = _writer_user_prompt(direct, original_content, is_scratch, track, word_limit)
        assert "DIRECT TASK INSTRUCTIONS" in result
        assert "Improve this document" in result
        assert "This is the original content" in result
        assert "3500" in result

    def test_editor_user_prompt(self):
        """_editor_user_prompt includes writer output and original content."""
        direct = ["Make it more concise"]
        original_content = "Original source content."
        writer_output = "Writer draft content."
        track = TRACK_TOPIC
        word_limit = 800
        
        result = _editor_user_prompt(direct, writer_output, original_content, track, word_limit)
        assert "DIRECT TASK INSTRUCTIONS" in result
        assert "Make it more concise" in result
        assert "Original source content" in result
        assert "Writer draft content" in result

    def test_qa_user_prompt(self):
        """_qa_user_prompt includes editor output for review."""
        editor_output = "Edited document content."
        track = TRACK_ARTICLE
        
        result = _qa_user_prompt(editor_output, track)
        assert "Edited document content" in result
        assert "Document to Review" in result or "review" in result.lower()

    def test_parse_direct_instructions(self):
        """parse_direct_instructions extracts > lines."""
        raw = "> Instruction 1\nNormal text\n> Instruction 2"
        result = parse_direct_instructions(raw)
        assert len(result) == 2
        assert "Instruction 1" in result[0]
        assert "Instruction 2" in result[1]

    def test_parse_direct_instructions_empty(self):
        """parse_direct_instructions returns empty list for no instructions."""
        raw = "Normal text without instructions."
        result = parse_direct_instructions(raw)
        assert result == []

    def test_track_constants(self):
        """Test that track constants are defined."""
        assert TRACK_TOPIC == "topic"
        assert TRACK_ARTICLE == "article"

    def test_default_words(self):
        """Test that default word counts are defined."""
        assert DEFAULT_WORDS[TRACK_TOPIC] == 800
        assert DEFAULT_WORDS[TRACK_ARTICLE] == 3500

    def test_disclosure_exists(self):
        """Test that disclosure statement is defined."""
        assert DISCLOSURE is not None
        assert "AI" in DISCLOSURE or "assistance" in DISCLOSURE


class TestWritingIntegration:
    """Integration tests for writing pipeline."""

    def test_run_writer_no_files(self, tmp_path):
        """run_writer handles scratch mode when no input files exist."""
        doc_root = tmp_path / "docs"
        doc_root.mkdir(parents=True)
        
        with patch("pipelines.writing.writing._paths") as mock_paths:
            mock_paths.return_value = {
                "doc_root": doc_root,
                "input": tmp_path / "input",
                "output": tmp_path / "output",
                "reports": tmp_path / "reports",
            }
            
            def mock_llm(system_prompt, user_prompt):
                return "Mock writer output"
            
            run_writer(
                direct_instructions=["Write about medical research"],
                call_llm_fn=mock_llm,
                track=TRACK_TOPIC,
                word_limit=800,
                verbose=True,
            )
            assert True

    def test_run_writer_with_files(self, tmp_path):
        """run_writer processes input files and creates outputs."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        reports_dir = tmp_path / "reports"
        doc_root = tmp_path / "docs"
        
        input_dir.mkdir(parents=True)
        output_dir.mkdir(parents=True)
        reports_dir.mkdir(parents=True)
        doc_root.mkdir(parents=True)
        
        (input_dir / "test_article.txt").write_text(
            "This is a test article for writing.",
            encoding="utf-8"
        )
        
        (doc_root / "writing").mkdir(parents=True, exist_ok=True)
        
        with patch("pipelines.writing.writing._paths") as mock_paths:
            mock_paths.return_value = {
                "doc_root": doc_root,
                "input": input_dir,
                "output": output_dir,
                "reports": reports_dir,
            }
            
            def mock_llm(system_prompt, user_prompt):
                return "Mock writer output with content."
            
            run_writer(
                direct_instructions=[],
                call_llm_fn=mock_llm,
                track=TRACK_TOPIC,
                word_limit=800,
                verbose=False,
            )
            
            output_files = list(output_dir.glob("*.md"))
            assert len(output_files) > 0, "Output files should be created"

    def test_run_editor_no_files(self, tmp_path, capsys):
        """run_editor handles empty input directory gracefully."""
        doc_root = tmp_path / "docs"
        doc_root.mkdir(parents=True)
        
        with patch("pipelines.writing.writing._paths") as mock_paths:
            mock_paths.return_value = {
                "doc_root": doc_root,
                "input": tmp_path / "input",
                "output": tmp_path / "output",
                "reports": tmp_path / "reports",
            }
            
            def mock_llm(system_prompt, user_prompt):
                return "Mock editor output"
            
            run_editor(
                direct_instructions=[],
                call_llm_fn=mock_llm,
                track=TRACK_TOPIC,
                verbose=True,
            )
            
            captured = capsys.readouterr()
            assert "No files" in captured.out or "no files" in captured.out.lower()

    def test_run_editor_with_files(self, tmp_path):
        """run_editor processes input files and creates outputs."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        reports_dir = tmp_path / "reports"
        doc_root = tmp_path / "docs"
        
        input_dir.mkdir(parents=True)
        output_dir.mkdir(parents=True)
        reports_dir.mkdir(parents=True)
        doc_root.mkdir(parents=True)
        
        (input_dir / "test_article.txt").write_text(
            "This is a test article to edit.",
            encoding="utf-8"
        )
        
        (doc_root / "writing").mkdir(parents=True, exist_ok=True)
        
        with patch("pipelines.writing.writing._paths") as mock_paths:
            mock_paths.return_value = {
                "doc_root": doc_root,
                "input": input_dir,
                "output": output_dir,
                "reports": reports_dir,
            }
            
            def mock_llm(system_prompt, user_prompt):
                return "Mock editor output with edits."
            
            run_editor(
                direct_instructions=[],
                call_llm_fn=mock_llm,
                track=TRACK_TOPIC,
                verbose=False,
            )
            
            output_files = list(output_dir.glob("*.md"))
            assert len(output_files) > 0, "Output files should be created"

    def test_run_qa_no_files(self, tmp_path, capsys):
        """run_qa handles empty input directory gracefully."""
        doc_root = tmp_path / "docs"
        doc_root.mkdir(parents=True)
        
        with patch("pipelines.writing.writing._paths") as mock_paths:
            mock_paths.return_value = {
                "doc_root": doc_root,
                "input": tmp_path / "input",
                "output": tmp_path / "output",
                "reports": tmp_path / "reports",
            }
            
            def mock_llm(system_prompt, user_prompt):
                return "Mock QA output"
            
            run_qa(
                direct_instructions=[],
                call_llm_fn=mock_llm,
                track=TRACK_TOPIC,
                verbose=True,
            )
            
            captured = capsys.readouterr()
            assert "No files" in captured.out or "no files" in captured.out.lower()

    def test_run_qa_with_files(self, tmp_path):
        """run_qa processes input files and creates QA reports."""
        input_dir = tmp_path / "input"
        reports_dir = tmp_path / "reports"
        doc_root = tmp_path / "docs"
        
        input_dir.mkdir(parents=True)
        reports_dir.mkdir(parents=True)
        doc_root.mkdir(parents=True)
        
        (input_dir / "test_article.txt").write_text(
            "This is a test article for QA review.",
            encoding="utf-8"
        )
        
        (doc_root / "writing").mkdir(parents=True, exist_ok=True)
        
        with patch("pipelines.writing.writing._paths") as mock_paths:
            mock_paths.return_value = {
                "doc_root": doc_root,
                "input": input_dir,
                "output": tmp_path / "output",
                "reports": reports_dir,
            }
            
            def mock_llm(system_prompt, user_prompt):
                return "Mock QA report with PASS/FAIL items."
            
            run_qa(
                direct_instructions=[],
                call_llm_fn=mock_llm,
                track=TRACK_TOPIC,
                verbose=False,
            )
            
            report_files = list(reports_dir.glob("*.md"))
            assert len(report_files) > 0, "QA report files should be created"


class TestWritingEdgeCases:
    """Edge case tests for writing module."""

    def test_load_input_files_with_large_files(self, tmp_path):
        """_load_input_files handles large files gracefully."""
        large_content = "x" * 50000
        (tmp_path / "large.txt").write_text(large_content, encoding="utf-8")
        
        result = _load_input_files(tmp_path)
        assert len(result) == 1
        assert result[0][1] == large_content

    def test_load_input_files_with_pdf(self, tmp_path):
        """_load_input_files handles PDF files (with mock)."""
        (tmp_path / "test.pdf").write_text("PDF content", encoding="utf-8")
        
        try:
            result = _load_input_files(tmp_path)
            assert isinstance(result, list)
        except ImportError:
            pytest.skip("PyMuPDF not installed")

    def test_run_writer_with_direct_instructions(self, tmp_path):
        """run_writer passes direct instructions to the LLM."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        reports_dir = tmp_path / "reports"
        doc_root = tmp_path / "docs"
        
        input_dir.mkdir(parents=True)
        output_dir.mkdir(parents=True)
        reports_dir.mkdir(parents=True)
        doc_root.mkdir(parents=True)
        
        writer_prompt_captured = ""
        call_order = []
        
        def mock_llm(system_prompt, user_prompt):
            nonlocal writer_prompt_captured, call_order
            # Capture the first call (Writer) prompt
            if "WRITER" in system_prompt.upper() or "newspaper" in system_prompt.lower():
                writer_prompt_captured = user_prompt
                call_order.append("writer")
            else:
                call_order.append("other")
            return "Mock response"
        
        with patch("pipelines.writing.writing._paths") as mock_paths:
            mock_paths.return_value = {
                "doc_root": doc_root,
                "input": input_dir,
                "output": output_dir,
                "reports": reports_dir,
            }
            
            direct_instructions = ["Focus on clinical relevance", "Include recent evidence"]
            run_writer(
                direct_instructions=direct_instructions,
                call_llm_fn=mock_llm,
                track=TRACK_ARTICLE,
                word_limit=3500,
                verbose=False,
            )
            
            # Check that the writer prompt contains the direct instructions
            assert "writer" in call_order, "Writer should have been called first"
            assert "Focus on clinical relevance" in writer_prompt_captured or "clinical" in writer_prompt_captured.lower()

    def test_run_editor_with_direct_instructions(self, tmp_path):
        """run_editor passes direct instructions to the LLM."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        reports_dir = tmp_path / "reports"
        doc_root = tmp_path / "docs"
        
        input_dir.mkdir(parents=True)
        output_dir.mkdir(parents=True)
        reports_dir.mkdir(parents=True)
        doc_root.mkdir(parents=True)
        
        (input_dir / "test.txt").write_text("Test content", encoding="utf-8")
        
        call_count = 0
        captured_prompt = ""
        
        def mock_llm(system_prompt, user_prompt):
            nonlocal call_count, captured_prompt
            call_count += 1
            captured_prompt = user_prompt
            return "Mock editor response"
        
        with patch("pipelines.writing.writing._paths") as mock_paths:
            mock_paths.return_value = {
                "doc_root": doc_root,
                "input": input_dir,
                "output": output_dir,
                "reports": reports_dir,
            }
            
            direct_instructions = ["Improve clarity and flow"]
            run_editor(
                direct_instructions=direct_instructions,
                call_llm_fn=mock_llm,
                track=TRACK_TOPIC,
                verbose=False,
            )
            
            assert call_count > 0, "LLM should have been called"
            assert "Improve clarity and flow" in captured_prompt or "clarity" in captured_prompt.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])