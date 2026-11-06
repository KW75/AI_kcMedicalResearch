"""SR --provider anthropic warning must describe what the code really skips.

The old warning (cited closed #61) said the Anthropic path runs without the
source-quote, SD/SE and group-timepoint tripwires. In data_extractor.py,
_extract_anthropic runs _coerce_extraction_result (group/timepoint) and
_flag_suspect_source_quotes(source_text=None), so only two checks are lost:
the verbatim quote-in-source check and the text-line SD/SE check.
"""
from pathlib import Path

import main


def _warning():
    return main.sr_provider_warning("sr", "anthropic")


def test_warning_only_for_sr_with_anthropic():
    assert main.sr_provider_warning("sr", "qwen") is None
    assert main.sr_provider_warning("coding", "anthropic") is None
    assert _warning()


def test_warning_names_the_two_checks_really_skipped():
    w = _warning()
    assert "word for word" in w
    assert "SD/SE" in w


def test_warning_does_not_claim_checks_that_still_run():
    w = _warning().lower()
    assert "group-timepoint" not in w
    assert "group/timepoint" not in w
    assert "without the source-quote" not in w
    assert "other checks still run" in w


def test_warning_points_to_reviewer_guide_not_a_closed_issue():
    w = _warning()
    assert "#61" not in w
    assert "docs/sr/REVIEWER_GUIDE.md section 6" in w


def test_main_no_longer_cites_known_issue_61():
    src = (Path(main.__file__)).read_text(encoding="utf-8")
    assert "Known Issue #61" not in src
    assert "(#61)" not in src
