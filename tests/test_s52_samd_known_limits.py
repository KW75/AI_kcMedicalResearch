"""Session 52 (cont. 7): readme_SaMD_pipeline.txt has a Known limits section; SaMD pipeline frozen."""
from pathlib import Path

README = Path(__file__).resolve().parents[1] / "Readme" / "readme_SaMD_pipeline.txt"
TITLE = "Known limits and freeze (Session 52 (cont. 7))"


def _text():
    with open(README, encoding="utf-8", newline="") as f:
        return f.read()


def test_known_limits_section_present():
    assert TITLE in _text()


def test_readme_says_frozen_bug_fixes_only():
    t = _text()
    assert TITLE in t
    assert "Only bug fixes go in" in t.split(TITLE)[-1]


def test_known_limits_name_main_risks():
    t = _text()
    assert TITLE in t
    part = t.split(TITLE)[-1]
    for words in ("not a cleared or certified medical device", "mislabelled",
                  "different warnings", "English text patterns"):
        assert words in part, words
