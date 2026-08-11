"""Tests for the coding pipeline module - Standard Way: Tests define the specification."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock

import pytest

# Add SOURCE_CODE to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_CODE_DIR = PROJECT_ROOT / "SOURCE_CODE"
sys.path.insert(0, str(SOURCE_CODE_DIR))

# Import the coding module
from pipelines.coding.coding import (
    _project_root,
    _ts,
    _paths,
    _load_md_guidelines,
    _load_code_files,
    _write_file,
    _strip_code_fences,
    _detect_extension,
    _is_truncated,
    _ensure_complete,
    _build_system_prompt,
    _build_builder_user_prompt,
    _build_reviewer_user_prompt,
    _build_tester_user_prompt,
    _reviewer_passed,
    _tester_passed,
    run_builder,
    run_reviewer,
    run_tester,
    parse_direct_instructions,
    MAX_ITERATIONS,
)


class TestCodingHelpers:
    """Test helper functions in coding.py."""

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
        """_paths returns expected directory structure."""
        root = _project_root()
        paths = _paths(root)
        
        expected_keys = ["doc", "input", "output", "reports"]
        for key in expected_keys:
            assert key in paths
            assert isinstance(paths[key], Path)

    def test_load_md_guidelines_empty(self, tmp_path):
        """_load_md_guidelines returns empty string when no guidelines exist."""
        result = _load_md_guidelines(tmp_path)
        assert result == ""

    def test_load_md_guidelines_with_files(self, tmp_path):
        """_load_md_guidelines loads and concatenates .md files."""
        doc_path = tmp_path / "coding"
        doc_path.mkdir()
        
        guideline_file = doc_path / "coding-standards.md"
        guideline_file.write_text("# Coding Standards\n\nWrite clean code.", encoding="utf-8")
        
        result = _load_md_guidelines(doc_path)
        assert "Coding Standards" in result
        assert "Write clean code" in result

    def test_load_code_files_empty(self, tmp_path):
        """_load_code_files returns empty list when no files exist."""
        result = _load_code_files(tmp_path)
        assert result == []

    def test_load_code_files_with_supported_files(self, tmp_path):
        """_load_code_files loads supported code files."""
        (tmp_path / "test1.py").write_text("print('Hello')", encoding="utf-8")
        (tmp_path / "test2.js").write_text("console.log('Hello')", encoding="utf-8")
        (tmp_path / "test3.txt").write_text("Text file", encoding="utf-8")
        (tmp_path / "test4.log").write_text("Log file", encoding="utf-8")  # Should be ignored
        
        result = _load_code_files(tmp_path)
        assert len(result) >= 3
        stems = [f[0] for f in result]
        assert "test1" in stems
        assert "test2" in stems

    def test_write_file(self, tmp_path):
        """_write_file creates file with content."""
        test_file = tmp_path / "test.txt"
        content = "Test content"
        
        _write_file(test_file, content)
        assert test_file.exists()
        assert test_file.read_text(encoding="utf-8") == content

    def test_strip_code_fences_no_fences(self):
        """_strip_code_fences returns text unchanged when no fences present."""
        text = "print('Hello')"
        assert _strip_code_fences(text) == text

    def test_strip_code_fences_with_python_fence(self):
        """_strip_code_fences removes ```python fences."""
        text = "```python\nprint('Hello')\n```"
        expected = "print('Hello')"
        assert _strip_code_fences(text) == expected

    def test_strip_code_fences_with_code_fence(self):
        """_strip_code_fences removes ``` fences."""
        text = "```\nSome code\n```"
        expected = "Some code"
        assert _strip_code_fences(text) == expected

    def test_detect_extension_html(self):
        """_detect_extension detects HTML files."""
        code = "<!DOCTYPE html>\n<html>\n<body>\n</body>\n</html>"
        ext = _detect_extension("test", code)
        assert ext == ".html"

    def test_detect_extension_python(self):
        """_detect_extension detects Python files."""
        code = "def test():\n    return True"
        ext = _detect_extension("test", code)
        assert ext == ".py"

    def test_detect_extension_javascript(self):
        """_detect_extension detects JavaScript files."""
        code = "const x = 1;\nconsole.log(x);"
        ext = _detect_extension("test", code)
        assert ext == ".js"

    def test_detect_extension_css(self):
        """_detect_extension detects CSS files."""
        code = ".selector { color: red; }"
        ext = _detect_extension("test", code)
        assert ext == ".css"

    def test_is_truncated_html(self):
        """_is_truncated detects truncated HTML files."""
        code = "<!DOCTYPE html>\n<html>\n<body>"
        assert _is_truncated(code) is True

    def test_is_truncated_complete_html(self):
        """_is_truncated returns False for complete HTML files."""
        code = "<!DOCTYPE html>\n<html>\n<body>\n</body>\n</html>"
        assert _is_truncated(code) is False

    def test_is_truncated_python_with_trailing_colon(self):
        """_is_truncated detects Python code ending with colon."""
        code = "def test():\n"
        # This ends with a colon, which is a truncation marker
        assert _is_truncated(code) is True

    def test_is_truncated_python_with_operator(self):
        """_is_truncated detects Python code ending with operator."""
        code = "x = "
        assert _is_truncated(code) is True

    def test_is_truncated_python_complete(self):
        """_is_truncated returns False for complete Python code."""
        code = "def test():\n    return True"
        assert _is_truncated(code) is False

    def test_build_system_prompt(self):
        """_build_system_prompt returns a system prompt with guidelines."""
        guidelines = "Test guidelines"
        result = _build_system_prompt(guidelines)
        assert isinstance(result, str)
        assert "You are an expert software engineer" in result
        assert guidelines in result

    def test_build_system_prompt_empty(self):
        """_build_system_prompt works with empty guidelines."""
        result = _build_system_prompt("")
        assert isinstance(result, str)
        assert "You are an expert software engineer" in result

    def test_build_builder_user_prompt_scratch(self):
        """_build_builder_user_prompt handles scratch mode."""
        direct = ["Build a calculator app"]
        code_context = None
        error_feedback = None
        is_scratch = True
        iteration = 1
        
        result = _build_builder_user_prompt(direct, code_context, error_feedback, is_scratch, iteration)
        assert "Direct Task Instructions" in result
        assert "Build a calculator app" in result
        assert "immediately runnable" in result or "scratch" in result

    def test_build_builder_user_prompt_with_context(self):
        """_build_builder_user_prompt includes code context."""
        direct = ["Fix the bug"]
        code_context = "def add(a, b):\n    return a + b"
        error_feedback = "Function missing error handling"
        is_scratch = False
        iteration = 2
        
        result = _build_builder_user_prompt(direct, code_context, error_feedback, is_scratch, iteration)
        assert "Direct Task Instructions" in result
        assert "Fix the bug" in result
        assert "def add(a, b)" in result
        assert "Function missing error handling" in result

    def test_build_reviewer_user_prompt(self):
        """_build_reviewer_user_prompt includes code for review."""
        direct = ["Check for security issues"]
        code_content = "def test():\n    return True"
        stem = "test_file"
        
        result = _build_reviewer_user_prompt(direct, code_content, stem)
        assert "Direct Review Instructions" in result
        assert "Check for security issues" in result
        assert "Code to Review: test_file" in result
        assert "def test()" in result

    def test_build_tester_user_prompt(self):
        """_build_tester_user_prompt includes code for testing."""
        direct = ["Test all functions"]
        code_content = "def add(a, b):\n    return a + b"
        stem = "calculator"
        
        result = _build_tester_user_prompt(direct, code_content, stem)
        assert "Direct Testing Instructions" in result
        assert "Test all functions" in result
        assert "Code to Test: calculator" in result
        assert "def add(a, b)" in result

    def test_reviewer_passed(self):
        """_reviewer_passed detects REVIEW_PASS in response."""
        response = "REVIEW_PASS\nAll good."
        assert _reviewer_passed(response) is True

    def test_reviewer_failed(self):
        """_reviewer_passed detects REVIEW_FAIL in response."""
        response = "REVIEW_FAIL\nFound issues."
        assert _reviewer_passed(response) is False

    def test_tester_passed(self):
        """_tester_passed detects TEST_PASS in response."""
        response = "TEST_PASS\nAll tests passed."
        assert _tester_passed(response) is True

    def test_tester_failed(self):
        """_tester_passed detects TEST_FAIL in response."""
        response = "TEST_FAIL\nTests failed."
        assert _tester_passed(response) is False

    def test_parse_direct_instructions(self):
        """parse_direct_instructions extracts > lines."""
        raw = "> Build a CSV parser\nNormal text\n> Add error handling"
        result = parse_direct_instructions(raw)
        assert len(result) == 2
        assert "Build a CSV parser" in result[0]
        assert "Add error handling" in result[1]

    def test_parse_direct_instructions_empty(self):
        """parse_direct_instructions returns empty list for no instructions."""
        raw = "Normal text without instructions."
        result = parse_direct_instructions(raw)
        assert result == []

    def test_max_iterations(self):
        """MAX_ITERATIONS is defined."""
        assert MAX_ITERATIONS == 3


class TestCodingIntegration:
    """Integration tests for coding pipeline."""

    def test_run_builder_no_files(self, tmp_path):
        """run_builder handles scratch mode when no input files exist."""
        doc_path = tmp_path / "docs" / "coding"
        doc_path.mkdir(parents=True)
        
        with patch("pipelines.coding.coding._paths") as mock_paths:
            mock_paths.return_value = {
                "doc": doc_path,
                "input": tmp_path / "input",
                "output": tmp_path / "output",
                "reports": tmp_path / "reports",
            }
            
            def mock_llm(system_prompt, user_prompt):
                return "print('Hello World')"
            
            run_builder(
                direct_instructions=["Create a hello world program"],
                call_llm_fn=mock_llm,
                verbose=True,
            )
            assert True

    def test_run_reviewer_no_files(self, tmp_path, capsys):
        """run_reviewer handles empty input directory gracefully."""
        doc_path = tmp_path / "docs" / "coding"
        doc_path.mkdir(parents=True)
        
        with patch("pipelines.coding.coding._paths") as mock_paths:
            mock_paths.return_value = {
                "doc": doc_path,
                "input": tmp_path / "input",
                "output": tmp_path / "output",
                "reports": tmp_path / "reports",
            }
            
            def mock_llm(system_prompt, user_prompt):
                return "REVIEW_PASS\nAll good."
            
            run_reviewer(
                direct_instructions=[],
                call_llm_fn=mock_llm,
                verbose=True,
            )
            
            captured = capsys.readouterr()
            assert "No code files" in captured.out or "no code" in captured.out.lower()

    def test_run_tester_no_files(self, tmp_path, capsys):
        """run_tester handles empty input directory gracefully."""
        doc_path = tmp_path / "docs" / "coding"
        doc_path.mkdir(parents=True)
        
        with patch("pipelines.coding.coding._paths") as mock_paths:
            mock_paths.return_value = {
                "doc": doc_path,
                "input": tmp_path / "input",
                "output": tmp_path / "output",
                "reports": tmp_path / "reports",
            }
            
            def mock_llm(system_prompt, user_prompt):
                return "TEST_PASS\nAll tests passed."
            
            run_tester(
                direct_instructions=[],
                call_llm_fn=mock_llm,
                verbose=True,
            )
            
            captured = capsys.readouterr()
            assert "No code files" in captured.out or "no code" in captured.out.lower()


class TestCodingEdgeCases:
    """Edge case tests for coding module."""

    def test_detect_extension_fallback(self):
        """_detect_extension falls back to .py for unknown types."""
        code = "Unknown content"
        ext = _detect_extension("test", code)
        assert ext == ".py"

    def test_load_code_files_with_large_files(self, tmp_path):
        """_load_code_files handles large files gracefully."""
        large_content = "x" * 50000
        (tmp_path / "large.py").write_text(large_content, encoding="utf-8")
        
        result = _load_code_files(tmp_path)
        assert len(result) == 1
        assert result[0][1] == large_content

    def test_ensure_complete_appends_closing_tags(self):
        """_ensure_complete appends missing closing tags for HTML."""
        system_prompt = "Test system prompt"
        
        def mock_llm(system_prompt, user_prompt):
            return "console.log('Hello')"
        
        code = "<!DOCTYPE html>\n<html>\n<body>\n<script>"
        result = _ensure_complete(code, system_prompt, mock_llm, max_continuations=1)
        assert "</html>" in result or "</body>" in result

    def test_ensure_complete_no_change_for_complete_code(self):
        """_ensure_complete leaves complete code unchanged."""
        system_prompt = "Test system prompt"
        
        def mock_llm(system_prompt, user_prompt):
            return ""
        
        code = "def test():\n    return True"
        result = _ensure_complete(code, system_prompt, mock_llm, max_continuations=1)
        assert result == code

    def test_build_reviewer_user_prompt_with_truncation(self):
        """_build_reviewer_user_prompt handles truncated code."""
        direct = ["Review this code"]
        code_content = "def test():\n    "  # Truncated
        stem = "test_file"
        
        result = _build_reviewer_user_prompt(direct, code_content, stem)
        assert "TRUNCATED" in result or "cut off" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])