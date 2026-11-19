"""Session 48: a dry run's screen text says no search and no AI call.

Before, a dry run printed "Searching PubMed/Europe PMC for relevant
articles..." and "Ranking check: 1 of 1 records scored by the AI",
though it sends no search and makes no AI call (the ranking is fake).
Real runs keep all three lines.
"""
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "SOURCE_CODE"))

import pipelines.rct_search.rct_search as m  # noqa: E402

TOPIC = "CBT for fibromyalgia"
ARTICLES = [
    {"pmid": "111", "title": "Trial one", "abstract": "A.",
     "url": "https://pubmed.ncbi.nlm.nih.gov/111/", "source": "PubMed"},
    {"pmid": "222", "title": "Trial two", "abstract": "B.",
     "url": "https://pubmed.ncbi.nlm.nih.gov/222/", "source": "PubMed"},
]
SEARCH_PUBMED = "[RCT Search] Searching PubMed for relevant articles..."
SEARCH_EUROPE = "[RCT Search] Searching Europe PMC for relevant articles..."
FAKE_RANKING = "[RCT Search] Dry run: fake ranking, no AI call."


def _run(tmp_path, dry_run):
    for sub in ("input/rct_search", "output/rct_search", "reports",
                "docs/rct_search", "input/sr", "prompts"):
        (tmp_path / sub).mkdir(parents=True, exist_ok=True)
    with patch.object(m, "BASE", tmp_path), \
         patch.object(m, "INPUT_DIR", tmp_path / "input"), \
         patch.object(m, "OUTPUT_RCT_SEARCH", tmp_path / "output" / "rct_search"), \
         patch.object(m, "REPORTS_DIR", tmp_path / "reports"), \
         patch.object(m, "DOCS_RCT_SEARCH", tmp_path / "docs" / "rct_search"), \
         patch.object(m, "INPUT_SR", tmp_path / "input" / "sr"), \
         patch.object(m, "AI_DIR", tmp_path / "prompts"), \
         patch.object(m, "call_ai", return_value="no rating lines"), \
         patch.object(m, "fetch_pubmed_articles",
                      return_value=[dict(a) for a in ARTICLES]), \
         patch.object(m, "fetch_europepmc_articles", return_value=[]), \
         patch("builtins.input", return_value=TOPIC):
        m.run_rct_search_pipeline(provider="ollama", model="x",
                                  reports_dir=tmp_path / "reports",
                                  dry_run=dry_run)


def test_dry_run_prints_no_searching_lines(tmp_path, capsys):
    _run(tmp_path, dry_run=True)
    out = capsys.readouterr().out
    assert SEARCH_PUBMED not in out
    assert SEARCH_EUROPE not in out


def test_dry_run_prints_fake_ranking_line(tmp_path, capsys):
    _run(tmp_path, dry_run=True)
    out = capsys.readouterr().out
    assert "scored by the AI" not in out
    assert FAKE_RANKING in out


def test_real_run_lines_unchanged(tmp_path, capsys):
    _run(tmp_path, dry_run=False)
    out = capsys.readouterr().out
    assert SEARCH_PUBMED in out
    assert SEARCH_EUROPE in out
    assert ("[RCT Search] Ranking check: 0 of 2 records scored by the AI; "
            "0 invented, 0 repeated, 2 left out (listed as unscored).") in out
    assert "Dry run:" not in out


def test_match_ranked_dry_run_same_list(capsys):
    ranked = [{"rank": 1, "score": 9, "pmid": "111", "title": "x",
               "url": "u", "source": "PubMed"}]
    real = m._match_ranked(ranked, [dict(a) for a in ARTICLES])
    capsys.readouterr()
    dry = m._match_ranked(ranked, [dict(a) for a in ARTICLES], dry_run=True)
    out = capsys.readouterr().out
    assert dry == real
    assert FAKE_RANKING in out
    assert "Ranking check:" not in out
