"""Session 48: menu 4 article type 5 (Protocol) must find protocols.

The old filter "research support[pt]" marks funded research of any kind.
The new filter is bracketed because _pubmed_search joins it as
"(query) AND <filter>"; without brackets an OR would escape the AND.
"""
from pathlib import Path

from pipelines.search import search as s

NEW_FILTER = (
    '("clinical trial protocol"[pt]'
    ' OR "study protocol"[ti] OR "trial protocol"[ti]'
    ' OR "review protocol"[ti] OR "protocol for a"[ti]'
    ' OR "protocol design"[ti])'
)


def test_protocol_filter_finds_protocols():
    assert list(s.ARTICLE_TYPES) == [str(i) for i in range(1, 9)]
    label, filt = s.ARTICLE_TYPES["5"]
    assert label == "Protocol"
    assert filt == NEW_FILTER


def test_no_research_support_filter():
    bad = [k for k, (_, f) in s.ARTICLE_TYPES.items()
           if "research support" in f.lower()]
    assert bad == []


def test_or_filters_are_fully_bracketed():
    for key, (_, f) in s.ARTICLE_TYPES.items():
        assert f.count("(") == f.count(")"), key
        if " OR " in f:
            assert f.startswith("(") and f.endswith(")"), key


def test_query_is_bracketed_before_and():
    src = Path(s.__file__).read_text(encoding="utf-8")
    assert 'search_term = f"({query})"' in src
    assert 'search_term += f" AND {article_filter}"' in src
