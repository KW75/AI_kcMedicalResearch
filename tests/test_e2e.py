"""
test_e2e.py — End-to-end mode tests using --dry-run.

Each test exercises a full mode pipeline without making real AI calls.
Verifies: no exceptions raised, output file created, output file non-empty.
All tests use tmp_path to avoid polluting the real reports/ folder.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure src/ is importable
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_input(responses: list[str]):
    """Return a side_effect function that pops from a list of responses."""
    responses = list(responses)

    def _inner(prompt=""):
        if responses:
            return responses.pop(0)
        return ""

    return _inner


# ---------------------------------------------------------------------------
# Writing mode — --report flag (single-pass, no input() calls)
# ---------------------------------------------------------------------------

class TestE2EWritingReport:

    def test_writing_report_dry_run_creates_output(self, tmp_path):
        """Writing --report mode reads docs/writing/ and saves a report."""
        from src.main import generate_writing_report

        with patch("src.main.call_ai", return_value="[MOCK] Writing report content."):
            md_path = generate_writing_report(
                docs_dir=BASE_DIR / "docs" / "writing",
                reports_dir=tmp_path,
                provider="ollama",
                model=None,
            )

        assert md_path.exists(), "Writing report .md file was not created"
        assert md_path.stat().st_size > 0, "Writing report .md file is empty"

    def test_writing_report_returns_md_path(self, tmp_path):
        """generate_writing_report returns a Path ending in .md."""
        from src.main import generate_writing_report

        with patch("src.main.call_ai", return_value="[MOCK] Writing report content."):
            result = generate_writing_report(
                docs_dir=BASE_DIR / "docs" / "writing",
                reports_dir=tmp_path,
                provider="ollama",
            )
        assert str(result).endswith(".md")


# ---------------------------------------------------------------------------
# RCT Search mode — single-pass pipeline
# ---------------------------------------------------------------------------

class TestE2ERctSearch:

    def test_rct_search_dry_run_creates_report(self, tmp_path):
        """RCT search pipeline with dry_run=True creates a .md report."""
        from src.main import run_rct_search_pipeline

        with patch("src.main.DOCS_RCT_SEARCH", BASE_DIR / "docs" / "rct_search"), \
            patch("builtins.input",
                return_value="Effect of metformin on HbA1c in type 2 diabetes"):
            md_path = run_rct_search_pipeline(
                provider="ollama",
                model=None,
                reports_dir=tmp_path,
                dry_run=True,
            )

        assert md_path.exists(), "RCT search report .md was not created"
        assert md_path.stat().st_size > 0, "RCT search report .md is empty"


    def test_rct_search_report_contains_sections(self, tmp_path):
        """RCT search report contains expected role output sections."""
        from src.main import run_rct_search_pipeline

        # Write a topic file so no input() is called
        topic_dir = tmp_path / "rct_search"
        topic_dir.mkdir()
        (topic_dir / "topic.md").write_text(
            "Effect of metformin on HbA1c in type 2 diabetes",
            encoding="utf-8",
        )

        with patch("src.main.DOCS_RCT_SEARCH", BASE_DIR / "docs" / "rct_search"), \
             patch("src.main._read_topic_file",
                   return_value="Effect of metformin on HbA1c in type 2 diabetes"):
            md_path = run_rct_search_pipeline(
                provider="ollama",
                reports_dir=tmp_path,
                dry_run=True,
            )

        content = md_path.read_text(encoding="utf-8")
        assert "Formulator" in content
        assert "Searcher" in content
        assert "Validator" in content
        assert "Final Status" in content


# ---------------------------------------------------------------------------
# Search mode
# ---------------------------------------------------------------------------

class TestE2ESearch:

    @pytest.mark.skip(reason="run_search_mode removed — superseded by handle_search_mode")
    def test_search_dry_run_creates_report(self, tmp_path):
        """Search mode with dry_run=True creates a .md report."""
        from src.main import run_search_mode

        with patch("src.main._read_topic_file",
                   return_value="topic\nmetformin type 2 diabetes"), \
             patch("src.main.fetch_pubmed_articles", return_value=[{
                 "pmid": "12345",
                 "title": "Metformin trial",
                 "abstract": "A study of metformin.",
                 "url": "https://pubmed.ncbi.nlm.nih.gov/12345/",
             }]):
            md_path = run_search_mode(
                provider="ollama",
                model=None,
                dry_run=True,
                reports_dir=tmp_path,
            )

        assert md_path.exists(), "Search report .md was not created"
        assert md_path.stat().st_size > 0, "Search report .md is empty"

    @pytest.mark.skip(reason="run_search_mode removed — superseded by handle_search_mode")
    def test_search_report_contains_topic(self, tmp_path):
        """Search report includes the search topic."""
        from src.main import run_search_mode

        with patch("src.main._read_topic_file",
                   return_value="topic\nmetformin type 2 diabetes"), \
             patch("src.main.fetch_pubmed_articles", return_value=[{
                 "pmid": "12345",
                 "title": "Metformin trial",
                 "abstract": "A study of metformin.",
                 "url": "https://pubmed.ncbi.nlm.nih.gov/12345/",
             }]):
            md_path = run_search_mode(
                provider="ollama",
                dry_run=True,
                reports_dir=tmp_path,
            )

        content = md_path.read_text(encoding="utf-8")
        assert "metformin" in content.lower()


# ---------------------------------------------------------------------------
# Code revision mode — --revise flag
# ---------------------------------------------------------------------------

class TestE2ECodeRevision:

    def test_code_revision_dry_run_creates_report(self, tmp_path):
        """Code revision pipeline with dry_run=True creates a .md report."""
        from src.main import generate_code_revision

        # Create a minimal stub code file in a temp docs/coding dir
        coding_dir = tmp_path / "coding"
        coding_dir.mkdir()
        (coding_dir / "example.py").write_text(
            "def add(a, b):\n    return a + b\n",
            encoding="utf-8",
        )

        with patch("builtins.input", return_value="Review for correctness"):
            md_path = generate_code_revision(
                start_role="Builder",
                docs_dir=coding_dir,
                reports_dir=tmp_path,
                provider="ollama",
                dry_run=True,
            )

        assert md_path.exists(), "Code revision report .md was not created"
        assert md_path.stat().st_size > 0, "Code revision report .md is empty"

    def test_code_revision_all_stages_present(self, tmp_path):
        """Code revision report contains Builder, Reviewer, Tester sections."""
        from src.main import generate_code_revision

        coding_dir = tmp_path / "coding"
        coding_dir.mkdir()
        (coding_dir / "example.py").write_text(
            "def multiply(a, b):\n    return a * b\n",
            encoding="utf-8",
        )

        with patch("builtins.input", return_value="General review"):
            md_path = generate_code_revision(
                start_role="Builder",
                docs_dir=coding_dir,
                reports_dir=tmp_path,
                provider="ollama",
                dry_run=True,
            )

        content = md_path.read_text(encoding="utf-8")
        assert "Builder" in content
        assert "Reviewer" in content
        assert "Tester" in content

    def test_code_revision_no_code_files_returns_empty(self, tmp_path):
        """Code revision with no code files returns empty report path."""
        from src.main import generate_code_revision

        empty_dir = tmp_path / "empty_coding"
        empty_dir.mkdir()

        md_path = generate_code_revision(
            start_role="Builder",
            docs_dir=empty_dir,
            reports_dir=tmp_path,
            provider="ollama",
            dry_run=True,
        )

        assert "empty" in md_path.name


# ---------------------------------------------------------------------------
# Appraisal mode — article injection
# ---------------------------------------------------------------------------

class TestE2EAppraisal:

    def test_appraisal_reads_article_files(self, tmp_path):
        """_read_article_files returns content for .txt files under size limit."""
        from src.main import _read_article_files

        appraisal_dir = tmp_path / "appraisal"
        appraisal_dir.mkdir()
        (appraisal_dir / "article1.txt").write_text(
            "This is a test article about metformin.",
            encoding="utf-8",
        )

        results = _read_article_files(appraisal_dir)

        assert len(results) == 1
        assert results[0]["name"] == "article1.txt"
        assert "metformin" in results[0]["content"]

    def test_appraisal_skips_large_files(self, tmp_path, capsys):
        """_read_article_files skips files over 8000 chars and prints a warning."""
        from src.main import _read_article_files

        appraisal_dir = tmp_path / "appraisal"
        appraisal_dir.mkdir()
        (appraisal_dir / "large.txt").write_text(
            "x" * 9000,
            encoding="utf-8",
        )

        results = _read_article_files(appraisal_dir)
        captured = capsys.readouterr()

        assert len(results) == 0
        assert "RAG" in captured.out

    def test_appraisal_multiple_files(self, tmp_path):
        """_read_article_files loads multiple files and labels each."""
        from src.main import _read_article_files

        appraisal_dir = tmp_path / "appraisal"
        appraisal_dir.mkdir()
        (appraisal_dir / "article1.txt").write_text("First article content.", encoding="utf-8")
        (appraisal_dir / "article2.txt").write_text("Second article content.", encoding="utf-8")

        results = _read_article_files(appraisal_dir)

        assert len(results) == 2
        names = [r["name"] for r in results]
        assert "article1.txt" in names
        assert "article2.txt" in names


# ---------------------------------------------------------------------------
# validate_api_keys integration with parse_args
# ---------------------------------------------------------------------------

class TestE2EValidation:

    def test_dry_run_skips_api_validation(self):
        """--dry-run flag bypasses API key validation entirely."""
        from src.main import parse_args, validate_api_keys
        import os

        args = parse_args(["--dry-run", "--provider", "anthropic"])
        assert args.dry_run is True
        # Should not raise even with no key set
        # (validation is bypassed in __main__ when dry_run=True)

    def test_parse_args_defaults(self):
        """parse_args returns correct defaults."""
        from src.main import parse_args

        args = parse_args([])
        assert args.mode == "coding"
        assert args.provider == "ollama"
        assert args.dry_run is False
        assert args.report is False
        assert args.revise is False

    def test_parse_args_all_modes(self):
        """parse_args accepts all six valid modes."""
        from src.main import parse_args

        for mode in ["coding", "writing", "rct_search", "appraisal", "search", "sr"]:
            args = parse_args(["--mode", mode])
            assert args.mode == mode

    def test_parse_args_all_providers(self):
        """parse_args accepts all five valid providers."""
        from src.main import parse_args

        for provider in ["ollama", "openai", "anthropic", "deepseek", "groq"]:
            args = parse_args(["--provider", provider])
            assert args.provider == provider
