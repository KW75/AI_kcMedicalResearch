"""
Regression tests for v2.4.12's source-quote verification (#48/#38) and the
'null'-sentinel group-label fix (#57).

Companion to test_data_extractor_flags.py - kept in a separate file so a
failure in the newer checks does not obscure the Session 12 tripwires.

The source-quote check binds verification to the numbers rather than to
the labels: the extraction schema now requires a verbatim per-arm quote
alongside every mean/SD, and _flag_suspect_source_quotes checks that (a)
the quote exists, (b) the extracted number actually appears in its own
quote, (c) an SD's quote does not carry an SE/SEM label, (d) the quote
does not describe a within-subject / multiple-timepoint contrast, and,
on the text path only, (e) the quote is present verbatim in the source.

All tests exercise pure logic - no network, no PDF, no real API key.

Run with: python -m pytest tests/test_data_extractor_source_quotes.py -v
"""
import pytest

from pipelines.sr.src.extraction.data_extractor import DataExtractor


@pytest.fixture
def extractor():
    return DataExtractor(
        pico_criteria={"outcome": "pain"},
        provider="qwen",
        api_key="dummy-not-a-real-key",
    )


# The exact documented zsy234 sentence from Session 8's post-mortem and
# reproduced in the v2.4.12 real run 20260826_113816. Both arms' means
# and SEs come from the same quote, which reports a within-subject
# contrast between two timepoints, and labels the dispersion as SE.
ZSY234_QUOTE = (
    "Regardless of treatment condition, participants reported less "
    "morning pain at posttreatment (M = 47.14, SE = 2.36) relative to "
    "baseline (M = 52.67, SE = 2.27)."
)


# ---------------------------------------------------------------------------
# #48: source-quote verification - the primary v2.4.12 tripwire
# ---------------------------------------------------------------------------

def test_source_quote_check_fires_on_zsy234_real_quote(extractor):
    """The exact real-run failure: quote carries an SE label and a
    within-subject 'relative to baseline' phrase for both arms. Must
    fire - this is the paper the mechanism exists to catch. Real run
    20260826_113816 recorded 4 quote flags (SE x2 + multi-timepoint x2)
    on this exact pattern."""
    result = {
        "primary_outcome": {
            "mean_intervention": 47.14, "sd_intervention": 2.36,
            "mean_control": 52.67, "sd_control": 2.27,
            "source_quote_intervention": ZSY234_QUOTE,
            "source_quote_control": ZSY234_QUOTE,
        },
        "extraction_method": "vision_smart",
        "filename": "zsy234.pdf",
    }
    extractor._flag_suspect_source_quotes(result)
    warning = result["source_quote_warning"]
    assert warning is not None
    lower = warning.lower()
    # The two failure signatures the handoff calls out explicitly on this
    # paper's real quote. Both must fire; the check accumulates findings
    # per-arm, so with the same quote on both arms we expect the SE and
    # timepoint mentions to each appear at least once.
    assert ("se" in lower) or ("sem" in lower) or ("standard error" in lower), (
        f"expected SE-label mention in warning, got: {warning!r}"
    )
    # Multiple-timepoint or within-subject phrasing - the check reports the
    # actual timepoint tokens it found ('baseline', 'posttreatment', ...)
    # or the within-subject phrase it matched ('relative to baseline').
    assert ("timepoint" in lower or "within-subject" in lower
            or "baseline" in lower or "relative to" in lower), (
        f"expected timepoint/within-subject mention, got: {warning!r}"
    )


def test_source_quote_check_stays_silent_on_clean_between_group_quote(extractor):
    """A clean single-timepoint between-group quote with genuine SDs must
    not be flagged. Negative control for the zsy234 test."""
    clean_intervention = "At 12 weeks the CBT group had a mean pain score of 4.10 (SD 1.85)."
    clean_control = "At 12 weeks the usual care group had a mean pain score of 5.30 (SD 1.95)."
    result = {
        "primary_outcome": {
            "mean_intervention": 4.10, "sd_intervention": 1.85,
            "mean_control": 5.30, "sd_control": 1.95,
            "source_quote_intervention": clean_intervention,
            "source_quote_control": clean_control,
        },
        "extraction_method": "vision_smart",
    }
    extractor._flag_suspect_source_quotes(result)
    assert result["source_quote_warning"] is None, (
        f"clean between-group quote must not trip the source-quote check; "
        f"got: {result['source_quote_warning']!r}"
    )
    # v2.4.12 contract: key ALWAYS set, None when clean (Session 14).
    assert "source_quote_warning" in result


def test_source_quote_check_flags_number_not_in_quote(extractor):
    """Jensen-style failure from run 20260826_113816: extracted values are
    absent from their own source quotes (model returned rounded 49.0 while
    the quote reads 49.1). The check must catch this."""
    result = {
        "primary_outcome": {
            "mean_intervention": 49.0, "sd_intervention": 19.0,
            "mean_control": 59.0, "sd_control": 26.0,
            # The quote contains 49.1 / 19.2, NOT 49.0 / 19.0.
            "source_quote_intervention": (
                "CBT group post-treatment: 49.1 (19.2) on the pain scale."
            ),
            "source_quote_control": (
                "Control group post-treatment: 59.2 (26.4) on the pain scale."
            ),
        },
        "extraction_method": "vision_expanded",
    }
    extractor._flag_suspect_source_quotes(result)
    assert result["source_quote_warning"] is not None, (
        "extracted values that do not appear in their own quotes must fire"
    )
    # The check names the mismatch explicitly - not just any warning.
    assert "does not appear" in result["source_quote_warning"].lower(), (
        f"expected 'does not appear' phrasing, got: "
        f"{result['source_quote_warning']!r}"
    )


def test_source_quote_check_tolerates_trailing_zero_formatting(extractor):
    """The handoff specifies a tolerant matcher: 7.4 must match '7.40' in
    the quote (same value, different formatting). Genuinely different
    values (7.45, 176, 76.3) are covered by the number-not-in-quote test
    above. This test covers the tolerant side."""
    result = {
        "primary_outcome": {
            "mean_intervention": 7.4, "sd_intervention": 1.8,
            "mean_control": 8.1, "sd_control": 2.0,
            "source_quote_intervention": (
                "Intervention arm: 7.40 (1.80) at post-treatment."
            ),
            "source_quote_control": (
                "Control arm: 8.10 (2.00) at post-treatment."
            ),
        },
        "extraction_method": "vision_smart",
    }
    extractor._flag_suspect_source_quotes(result)
    assert result["source_quote_warning"] is None, (
        f"trailing-zero formatting must not trip the number-match check; "
        f"got: {result['source_quote_warning']!r}"
    )


def test_source_quote_check_rejects_wrong_decimal_extension(extractor):
    """The tolerant matcher must not over-tolerate: 7.4 must NOT match
    '7.45' in the quote (different value, extra digit). Companion to the
    trailing-zero test above."""
    result = {
        "primary_outcome": {
            "mean_intervention": 7.4, "sd_intervention": 1.8,
            "mean_control": 8.1, "sd_control": 2.0,
            # Quote's intervention mean is 7.45, not 7.4 - must fire.
            "source_quote_intervention": (
                "Intervention arm: 7.45 (1.80) at post-treatment."
            ),
            "source_quote_control": (
                "Control arm: 8.10 (2.00) at post-treatment."
            ),
        },
        "extraction_method": "vision_smart",
    }
    extractor._flag_suspect_source_quotes(result)
    assert result["source_quote_warning"] is not None
    assert "does not appear" in result["source_quote_warning"].lower()


def test_source_quote_check_flags_missing_quote(extractor):
    """A number without a source quote is unauditable - the whole point of
    #48 is that a value the reviewer cannot trace to a source string is
    not verifiable."""
    result = {
        "primary_outcome": {
            "mean_intervention": 4.10, "sd_intervention": 1.85,
            "mean_control": 5.30, "sd_control": 1.95,
            "source_quote_intervention": None,
            "source_quote_control": None,
        },
        "extraction_method": "vision_smart",
    }
    extractor._flag_suspect_source_quotes(result)
    assert result["source_quote_warning"] is not None
    assert "no source quote" in result["source_quote_warning"].lower()


def test_source_quote_check_text_path_flags_quote_absent_from_source(extractor):
    """Text-fallback path only (check 5 in the docstring): if the model's
    quote is not present verbatim in the source text, it may be
    paraphrased or fabricated. When source_text is supplied and the quote
    is not in it, fire."""
    real_source = (
        "===== PDF PAGE 7 | text_score=32 =====\n"
        "0042: At 12 weeks the CBT group had a mean pain score of 4.10 (SD 1.85).\n"
        "0043: At 12 weeks the usual care group had a mean pain score of 5.30 (SD 1.95).\n"
    )
    fabricated_quote = "CBT arm reported a mean pain of 4.10 (SD 1.85)."
    result = {
        "primary_outcome": {
            "mean_intervention": 4.10, "sd_intervention": 1.85,
            "source_quote_intervention": fabricated_quote,
            "source_quote_control": None,   # not the point of this test
        },
        "extraction_method": "text_fallback",
    }
    extractor._flag_suspect_source_quotes(result, source_text=real_source)
    assert result["source_quote_warning"] is not None
    assert ("not found verbatim" in result["source_quote_warning"].lower()
            or "paraphrased or fabricated" in result["source_quote_warning"].lower())


def test_source_quote_check_always_sets_key_on_clean_run(extractor):
    """v2.4.12 contract (Session 14): the key is ALWAYS set (None when
    clean), so extracted_data.csv's dynamically-built columns exist on a
    clean run - a key set only on failure makes 'checked and clean' look
    identical to 'never ran' in the CSV."""
    result = {
        "primary_outcome": {
            "mean_intervention": 4.10, "sd_intervention": 1.85,
            "mean_control": 5.30, "sd_control": 1.95,
            "source_quote_intervention": "CBT arm: 4.10 (1.85) at post-treatment.",
            "source_quote_control": "Control arm: 5.30 (1.95) at post-treatment.",
        },
        "extraction_method": "vision_smart",
    }
    extractor._flag_suspect_source_quotes(result)
    assert "source_quote_warning" in result
    assert result["source_quote_warning"] is None


# ---------------------------------------------------------------------------
# #57: 'null' string sentinel must behave like JSON null at every read site
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("sentinel", [
    "null", "NULL", "None", "n/a", "N/A", "NA", "nan",
    "not reported", "Not Stated", "not specified",
    "unknown", "unclear", "-", " ", "",
])
def test_clean_group_label_rejects_sentinels(extractor, sentinel):
    """Every documented decline sentinel must be normalized to None so a
    truthy string like 'null' never masquerades as a real arm name
    (real-run incident: run 20260826_111938, Lami). Case-insensitive,
    whitespace-tolerant."""
    assert extractor._clean_group_label(sentinel) is None


@pytest.mark.parametrize("value", ["CBT", "Usual Medical Care", "Placebo",
                                    "Waitlist Control", "Metformin"])
def test_clean_group_label_preserves_real_names(extractor, value):
    """Genuine arm names, including ones that CONTAIN the word 'Control',
    must pass through unchanged - the sentinel check must not over-match."""
    assert extractor._clean_group_label(value) == value


def test_null_sentinel_does_not_trip_identical_labels_check(extractor):
    """Before #57's fix: the follow-up returned the string 'null' for both
    fields, the identical-labels check saw two truthy strings and fired
    with a misleading within/between message. After: both are normalized
    to None and the check finds nothing to compare."""
    result = {
        "intervention_group": "null",
        "control_group": "null",
    }
    extractor._flag_group_timepoint_confusion(result)
    assert result["group_timepoint_warning"] is None, (
        f"'null' sentinels must not fire the identical-labels check; "
        f"got: {result['group_timepoint_warning']!r}"
    )


def test_null_sentinel_at_main_extraction_does_not_suppress_followup(extractor):
    """Before #57's fix: a truthy sentinel from the MAIN extraction would
    have caused _needs_group_labels() to skip the follow-up entirely,
    silently accepting the sentinel as a real answer. This is the
    'suppression' scenario the handoff calls out."""
    result = {
        "intervention_group": "null",
        "control_group": "N/A",
    }
    assert extractor._needs_group_labels(result) is True, (
        "truthy sentinel strings must NOT suppress the group-label "
        "follow-up - that was the mechanism that silently accepted "
        "'null' as a real answer before #57"
    )


def test_real_arm_names_do_suppress_followup(extractor):
    """Companion to the sentinel-suppression test: genuine arm names SHOULD
    suppress the follow-up (the follow-up exists to fill a gap, not to
    second-guess an answer that's already there)."""
    result = {
        "intervention_group": "CBT",
        "control_group": "Usual Medical Care",
    }
    assert extractor._needs_group_labels(result) is False

def test_integer_in_quote_matches_float_extraction():
    """Jensen 2012 case (#62): paper prints '49', extraction stores 49.0.
    The tolerant matcher should treat integer-valued floats as matching
    their integer form in the quote."""
    from pipelines.sr.src.extraction.data_extractor import DataExtractor

    result = {
        "filename": "jensen_test.pdf",
        "primary_outcome": {
            "mean_intervention": 49.0,
            "sd_intervention": 19.0,
            "mean_control": 59.0,
            "sd_control": 26.0,
            "source_quote_intervention": "Posttreat CBT: 49 \u00b1 19",
            "source_quote_control": "Posttreat controls: 59 \u00b1 26",
        },
    }
    extractor = DataExtractor.__new__(DataExtractor)
    extractor._flag_suspect_source_quotes(result)

    warning = result.get("source_quote_warning")
    # The tripwire must not flag "does not appear" - all four integer
    # values are present in their quotes as integers.
    assert warning is None or "does not appear" not in warning, (
        f"False-positive on integer-in-quote / float-in-extraction: {warning}"
    )
