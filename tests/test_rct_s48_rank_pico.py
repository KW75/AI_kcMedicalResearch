"""Session 48: menu 5 ranking prompt gets the Formulator's PICO.

Before, the ranking prompt's "PICO Question" was previous_response, which
after the stage loop holds the Validator's answer (the last stage), not
the PICO. If the Formulator fails or is skipped, the topic and the typed
P/I/C/O are used instead of an error text or the Validator's answer.
"""
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


def _fake_ai(captured, formulator_fails):
    def fake(prompt="", provider="", model=None):
        if "Your ONLY task is to rate articles" in prompt:
            captured.append(prompt)
            return RANK_LINE
        if "Validate the search strategy" in prompt:
            return "VALIDATOR-VERDICT: APPROVED FOR DOWNLOAD"
        if "Build a comprehensive Boolean" in prompt:
            return "SEARCHER-STRATEGY"
        if "Structure this into a formal PICO question" in prompt:
            if formulator_fails:
                raise RuntimeError("Ollama timed out")
            return "FORMULATOR-PICO: adults with fibromyalgia, CBT vs care"
        raise AssertionError("unexpected prompt: " + prompt[:80])
    return fake


def _run(tmp_path, skip_formulator=False, formulator_fails=False):
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
    captured = []
    with patch.object(m, "BASE", tmp_path), \
         patch.object(m, "INPUT_DIR", tmp_path / "input"), \
         patch.object(m, "OUTPUT_RCT_SEARCH",
                      tmp_path / "output" / "rct_search"), \
         patch.object(m, "REPORTS_DIR", tmp_path / "reports"), \
         patch.object(m, "DOCS_RCT_SEARCH", tmp_path / "docs" / "rct_search"), \
         patch.object(m, "INPUT_SR", tmp_path / "input" / "sr"), \
         patch.object(m, "AI_DIR", ai_dir), \
         patch.object(m, "call_ai", _fake_ai(captured, formulator_fails)), \
         patch.object(m, "fetch_pubmed_articles",
                      return_value=[dict(ARTICLE)]), \
         patch.object(m, "fetch_europepmc_articles", return_value=[]), \
         patch("builtins.input", lambda *a: TOPIC):
        m.run_rct_search_pipeline(provider="ollama", model="x",
                                  reports_dir=tmp_path / "reports",
                                  dry_run=False)
    assert len(captured) == 1, "ranking prompt was not sent"
    return captured[0]


def _pico_section(prompt):
    start = prompt.index("PICO Question:\n") + len("PICO Question:\n")
    return prompt[start:prompt.index("\n\nINSTRUCTIONS:")]


def test_ranking_gets_formulator_pico_not_validator(tmp_path):
    sec = _pico_section(_run(tmp_path))
    assert "FORMULATOR-PICO" in sec
    assert "VALIDATOR-VERDICT" not in sec


def test_ranking_uses_topic_when_formulator_fails(tmp_path):
    sec = _pico_section(_run(tmp_path, formulator_fails=True))
    assert TOPIC in sec
    assert "[ERROR" not in sec
    assert "VALIDATOR-VERDICT" not in sec


def test_ranking_uses_topic_when_formulator_skipped(tmp_path):
    sec = _pico_section(_run(tmp_path, skip_formulator=True))
    assert TOPIC in sec
    assert "VALIDATOR-VERDICT" not in sec
