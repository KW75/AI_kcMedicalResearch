"""Tests for SOURCE_CODE/ollama_models.py (Ollama model picker data).

Ranks come from the local model comparison doc, 2026-10 (1 = best).
Sizes, parameter counts and capabilities come live from Ollama, so they
are mocked here and never hard-coded in the module.
"""
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

TAGS = {"models": [
    {"name": "gemma4:e4b", "size": 6_600_000_000, "details": {"parameter_size": "7.5B"}},
    {"name": "qwen3:8b", "size": 5_200_000_000, "details": {"parameter_size": "8.2B"}},
    {"name": "qwen2.5:14b-instruct", "size": 9_000_000_000, "details": {"parameter_size": "14.8B"}},
    {"name": "llama3.2:latest", "size": 2_000_000_000, "details": {"parameter_size": "3.2B"}},
    {"name": "nomic-embed-text:latest", "size": 274_000_000, "details": {"parameter_size": "137M"}},
]}


def _resp(body):
    r = MagicMock()
    r.read.return_value = json.dumps(body).encode()
    r.__enter__ = lambda s: s
    r.__exit__ = MagicMock(return_value=False)
    return r


def _pulled():
    import ollama_models
    with patch("urllib.request.urlopen", return_value=_resp(TAGS)):
        return ollama_models.list_ollama_models("http://localhost:11434")


class TestRanks:
    def test_ranks_match_comparison_doc(self):
        from ollama_models import MODEL_RANKS
        assert MODEL_RANKS == {
            "qwen3:4b":             {"coding": 4, "reasoning": 3},
            "gemma4:e4b":           {"coding": 1, "reasoning": 2},
            "granite3.3:latest":    {"coding": 5, "reasoning": 5},
            "qwen3:8b":             {"coding": 2, "reasoning": 1},
            "qwen2.5:14b-instruct": {"coding": 3, "reasoning": 4},
        }

    def test_each_rank_column_is_1_to_n_with_no_gaps(self):
        from ollama_models import MODEL_RANKS
        n = len(MODEL_RANKS)
        for column in ("coding", "reasoning"):
            assert sorted(r[column] for r in MODEL_RANKS.values()) == list(range(1, n + 1))

    def test_rank_label_counts_from_table_length(self):
        from ollama_models import MODEL_RANKS, rank_label
        n = len(MODEL_RANKS)
        assert rank_label("gemma4:e4b") == f"Coding 1 of {n}, Reasoning 2 of {n} (1 = best)"

    def test_unranked_model_says_not_ranked(self):
        from ollama_models import rank_label
        assert rank_label("llama3.2:latest") == "not ranked"

    def test_rank_lookup_treats_missing_tag_as_latest(self):
        from ollama_models import rank_label
        assert rank_label("granite3.3") == rank_label("granite3.3:latest") != "not ranked"


class TestListModels:
    def test_skips_embedding_models_and_sorts_smallest_first(self):
        names = [m["name"] for m in _pulled()]
        assert names == ["llama3.2:latest", "gemma4:e4b", "qwen3:8b", "qwen2.5:14b-instruct"]

    def test_reads_disk_size_and_params_from_ollama(self):
        gemma = next(m for m in _pulled() if m["name"] == "gemma4:e4b")
        assert gemma["size_gb"] == 6.6
        assert gemma["params_b"] == 7.5

    def test_unreachable_ollama_returns_empty_list(self):
        import ollama_models
        with patch("urllib.request.urlopen", side_effect=Exception("refused")):
            assert ollama_models.list_ollama_models("http://localhost:11434") == []


class TestChooseDefault:
    def test_default_is_gemma4_e4b(self):
        from ollama_models import OLLAMA_DEFAULT_MODEL
        assert OLLAMA_DEFAULT_MODEL == "gemma4:e4b"

    def test_prefers_default_when_pulled_even_if_not_largest(self):
        from ollama_models import choose_default
        assert choose_default(_pulled()) == "gemma4:e4b"

    def test_falls_back_to_largest_when_default_not_pulled(self):
        from ollama_models import choose_default
        models = [m for m in _pulled() if m["name"] != "gemma4:e4b"]
        assert choose_default(models) == "qwen2.5:14b-instruct"

    def test_nothing_pulled_returns_default(self):
        from ollama_models import OLLAMA_DEFAULT_MODEL, choose_default
        assert choose_default([]) == OLLAMA_DEFAULT_MODEL


class TestCapabilities:
    def test_reads_capabilities_from_api_show(self):
        import ollama_models
        sent = {}

        def fake_urlopen(req, timeout=0):
            sent["url"] = req.full_url
            sent["body"] = json.loads(req.data)
            return _resp({"capabilities": ["completion", "vision", "thinking"]})

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            caps = ollama_models.model_capabilities("http://localhost:11434", "gemma4:e4b")
        assert caps == {"completion", "vision", "thinking"}
        assert sent["url"].endswith("/api/show")
        assert sent["body"]["model"] == "gemma4:e4b"

    def test_unreachable_returns_empty_set(self):
        import ollama_models
        with patch("urllib.request.urlopen", side_effect=Exception("refused")):
            assert ollama_models.model_capabilities("http://localhost:11434", "x") == set()


class TestMissingRanked:
    def test_lists_ranked_models_that_are_not_pulled(self):
        from ollama_models import missing_ranked
        assert set(missing_ranked(_pulled())) == {"qwen3:4b", "granite3.3:latest"}


class TestDescribe:
    def test_line_has_name_params_size_vision_and_rank(self):
        from ollama_models import describe, rank_label
        gemma = next(m for m in _pulled() if m["name"] == "gemma4:e4b")
        line = describe(gemma, {"completion", "vision"})
        for part in ("gemma4:e4b", "7.5B", "6.6 GB", "Image/OCR: yes", rank_label("gemma4:e4b")):
            assert part in line

    def test_no_vision_says_no(self):
        from ollama_models import describe
        qwen = next(m for m in _pulled() if m["name"] == "qwen3:8b")
        assert "Image/OCR: no" in describe(qwen, {"completion", "thinking"})

    def test_line_is_ascii_for_launcher_border_alignment(self):
        from ollama_models import describe
        for m in _pulled():
            assert describe(m, {"vision"}).isascii()


class TestWiring:
    def test_providers_uses_the_same_default(self):
        import ollama_models
        import providers
        assert providers.OLLAMA_DEFAULT_MODEL == ollama_models.OLLAMA_DEFAULT_MODEL

    def test_auto_detect_prefers_default_over_largest(self):
        from providers import _ollama_detect_best_model
        with patch("urllib.request.urlopen", return_value=_resp(TAGS)):
            assert _ollama_detect_best_model("http://localhost:11434") == "gemma4:e4b"

    def test_module_is_stdlib_only_so_the_launcher_can_import_it(self):
        src = (Path(__file__).resolve().parent.parent
               / "SOURCE_CODE" / "ollama_models.py").read_text(encoding="utf-8")
        for banned in ("dotenv", "import requests", "import streamlit"):
            assert banned not in src
