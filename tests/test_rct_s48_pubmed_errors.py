"""Session 48: menu 5 PubMed errors print a line; requests time out.

Before, a failed PubMed search, fetch or XML parse returned 0 records
with no message (a failed Europe PMC search already printed a line), and
neither urlopen call had a timeout, so a stalled connection could hang
the run. Now each failure prints one [PubMed] line and still returns [];
both requests use timeout=30.
"""
import json
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "SOURCE_CODE"))

from pipelines.rct_search.rct_search import fetch_pubmed_articles  # noqa: E402

SEARCH_OK = json.dumps({"esearchresult": {"idlist": ["12345"]}}).encode()
FETCH_OK = (b"<PubmedArticleSet><PubmedArticle><MedlineCitation>"
            b"<PMID>12345</PMID><Article><ArticleTitle>Real title"
            b"</ArticleTitle><Abstract><AbstractText>Abs</AbstractText>"
            b"</Abstract></Article></MedlineCitation></PubmedArticle>"
            b"</PubmedArticleSet>")


class _Resp:
    def __init__(self, body):
        self._body = body

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _fake(answers, calls):
    """answers: one item per call; bytes = body, Exception = raised."""
    seq = list(answers)

    def urlopen(url, timeout=None, **kw):
        calls.append(timeout)
        item = seq.pop(0)
        if isinstance(item, Exception):
            raise item
        return _Resp(item)
    return urlopen


def _run(answers):
    calls = []
    with patch("urllib.request.urlopen", _fake(answers, calls)):
        result = fetch_pubmed_articles("cbt fibromyalgia", max_results=5)
    return result, calls


def test_search_failure_prints_line(capsys):
    result, _ = _run([OSError("search boom")])
    assert result == []
    assert "[PubMed] Search failed: search boom" in capsys.readouterr().out


def test_fetch_failure_prints_line(capsys):
    result, _ = _run([SEARCH_OK, OSError("fetch boom")])
    assert result == []
    assert "[PubMed] Fetch failed: fetch boom" in capsys.readouterr().out


def test_bad_xml_prints_line(capsys):
    result, _ = _run([SEARCH_OK, b"<not xml"])
    assert result == []
    assert "[PubMed] XML could not be read:" in capsys.readouterr().out


def test_success_uses_timeout_and_returns_records():
    result, calls = _run([SEARCH_OK, FETCH_OK])
    assert [a["pmid"] for a in result] == ["12345"]
    assert result[0]["title"] == "Real title"
    assert calls == [30, 30]
