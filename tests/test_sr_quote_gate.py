"""Session 41 option B: quote gate (extends the F4 gate).

Run 20261114_202253 pooled Karlsson (S1877886015000567) with three wrong
numbers (mean_int 3.61 vs 3.88, sd_int 0.85 vs 1.05, sd_ctrl 0.92 vs 0.75):
the N=3 runs agreed on the same misread, nondet_flag was only
'mean_control:majority', and both source quotes were "not found verbatim".
Run 20261114_133303 did the same for Lami with a unanimous vote.
Rule: numbers read from page images (extraction_method not starting with
"text", or missing) whose source quote was not found in the paper text
need review (token quote_not_found) and stay out of the primary pool until
a reviewer overrides all four means/SDs in input/sr/study_overrides.yaml.
Text-extracted studies keep today's behaviour.
"""
from pathlib import Path

from pipelines.sr.src.utils import audit_logger as audit

NOT_FOUND = (
    "intervention source quote was not found verbatim in the extracted "
    "source text - it may be paraphrased or fabricated | control source "
    "quote was not found verbatim in the extracted source text - it may be "
    "paraphrased or fabricated")
# Session 42: the mean/SD-not-in-quote warning now has its own gate
# (number_not_in_quote); these two warnings must still trip no gate.
OTHER_ONLY = ("control N (41) does not appear in its own source quote (quote "
              "has 36) - check the analysed N for this arm (F8) | intervention "
              "SD (2.1) was quoted from text containing 'SE'/'SEM'/'standard "
              "error' - verify this is really an SD, not a standard error "
              "(Known Issue #9)")
ALL_FOUR = ("mean_intervention(3.61->3.88); sd_intervention(0.85->1.05); "
            "mean_control(confirmed 3.67); sd_control(0.92->0.75)")
THREE = ("mean_intervention(3.61->3.88); sd_intervention(0.85->1.05); "
         "sd_control(0.92->0.75)")
MAIN = (Path(__file__).resolve().parents[1]
        / "SOURCE_CODE" / "pipelines" / "sr" / "main.py")


def gate(cell, overrides=None, warn=None, method="vision_smart"):
    return audit.review_skip_reason(cell, overrides, quote_warning=warn,
                                    extraction_method=method)


def test_karlsson_unanimous_misread_needs_review():
    r = gate("mean_control:majority", warn=NOT_FOUND)
    assert r and "quote_not_found" in r
    assert "study_overrides.yaml" in r


def test_lami_unanimous_needs_review():
    assert "quote_not_found" in (gate("unanimous", warn=NOT_FOUND) or "")


def test_anthropic_file_counts_as_page_images():
    r = gate("not_checked", warn=NOT_FOUND, method="anthropic_file")
    assert "quote_not_found" in (r or "")


def test_unknown_method_is_treated_as_page_images():
    r = gate("unanimous", warn=NOT_FOUND, method=None)
    assert "quote_not_found" in (r or "")


def test_all_four_overrides_clear_it():
    assert gate("mean_control:majority", ALL_FOUR, NOT_FOUND) is None


def test_three_overrides_do_not_clear_it():
    assert "quote_not_found" in (gate("unanimous", THREE, NOT_FOUND) or "")


def test_both_reasons_named_when_both_open():
    r = gate("sd_control:no_majority", None, NOT_FOUND) or ""
    assert "sd_control:no_majority" in r and "quote_not_found" in r


def test_text_fallback_unchanged():
    assert gate("unanimous", warn=NOT_FOUND, method="text_fallback") is None


def test_other_quote_warnings_do_not_trip_the_gate():
    assert gate("unanimous", warn=OTHER_ONLY) is None


def test_no_warning_is_pooled():
    assert gate("unanimous", warn=None) is None
    assert gate("unanimous", warn="") is None


def test_old_two_argument_call_unchanged():
    assert audit.review_skip_reason("mean_control:majority") is None
    assert "table_shift" in audit.review_skip_reason("table_shift")


def test_main_passes_quote_and_method_to_gate():
    src = MAIN.read_text(encoding="utf-8")
    i = src.index("_review = review_skip_reason(")
    call = src[i:i + 400]
    assert "quote_warning=" in call
    assert "extraction_method=" in call


QUOTE_REASON = ("needs review: source quote not found (quote_not_found) - "
                "numbers read from page images; verify all four means/SDs "
                "against the PDF and enter them in "
                "input/sr/study_overrides.yaml with a source-page note")
SHIFT_REASON = ("needs review: runs disagree (table_shift) - verify against "
                "the PDF, or enter the values in input/sr/study_overrides.yaml "
                "with a source-page note")


def _hr():
    import importlib
    return importlib.import_module("pipelines.sr.src.reporting.html_report")


def test_gate_reason_text_is_pinned():
    assert gate("unanimous", warn=NOT_FOUND) == QUOTE_REASON


def test_plain_wording_quote_only():
    s = _hr().plain_skip_reason(QUOTE_REASON)
    assert "page images" in s and "not found in the paper" in s
    assert "different values" not in s


def test_plain_wording_shift_plus_quote():
    s = _hr().plain_skip_reason(SHIFT_REASON + "; also: " + QUOTE_REASON)
    assert "neighbouring table row" in s and "page images" in s


# --- Session 42 item 3: number not in its own (found) source quote ----------
# Run 20261114_224231: Ang's control mean -8.9 / SD 25.3 were not in their
# own quote although the quote was found verbatim; only table_shift kept Ang
# out. Same rule as quote_not_found: page images only, cleared by all four
# means/SDs. The F8 N warning is not caught (overriding means/SDs cannot fix N).

ANG = ("control mean (-8.9) does not appear in its own source quote - the "
       "quote does not support this number | control SD (25.3) does not "
       "appear in its own source quote - the quote does not support this number")
NUMBER_REASON = ("needs review: a mean/SD is not in its own source quote "
                 "(number_not_in_quote) - numbers read from page images; verify "
                 "all four means/SDs against the PDF and enter them in "
                 "input/sr/study_overrides.yaml with a source-page note")
EXTRACTOR = (Path(__file__).resolve().parents[1] / "SOURCE_CODE" / "pipelines"
             / "sr" / "src" / "extraction" / "data_extractor.py")


def test_ang_number_not_in_own_quote_needs_review():
    assert gate("unanimous", warn=ANG) == NUMBER_REASON


def test_number_gate_cleared_by_all_four_overrides():
    assert gate("unanimous", ALL_FOUR, ANG) is None


def test_number_gate_three_overrides_do_not_clear_it():
    assert "number_not_in_quote" in (gate("unanimous", THREE, ANG) or "")


def test_number_gate_text_fallback_unchanged():
    assert gate("unanimous", warn=ANG, method="text_fallback") is None


def test_quote_not_found_and_number_gate_both_named():
    r = gate("unanimous", warn=NOT_FOUND + " | " + ANG) or ""
    assert "quote_not_found" in r and "number_not_in_quote" in r


def test_number_gate_marker_matches_extractor_wording():
    src = EXTRACTOR.read_text(encoding="utf-8")
    assert audit.NUMBER_NOT_IN_QUOTE_MARKER in src
    assert audit.NUMBER_NOT_IN_QUOTE_MARKER not in "check the analysed N for this arm (F8)"


def test_plain_wording_number_only():
    s = _hr().plain_skip_reason(NUMBER_REASON)
    assert "not in its own source quote" in s and "page images" in s
    assert "not found in the paper" not in s
    assert "different values" not in s
