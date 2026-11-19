"""Session 48: menu 5 writes the ranking only into this run's pico_*.json.

Before: the ranking was added to the newest pico_*.json in
output/rct_search/, and that file was offered for copying to input/sr/.
If this run saved none (formulator-prompt.md missing, or a dry run), that
was an older run's file. Now only the file this run saved is used.
"""
import json
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "SOURCE_CODE"))

import pipelines.rct_search.rct_search as m  # noqa: E402

TOPIC = "CBT for fibromyalgia"
ARTICLE = {"pmid": "12345", "title": "Mock PubMed Article",
           "abstract": "Test abstract", "url": "http://example.com",
           "source": "PubMed"}
RANK_LINE = ("ARTICLE_RANK: 1 | SCORE: 9 | PMID: 12345 | SOURCE: PubMed | "
             "TITLE: Mock PubMed Article | URL: http://example.com")
ROLES = ("formulator", "searcher", "validator")
OLD_NAME = "pico_20000101_000000.json"
OLD_TEXT = json.dumps({"topic": "OLD RUN"}, indent=2) + "\n"


def _fake_ai(prompt="", provider="", model=None):
    if "Your ONLY task is to rate articles" in prompt:
        return RANK_LINE
    if "Validate the search strategy" in prompt:
        return "Overall decision: APPROVED FOR DOWNLOAD"
    if "Build a comprehensive Boolean" in prompt:
        return "SEARCHER-STRATEGY"
    if "Structure this into a formal PICO question" in prompt:
        return "FORMULATOR-PICO: adults with fibromyalgia, CBT vs care"
    raise AssertionError("unexpected prompt: " + prompt[:80])


def _answer(prompt=""):
    return "Y" if "Copy pico" in prompt else TOPIC


def _run(tmp_path, skip_formulator=False, dry_run=False):
    ai_dir = tmp_path / "prompts"
    ai_dir.mkdir()
    for role in ROLES:
        if role == "formulator" and skip_formulator:
            continue
        (ai_dir / f"{role}-prompt.md").write_text(
            "ROLE PROMPT " + role, encoding="utf-8")
    for d in ("input/rct_search", "output/rct_search", "reports",
              "docs/rct_search", "input/sr"):
        (tmp_path / d).mkdir(parents=True, exist_ok=True)
    out_dir = tmp_path / "output" / "rct_search"
    (out_dir / OLD_NAME).write_text(OLD_TEXT, encoding="utf-8")
    with patch.object(m, "BASE", tmp_path), \
         patch.object(m, "INPUT_DIR", tmp_path / "input"), \
         patch.object(m, "OUTPUT_RCT_SEARCH", out_dir), \
         patch.object(m, "REPORTS_DIR", tmp_path / "reports"), \
         patch.object(m, "DOCS_RCT_SEARCH", tmp_path / "docs" / "rct_search"), \
         patch.object(m, "INPUT_SR", tmp_path / "input" / "sr"), \
         patch.object(m, "AI_DIR", ai_dir), \
         patch.object(m, "call_ai", _fake_ai), \
         patch.object(m, "fetch_pubmed_articles",
                      return_value=[dict(ARTICLE)]), \
         patch.object(m, "fetch_europepmc_articles", return_value=[]), \
         patch("builtins.input", _answer):
        m.run_rct_search_pipeline(provider="ollama", model="x",
                                  reports_dir=tmp_path / "reports",
                                  dry_run=dry_run)
    return out_dir, tmp_path / "input" / "sr"


def test_skipped_formulator_leaves_old_file_alone(tmp_path):
    out_dir, sr_dir = _run(tmp_path, skip_formulator=True)
    assert (out_dir / OLD_NAME).read_text(encoding="utf-8") == OLD_TEXT
    assert [p.name for p in out_dir.glob("pico_*.json")] == [OLD_NAME]
    assert list(sr_dir.glob("*.json")) == []


def test_dry_run_leaves_old_file_alone(tmp_path):
    out_dir, sr_dir = _run(tmp_path, dry_run=True)
    assert (out_dir / OLD_NAME).read_text(encoding="utf-8") == OLD_TEXT
    assert list(sr_dir.glob("*.json")) == []


def test_normal_run_updates_and_offers_own_file(tmp_path):
    out_dir, sr_dir = _run(tmp_path)
    assert (out_dir / OLD_NAME).read_text(encoding="utf-8") == OLD_TEXT
    new = [p for p in out_dir.glob("pico_*.json") if p.name != OLD_NAME]
    assert len(new) == 1
    data = json.loads(new[0].read_text(encoding="utf-8"))
    assert [r["pmid"] for r in data["ranked_articles"]] == ["12345"]
    assert [p.name for p in sr_dir.glob("*.json")] == [new[0].name]
