"""Session 48: menu 5 ranked list is matched to the fetched records.

Before, PMID, title and URL were copied from the AI's ranking lines, so
an invented or repeated record could appear, a wrong title was kept, and
records the AI left out vanished. Below 50% parsed (or on an AI error)
all records got position-based scores shown as relevance scores.
Now: only fetched PMIDs, once each, with fetched title/URL/source; every
record the AI did not score is listed as unscored (score None, "-"),
and one screen line counts invented, repeated and left-out records.
"""
import json
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "SOURCE_CODE"))

import pipelines.rct_search.rct_search as m  # noqa: E402

TOPIC = "CBT for fibromyalgia"
FETCHED = [
    {"pmid": "111", "title": "Real A", "abstract": "a",
     "url": "http://a", "source": "PubMed"},
    {"pmid": "222", "title": "Real B", "abstract": "b",
     "url": "http://b", "source": "PubMed"},
    {"pmid": "333", "title": "Real C", "abstract": "c",
     "url": "http://c", "source": "PubMed"},
]
MIXED = "\n".join([
    "ARTICLE_RANK: 1 | SCORE: 9 | PMID: 111 | SOURCE: PubMed | "
    "TITLE: Real A | URL: http://a",
    "ARTICLE_RANK: 2 | SCORE: 8 | PMID: 999 | SOURCE: PubMed | "
    "TITLE: Invented study | URL: http://fake",
    "ARTICLE_RANK: 3 | SCORE: 7 | PMID: 111 | SOURCE: PubMed | "
    "TITLE: Real A again | URL: http://a",
    "ARTICLE_RANK: 4 | SCORE: 6 | PMID: 222 | SOURCE: PubMed | "
    "TITLE: Wrong title | URL: http://wrong",
])
ROLES = ("formulator", "searcher", "validator")


def _fake_ai(rank_answer):
    def fake(prompt="", provider="", model=None):
        if "Your ONLY task is to rate articles" in prompt:
            if isinstance(rank_answer, Exception):
                raise rank_answer
            return rank_answer
        if "Validate the search strategy" in prompt:
            return "APPROVED FOR DOWNLOAD"
        if "Build a comprehensive Boolean" in prompt:
            return "SEARCHER-STRATEGY"
        return "FORMULATOR-PICO"
    return fake


def _run(tmp_path, rank_answer, capsys):
    ai_dir = tmp_path / "prompts"
    ai_dir.mkdir()
    for role in ROLES:
        (ai_dir / f"{role}-prompt.md").write_text("ROLE " + role,
                                                  encoding="utf-8")
    for d in ("input/rct_search", "output/rct_search", "reports",
              "docs/rct_search", "input/sr"):
        (tmp_path / d).mkdir(parents=True, exist_ok=True)
    out_dir = tmp_path / "output" / "rct_search"
    with patch.object(m, "BASE", tmp_path), \
         patch.object(m, "INPUT_DIR", tmp_path / "input"), \
         patch.object(m, "OUTPUT_RCT_SEARCH", out_dir), \
         patch.object(m, "REPORTS_DIR", tmp_path / "reports"), \
         patch.object(m, "DOCS_RCT_SEARCH", tmp_path / "docs" / "rct_search"), \
         patch.object(m, "INPUT_SR", tmp_path / "input" / "sr"), \
         patch.object(m, "AI_DIR", ai_dir), \
         patch.object(m, "call_ai", _fake_ai(rank_answer)), \
         patch.object(m, "fetch_pubmed_articles",
                      side_effect=lambda *a, **k: [dict(x) for x in FETCHED]), \
         patch.object(m, "fetch_europepmc_articles", return_value=[]), \
         patch("builtins.input", lambda *a: TOPIC):
        m.run_rct_search_pipeline(provider="ollama", model="x",
                                  reports_dir=tmp_path / "reports",
                                  dry_run=False)
    out = capsys.readouterr().out
    pico = list(out_dir.glob("pico_*.json"))
    assert len(pico) == 1, pico
    ranked = json.loads(pico[0].read_text(encoding="utf-8"))["ranked_articles"]
    md = list(out_dir.glob("rct_search_*.md"))
    assert len(md) == 1, md
    return ranked, md[0].read_text(encoding="utf-8"), out


def test_only_fetched_records_once_with_fetched_details(tmp_path, capsys):
    ranked, _md, out = _run(tmp_path, MIXED, capsys)
    pmids = [r["pmid"] for r in ranked]
    assert sorted(pmids) == ["111", "222", "333"]
    by = {r["pmid"]: r for r in ranked}
    assert by["222"]["title"] == "Real B"
    assert by["222"]["url"] == "http://b"
    assert by["111"]["score"] == 9
    assert by["222"]["score"] == 6
    assert by["333"]["score"] is None
    assert pmids == ["111", "222", "333"]
    assert ("Ranking check: 2 of 3 records scored by the AI; "
            "1 invented, 1 repeated, 1 left out") in out


def test_unparseable_answer_lists_all_unscored(tmp_path, capsys):
    ranked, md, out = _run(tmp_path, "Sorry, I cannot rate these.", capsys)
    assert sorted(r["pmid"] for r in ranked) == ["111", "222", "333"]
    assert all(r["score"] is None for r in ranked)
    assert "Using fallback ranking" not in out
    assert "Ranking check: 0 of 3 records scored by the AI" in out
    assert "| - |" in md


def test_ai_error_lists_all_unscored(tmp_path, capsys):
    ranked, md, out = _run(tmp_path, RuntimeError("Ollama timed out"),
                           capsys)
    assert all(r["score"] is None for r in ranked)
    assert "Ranking error" in out
    assert "| - |" in md
