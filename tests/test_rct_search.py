"""Tests for the RCT Search pipeline module - Standard Way: Tests define the specification."""

import sys
import json
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock

import pytest

# Add SOURCE_CODE to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_CODE_DIR = PROJECT_ROOT / "SOURCE_CODE"
sys.path.insert(0, str(SOURCE_CODE_DIR))

# Import the rct_search module
from pipelines.rct_search.rct_search import (
    role_color,
    _read_topic_file,
    _clean_pico_term,
    fetch_pubmed_articles,
    fetch_europepmc_articles,
    merge_search_results,
    call_ai,
    run_rct_search_pipeline,
    RESET,
    ACCENT,
    DIM,
)


class TestRCTSearchHelpers:
    """Test helper functions in rct_search.py."""

    def test_role_color_returns_color(self):
        """role_color returns appropriate color for each role."""
        formulator = role_color("Formulator")
        searcher = role_color("Searcher")
        validator = role_color("Validator")
        unknown = role_color("Unknown")

        assert isinstance(formulator, str)
        assert isinstance(searcher, str)
        assert isinstance(validator, str)
        assert isinstance(unknown, str)
        assert unknown == ACCENT

    def test_read_topic_file_exists(self, tmp_path):
        """_read_topic_file reads topic file when it exists."""
        topic_file = tmp_path / "topic.md"
        topic_file.write_text("Effect of metformin on HbA1c", encoding="utf-8")
        result = _read_topic_file(topic_file)
        assert result == "Effect of metformin on HbA1c"

    def test_read_topic_file_missing(self, tmp_path):
        """_read_topic_file returns None when topic file doesn't exist."""
        topic_file = tmp_path / "topic.md"
        result = _read_topic_file(topic_file)
        assert result is None

    def test_read_topic_file_empty(self, tmp_path):
        """_read_topic_file returns empty string when topic file is empty."""
        topic_file = tmp_path / "topic.md"
        topic_file.write_text("", encoding="utf-8")
        result = _read_topic_file(topic_file)
        assert result == ""

    def test_clean_pico_term_removes_parentheses(self):
        """_clean_pico_term removes parenthetical qualifiers."""
        result = _clean_pico_term("metformin (for diabetes)")
        assert "metformin" in result
        assert "(" not in result
        assert ")" not in result

    def test_clean_pico_term_removes_time_phrases(self):
        """_clean_pico_term removes time-related phrases."""
        result = _clean_pico_term("metformin at 12 weeks")
        assert "metformin" in result

    def test_clean_pico_term_removes_special_chars(self):
        """_clean_pico_term removes special characters except hyphen."""
        result = _clean_pico_term("metformin & HbA1c (test)")
        assert "&" not in result
        assert "(" not in result
        assert ")" not in result

    def test_clean_pico_term_limits_words(self):
        """_clean_pico_term limits to first 4 words."""
        result = _clean_pico_term("one two three four five six seven eight")
        words = result.split()
        assert len(words) <= 4

    def test_clean_pico_term_handles_empty(self):
        """_clean_pico_term handles empty string."""
        result = _clean_pico_term("")
        assert result == ""

    def test_clean_pico_term_handles_whitespace(self):
        """_clean_pico_term collapses whitespace."""
        result = _clean_pico_term("  metformin   for   diabetes  ")
        assert result == "metformin for diabetes"


class TestRCTSearchFetch:
    """Test article fetching functions."""

    def test_fetch_pubmed_articles_success(self):
        """fetch_pubmed_articles returns list of articles on success."""
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_search_response = Mock()
            mock_search_response.read.return_value = json.dumps({
                "esearchresult": {"idlist": ["12345", "67890"]}
            }).encode()
            
            mock_fetch_response = Mock()
            mock_fetch_response.read.return_value = b"""
            <PubmedArticleSet>
                <PubmedArticle>
                    <MedlineCitation>
                        <PMID>12345</PMID>
                        <Article>
                            <ArticleTitle>Test Article 1</ArticleTitle>
                            <Abstract><AbstractText>Test abstract 1</AbstractText></Abstract>
                        </Article>
                    </MedlineCitation>
                </PubmedArticle>
            </PubmedArticleSet>
            """
            
            mock_urlopen.side_effect = [mock_search_response, mock_fetch_response]
            result = fetch_pubmed_articles("test query", max_results=10)
            assert isinstance(result, list)

    def test_fetch_pubmed_articles_handles_error(self):
        """fetch_pubmed_articles returns empty list on error."""
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = Exception("Network error")
            result = fetch_pubmed_articles("test query")
            assert result == []

    def test_fetch_europepmc_articles_success(self):
        """fetch_europepmc_articles returns list of articles on success."""
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = Mock()
            mock_response.read.return_value = json.dumps({
                "resultList": {
                    "result": [
                        {
                            "id": "12345",
                            "title": "Test Europe PMC Article",
                            "abstractText": "Test abstract",
                            "source": "Europe PMC"
                        }
                    ]
                }
            }).encode()
            mock_urlopen.return_value = mock_response
            result = fetch_europepmc_articles("test query")
            assert isinstance(result, list)

    def test_fetch_europepmc_articles_handles_error(self):
        """fetch_europepmc_articles returns empty list on error."""
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = Exception("Network error")
            result = fetch_europepmc_articles("test query")
            assert result == []

    def test_merge_search_results(self):
        """merge_search_results combines PubMed and Europe PMC results."""
        pubmed_results = [
            {"pmid": "1", "title": "PubMed Article 1", "source": "PubMed"},
            {"pmid": "2", "title": "PubMed Article 2", "source": "PubMed"},
        ]
        europe_results = [
            {"pmid": "3", "title": "Europe Article 1", "source": "Europe PMC"},
        ]
        
        result = merge_search_results(pubmed_results, europe_results)
        assert isinstance(result, list)
        assert len(result) == 3


class TestRCTSearchCallAI:
    """Test AI call function."""

    def test_call_ai_with_ollama(self):
        """call_ai uses ollama provider by default."""
        # Mock the main.call_ai function
        with patch("main.call_ai") as mock_main_call:
            mock_main_call.return_value = "Mock response"
            result = call_ai("Test prompt", provider="ollama")
            mock_main_call.assert_called_with(prompt="Test prompt", provider="ollama", model=None)
            assert result == "Mock response"

    def test_call_ai_with_qwen(self):
        """call_ai uses qwen provider when specified."""
        with patch("main.call_ai") as mock_main_call:
            mock_main_call.return_value = "Mock response"
            result = call_ai("Test prompt", provider="qwen")
            mock_main_call.assert_called_with(prompt="Test prompt", provider="qwen", model=None)
            assert result == "Mock response"

    def test_call_ai_with_openai(self):
        """call_ai uses openai provider when specified."""
        with patch("main.call_ai") as mock_main_call:
            mock_main_call.return_value = "Mock response"
            result = call_ai("Test prompt", provider="openai")
            mock_main_call.assert_called_with(prompt="Test prompt", provider="openai", model=None)
            assert result == "Mock response"

    def test_call_ai_with_anthropic(self):
        """call_ai uses anthropic provider when specified."""
        with patch("main.call_ai") as mock_main_call:
            mock_main_call.return_value = "Mock response"
            result = call_ai("Test prompt", provider="anthropic")
            mock_main_call.assert_called_with(prompt="Test prompt", provider="anthropic", model=None)
            assert result == "Mock response"

    def test_call_ai_with_groq(self):
        """call_ai uses groq provider when specified."""
        with patch("main.call_ai") as mock_main_call:
            mock_main_call.return_value = "Mock response"
            result = call_ai("Test prompt", provider="groq")
            mock_main_call.assert_called_with(prompt="Test prompt", provider="groq", model=None)
            assert result == "Mock response"

    def test_call_ai_invalid_provider(self):
        """call_ai handles invalid provider."""
        with patch("main.call_ai") as mock_main_call:
            mock_main_call.return_value = "Mock response"
            result = call_ai("Test prompt", provider="invalid")
            mock_main_call.assert_called_with(prompt="Test prompt", provider="invalid", model=None)
            assert result == "Mock response"


class TestRCTSearchPipeline:
    """Integration tests for RCT Search pipeline."""

    def test_run_rct_search_pipeline_dry_run(self, tmp_path):
        """run_rct_search_pipeline with dry_run=True creates report."""
        with patch("pipelines.rct_search.rct_search.BASE", tmp_path):
            with patch("pipelines.rct_search.rct_search.INPUT_DIR", tmp_path / "input"):
                with patch("pipelines.rct_search.rct_search.OUTPUT_RCT_SEARCH", tmp_path / "output" / "rct_search"):
                    with patch("pipelines.rct_search.rct_search.REPORTS_DIR", tmp_path / "reports"):
                        with patch("pipelines.rct_search.rct_search.DOCS_RCT_SEARCH", tmp_path / "docs" / "rct_search"):
                            with patch("pipelines.rct_search.rct_search.INPUT_SR", tmp_path / "input" / "sr"):
                                # Create directories
                                (tmp_path / "input" / "rct_search").mkdir(parents=True, exist_ok=True)
                                (tmp_path / "output" / "rct_search").mkdir(parents=True, exist_ok=True)
                                (tmp_path / "reports").mkdir(parents=True, exist_ok=True)
                                (tmp_path / "docs" / "rct_search").mkdir(parents=True, exist_ok=True)
                                (tmp_path / "input" / "sr").mkdir(parents=True, exist_ok=True)
                                
                                # Mock input to avoid interactive prompt
                                with patch("builtins.input", return_value="test topic"):
                                    with patch("main.call_ai") as mock_call_ai:
                                        mock_call_ai.return_value = "Mock AI response"
                                        
                                        with patch("pipelines.rct_search.rct_search.fetch_pubmed_articles") as mock_pubmed:
                                            mock_pubmed.return_value = [
                                                {
                                                    "pmid": "12345",
                                                    "title": "Mock PubMed Article",
                                                    "abstract": "Test abstract",
                                                    "url": "http://example.com",
                                                    "source": "PubMed"
                                                }
                                            ]
                                            
                                            with patch("pipelines.rct_search.rct_search.fetch_europepmc_articles") as mock_europe:
                                                mock_europe.return_value = []
                                                
                                                result = run_rct_search_pipeline(
                                                    provider="ollama",
                                                    model="llama3.2",
                                                    reports_dir=tmp_path / "reports",
                                                    dry_run=True,
                                                )
                                                
                                                assert result is not None

    def test_run_rct_search_pipeline_with_topic_file(self, tmp_path):
        """run_rct_search_pipeline uses topic.md file if present."""
        with patch("pipelines.rct_search.rct_search.BASE", tmp_path):
            with patch("pipelines.rct_search.rct_search.INPUT_DIR", tmp_path / "input"):
                with patch("pipelines.rct_search.rct_search.OUTPUT_RCT_SEARCH", tmp_path / "output" / "rct_search"):
                    with patch("pipelines.rct_search.rct_search.REPORTS_DIR", tmp_path / "reports"):
                        with patch("pipelines.rct_search.rct_search.DOCS_RCT_SEARCH", tmp_path / "docs" / "rct_search"):
                            with patch("pipelines.rct_search.rct_search.INPUT_SR", tmp_path / "input" / "sr"):
                                # Create topic file
                                topic_dir = tmp_path / "input" / "rct_search"
                                topic_dir.mkdir(parents=True, exist_ok=True)
                                (topic_dir / "topic.md").write_text(
                                    "Effect of metformin on HbA1c",
                                    encoding="utf-8"
                                )
                                
                                # Create other directories
                                (tmp_path / "output" / "rct_search").mkdir(parents=True, exist_ok=True)
                                (tmp_path / "reports").mkdir(parents=True, exist_ok=True)
                                (tmp_path / "docs" / "rct_search").mkdir(parents=True, exist_ok=True)
                                (tmp_path / "input" / "sr").mkdir(parents=True, exist_ok=True)
                                
                                with patch("builtins.input", return_value="test topic"):
                                    with patch("main.call_ai") as mock_call_ai:
                                        mock_call_ai.return_value = "Mock AI response"
                                        
                                        with patch("pipelines.rct_search.rct_search.fetch_pubmed_articles") as mock_pubmed:
                                            mock_pubmed.return_value = []
                                            
                                            with patch("pipelines.rct_search.rct_search.fetch_europepmc_articles") as mock_europe:
                                                mock_europe.return_value = []
                                                
                                                result = run_rct_search_pipeline(
                                                    provider="ollama",
                                                    model="llama3.2",
                                                    reports_dir=tmp_path / "reports",
                                                    dry_run=True,
                                                )
                                                
                                                assert result is not None


class TestRCTSearchEdgeCases:
    """Edge case tests for rct_search module."""

    def test_clean_pico_term_with_special_chars(self):
        """_clean_pico_term handles various special characters."""
        result = _clean_pico_term("metformin (for diabetes) 12 weeks")
        assert "&" not in result
        assert "(" not in result
        assert ")" not in result

    def test_merge_search_results_with_duplicates(self):
        """merge_search_results handles duplicate articles."""
        pubmed_results = [
            {"pmid": "1", "title": "Article 1", "source": "PubMed"},
            {"pmid": "2", "title": "Article 2", "source": "PubMed"},
        ]
        europe_results = [
            {"pmid": "1", "title": "Article 1", "source": "Europe PMC"},
        ]
        
        result = merge_search_results(pubmed_results, europe_results)
        assert isinstance(result, list)

    def test_read_topic_file_with_whitespace(self, tmp_path):
        """_read_topic_file strips whitespace from topic content."""
        topic_file = tmp_path / "topic.md"
        topic_file.write_text("  \n  Effect of metformin on HbA1c  \n  ", encoding="utf-8")
        result = _read_topic_file(topic_file)
        assert result == "Effect of metformin on HbA1c"

    def test_role_color_returns_ansi_string(self):
        """role_color returns valid ANSI color codes."""
        roles = ["Formulator", "Searcher", "Validator", "Custom"]
        for role in roles:
            color = role_color(role)
            assert isinstance(color, str)
            assert color.startswith("\033[") or color == ACCENT


if __name__ == "__main__":
    pytest.main([__file__, "-v"])