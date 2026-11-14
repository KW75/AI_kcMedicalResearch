"""Session 38 (7k, option B): a reviewer can exclude a study from the
meta-analysis with a reason (study_overrides.yaml exclude_from_meta), and the
HTML/PDF report lists every study not pooled, with its reason. Before: unknown
override keys were dropped (study_overrides.py lines 258-263) and no report
mentioned skip_reason, so Ang and Jensen left the pool without explanation.
No PDFs, no AI."""
import inspect
import logging
from pathlib import Path

import yaml

try:
    from pipelines.sr.src.extraction import study_overrides as so
    from pipelines.sr.src.utils import audit_logger as al
    from pipelines.sr.src.reporting import html_report as hr
    from pipelines.sr.src.reporting import pdf_report as pr
except ImportError:
    from SOURCE_CODE.pipelines.sr.src.extraction import study_overrides as so
    from SOURCE_CODE.pipelines.sr.src.utils import audit_logger as al
    from SOURCE_CODE.pipelines.sr.src.reporting import html_report as hr
    from SOURCE_CODE.pipelines.sr.src.reporting import pdf_report as pr

ROOT = Path(__file__).resolve().parents[1]
MAIN_SRC = ROOT / "SOURCE_CODE" / "pipelines" / "sr" / "main.py"
REASON = ("clinical pain (FIQ pain) reported only as Week 6 change scores; "
          "Table 2 values are the NFR pain rating")

META = [
    {"first_author": "Ang", "year": 2010, "included_in_meta": False,
     "skip_reason": f"excluded by reviewer: {REASON}"},
    {"first_author": "Jensen", "year": 2012, "included_in_meta": False,
     "skip_reason": "insufficient mean/SD/N to derive effect size"},
    {"first_author": "Karlsson", "year": 2015, "included_in_meta": True, "skip_reason": None},
    {"first_author": "Lami", "year": 2018, "included_in_meta": True, "skip_reason": None},
    {"first_author": "McCrae", "year": 2019, "included_in_meta": True, "skip_reason": None},
]


def _ovr(tmp_path, entry):
    p = tmp_path / "ovr.yaml"
    p.write_text(yaml.safe_dump({"ang.pdf": entry}), encoding="utf-8")
    return so.StudyOverrides(path=str(p))


def test_exclude_key_is_accepted(tmp_path, caplog):
    with caplog.at_level(logging.WARNING):
        o = _ovr(tmp_path, {"first_author": "Ang", "exclude_from_meta": REASON})
    assert "unknown fields" not in caplog.text
    assert o.lookup("ang.pdf").get("exclude_from_meta") == REASON


def test_apply_carries_the_reason_and_leaves_values(tmp_path):
    o = _ovr(tmp_path, {"exclude_from_meta": REASON})
    r = o.apply({"filename": "ang.pdf",
                 "primary_outcome": {"mean_intervention": -20.2}}, "ang.pdf")
    assert r["reviewer_exclusion"] == REASON
    assert "exclude_from_meta" in r["override_fields"]
    assert r["primary_outcome"]["mean_intervention"] == -20.2


def test_reviewer_exclusion_reason():
    assert (al.reviewer_exclusion_reason({"reviewer_exclusion": REASON})
            == f"excluded by reviewer: {REASON}")
    assert al.reviewer_exclusion_reason({}) is None
    assert al.reviewer_exclusion_reason({"reviewer_exclusion": "  "}) is None


def test_main_checks_exclusion_before_gate_and_effect_size():
    src = MAIN_SRC.read_text(encoding="utf-8")
    i = src.find("reviewer_exclusion_reason(r")
    g = src.find("_review = review_skip_reason(")
    assert i != -1, "main.py does not check reviewer exclusions"
    assert i < g, "exclusion must come before the review gate"
    assert "continue" in src[i:g], "excluded study must skip effect size and [SENSITIVITY]"


def test_report_lists_studies_not_pooled():
    h = hr.HTMLReportGenerator()._not_pooled_html(META)
    assert "Studies included in the review but not in the meta-analysis" in h
    assert "3 of 5 studies pooled" in h
    assert "Ang (2010)" in h and "Jensen (2012)" in h
    assert "Karlsson" not in h
    assert "FIQ pain" in h and "insufficient mean/SD/N" in h
    assert "Reviewer" in h and "Automatic" in h


def test_report_says_none_when_all_pooled():
    allin = [dict(r, included_in_meta=True, skip_reason=None) for r in META]
    h = hr.HTMLReportGenerator()._not_pooled_html(allin)
    assert "5 of 5 studies pooled" in h and "none" in h.lower()


def test_reports_accept_meta_audit_and_template_has_section():
    for gen in (hr.HTMLReportGenerator.generate, pr.PDFReportGenerator.generate):
        assert "meta_audit" in inspect.signature(gen).parameters
    assert "{not_pooled_html}" in hr.HTML_TEMPLATE

# --- Session 38 (7n e): report wording for the not-pooled table.
# Statistical reasons stay verbatim (exact for technical readers); only
# pipeline-internal text (file paths, flag names, code syntax) is reworded.
# The CSV/console keep the technical skip_reason unchanged.
import pytest

_REVIEW_TAIL = (" - verify against the PDF, or enter the values in "
                "input/sr/study_overrides.yaml with a source-page note")
NEEDS_REVIEW = ("needs review: runs disagree (mean_intervention:no_majority|"
                "mean_control:no_majority)" + _REVIEW_TAIL)
TABLE_SHIFT = "needs review: runs disagree (table_shift)" + _REVIEW_TAIL
INSUFFICIENT = "insufficient mean/SD/N to derive effect size"
TECH_WORDS = ("study_overrides", "no_majority", "table_shift", "needs review", "; also:")


def test_plain_reason_needs_review_names_fields_hides_internal_text():
    out = hr.plain_skip_reason(NEEDS_REVIEW)
    assert "repeated readings" in out
    assert "intervention mean" in out and "control mean" in out
    for w in TECH_WORDS:
        assert w not in out


def test_plain_reason_table_shift():
    out = hr.plain_skip_reason(TABLE_SHIFT)
    assert "neighbouring table row" in out
    for w in TECH_WORDS:
        assert w not in out


def test_plain_reason_combined_keeps_statistical_part_exact():
    out = hr.plain_skip_reason(f"{NEEDS_REVIEW}; also: {INSUFFICIENT}")
    assert "repeated readings" in out
    assert f"Also: {INSUFFICIENT}" in out
    for w in TECH_WORDS:
        assert w not in out


def test_plain_reason_reviewer_text_kept():
    out = hr.plain_skip_reason(f"excluded by reviewer: {REASON}")
    assert out == f"Excluded by the reviewer: {REASON}"


@pytest.mark.parametrize("raw", [
    INSUFFICIENT,
    "missing effect_estimate/CI (no raw-mean fallback for OR/RR)",
    "insufficient df for Hedges g",
    "pooled SD is zero",
])
def test_plain_reason_statistical_messages_verbatim(raw):
    assert hr.plain_skip_reason(raw) == raw


def test_plain_reason_outcome_mismatch_keeps_rationale():
    out = hr.plain_skip_reason("outcome_match=False: measures anxiety, not pain")
    assert out == "Outcome does not match the review outcome: measures anxiety, not pain"


def test_plain_reason_unknown_unchanged_and_empty():
    assert hr.plain_skip_reason("some new reason") == "some new reason"
    assert hr.plain_skip_reason(None) == "no reason recorded"
    assert hr.plain_skip_reason("") == "no reason recorded"


def test_report_shows_plain_reason_and_keeps_decided_by():
    rows = [
        {"first_author": "Ang", "year": 2010, "included_in_meta": False,
         "skip_reason": f"excluded by reviewer: {REASON}"},
        {"first_author": "Jensen", "year": 2012, "included_in_meta": False,
         "skip_reason": f"{NEEDS_REVIEW}; also: {INSUFFICIENT}"},
        {"first_author": "Karlsson", "year": 2015, "included_in_meta": True,
         "skip_reason": None},
    ]
    html = hr.HTMLReportGenerator()._not_pooled_html(rows)
    assert "1 of 3 studies pooled" in html
    assert "Reviewer" in html and "Automatic" in html
    assert "repeated readings" in html and INSUFFICIENT in html
    for w in ("study_overrides", "no_majority", "needs review"):
        assert w not in html

