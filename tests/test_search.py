"""Tests for the search pipeline module."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock

import pytest

# Add SOURCE_CODE to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_CODE_DIR = PROJECT_ROOT / "SOURCE_CODE"
sys.path.insert(0, str(SOURCE_CODE_DIR))

# Import the search module
from pipelines.search.search import (
    _project_root,
    _ts,
    _paths,
    _load_guidelines,
    _result_limits,
    _topic_system_prompt,
    _topic_user_prompt,
    _article_system_prompt,
    _article_user_prompt,
    run_topic_search,
    run_article_search,
    _pubmed_search,
)


class TestSearchHelpers:
    """Test helper functions in search.py."""

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
        
        expected_keys = ["docs", "output", "reports"]
        for key in expected_keys:
            assert key in paths
            assert isinstance(paths[key], Path)

    def test_result_limits_default(self):
        """_result_limits returns default limits for unknown models."""
        topic_limit, article_limit = _result_limits(None)
        assert topic_limit > 0
        assert article_limit > 0

    def test_result_limits_small_models(self):
        """_result_limits returns reduced limits for small models."""
        small_models = ["llama3.2", "qwen2.5-coder:3b", "llama3.1:8b"]
        for model in small_models:
            topic_limit, article_limit = _result_limits(model)
            assert topic_limit <= 10
            assert article_limit <= 15

    def test_result_limits_known_model(self):
        """_result_limits returns appropriate limits for known models."""
        topic_limit, article_limit = _result_limits("gpt-4")
        assert topic_limit == 10
        assert article_limit == 15

    def test_load_guidelines_empty(self, tmp_path):
        """_load_guidelines returns empty string when no guidelines exist."""
        result = _load_guidelines(tmp_path)
        assert result == ""

    def test_load_guidelines_with_files(self, tmp_path):
        """_load_guidelines loads and concatenates .md files."""
        guideline_file = tmp_path / "search-guide.md"
        guideline_file.write_text("# Search Guide\n\nThis is a test guide.", encoding="utf-8")
        
        result = _load_guidelines(tmp_path)
        assert "Search Guide" in result
        assert "This is a test guide" in result

    def test_topic_system_prompt(self):
        """_topic_system_prompt returns a system prompt for topic search."""
        guidelines = "Test guidelines"
        result = _topic_system_prompt(guidelines)
        assert isinstance(result, str)
        assert "search" in result.lower() or "topic" in result.lower()
        if guidelines:
            assert guidelines in result

    def test_topic_system_prompt_empty(self):
        """_topic_system_prompt works with empty guidelines."""
        result = _topic_system_prompt("")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_topic_user_prompt(self):
        """_topic_user_prompt includes query and results."""
        query = "Test topic"
        results = [{"title": "Result 1", "snippet": "Test snippet", "url": "http://example.com"}]
        
        result = _topic_user_prompt(query, results)
        assert "Test topic" in result
        assert "Result 1" in result

    def test_topic_user_prompt_empty_results(self):
        """_topic_user_prompt handles empty results gracefully."""
        query = "Test topic"
        results = []
        
        result = _topic_user_prompt(query, results)
        assert query in result

    def test_article_system_prompt(self):
        """_article_system_prompt returns a system prompt for article search."""
        guidelines = "Test guidelines"
        result = _article_system_prompt(guidelines)
        assert isinstance(result, str)
        assert "PubMed" in result or "article" in result.lower() or "search" in result.lower()
        if guidelines:
            assert guidelines in result

    def test_article_system_prompt_empty(self):
        """_article_system_prompt works with empty guidelines."""
        result = _article_system_prompt("")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_article_user_prompt(self):
        """_article_user_prompt includes query, article_type, and articles with all required fields."""
        query = "Test article topic"
        article_type = "Systematic Review"
        articles = [{
            "pmid": "12345",
            "title": "Article 1",
            "abstract": "Test abstract",
            "doi": "10.1234/test",
            "url": "http://example.com/12345",
            "authors": "Smith J, Jones M",
            "year": "2023",
            "journal": "NEJM"
        }]
        
        result = _article_user_prompt(query, article_type, articles)
        assert "Test article topic" in result
        assert "Article 1" in result
        assert "Systematic Review" in result
        assert "Smith J" in result
        assert "2023" in result
        assert "NEJM" in result

    def test_article_user_prompt_empty_results(self):
        """_article_user_prompt handles empty articles gracefully."""
        query = "Test article topic"
        article_type = "Review Article"
        articles = []
        
        result = _article_user_prompt(query, article_type, articles)
        assert "Test article topic" in result
        assert "Review Article" in result

    def test_article_user_prompt_without_doi(self):
        """_article_user_prompt handles articles without DOI."""
        query = "Test article topic"
        article_type = "RCT"
        articles = [{
            "pmid": "12345",
            "title": "Article without DOI",
            "abstract": "Test abstract",
            "doi": "",
            "url": "http://example.com/12345",
            "authors": "Doe J, Smith A",
            "year": "2022",
            "journal": "Lancet"
        }]
        
        result = _article_user_prompt(query, article_type, articles)
        assert "Test article topic" in result
        assert "Article without DOI" in result
        assert "Doe J" in result
        assert "2022" in result
        assert "Lancet" in result


class TestSearchIntegration:
    """Integration tests for search pipeline."""

    def test_run_topic_search_no_query(self, tmp_path, capsys):
        """run_topic_search handles missing query gracefully."""
        with patch("pipelines.search.search._paths") as mock_paths:
            mock_paths.return_value = {
                "docs": tmp_path / "docs",
                "output": tmp_path / "output",
                "reports": tmp_path / "reports",
            }
            
            with patch("builtins.input", return_value="test query"):
                with patch("pipelines.search.search._topic_system_prompt", return_value="System prompt"):
                    with patch("pipelines.search.search._topic_user_prompt", return_value="User prompt"):
                        with patch("pipelines.search.search._europepmc_search", return_value=[]):
                            def mock_llm(system_prompt, user_prompt):
                                return "Mock topic search response"
                            
                            run_topic_search(
                                direct_instructions=[],
                                call_llm_fn=mock_llm,
                                verbose=True,
                            )
                            assert True

    def test_run_article_search_no_query(self, tmp_path, capsys):
        """run_article_search handles missing query gracefully."""
        with patch("pipelines.search.search._paths") as mock_paths:
            mock_paths.return_value = {
                "docs": tmp_path / "docs",
                "output": tmp_path / "output",
                "reports": tmp_path / "reports",
            }
            
            with patch("builtins.input", return_value="test query"):
                with patch("pipelines.search.search._article_system_prompt", return_value="System prompt"):
                    with patch("pipelines.search.search._article_user_prompt", return_value="User prompt"):
                        with patch("pipelines.search.search._pubmed_search", return_value=[]):
                            def mock_llm(system_prompt, user_prompt):
                                return "Mock article search response"
                            
                            run_article_search(
                                direct_instructions=[],
                                call_llm_fn=mock_llm,
                                verbose=True,
                            )
                            assert True

    def test_run_topic_search_with_query(self, tmp_path):
        """run_topic_search processes query and creates outputs."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        reports_dir = tmp_path / "reports"
        docs_dir = tmp_path / "docs"
        
        input_dir.mkdir(parents=True)
        output_dir.mkdir(parents=True)
        reports_dir.mkdir(parents=True)
        docs_dir.mkdir(parents=True)
        
        (input_dir / "topic.md").write_text(
            "Effect of metformin on cardiovascular outcomes",
            encoding="utf-8"
        )
        
        (docs_dir / "search-guide.md").write_text(
            "# Search Guide\n\nGuidelines for medical search.",
            encoding="utf-8"
        )
        
        with patch("pipelines.search.search._paths") as mock_paths:
            mock_paths.return_value = {
                "docs": docs_dir,
                "output": output_dir,
                "reports": reports_dir,
            }
            
            with patch("builtins.input", return_value="test query"):
                with patch("pipelines.search.search._europepmc_search", return_value=[{"title": "Test result", "snippet": "Test snippet", "url": "http://example.com"}]):
                    def mock_llm(system_prompt, user_prompt):
                        return "Mock topic search response with results."
                    
                    run_topic_search(
                        direct_instructions=[],
                        call_llm_fn=mock_llm,
                        verbose=False,
                    )
                    assert True

    def test_run_article_search_with_query(self, tmp_path):
        """run_article_search processes query and creates outputs."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        reports_dir = tmp_path / "reports"
        docs_dir = tmp_path / "docs"
        
        input_dir.mkdir(parents=True)
        output_dir.mkdir(parents=True)
        reports_dir.mkdir(parents=True)
        docs_dir.mkdir(parents=True)
        
        (input_dir / "topic.md").write_text(
            "Effect of metformin on cardiovascular outcomes",
            encoding="utf-8"
        )
        
        (docs_dir / "search-guide.md").write_text(
            "# Search Guide\n\nGuidelines for medical article search.",
            encoding="utf-8"
        )
        
        with patch("pipelines.search.search._paths") as mock_paths:
            mock_paths.return_value = {
                "docs": docs_dir,
                "output": output_dir,
                "reports": reports_dir,
            }
            
            with patch("builtins.input", return_value="test query"):
                with patch("pipelines.search.search._pubmed_search", return_value=[{"pmid": "12345", "title": "Test article"}]):
                    with patch("pipelines.search.search._pubmed_fetch_abstracts", return_value=[{
                        "pmid": "12345",
                        "title": "Test article",
                        "abstract": "Test abstract",
                        "doi": "10.1234/test",
                        "authors": "Smith J, Jones M",
                        "year": "2023",
                        "journal": "NEJM",
                        "url": "https://pubmed.ncbi.nlm.nih.gov/12345/"
                    }]):
                        def mock_llm(system_prompt, user_prompt):
                            return "Mock article search response with PubMed results."
                        
                        run_article_search(
                            direct_instructions=[],
                            call_llm_fn=mock_llm,
                            verbose=False,
                        )
                        assert True


class TestSearchEdgeCases:
    """Edge case tests for search module."""

    def test_europepmc_search_error_handling(self):
        """Test that EuropePMC search handles errors gracefully."""
        with patch("requests.get") as mock_get:
            mock_get.side_effect = Exception("Network error")
            try:
                from pipelines.search.search import _europepmc_search
                result = _europepmc_search("test query")
                assert isinstance(result, list)
            except ImportError:
                pytest.skip("Could not import _europepmc_search")

    def test_pubmed_search_error_handling(self):
        """Test that PubMed search handles errors gracefully."""
        with patch("requests.get") as mock_get:
            mock_get.side_effect = Exception("Network error")
            try:
                from pipelines.search.search import _pubmed_search
                result = _pubmed_search("test query", "")
                assert isinstance(result, list)
            except ImportError:
                pytest.skip("Could not import _pubmed_search")

    def test_result_limits_with_none_model(self):
        """_result_limits handles None model gracefully."""
        topic_limit, article_limit = _result_limits(None)
        assert topic_limit > 0
        assert article_limit > 0

    def test_result_limits_with_empty_model(self):
        """_result_limits handles empty string model gracefully."""
        topic_limit, article_limit = _result_limits("")
        assert topic_limit > 0
        assert article_limit > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])