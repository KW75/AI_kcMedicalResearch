"""Session 48: PubMed abstracts are matched to records by PMID.

Before, _pubmed_fetch_abstracts asked for plain text, split it on blank
lines and gave block i to record i, so an abstract could end up under
the wrong record. A failed fetch was silent (except: pass).
"""
from unittest.mock import MagicMock, patch

import pytest

from pipelines.search import search as s

# PubMed order differs from the records; 222 has no abstract; 111 is
# structured, has inline markup, and cites another PMID (999) later on.
XML = """<?xml version="1.0" ?>
<PubmedArticleSet>
<PubmedArticle><MedlineCitation><PMID Version="1">333</PMID><Article>
<ArticleTitle>C</ArticleTitle><Abstract><AbstractText>Abstract of 333.\
</AbstractText></Abstract></Article></MedlineCitation></PubmedArticle>
<PubmedArticle><MedlineCitation><PMID Version="1">111</PMID><Article>
<ArticleTitle>A</ArticleTitle><Abstract>
<AbstractText Label="BACKGROUND">Why.</AbstractText>
<AbstractText Label="RESULTS">What <i>was</i> found.</AbstractText>
</Abstract></Article></MedlineCitation><PubmedData><ReferenceList>
<Reference><ArticleIdList><ArticleId IdType="pubmed">999</ArticleId>
</ArticleIdList></Reference></ReferenceList></PubmedData></PubmedArticle>
<PubmedArticle><MedlineCitation><PMID Version="1">222</PMID><Article>
<ArticleTitle>B</ArticleTitle></Article></MedlineCitation></PubmedArticle>
</PubmedArticleSet>
"""


def _articles():
    return [{"uid": u, "abstract": ""} for u in ("111", "222", "333")]


def _resp(xml=XML):
    r = MagicMock()
    r.content = xml.encode("utf-8")
    r.text = xml
    r.raise_for_status.return_value = None
    return r


def test_abstracts_matched_by_pmid_not_position():
    with patch.object(s.requests, "get", return_value=_resp()):
        out = s._pubmed_fetch_abstracts(_articles())
    by_uid = {a["uid"]: a["abstract"] for a in out}
    assert by_uid["333"] == "Abstract of 333."
    assert by_uid["222"] == ""
    assert by_uid["111"].startswith("BACKGROUND: Why.")


def test_structured_abstract_keeps_labels_and_inline_text():
    with patch.object(s.requests, "get", return_value=_resp()):
        out = s._pubmed_fetch_abstracts(_articles())
    assert out[0]["abstract"] == "BACKGROUND: Why.\nRESULTS: What was found."


def test_requests_xml_not_text():
    with patch.object(s.requests, "get", return_value=_resp()) as get:
        s._pubmed_fetch_abstracts(_articles())
    assert get.call_args.kwargs["params"]["retmode"] == "xml"


@pytest.mark.parametrize("how", ["network", "http"])
def test_fetch_error_prints_line_and_keeps_records(how, capsys):
    if how == "network":
        ctx = patch.object(s.requests, "get", side_effect=Exception("boom"))
    else:
        r = _resp()
        r.raise_for_status.side_effect = Exception("503 Server Error")
        ctx = patch.object(s.requests, "get", return_value=r)
    with ctx:
        out = s._pubmed_fetch_abstracts(_articles())
    text = capsys.readouterr().out
    assert "[SEARCH] PubMed abstract fetch error:" in text
    assert "summary uses titles only." in text
    assert [a["uid"] for a in out] == ["111", "222", "333"]
    assert all(a["abstract"] == "" for a in out)


def test_no_articles_makes_no_request():
    with patch.object(s.requests, "get") as get:
        assert s._pubmed_fetch_abstracts([]) == []
    get.assert_not_called()
