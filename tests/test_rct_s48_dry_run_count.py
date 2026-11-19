"""Session 48: a dry run's count line says no searches were sent.

Before, a dry run printed "Found 0 PubMed + 0 Europe PMC = 1 unique
articles": the fake test record was counted as if a search found it.
Real runs keep the old count line.
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


def test_dry_run_count_line_says_no_searches(tmp_path, capsys):
    _run(tmp_path, dry_run=True)
    out = capsys.readouterr().out
    assert "Europe PMC = 1 unique" not in out
    assert "[RCT Search] Dry run: no searches sent, 1 fake test record." in out


def test_real_run_count_line_unchanged(tmp_path, capsys):
    _run(tmp_path, dry_run=False)
    out = capsys.readouterr().out
    assert "[RCT Search] Found 2 PubMed + 0 Europe PMC = 2 unique articles" in out
    assert "Dry run:" not in out
