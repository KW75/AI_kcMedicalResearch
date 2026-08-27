"""Tests for the appraisal pipeline module."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add SOURCE_CODE to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_CODE_DIR = PROJECT_ROOT / "SOURCE_CODE"
sys.path.insert(0, str(SOURCE_CODE_DIR))

from pipelines.appraisal.appraisal import (
    _project_root,
    _ts,
    _paths,
    _load_guidelines,
    _load_input_files,
    _write_text,
    _strip_fences,
    _system_prompt,
    _appraiser_user_prompt,
    _write_process_log,
    _write_session_summary,
    run_appraisal,
    parse_direct_instructions,
)


class TestAppraisalHelpers:
    """Test helper functions in appraisal.py."""

    def test_project_root(self):
        """_project_root returns a Path object."""
        root = _project_root()
        assert isinstance(root, Path)
        assert root.exists()

    def test_ts(self):
        """_ts returns a timestamp string."""
        ts = _ts()
        assert isinstance(ts, str)
        assert len(ts) == 15  # YYYYMMDD_HHMMSS

    def test_paths(self):
        """_paths returns expected directory structure."""
        root = _project_root()
        paths = _paths(root)
        
        # Original expectation: "doc_root" key
        expected_keys = ["doc_root", "input", "output", "reports"]
        for key in expected_keys:
            assert key in paths
            assert isinstance(paths[key], Path)

    def test_load_guidelines_empty(self, tmp_path):
        """_load_guidelines returns empty string when no guidelines exist."""
        result = _load_guidelines(tmp_path)
        assert result == ""

    def test_load_guidelines_with_files(self, tmp_path):
        """_load_guidelines loads and concatenates .md files."""
        guideline_file = tmp_path / "test-guide.md"
        guideline_file.write_text("# Test Guideline\n\nThis is a test.", encoding="utf-8")
        
        result = _load_guidelines(tmp_path)
        assert "Test Guideline" in result
        assert "This is a test" in result

    def test_load_input_files_empty(self, tmp_path):
        """_load_input_files returns empty list when no files exist."""
        result = _load_input_files(tmp_path)
        assert result == []

    def test_load_input_files_with_supported_files(self, tmp_path):
        """_load_input_files loads supported file types."""
        (tmp_path / "test1.txt").write_text("Text file content", encoding="utf-8")
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

    def test_strip_fences_with_python_fence(self):
        """_strip_fences removes ```python fences."""
        text = "```python\nprint('Hello')\n```"
        expected = "print('Hello')"
        assert _strip_fences(text) == expected

    def test_strip_fences_with_code_fence(self):
        """_strip_fences removes ``` fences."""
        text = "```\nSome code\n```"
        expected = "Some code"
        assert _strip_fences(text) == expected

    def test_system_prompt(self):
        """_system_prompt returns a system prompt string."""
        guidelines = "Test guidelines"
        result = _system_prompt(guidelines)
        assert isinstance(result, str)
        # Original expectation: "medical research appraisal expert"
        assert "medical research appraisal expert" in result
        assert guidelines in result

    def test_system_prompt_empty(self):
        """_system_prompt works with empty guidelines."""
        result = _system_prompt("")
        assert isinstance(result, str)
        assert "medical research appraisal expert" in result

    def test_appraiser_user_prompt_with_direct_instructions(self):
        """_appraiser_user_prompt includes direct instructions."""
        direct = ["Test instruction 1", "Test instruction 2"]
        content = "Article content"
        stem = "test_article"
        
        result = _appraiser_user_prompt(direct, content, stem)
        # Original expectation: "DIRECT TASK INSTRUCTIONS"
        assert "DIRECT TASK INSTRUCTIONS" in result
        assert "Test instruction 1" in result
        assert "Test instruction 2" in result
        assert stem in result

    def test_appraiser_user_prompt_without_instructions(self):
        """_appraiser_user_prompt works without direct instructions."""
        direct = []
        content = "Article content"
        stem = "test_article"
        
        result = _appraiser_user_prompt(direct, content, stem)
        assert "DIRECT TASK INSTRUCTIONS" not in result
        assert "Article content" in result
        assert stem in result

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


class TestAppraisalIntegration:
    """Integration tests for appraisal pipeline."""

    def test_run_appraisal_no_files(self, tmp_path, capsys):
        """run_appraisal handles empty input directory gracefully."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        reports_dir = tmp_path / "reports"
        docs_dir = tmp_path / "docs"
        
        input_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)
        reports_dir.mkdir(parents=True, exist_ok=True)
        docs_dir.mkdir(parents=True, exist_ok=True)
        
        with patch("pipelines.appraisal.appraisal._paths") as mock_paths:
            # Original expectation: "doc_root" key
            mock_paths.return_value = {
                "doc_root": docs_dir,
                "input": input_dir,
                "output": output_dir,
                "reports": reports_dir,
            }
            
            def mock_llm(system_prompt, user_prompt):
                return "Mock appraisal response"
            
            run_appraisal(
                direct_instructions=[],
                call_llm_fn=mock_llm,
                verbose=True,
            )
            
            captured = capsys.readouterr()
            assert "No files" in captured.out or "no files" in captured.out.lower()

    def test_run_appraisal_with_files(self, tmp_path):
        """run_appraisal processes files and creates outputs."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        reports_dir = tmp_path / "reports"
        docs_dir = tmp_path / "docs"
        
        input_dir.mkdir(parents=True)
        output_dir.mkdir(parents=True)
        reports_dir.mkdir(parents=True)
        docs_dir.mkdir(parents=True)
        
        (input_dir / "test_article.txt").write_text(
            "This is a test article for appraisal.\n\n"
            "It contains multiple paragraphs of content.",
            encoding="utf-8"
        )
        
        (docs_dir / "appraisal-guide.md").write_text(
            "# Appraisal Guide\n\nThis is the appraisal guide.",
            encoding="utf-8"
        )
        
        with patch("pipelines.appraisal.appraisal._paths") as mock_paths:
            # Original expectation: "doc_root" key
            mock_paths.return_value = {
                "doc_root": docs_dir,
                "input": input_dir,
                "output": output_dir,
                "reports": reports_dir,
            }
            
            def mock_llm(system_prompt, user_prompt):
                return "Mock appraisal response with detailed analysis."
            
            run_appraisal(
                direct_instructions=[],
                call_llm_fn=mock_llm,
                verbose=False,
            )
            
            output_files = list(output_dir.glob("*.md"))
            assert len(output_files) > 0, "Output files should be created"
            
            report_files = list(reports_dir.glob("*.md"))
            assert len(report_files) > 0, "Report files should be created"


class TestAppraisalEdgeCases:
    """Edge case tests for appraisal module."""

    def test_load_input_files_with_large_files(self, tmp_path):
        """_load_input_files handles large files (>8000 chars)."""
        large_content = "x" * 10000
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

    def test_run_appraisal_with_direct_instructions(self, tmp_path):
        """run_appraisal passes direct instructions to the LLM."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        reports_dir = tmp_path / "reports"
        docs_dir = tmp_path / "docs"
        
        input_dir.mkdir(parents=True)
        output_dir.mkdir(parents=True)
        reports_dir.mkdir(parents=True)
        docs_dir.mkdir(parents=True)
        
        (input_dir / "test.txt").write_text("Test article content", encoding="utf-8")
        
        call_count = 0
        captured_prompt = ""
        
        def mock_llm(system_prompt, user_prompt):
            nonlocal call_count, captured_prompt
            call_count += 1
            captured_prompt = user_prompt
            return "Mock response"
        
        with patch("pipelines.appraisal.appraisal._paths") as mock_paths:
            # Original expectation: "doc_root" key
            mock_paths.return_value = {
                "doc_root": docs_dir,
                "input": input_dir,
                "output": output_dir,
                "reports": reports_dir,
            }
            
            direct_instructions = ["Focus on methodology", "Check for bias"]
            run_appraisal(
                direct_instructions=direct_instructions,
                call_llm_fn=mock_llm,
                verbose=False,
            )
            
            assert call_count > 0, "LLM should have been called"
            assert "Focus on methodology" in captured_prompt or "methodology" in captured_prompt.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])