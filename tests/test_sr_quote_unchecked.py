"""Session 41 empty-text gap + missing-quote hole (quote gate follow-up).

1) _flag_suspect_source_quotes ran the verbatim check only `if source_text:`.
   With no paper text it wrote nothing, and the quote gate pooled the study.
   Now the production calls pass require_source_text=True: a quote with no
   (or whitespace-only) paper text warns "could not be checked against the
   paper text". Calls without the keyword keep the old behaviour.
2) A page-image study with NO quote ("no source quote provided") was pooled,
   because the gate only looked for "was not found verbatim".
Both now count as unverified: page-image studies need review until all four
means/SDs are overridden. Text-fallback studies are unchanged. Branch count
stays 5 (the new outcome belongs to branch 5, verbatim_mismatch).
"""
import importlib
import re
from pathlib import Path

from pipelines.sr.src.extraction.data_extractor import (
    DataExtractor, SOURCE_QUOTE_WARNING_BRANCHES)
from pipelines.sr.src.utils import audit_logger as audit

REPO = Path(__file__).resolve().parents[1]
DE = REPO / "SOURCE_CODE" / "pipelines" / "sr" / "src" / "extraction" / "data_extractor.py"
GUIDE = REPO / "docs" / "sr" / "REVIEWER_GUIDE.md"
UNCHECKED = ("intervention source quote could not be checked against the paper "
             "text - no paper text was available")
MISSING = ("no source quote provided for the intervention values - the numbers "
           "cannot be audited against the source text")
ALL_FOUR = ("mean_intervention(3.61->3.88); sd_intervention(0.85->1.05); "
            "mean_control(confirmed 3.67); sd_control(0.92->0.75)")


def _res():
    return {"filename": "k.pdf", "primary_outcome": {
        "mean_intervention": 3.88, "sd_intervention": 1.05,
        "mean_control": 3.67, "sd_control": 0.75,
        "source_quote_intervention": "CBT 3.88 (1.05)",
        "source_quote_control": "WLC 3.67 (0.75)"}}


def _check(source_text, **kw):
    ex = DataExtractor.__new__(DataExtractor)
    return ex._flag_suspect_source_quotes(_res(), source_text=source_text,
                                          **kw)["source_quote_warning"]


def gate(warn, method="vision_smart", overrides=None):
    return audit.review_skip_reason("unanimous", overrides, quote_warning=warn,
                                    extraction_method=method)


def test_no_paper_text_warns_unchecked_for_both_arms():
    w = _check(None, require_source_text=True) or ""
    assert w.count("could not be checked against the paper text") == 2


def test_whitespace_paper_text_warns_unchecked():
    w = _check("  \n ", require_source_text=True) or ""
    assert w.count("could not be checked against the paper text") == 2


def test_default_call_without_text_unchanged():
    assert _check(None) is None


def test_quote_found_in_text_no_warning():
    text = "Table 2. CBT 3.88 (1.05) vs WLC 3.67 (0.75) after therapy."
    assert _check(text, require_source_text=True) is None


def test_quote_not_in_text_still_not_found():
    w = _check("Completely different text about sleep.",
               require_source_text=True) or ""
    assert "was not found verbatim" in w
    assert "could not be checked" not in w


def test_both_production_calls_require_text():
    assert DE.read_text(encoding="utf-8").count("require_source_text=True") == 2


def test_gate_blocks_unchecked_on_page_images():
    assert "quote_not_found" in (gate(UNCHECKED) or "")


def test_gate_blocks_missing_quote_on_anthropic_file():
    assert "quote_not_found" in (gate(MISSING, method="anthropic_file") or "")


def test_gate_text_fallback_unchanged():
    assert gate(UNCHECKED, method="text_fallback") is None
    assert gate(MISSING, method="text_fallback") is None


def test_gate_all_four_overrides_clear_unchecked():
    assert gate(UNCHECKED, overrides=ALL_FOUR) is None


def test_plain_wording_covers_missing_and_unchecked():
    hr = importlib.import_module("pipelines.sr.src.reporting.html_report")
    s = hr.plain_skip_reason(audit.QUOTE_GATE_REASON)
    assert "missing" in s and "could not be checked" in s
    assert "page images" in s and "not found in the paper" in s


def test_branch_count_stays_five():
    assert len(SOURCE_QUOTE_WARNING_BRANCHES) == 5


def test_reviewer_guide_item5_mentions_unchecked():
    body = GUIDE.read_text(encoding="utf-8").split("### 2.2", 1)[1]
    sec = re.split(r"\n#{2,3} ", body, maxsplit=1)[0]
    assert "could not be checked against the paper text" in sec