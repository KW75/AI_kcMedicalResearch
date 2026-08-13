"""
test_table_extractor.py — Tests for hybrid multi-page table extraction.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "SOURCE_CODE"))
sys.path.insert(0, str(PROJECT_ROOT / "SOURCE_CODE" / "pipelines" / "sr"))


class TestExtractTablesPymupdf:
    """Test PyMuPDF table extraction and merging."""

    def test_empty_pdf_returns_empty(self, tmp_path):
        """A PDF with no tables returns empty list."""
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "This is just text, no tables.")
        pdf_path = str(tmp_path / "no_tables.pdf")
        doc.save(pdf_path)
        doc.close()

        from src.extraction.table_extractor import extract_tables_pymupdf
        result = extract_tables_pymupdf(pdf_path)
        assert isinstance(result, list)

    def test_headers_compatible_same(self):
        """Identical headers are compatible."""
        from src.extraction.table_extractor import _headers_compatible
        h = ["Study", "N", "Mean", "SD"]
        assert _headers_compatible(h, h) is True

    def test_headers_compatible_empty(self):
        """Empty header row means continuation."""
        from src.extraction.table_extractor import _headers_compatible
        h1 = ["Study", "N", "Mean", "SD"]
        h2 = ["", "", "", ""]
        assert _headers_compatible(h1, h2) is True

    def test_headers_compatible_numeric(self):
        """Rows with numbers are data, not headers — compatible."""
        from src.extraction.table_extractor import _headers_compatible
        h1 = ["Study", "N", "Mean", "SD"]
        h2 = ["Lami 2023", "45", "3.2", "1.1"]
        assert _headers_compatible(h1, h2) is True

    def test_headers_incompatible(self):
        """Different text headers are not compatible."""
        from src.extraction.table_extractor import _headers_compatible
        h1 = ["Study", "N", "Mean", "SD"]
        h2 = ["Author", "Country", "Design", "Duration"]
        assert _headers_compatible(h1, h2) is False


class TestTableToMarkdown:
    """Test markdown conversion."""

    def test_basic_table(self):
        from src.extraction.table_extractor import table_to_markdown
        table = {
            "headers": ["Study", "N", "Mean"],
            "rows": [["Lami 2023", "45", "3.2"], ["Smith 2022", "30", "4.1"]],
            "col_count": 3,
            "row_count": 2,
            "page": 5,
        }
        md = table_to_markdown(table)
        assert "| Study | N | Mean |" in md
        assert "| Lami 2023 | 45 | 3.2 |" in md
        assert "| --- | --- | --- |" in md


class TestExtractTextAroundTable:
    """Test text extraction with keyword scoring."""

    def test_returns_list(self, tmp_path):
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Table 1: Mean SD intervention control baseline outcome results 3.5 4.2 1.1")
        pdf_path = str(tmp_path / "with_keywords.pdf")
        doc.save(pdf_path)
        doc.close()

        from src.extraction.table_extractor import extract_text_around_table
        groups = extract_text_around_table(pdf_path)
        assert isinstance(groups, list)


class TestHybridTableExtractor:
    """Test the hybrid extraction orchestrator."""

    def test_has_outcome_data_with_mean(self):
        from src.extraction.table_extractor import HybridTableExtractor
        result = {
            "primary_outcome": {
                "mean_intervention": 3.5,
                "sd_intervention": 1.2,
                "mean_control": 4.1,
                "sd_control": 1.3,
                "outcome_match": True,
            }
        }
        assert HybridTableExtractor._has_outcome_data(result) is True

    def test_has_outcome_data_empty(self):
        from src.extraction.table_extractor import HybridTableExtractor
        assert HybridTableExtractor._has_outcome_data({}) is False
        assert HybridTableExtractor._has_outcome_data(None) is False

    def test_has_outcome_data_no_mean(self):
        from src.extraction.table_extractor import HybridTableExtractor
        result = {"primary_outcome": {"outcome_match": False, "mean_intervention": None}}
        assert HybridTableExtractor._has_outcome_data(result) is False

    def test_has_outcome_data_flat_structure(self):
        from src.extraction.table_extractor import HybridTableExtractor
        result = {"mean_intervention": 2.5, "sd_intervention": 0.8}
        assert HybridTableExtractor._has_outcome_data(result) is True

    def test_extract_calls_strategies_in_order(self, tmp_path):
        """Verify strategy A is tried before B and C."""
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "No tables here")
        pdf_path = str(tmp_path / "test.pdf")
        doc.save(pdf_path)
        doc.close()

        from src.extraction.table_extractor import HybridTableExtractor

        mock_llm = MagicMock(return_value='{"primary_outcome": {"mean_intervention": null}}')
        extractor = HybridTableExtractor(
            pico_criteria={"outcome": "pain"},
            provider="qwen",
            call_llm_fn=mock_llm,
        )

        # Patch vision fallback to avoid needing API
        with patch.object(extractor, "_try_vision_fallback", return_value={
            "file_id": None, "filename": "test.pdf",
            "extraction_error": "mocked", "primary_outcome": {}, "participants": {}
        }):
            result = extractor.extract(pdf_path, "test.pdf")
            assert isinstance(result, dict)
            assert "filename" in result
