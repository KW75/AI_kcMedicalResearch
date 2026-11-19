"""Session 48: menu 5 ranks in batches that fit the local AI window.

Before: one ranking prompt held every record with its full abstract (up
to 200) with no size check. Ollama's window (num_ctx = OLLAMA_CONTEXT)
holds prompt + answer and drops what does not fit without a message, and
the answer limit (8192 tokens) is too small for 200 rating lines. Now
local runs are split into batches (_rank_batches); cloud runs stay one
call. A failed batch leaves only its own records unscored.
"""
import json
import re
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "SOURCE_CODE"))

import pipelines.rct_search.rct_search as m  # noqa: E402

TOPIC = "CBT for fibromyalgia"
ROLES = ("formulator", "searcher", "validator")
ABSTRACT = "word " * 500
ARTICLES = [
    {"pmid": str(1000 + k), "title": f"Trial {k} of CBT",
     "abstract": ABSTRACT,
     "url": f"https://pubmed.ncbi.nlm.nih.gov/{1000 + k}/",
     "source": "PubMed"}
    for k in range(6)
]
BUDGET = (12000 - 8192 - 1000) * 3
PMID_LINE = re.compile(r"^PMID: (\S+)$", re.M)


def test_cloud_gets_one_batch():
    blocks = ["x" * 100000] * 3
    assert m._rank_batches(blocks, 1000, "deepseek") == [[0, 1, 2]]


def test_local_batches_fit_window(monkeypatch):
    monkeypatch.setenv("OLLAMA_CONTEXT", "32768")
    blocks = ["y" * 2000] * 200
    batches = m._rank_batches(blocks, 3000, "ollama")
    assert [i for b in batches for i in b] == list(range(200))
    limit = (32768 - 8192 - 1000) * 3
    for b in batches:
        assert 3000 + sum(len(blocks[i]) for i in b) <= limit
        assert len(b) <= 109
    assert len(batches) > 1


def test_local_batch_count_cap(monkeypatch):
    monkeypatch.setenv("OLLAMA_CONTEXT", "32768")
    batches = m._rank_batches(["z" * 10] * 300, 3000, "ollama")
    assert [len(b) for b in batches] == [109, 109, 82]


def test_oversize_block_gets_own_batch(monkeypatch):
    monkeypatch.setenv("OLLAMA_CONTEXT", "32768")
    blocks = ["a" * 100, "b" * 200000, "c" * 100]
    assert m._rank_batches(blocks, 3000, "ollama") == [[0], [1], [2]]


def _fake_ai(prompts, fail_pmid):
    def fake(prompt="", provider="", model=None):
        if "Your ONLY task is to rate articles" in prompt:
            prompts.append(prompt)
            pmids = PMID_LINE.findall(prompt)
            if fail_pmid in pmids:
                raise RuntimeError("Ollama timed out")
            return "\n".join(
                f"ARTICLE_RANK: {n} | SCORE: 8 | PMID: {p} | SOURCE: PubMed"
                f" | TITLE: x | URL: https://pubmed.ncbi.nlm.nih.gov/{p}/"
                for n, p in enumerate(pmids, 1))
        if "Validate the search strategy" in prompt:
            return "Overall decision: APPROVED FOR DOWNLOAD"
        if "Build a comprehensive Boolean" in prompt:
            return "SEARCHER-STRATEGY"
        if "Structure this into a formal PICO question" in prompt:
            return "FORMULATOR-PICO: adults with fibromyalgia, CBT vs care"
        raise AssertionError("unexpected prompt: " + prompt[:80])
    return fake


def _run(tmp_path, monkeypatch, fail_pmid=None):
    monkeypatch.setenv("OLLAMA_CONTEXT", "12000")
    ai_dir = tmp_path / "prompts"
    ai_dir.mkdir()
    for role in ROLES:
        (ai_dir / f"{role}-prompt.md").write_text(
            "ROLE PROMPT " + role, encoding="utf-8")
    for d in ("input/rct_search", "output/rct_search", "reports",
              "docs/rct_search", "input/sr"):
        (tmp_path / d).mkdir(parents=True, exist_ok=True)
    out_dir = tmp_path / "output" / "rct_search"
    prompts = []
    with patch.object(m, "BASE", tmp_path), \
         patch.object(m, "INPUT_DIR", tmp_path / "input"), \
         patch.object(m, "OUTPUT_RCT_SEARCH", out_dir), \
         patch.object(m, "REPORTS_DIR", tmp_path / "reports"), \
         patch.object(m, "DOCS_RCT_SEARCH", tmp_path / "docs" / "rct_search"), \
         patch.object(m, "INPUT_SR", tmp_path / "input" / "sr"), \
         patch.object(m, "AI_DIR", ai_dir), \
         patch.object(m, "call_ai", _fake_ai(prompts, fail_pmid)), \
         patch.object(m, "fetch_pubmed_articles",
                      return_value=[dict(a) for a in ARTICLES]), \
         patch.object(m, "fetch_europepmc_articles", return_value=[]), \
         patch("builtins.input", lambda *a: TOPIC):
        m.run_rct_search_pipeline(provider="ollama", model="x",
                                  reports_dir=tmp_path / "reports",
                                  dry_run=False)
    saved = list(out_dir.glob("pico_*.json"))
    assert len(saved) == 1
    data = json.loads(saved[0].read_text(encoding="utf-8"))
    return prompts, data["ranked_articles"]


def test_local_run_ranks_in_batches(tmp_path, monkeypatch):
    prompts, ranked = _run(tmp_path, monkeypatch)
    assert len(prompts) >= 2
    assert all(len(p) <= BUDGET for p in prompts)
    seen = [p for pr in prompts for p in PMID_LINE.findall(pr)]
    assert sorted(seen) == sorted(a["pmid"] for a in ARTICLES)
    assert len(ranked) == 6
    assert all(r["score"] is not None for r in ranked)


def test_failed_batch_unscores_only_its_records(tmp_path, monkeypatch, capsys):
    prompts, ranked = _run(tmp_path, monkeypatch, fail_pmid="1000")
    by_pmid = {r["pmid"]: r["score"] for r in ranked}
    assert by_pmid["1000"] is None
    assert any(s is not None for s in by_pmid.values())
    assert "failed: Ollama timed out" in capsys.readouterr().out
