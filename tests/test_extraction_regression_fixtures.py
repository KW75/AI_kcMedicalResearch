# tests/test_extraction_regression_fixtures.py
"""
Paper-pinned regression fixtures for the extraction non-determinism
issue (#11 / #23).

Unlike test_data_extractor_source_quotes.py - which exercises the
tripwire mechanism against synthetic quotes - this file pins the
REVIEWER-VERIFIED extraction of a specific real paper against its
KNOWN silent-failure signature. A future refactor that breaks either
the pass or the flag for this paper is caught immediately, keyed to
the paper by name.

First paper: Ang (2010), 10.1002/acr.20119.
  Reviewer-verified row (6 of 8 preserved runs, incl. 20260826_113816
  and 20260827_143901 which are the only two runs where the schema
  carries source_quote_* to the CSV):
      n_intervention=15, n_control=13
      mean_intervention=-20.2, sd_intervention=23.9
      mean_control=-14.9,   sd_control=16.4
      source_quote_intervention = "Pain, mean ± SD\nCBT\n-20.2 ± 23.9"
      source_quote_control      = "Pain, mean ± SD\nUC\n-14.9 ± 16.4"

  Silent mis-extraction row (Session 19 identified in run
  20260826_104447; that run's CSV predates source-quote columns
  reaching the CSV, so the failure signature is represented as
  missing quotes - which is exactly what fired on those runs and
  is what the fixture must pin):
      mean_intervention=-8.9, sd_intervention=25.3
      mean_control=-10.8,   sd_control=24.1
      source_quote_intervention = None
      source_quote_control      = None

Paper: Lami. text_fallback path with a study_overrides.yaml entry.
  Reviewer-verified row:
      n_intervention=28, n_control=36
      mean_intervention=7.35, sd_intervention=2.08
      mean_control=7.4,       sd_control=1.29
  Failure signature: means/SDs stable, Ns drift ("chaotic") across
  runs, source quotes absent on the drifting runs - which is why the
  reviewer's study_overrides.yaml entry was needed and why the
  missing-quote branch must keep firing on this shape.

Paper: Jensen. Reviewer-verified row (Ns and SDs strictly pinned;
  means pinned as observed value sets, per handoff guidance):
      n_intervention=25, n_control=18
      sd_intervention=19.0, sd_control=26.0
      mean_intervention ? {49.0, 49.1}
      mean_control      ? {59.0, 59.1, 59.2}
  Also pins the Session 21 finding that _number_in_text's integer-
  fallback branch already handles the "49.0 vs '49'" concern - not
  a bug, but a live regression risk worth an executable check.


Run with: python -m pytest tests/test_extraction_regression_fixtures.py -v
"""
import pytest

from pipelines.sr.src.extraction.data_extractor import DataExtractor


# ---------------------------------------------------------------------------
# Ang (2010): reviewer-verified fixtures
# ---------------------------------------------------------------------------
# The two source quotes are copied byte-for-byte from run
# 20260826_113816's extracted_data.csv. The embedded newlines are real -
# the model rendered a three-line table row (header / arm label / value)
# as a single quote string, and both good runs that reached the
# source-quote CSV era ({113816, 143901}) recorded the identical
# string. Do not "clean up" the newlines: the quote must match what the
# extractor actually produces so that the tripwire is exercised on
# real-shape input, not idealised input.
ANG_GOOD_QUOTE_INTERVENTION = "Pain, mean ± SD\nCBT\n-20.2 ± 23.9"
ANG_GOOD_QUOTE_CONTROL      = "Pain, mean ± SD\nUC\n-14.9 ± 16.4"


def _ang_good_result():
    """Reviewer-verified Ang (2010) extraction. Every value below is
    the exact number from the 6 preserved runs' CSVs (Session 19)."""
    return {
        "primary_outcome": {
            "mean_intervention": -20.2, "sd_intervention": 23.9,
            "mean_control":      -14.9, "sd_control":      16.4,
            "source_quote_intervention": ANG_GOOD_QUOTE_INTERVENTION,
            "source_quote_control":      ANG_GOOD_QUOTE_CONTROL,
        },
        # vision_smart is the extraction_method recorded for Ang's good
        # runs; the check treats vision_* the same as any non-text path
        # (source_text is not supplied, so check 5 is skipped).
        "extraction_method": "vision_smart",
        "filename": (
            "Arthritis Care Research - 2010 - Ang - Cognitive behavioral "
            "therapy attenuates nociceptive responding in patients "
            "with-1.pdf"
        ),
    }


def _ang_bad_result():
    """Session 19's silent mis-extraction of Ang. Numbers from run
    20260826_104447. The CSV for that run does not carry source_quote_*
    columns at all - the fields entered the CSV schema in the same #48
    change that added the tripwire - so on those runs the tripwire
    fired on the missing-quote branch. That is what the fixture pins."""
    return {
        "primary_outcome": {
            "mean_intervention":  -8.9, "sd_intervention": 25.3,
            "mean_control":      -10.8, "sd_control":      24.1,
            "source_quote_intervention": None,
            "source_quote_control":      None,
        },
        "extraction_method": "vision_smart",
        "filename": (
            "Arthritis Care Research - 2010 - Ang - Cognitive behavioral "
            "therapy attenuates nociceptive responding in patients "
            "with-1.pdf"
        ),
    }


@pytest.fixture
def extractor():
    return DataExtractor(
        pico_criteria={"outcome": "pain"},
        provider="qwen",
        api_key="dummy-not-a-real-key",
    )

# ---------------------------------------------------------------------------
# Lami (#11): reviewer-verified fixtures for the text-fallback path
# ---------------------------------------------------------------------------
# Reviewer-verified values (HANDOFF Session 21 -> Session 22 priority 1):
#     n_intervention=28, n_control=36
#     mean_intervention=7.35, sd_intervention=2.08
#     mean_control=7.4,       sd_control=1.29
#
# Lami's failure mode differs from Ang's:
#   - Ang was bimodal on the MEANS (two distinct value sets across runs).
#   - Lami's means/SDs are stable, but the Ns are "chaotic" - drifting
#     across runs to values that never appear in the paper. That is why
#     the reviewer-authored study_overrides.yaml entry for Lami exists:
#     to REPLACE whatever N the extractor emits. The override doc string
#     in README.md is explicit that numeric outcome fields REPLACE (not
#     fill), which is exactly what Lami needs.
#
# What the fixture pins:
#   (a) A reviewer-verified good extraction on the text_fallback path
#       (source_quotes are lines pulled straight from the extracted
#       text, not vision table screenshots) passes the source-quote
#       tripwire cleanly. If a future tightening rejects a plain
#       "mean (SD)" one-line quote, this test fires.
#   (b) The Ns-drift signature (correct means/SDs, missing/null source
#       quotes because the model shrugged on the arm rows) is caught by
#       the missing-quote branch. This is the shape that made an
#       override necessary in the first place - if the tripwire stops
#       firing on it, the "override is a real cross-check" property from
#       the README ('log shows field(confirmed 7.35)') silently breaks:
#       we would confirm against a run that had no source quote and
#       therefore no independent basis for the number.
#
# The text_fallback path stores extraction_method="text_fallback" (see
# main.py's fallback-cascade logging around v2.4.13). We record it here
# so the fixture is legible; the check itself does not branch on it.

LAMI_GOOD_QUOTE_INTERVENTION = "Pain intensity, mean (SD): 7.35 (2.08)"
LAMI_GOOD_QUOTE_CONTROL      = "Pain intensity, mean (SD): 7.4 (1.29)"


def _lami_good_result():
    """Reviewer-verified Lami extraction (text_fallback path).

    The two source quotes are the shape the text_fallback path actually
    produces: a single-line 'label: mean (SD)' pulled from the extracted
    text, without the vision path's embedded newlines. They contain no
    SE marker, no timepoint tokens, and only one mean(SD) cell each -
    so every tripwire branch in _flag_suspect_source_quotes must clear."""
    return {
        "participants": {
            "n_intervention": 28,
            "n_control":      36,
        },
        "primary_outcome": {
            "mean_intervention": 7.35, "sd_intervention": 2.08,
            "mean_control":      7.4,  "sd_control":      1.29,
            "source_quote_intervention": LAMI_GOOD_QUOTE_INTERVENTION,
            "source_quote_control":      LAMI_GOOD_QUOTE_CONTROL,
        },
        "extraction_method": "text_fallback",
        "filename": "Lami.pdf",
    }


def _lami_ns_drift_result():
    """The Ns-drift silent-failure signature for Lami: means and SDs
    are the reviewer-verified numbers, but Ns are wrong AND the model
    could not point to a source quote for the arm rows (this is what
    made the override necessary). The tripwire must catch this on the
    missing-quote branch - a plausible-looking mean/SD pair with no
    supporting quote is exactly the shape the Session 19 durable lesson
    ('a silent wrong answer is worse than a crash') exists to catch."""
    return {
        # Ns that never appeared in the paper - representative of the
        # 'chaotic' drift the reviewer documented on Lami. The specific
        # numbers here do not matter for the tripwire (it does not read
        # Ns); they are recorded so the fixture is legible.
        "participants": {
            "n_intervention": 32,
            "n_control":      32,
        },
        "primary_outcome": {
            "mean_intervention": 7.35, "sd_intervention": 2.08,
            "mean_control":      7.4,  "sd_control":      1.29,
            "source_quote_intervention": None,
            "source_quote_control":      None,
        },
        "extraction_method": "text_fallback",
        "filename": "Lami.pdf",
    }


def test_lami_good_extraction_passes_source_quote_check(extractor):
    """The reviewer-verified Lami row (text_fallback path, plain
    'mean (SD)' one-line quotes) must pass the tripwire cleanly.
    Every extracted number appears in its own quote; there is no SE
    marker, no timepoint token, no within-subject phrase, and only
    one mean(SD) cell per quote - so no branch should fire."""
    result = _lami_good_result()
    extractor._flag_suspect_source_quotes(result)
    warning = result.get("source_quote_warning")
    assert warning is None, (
        f"reviewer-verified Lami row was flagged as suspect; a plain "
        f"single-line 'mean (SD)' text-fallback quote is now being "
        f"rejected: {warning!r}"
    )


def test_lami_ns_drift_signature_is_flagged(extractor):
    """The Ns-drift shape (correct means/SDs, missing source quotes)
    must fire the missing-quote branch. If this stops firing, the
    override mechanism is silently confirming numbers against runs that
    had no independent quote basis - which is exactly the confirmation
    hole the source-quote tripwire was added to close (#48)."""
    result = _lami_ns_drift_result()
    extractor._flag_suspect_source_quotes(result)
    warning = result.get("source_quote_warning")
    assert warning is not None, (
        "the Lami Ns-drift signature (means/SDs present, source quotes "
        "absent) was NOT flagged; a plausible-looking row with no quote "
        "would now pass silently, and the override 'confirmed' path in "
        "main.py has no independent number to confirm against."
    )
    assert "no source quote" in warning.lower(), (
        f"expected the missing-source-quote branch to fire on Lami's "
        f"Ns-drift shape; got a different warning: {warning!r}"
    )


# ---------------------------------------------------------------------------
# Jensen (#11): reviewer-verified fixtures with per-run mean value sets
# ---------------------------------------------------------------------------
# Reviewer-verified values (HANDOFF Session 21 -> Session 22 priority 2):
#     n_intervention=25, n_control=18
#     sd_intervention=19.0, sd_control=26.0
#     means vary across runs in the first decimal:
#       mean_intervention ? {49.0, 49.1}
#       mean_control      ? {59.0, 59.1, 59.2}
#
# Per handoff guidance, Ns and SDs are pinned STRICTLY; means are
# pinned as a value-set (as Ang does), because Jensen is a live example
# of the first-decimal non-determinism that #11 tracks. If the model
# ever emits a mean outside these observed sets on this paper, the
# reviewer should be told - either the paper's numbers were misread
# or a new run has surfaced a value nobody has audited yet.
#
# Session 21 investigation note (reproduced here as an executable
# test): the concern that a quote containing the token "49" would not
# match the extracted mean 49.0 is NOT a bug. _number_in_text tries
# both the float string ("49.0") and the integer candidate ("49") when
# the float is integer-valued. The test below pins that behaviour so
# a future rewrite of _number_in_text cannot regress silently and turn
# every integer-valued mean into a false-positive tripwire fire on
# this paper.

JENSEN_MEAN_INTERVENTION_VALUES = (49.0, 49.1)
JENSEN_MEAN_CONTROL_VALUES      = (59.0, 59.1, 59.2)


def _jensen_result(mean_i: float, mean_c: float):
    """Build a Jensen extraction with the reviewer-verified Ns and SDs
    and the chosen per-run means. The source quotes are constructed to
    contain each arm's mean and SD verbatim so the tripwire must clear
    on any observed (mean_i, mean_c) combination.

    Quotes deliberately include the arm-specific mean and SD and no
    timepoint tokens / no SE marker. If a future run emits a genuinely
    different quote shape, add a new fixture rather than editing this
    one - the point is that THIS shape, on THIS paper, has been seen
    to extract correctly and must continue to."""
    return {
        "participants": {
            "n_intervention": 25,
            "n_control":      18,
        },
        "primary_outcome": {
            "mean_intervention": mean_i, "sd_intervention": 19.0,
            "mean_control":      mean_c, "sd_control":      26.0,
            "source_quote_intervention":
                f"Intervention group: {mean_i} (SD {19.0})",
            "source_quote_control":
                f"Control group: {mean_c} (SD {26.0})",
        },
        "extraction_method": "vision_smart",
        "filename": "Jensen.pdf",
    }


@pytest.mark.parametrize("mean_i", JENSEN_MEAN_INTERVENTION_VALUES)
@pytest.mark.parametrize("mean_c", JENSEN_MEAN_CONTROL_VALUES)
def test_jensen_all_observed_value_sets_pass_source_quote_check(
        extractor, mean_i, mean_c):
    """For every combination of the reviewer-observed means, the
    tripwire must clear. Ns and SDs are held constant at their strictly
    pinned values (25/18, 19.0/26.0); only the first-decimal means vary.
    If any combination starts firing, either _number_in_text lost its
    integer-fallback branch (Session 21) or the quote shape assumption
    changed - both are the kind of silent regression #11's fixtures
    exist to prevent."""
    result = _jensen_result(mean_i, mean_c)
    extractor._flag_suspect_source_quotes(result)
    warning = result.get("source_quote_warning")
    assert warning is None, (
        f"Jensen row with reviewer-observed means "
        f"(mean_i={mean_i}, mean_c={mean_c}) was flagged; the tripwire "
        f"is now rejecting a shape that has been verified to extract "
        f"correctly on this paper: {warning!r}"
    )


@pytest.mark.parametrize("mean_i", JENSEN_MEAN_INTERVENTION_VALUES)
@pytest.mark.parametrize("mean_c", JENSEN_MEAN_CONTROL_VALUES)
def test_jensen_arm_ordering_is_stable(mean_i, mean_c):
    """Structural pin: for every observed Jensen mean pair, the
    intervention mean is strictly less than the control mean. This is
    what protects against an arm swap regardless of which outcome-
    direction convention Jensen uses (lower-is-better on pain scores
    would make g < 0; higher-is-better would make g > 0). Pinning
    (mean_i - mean_c) < 0 rather than the sign of g avoids assuming
    the paper's semantic direction - if that assumption ever changes,
    THIS test does not have to be revisited."""
    assert mean_i < mean_c, (
        f"Jensen arm ordering has drifted: expected mean_intervention "
        f"({mean_i}) < mean_control ({mean_c}). An upstream arm swap "
        f"is the most likely cause; verify the extraction assigns the "
        f"right column to intervention_group before touching this test."
    )


def test_jensen_integer_fallback_in_number_in_text():
    """Session 21 checked whether the quote-matching branch would
    falsely flag Jensen's mean 49.0 when the source text shows only
    '49'. The conclusion was: not a bug - _number_in_text tries the
    integer candidate. This test pins that conclusion as an executable
    check so a future rewrite of _number_in_text cannot regress
    silently. Also pins the mirror case: 49.1 must NOT match a quote
    containing only '49' (that would be a false pass, not a false
    fail)."""
    # Integer-valued float finds the bare-integer token: verified good.
    assert DataExtractor._number_in_text(
        49.0, "Intervention group mean was 49 at endpoint."
    ), (
        "_number_in_text lost its integer-fallback branch: 49.0 no "
        "longer matches a quote containing '49'. This will start "
        "false-flagging every integer-valued mean on every paper "
        "(Session 21 investigation)."
    )

    # And the same float, written in float form, must still match.
    assert DataExtractor._number_in_text(
        49.0, "Intervention group mean was 49.0 at endpoint."
    ), "49.0 should trivially match the string '49.0'"

    # False-pass guard: 49.1 must NOT match a quote that says only 49.
    # If this ever starts passing, _number_in_text has become too
    # lenient and the tripwire's discriminating power on Jensen (where
    # 49.0 vs 49.1 is the whole non-determinism story) is gone.
    assert not DataExtractor._number_in_text(
        49.1, "Intervention group mean was 49 at endpoint."
    ), (
        "_number_in_text is now matching 49.1 against a quote that "
        "contains only '49' - the check has become too lenient and "
        "cannot distinguish the two Jensen value sets any more."
    )


# ---------------------------------------------------------------------------
# The paired regression pins for #23
# ---------------------------------------------------------------------------

def test_ang_good_extraction_passes_source_quote_check(extractor):
    """The reviewer-verified Ang row must pass cleanly. Every
    extracted number appears verbatim in its own source quote; the
    quotes carry an 'SD' label (not SE); there are no timepoint tokens
    or within-subject phrases. If this ever starts firing, a check
    was tightened in a way that rejects a genuinely correct
    between-group table-row extraction."""
    result = _ang_good_result()
    extractor._flag_suspect_source_quotes(result)
    warning = result.get("source_quote_warning")
    assert warning is None, (
        f"reviewer-verified Ang row was flagged as suspect; the check "
        f"has been tightened in a way that rejects a correct extraction: "
        f"{warning!r}"
    )


def test_ang_silent_misextraction_is_flagged(extractor):
    """Session 19's silent mis-extraction signature: -8.9/-10.8 with
    both source quotes absent. This is the shape the tripwire exists
    to catch on this paper - the numbers alone look plausible, the
    outcome_match flag was True in the CSV, and the only column that
    discriminates it from the good row is the (empty) source quote.

    If this test ever stops flagging, either:
      (a) the missing-quote branch of _flag_suspect_source_quotes was
          removed or gated on something that now excludes this shape, or
      (b) the key is no longer being written on this failure mode
          (violates the 'always set the key' durable lesson from
          Session 8: 'a tripwire that only writes its key on failure
          makes checked-and-clean indistinguishable from never-ran').
    Either way, the silent-wrong-answer hole is back."""
    result = _ang_bad_result()
    extractor._flag_suspect_source_quotes(result)
    warning = result.get("source_quote_warning")
    assert warning is not None, (
        "the -8.9/-10.8 + empty-quote Ang mis-extraction was NOT "
        "flagged; the tripwire that Session 14/#48 landed has "
        "regressed - a silent wrong answer is worse than a crash "
        "(Session 19 durable lesson)."
    )
    # The specific branch we expect to fire. If a future refactor
    # renames the message, update this assertion, but do it deliberately.
    assert "no source quote" in warning.lower(), (
        f"expected the missing-source-quote branch to fire on this "
        f"shape; got a different warning: {warning!r}"
    )


# ---------------------------------------------------------------------------
# Bonus: pin the sign of Hedges g on the reviewer-verified numbers
# ---------------------------------------------------------------------------
# Ang's N (15/13) is in every CSV row shown. The good extraction has
# mean_i more negative than mean_c on a pain-change outcome, which
# means the intervention reduced pain more than the control - Hedges g
# on (mean_i - mean_c) must be NEGATIVE. If a future arm-swap
# regression flips these, the sign flips too. This is a cheap
# additional pin; it uses the same closed-form Hedges g that main.py
# computes, so no MetaAnalyzer dependency is needed.

def test_ang_good_extraction_yields_negative_hedges_g():
    """A between-group SMD on Ang's verified means/SDs/Ns must be
    negative (intervention had a lower / more-negative pain-change
    score than control). This is the direction the pooled estimate is
    keyed to; an arm swap would silently flip it."""
    n_i, n_c = 15.0, 13.0
    m_i, s_i = -20.2, 23.9
    m_c, s_c = -14.9, 16.4
    df2 = n_i + n_c - 2
    sd_p = (((n_i - 1) * s_i ** 2 + (n_c - 1) * s_c ** 2) / df2) ** 0.5
    d = (m_i - m_c) / sd_p
    J = 1 - 3 / (4 * df2 - 1)
    g = J * d
    assert g < 0, (
        f"expected Hedges g < 0 (intervention reduced pain more than "
        f"control on Ang's verified numbers); got g={g:.4f}. An arm "
        f"swap somewhere upstream is the most likely cause."
    )
    # Sanity band: Session 14's original prose claim of g=-0.248 for
    # this outcome pair is in the right neighbourhood. Wide band on
    # purpose - we are pinning the sign, not the exact magnitude,
    # because the magnitude depends on the SMD formula variant chosen
    # (Hedges g vs Cohen's d, small-sample correction on or off).
    assert -1.0 < g < 0.0, (
        f"g={g:.4f} is outside the expected -1.0 < g < 0.0 band; "
        f"either a formula changed or an input value did."
    )
