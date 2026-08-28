"""
Unit tests for the broken-CMap offset decoder (Known Issue #18 / #12).

Session 24 found that v2.4.13's offset decode had no test and no live
test case: every broken-CMap PDF in the corpus is a "(cid:XX)" case,
which the decoder skips by design, and the one clean PDF never reaches
the fallback. These tests are the only verification the decoder has.

The garble is simulated with the module's own _shift_text, which mirrors
the observed failure ("Uif!qbujfout" for "The patients"): letters shift
by a constant, non-letters do not. Note that spaces in a real +1-shifted
PDF arrive as '!' and are NOT restored by the decoder; the tests reflect
that rather than hide it.

Run with: python -m pytest tests/test_cmap_offset_decode.py -v
"""
import pytest

from pipelines.sr.src.screening.relevance_screener import (
    _cmap_score,
    _shift_text,
    _try_cmap_offset_decode,
)

# Dense in stopwords so a correct decode clears min_score=15 comfortably.
CLEAN = (
    "The patients in the treatment group were compared with the control "
    "group at the end of the trial. The mean pain score was significant "
    "for the treatment group and not for the control group. This is a "
    "study of the results in patients with pain, and we report the mean "
    "for the trial as a whole."
)


def test_score_counts_stopwords_case_insensitively():
    assert _cmap_score("The THE tHe") == 3
    assert _cmap_score("xyzzy plugh") == 0
    assert _cmap_score("") == 0


@pytest.mark.parametrize("offset", [1, -1, 2, -2])
def test_shift_round_trips(offset):
    assert _shift_text(_shift_text(CLEAN, offset), -offset) == CLEAN


def test_shift_leaves_non_letters_alone():
    assert _shift_text("a1 B! z?", 1) == "b1 C! a?"


@pytest.mark.parametrize("garble_offset", [1, -1, 2, -2])
def test_decoder_recovers_each_supported_offset(garble_offset):
    garbled = _shift_text(CLEAN, garble_offset)
    decoded, found = _try_cmap_offset_decode(garbled)
    assert found == -garble_offset
    assert decoded == CLEAN


def test_decoder_recovers_the_observed_failure_shape():
    # Real +1 shift: spaces become '!'. Decoder restores letters only.
    garbled = _shift_text(CLEAN, 1).replace(" ", "!")
    decoded, found = _try_cmap_offset_decode(garbled)
    assert found == -1
    assert decoded == CLEAN.replace(" ", "!")
    assert " " not in decoded  # documented limitation, not a bug


def test_decoder_leaves_clean_text_alone():
    decoded, found = _try_cmap_offset_decode(CLEAN)
    assert (decoded, found) == (None, None)


def test_decoder_does_not_touch_unsupported_offset():
    garbled = _shift_text(CLEAN, 3)
    assert _try_cmap_offset_decode(garbled) == (None, None)


def test_decoder_ignores_cid_markers():
    # (cid:XX) means the ToUnicode map is missing, not shifted. The call
    # site skips the decoder for these; the decoder itself must not
    # produce a false positive if handed one.
    text = " ".join("(cid:%d)" % i for i in range(40))
    assert _try_cmap_offset_decode(text) == (None, None)


def test_decoder_requires_clear_win_over_baseline():
    # A short snippet decodes to only a handful of stopwords - below
    # min_score - so the decoder must refuse rather than guess.
    garbled = _shift_text("The patients were in pain.", 1)
    assert _try_cmap_offset_decode(garbled) == (None, None)
    # ...but succeeds once the threshold is lowered.
    decoded, found = _try_cmap_offset_decode(garbled, min_score=3)
    assert found == -1 and decoded == "The patients were in pain."


def test_empty_input():
    assert _try_cmap_offset_decode("") == (None, None)
    assert _try_cmap_offset_decode(None) == (None, None)
