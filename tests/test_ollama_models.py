"""Tests for SOURCE_CODE/ollama_models.py (Ollama model picker data).

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


class TestListModels:
    def test_lists_every_model_smallest_first(self):
        """No name-based skipping: embedding models are listed too.
        The launcher hides them by capability ('completion' missing)."""
        names = [m["name"] for m in _pulled()]
        assert names == ["nomic-embed-text:latest", "llama3.2:latest",
                         "gemma4:e4b", "qwen3:8b", "qwen2.5:14b-instruct"]

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


class TestDescribe:
    def test_line_has_name_params_size_and_vision_only(self):
        from ollama_models import describe
        m = {"name": "gemma4:e4b", "size_gb": 6.6, "params_b": 7.5}
        assert describe(m, {"completion", "vision"}) == "gemma4:e4b  7.5B  6.6 GB  Image/OCR: yes"

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

    def test_module_is_stdlib_only_so_the_launcher_can_import_it(self):
        src = (Path(__file__).resolve().parent.parent
               / "SOURCE_CODE" / "ollama_models.py").read_text(encoding="utf-8")
        for banned in ("dotenv", "import requests", "import streamlit"):
            assert banned not in src


class TestNoRankings:
    def test_ranking_and_auto_pick_names_are_gone(self):
        """Session 33: no hard-coded ranks, no auto-pick, no name-based skipping."""
        import ollama_models
        for name in ("MODEL_RANKS", "RANKS_SOURCE", "rank_label",
                     "missing_ranked", "choose_default", "_SKIP_PATTERNS"):
            assert not hasattr(ollama_models, name), name


class TestVersion:
    def test_reads_version_from_api_version(self):
        import ollama_models
        with patch("urllib.request.urlopen", return_value=_resp({"version": "0.40.11"})) as fake:
            assert ollama_models.ollama_version("http://localhost:11434") == "0.40.11"
        assert fake.call_args[0][0].full_url.endswith("/api/version")

    def test_unreachable_returns_empty(self):
        import ollama_models
        with patch("urllib.request.urlopen", side_effect=OSError("refused")):
            assert ollama_models.ollama_version("http://localhost:11434") == ""
