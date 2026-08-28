"""
Doc-sync guard for the source-quote tripwire (Session 24).

REVIEWER_GUIDE.md §2.2 numbers the branches of
DataExtractor._flag_suspect_source_quotes, and HANDOFF.md states the count
in prose. Both are claims that nothing re-verified; between Sessions 22 and
23 one said "six" while the code had five. This test derives the count
from SOURCE_QUOTE_WARNING_BRANCHES in the extractor so a branch added
without touching the docs turns CI red instead of rotting silently.

Run with: python -m pytest tests/test_source_quote_doc_sync.py -v
"""
import re
from pathlib import Path

from pipelines.sr.src.extraction.data_extractor import SOURCE_QUOTE_WARNING_BRANCHES

REPO = Path(__file__).resolve().parents[1]

def _find_doc(name: str) -> Path:
    hits = [p for p in REPO.rglob(name)
            if ".venv" not in p.parts and "archive" not in p.name.lower()]
    assert len(hits) == 1, f"expected exactly one {name} in repo, found {hits}"
    return hits[0]


GUIDE = _find_doc("REVIEWER_GUIDE.md")
HANDOFF = _find_doc("HANDOFF.md")

_WORDS = {"three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8}


def _section_2_2() -> str:
    text = GUIDE.read_text(encoding="utf-8")
    body = text.split("### 2.2", 1)[1]
    # Stop at the next heading of any level.
    return re.split(r"\n#{2,3} ", body, maxsplit=1)[0]


def test_reviewer_guide_branch_count_matches_extractor():
    numbered = re.findall(r"^\d+\. \*\*", _section_2_2(), flags=re.M)
    assert len(numbered) == len(SOURCE_QUOTE_WARNING_BRANCHES), (
        f"REVIEWER_GUIDE.md §2.2 numbers {len(numbered)} branches; "
        f"extractor defines {len(SOURCE_QUOTE_WARNING_BRANCHES)}. Update the doc."
    )


def test_handoff_branch_count_matches_extractor():
    handoff = HANDOFF.read_text(encoding="utf-8")
    hits = re.findall(r"actually fires\s+on\s+(\w+)", handoff)
    assert hits, "HANDOFF.md no longer states the branch count; update this test"
    for word in hits:
        assert _WORDS.get(word) == len(SOURCE_QUOTE_WARNING_BRANCHES), (
            f"HANDOFF.md says the tripwire fires on {word!r} branches; "
            f"extractor defines {len(SOURCE_QUOTE_WARNING_BRANCHES)}"
        )
