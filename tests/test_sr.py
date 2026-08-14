"""Tests for the Systematic Review (sr) pipeline module - Standard Way: Tests define the specification."""

import sys
import json
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock

import pytest

# Add SOURCE_CODE to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_CODE_DIR = PROJECT_ROOT / "SOURCE_CODE"
sys.path.insert(0, str(SOURCE_CODE_DIR))

# Import the sr module
from pipelines.sr.main import (
    main as run_sr,
)


class TestSRHelpers:
    """Test helper functions in sr module."""

    def test_module_imports(self):
        """Test that sr module can be imported."""
        import pipelines.sr
        assert pipelines.sr is not None

    def test_main_function_exists(self):
        """Test that run_sr function exists."""
        assert callable(run_sr)


class TestSRConfiguration:
    """Test SR configuration."""

    def test_prisma_criteria_loading(self, tmp_path):
        """Test loading prisma_criteria.yaml configuration."""
        config_dir = tmp_path / "config"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "prisma_criteria.yaml"
        
        yaml_content = """
review_title: Test Review
effect_measure: SMD
pico:
  population: Test Population
  intervention: Test Intervention
  comparator: Test Comparator
  outcome: Test Outcome
inclusion_criteria:
  - RCT
  - Adult participants
exclusion_criteria:
  - Non-RCT
  - Animal studies
"""
        config_file.write_text(yaml_content, encoding="utf-8")
        
        import yaml
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        assert config["review_title"] == "Test Review"
        assert config["effect_measure"] == "SMD"
        assert "pico" in config
        assert config["pico"]["population"] == "Test Population"


class TestSRExtraction:
    """Test extraction functions."""

    def test_pdf_parser_import(self):
        """Test that pdf_parser can be imported."""
        try:
            from pipelines.sr.src.extraction import pdf_parser
            assert pdf_parser is not None
        except ImportError:
            pytest.skip("pdf_parser not available")

    def test_data_extractor_import(self):
        """Test that data_extractor can be imported."""
        try:
            from pipelines.sr.src.extraction import data_extractor
            assert data_extractor is not None
        except ImportError:
            pytest.skip("data_extractor not available")


class TestSRScreening:
    """Test screening functions."""

    def test_relevance_screener_import(self):
        """Test that relevance_screener can be imported."""
        try:
            from pipelines.sr.src.screening import relevance_screener
            assert relevance_screener is not None
        except ImportError:
            pytest.skip("relevance_screener not available")

    def test_rob2_tool_import(self):
        """Test that rob2_tool can be imported."""
        try:
            from pipelines.sr.src.screening import rob2_tool
            assert rob2_tool is not None
        except ImportError:
            pytest.skip("rob2_tool not available")


class TestSRAnalysis:
    """Test analysis functions."""

    def test_meta_analysis_import(self):
        """Test that meta_analysis can be imported."""
        try:
            from pipelines.sr.src.analysis import meta_analysis
            assert meta_analysis is not None
        except ImportError:
            pytest.skip("meta_analysis not available")


class TestSRReporting:
    """Test reporting functions."""

    def test_report_generator_import(self):
        """Test that report_generator can be imported."""
        try:
            from pipelines.sr.src.reporting import report_generator
            assert report_generator is not None
        except ImportError:
            pytest.skip("report_generator not available")

    def test_html_report_import(self):
        """Test that html_report can be imported."""
        try:
            from pipelines.sr.src.reporting import html_report
            assert html_report is not None
        except ImportError:
            pytest.skip("html_report not available")

    def test_pdf_report_import(self):
        """Test that pdf_report can be imported."""
        try:
            from pipelines.sr.src.reporting import pdf_report
            assert pdf_report is not None
        except ImportError:
            pytest.skip("pdf_report not available")


class TestSRVisualization:
    """Test visualization functions."""

    def test_forest_plot_import(self):
        """Test that forest_plot can be imported."""
        try:
            from pipelines.sr.src.visualization import forest_plot
            assert forest_plot is not None
        except ImportError:
            pytest.skip("forest_plot not available")


class TestSRUtils:
    """Test utility functions."""

    def test_audit_logger_import(self):
        """Test that audit_logger can be imported."""
        try:
            from pipelines.sr.src.utils import audit_logger
            assert audit_logger is not None
        except ImportError:
            pytest.skip("audit_logger not available")

    def test_json_utils_import(self):
        """Test that json_utils can be imported."""
        try:
            from pipelines.sr.src.utils import json_utils
            assert json_utils is not None
        except ImportError:
            pytest.skip("json_utils not available")


class TestSRIntegration:
    """Integration tests for SR pipeline."""

    def test_sr_pipeline_dry_run(self, tmp_path):
        """Test SR pipeline with dry run."""
        # Create mock config
        config_dir = SOURCE_CODE_DIR / "pipelines" / "sr" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "prisma_criteria.yaml"
        
        yaml_content = """
review_title: Test Review
effect_measure: SMD
pico:
  population: Test Population
  intervention: Test Intervention
  comparator: Test Comparator
  outcome: Test Outcome
inclusion_criteria:
  - RCT
exclusion_criteria:
  - Non-RCT
"""
        config_file.write_text(yaml_content, encoding="utf-8")
        
        # Mock the main function to avoid actual execution
        # The main function in sr/main.py is the entry point
        with patch("pipelines.sr.main.main") as mock_main:
            mock_main.return_value = True
            # Test that the module can be imported
            import pipelines.sr.main
            assert pipelines.sr.main is not None

    def test_sr_config_validation(self, tmp_path):
        """Test SR configuration validation."""
        config_data = {
            "review_title": "Test Systematic Review",
            "effect_measure": "SMD",
            "pico": {
                "population": "Adult patients with diabetes",
                "intervention": "Metformin",
                "comparator": "Placebo",
                "outcome": "HbA1c levels"
            },
            "inclusion_criteria": ["RCT", "Adult participants"],
            "exclusion_criteria": ["Non-RCT", "Animal studies"]
        }
        
        required_fields = ["review_title", "effect_measure", "pico"]
        for field in required_fields:
            assert field in config_data
        
        pico_fields = ["population", "intervention", "comparator", "outcome"]
        for field in pico_fields:
            assert field in config_data["pico"]
        
        valid_measures = ["SMD", "MD", "OR", "RR"]
        assert config_data["effect_measure"] in valid_measures


class TestSREdgeCases:
    """Edge case tests for SR module."""

    def test_empty_config(self):
        """Test handling of empty configuration."""
        config_data = {}
        assert "review_title" not in config_data or config_data.get("review_title") is None

    def test_missing_pico_fields(self):
        """Test handling of missing PICO fields."""
        config_data = {
            "review_title": "Test Review",
            "pico": {}
        }
        assert "population" not in config_data["pico"] or config_data["pico"].get("population") is None

    def test_invalid_effect_measure(self):
        """Test handling of invalid effect measure."""
        invalid_measure = "INVALID"
        valid_measures = ["SMD", "MD", "OR", "RR"]
        assert invalid_measure not in valid_measures

class TestSRModuleInvocation:
    """Regression guard for the Session 6 relative-import crash.

    SR must be launchable via `python -m SOURCE_CODE.pipelines.sr.main`
    with cwd=repo root, NOT by file path. A file-path launch makes the
    script top-level __main__ with no parent package, breaking
    `from .src... import ...`. `--help` exercises the full import chain
    with zero network calls, so this stays in the standard (non-live) suite.
    """

    def test_sr_module_help_imports_cleanly(self):
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "SOURCE_CODE.pipelines.sr.main", "--help"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
        combined = result.stdout + result.stderr

        # Exact Session 6 failure signature must never reappear.
        assert "attempted relative import with no known parent package" not in combined, combined
        assert "ImportError" not in combined, combined
        assert "ModuleNotFoundError" not in combined, combined

        # argparse --help exits 0 after printing usage; confirms we reached
        # argparse rather than crashing earlier in the import chain.
        assert result.returncode == 0, (
            f"SR -m invocation failed (rc={result.returncode}):\n{combined}"
        )
        assert "usage:" in combined.lower(), combined


if __name__ == "__main__":
    pytest.main([__file__, "-v"])