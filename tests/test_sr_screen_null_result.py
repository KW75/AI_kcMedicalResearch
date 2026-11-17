# tests/test_sr_screen_null_result.py
"""Session 41 (option 3): a null result still reports the outcome.

Run 20261114_133303 (gemma4:e4b): Jensen and Karlsson were EXCLUDED at
confidence 1.0 because CBT had "no effects on clinical pain" / "pain
intensity was not affected". Both trials measured and reported pain, so the
outcome criterion was met; excluding on the result biases the review. The
screening PROMPT now says so. These tests prove the rule is SENT, not that a
model obeys it - that needs a repeat of the reference run.
"""
from pipelines.sr.src.screening.relevance_screener import RelevanceScreener

PICO = {"population": "adults with fibromyalgia",
        "intervention": "CBT",
        "comparator": "waiting list or usual care",
        "outcome": "Pain intensity at post-intervention"}


def _prompt():
    s = RelevanceScreener.__new__(RelevanceScreener)   # no client, no key
    s.pico = PICO
    s.inclusion = ["Randomised controlled trial"]
    s.exclusion = ["Not an RCT"]
    return s._prompt()


def test_prompt_has_null_result_rule():
    p = " ".join(_prompt().split()).lower()
    for phrase in ("measured", "no effect", "null result",
                   "non-significant", "never exclude"):
        assert phrase in p, f"screening prompt lacks {phrase!r}"


def test_rule_comes_before_the_json_instruction():
    p = _prompt().lower()
    assert "null result" in p
    assert p.index("null result") < p.index("return only valid json")


def test_prompt_still_formats_with_json_intact():
    p = _prompt()
    assert "{pico}" not in p and "{inclusion}" not in p and "{exclusion}" not in p
    assert "OUTCOME: Pain intensity at post-intervention" in p
    assert '{"decision":' in p
    assert "Bias toward INCLUDE when uncertain." in p
