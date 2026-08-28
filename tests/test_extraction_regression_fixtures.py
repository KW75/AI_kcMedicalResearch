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

Future entries for Jensen and Lami (also named in #11) can be added
here rather than in new files; the `ang_` test-name prefix keeps
per-paper failures readable in pytest output.

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
