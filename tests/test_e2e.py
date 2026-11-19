"""
test_e2e.py ??End-to-end mode tests using --dry-run.

Each test exercises a full mode pipeline without making real AI calls.
Verifies: no exceptions raised, output file created, output file non-empty.
All tests use tmp_path to avoid polluting the real reports/ folder.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure SOURCE_CODE is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_CODE_DIR = PROJECT_ROOT / "SOURCE_CODE"
sys.path.insert(0, str(SOURCE_CODE_DIR))
sys.path.insert(0, str(PROJECT_ROOT))

# Now import from SOURCE_CODE
from SOURCE_CODE.main import (
    generate_writing_report,
    run_rct_search_pipeline,
    generate_code_revision,
    parse_args,
    validate_api_keys,
)


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
# Writing mode ??--report flag (single-pass, no input() calls)
# ---------------------------------------------------------------------------

class TestE2EWritingReport:

    @staticmethod
    def _run(tmp_path, **kwargs):
        """Input and output both point into tmp_path, so the test never reads
        input/writing/ or docs/writing/ and never writes output/writing/
        (Session 48: OUTPUT_WRITING is the only output folder)."""
        in_dir = tmp_path / "input"
        in_dir.mkdir()
        (in_dir / "note.txt").write_text("Short test document.", encoding="utf-8")
        out_dir = tmp_path / "output"
        with patch("SOURCE_CODE.main.call_ai",
                   return_value="[MOCK] Writing report content."), \
             patch("SOURCE_CODE.main.OUTPUT_WRITING", out_dir):
            md_path = generate_writing_report(
                docs_dir=tmp_path / "docs",
                provider="ollama",
                input_dir=in_dir,
                **kwargs,
            )
        return md_path, out_dir

    def test_writing_report_dry_run_creates_output(self, tmp_path):
        """Writing --report mode reads the input folder and saves a report."""
        md_path, _ = self._run(tmp_path, model=None)
        assert md_path.exists(), "Writing report .md file was not created"
        assert md_path.stat().st_size > 0, "Writing report .md file is empty"

    def test_writing_report_returns_md_path(self, tmp_path):
        """generate_writing_report returns a Path ending in .md."""
        result, _ = self._run(tmp_path)
        assert str(result).endswith(".md")

    def test_writing_report_stays_in_tmp_path(self, tmp_path):
        """The report is saved under tmp_path; real output/writing/ is untouched."""
        real = PROJECT_ROOT / "output" / "writing"
        before = set(real.glob("writing_report_*")) if real.exists() else set()
        md_path, out_dir = self._run(tmp_path)
        after = set(real.glob("writing_report_*")) if real.exists() else set()
        assert md_path.parent == out_dir
        assert after == before


# ---------------------------------------------------------------------------
# RCT Search mode ??single-pass pipeline
# ---------------------------------------------------------------------------

class TestE2ERctSearch:

    def test_rct_search_dry_run_creates_report(self, tmp_path):
        """RCT search pipeline with dry_run=True creates a .md report."""
        with patch("builtins.input", return_value="Effect of metformin on HbA1c in type 2 diabetes"):
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
        # Write a topic file so no input() is called
        topic_dir = tmp_path / "rct_search"
        topic_dir.mkdir()
        (topic_dir / "topic.md").write_text(
            "Effect of metformin on HbA1c in type 2 diabetes",
            encoding="utf-8",
        )

        with patch("builtins.input", return_value="0"):
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
# Code revision mode ??--revise flag
# ---------------------------------------------------------------------------

class TestE2ECodeRevision:

    def test_code_revision_dry_run_creates_report(self, tmp_path):
        """Code revision pipeline with dry_run=True creates a .md report."""
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
# validate_api_keys integration with parse_args
# ---------------------------------------------------------------------------

class TestE2EValidation:

    def test_dry_run_skips_api_validation(self):
        """--dry-run flag bypasses API key validation entirely."""
        args = parse_args(["--dry-run", "--provider", "anthropic"])
        assert args.dry_run is True
        # Should not raise even with no key set
        # (validation is bypassed in __main__ when dry_run=True)

    def test_parse_args_defaults(self):
        """parse_args returns correct defaults.

        The provider default comes from .env (DEFAULT_PROVIDER), so it is
        compared with the module's own value, not a hard-coded name.
        """
        import sys
        args = parse_args([])
        assert args.mode == "coding"
        assert args.provider == sys.modules[parse_args.__module__].DEFAULT_PROVIDER
        assert args.dry_run is False
        assert args.report is False
        assert args.revise is False

    def test_parse_args_all_modes(self):
        """parse_args accepts all six valid modes."""
        for mode in ["coding", "writing", "rct_search", "appraisal", "search", "sr"]:
            args = parse_args(["--mode", mode])
            assert args.mode == mode

    def test_parse_args_all_providers(self):
        """parse_args accepts all valid providers."""
        for provider in ["ollama", "openai", "anthropic", "deepseek", "groq", "qwen"]:
            args = parse_args(["--provider", provider])
            assert args.provider == provider
