"""Session 48: Search writes no file when the AI call fails.

Before, _call_llm returned "[ERROR] ..." and that text was saved as the
synopsis/summary, and the screen still said "Complete."
"""
import sys
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "SOURCE_CODE"))

import pipelines.search.search as s  # noqa: E402

RESULTS = [{"title": "T1", "url": "https://pubmed.ncbi.nlm.nih.gov/1/",
            "snippet": "snippet"}]
ARTICLES = [{"uid": "1", "title": "T1", "url": "https://x/1", "doi": ""}]


def _paths(tmp_path):
    return {k: tmp_path / k for k in ("docs", "input", "output", "reports")}


def _boom(system_prompt="", user_prompt=""):
    raise RuntimeError("Ollama timed out")


def _ok(system_prompt="", user_prompt=""):
    return "## Overview\nText."


def _run_topic(tmp_path, fn):
    paths = _paths(tmp_path)
    with patch.object(s, "_paths", return_value=paths), \
         patch.object(s, "_Spinner", lambda *a, **k: nullcontext()), \
         patch.object(s, "_europepmc_search", return_value=RESULTS):
        s.run_topic_search(["cbt fibromyalgia"], fn, verbose=False)
    return paths


def _run_article(tmp_path, fn, monkeypatch):
    paths = _paths(tmp_path)
    monkeypatch.setattr("builtins.input", lambda *a: "3")
    with patch.object(s, "_paths", return_value=paths), \
         patch.object(s, "_Spinner", lambda *a, **k: nullcontext()), \
         patch.object(s, "_pubmed_search", return_value=ARTICLES), \
         patch.object(s, "_pubmed_fetch_abstracts", side_effect=lambda a, **k: a), \
         patch.object(s, "_article_user_prompt", return_value="prompt"):
        s.run_article_search(["cbt fibromyalgia"], fn, verbose=False)
    return paths


def _files(paths):
    return [p.name for k in ("output", "reports") for p in paths[k].iterdir()]


def test_topic_ai_error_writes_nothing(tmp_path, capsys):
    paths = _run_topic(tmp_path, _boom)
    out = capsys.readouterr().out
    assert _files(paths) == []
    assert "[TOPIC SEARCH] AI call failed - no file written." in out
    assert "Ollama timed out" in out
    assert "Complete." not in out


def test_topic_empty_answer_writes_nothing(tmp_path, capsys):
    paths = _run_topic(tmp_path, lambda **k: "   ")
    assert _files(paths) == []
    assert "AI call failed - no file written." in capsys.readouterr().out


def test_article_ai_error_writes_nothing(tmp_path, capsys, monkeypatch):
    paths = _run_article(tmp_path, _boom, monkeypatch)
    out = capsys.readouterr().out
    assert _files(paths) == []
    assert "[ARTICLE SEARCH] AI call failed - no file written." in out
    assert "Complete." not in out


def test_topic_success_still_writes(tmp_path, capsys):
    paths = _run_topic(tmp_path, _ok)
    assert any(n.startswith("TOPIC_") and n.endswith(".md")
               for n in _files(paths))
    assert "Complete." in capsys.readouterr().out


def test_article_success_still_writes(tmp_path, capsys, monkeypatch):
    paths = _run_article(tmp_path, _ok, monkeypatch)
    assert any(n.startswith("ARTICLE_") and n.endswith(".md")
               for n in _files(paths))
    assert "Complete." in capsys.readouterr().out
