"""OCR summary prompts (Session 36, Next work item 2).

Ang 2010 summary labelled the table's "Week 12 change (from baseline)" as
"Week 6 to Week 12", and Session 35 saw a summary drop a [?] before a
number (-0.3 shown as 0.3). These tests pin that each prompt that writes
summary text carries both rules. They check keywords, not exact wording.
"""
import pytest

from pipelines.ocr import engine

PROMPTS = {
    "SUMMARY_PROMPT": engine.SUMMARY_PROMPT,
    "SYNOPSIS_PROMPT": engine.SYNOPSIS_PROMPT,
    "PART_PROMPT": engine.PART_PROMPT,
}


@pytest.mark.parametrize("name", PROMPTS)
def test_prompt_says_copy_lost_symbol_marks(name):
    assert "[?]" in PROMPTS[name]


@pytest.mark.parametrize("name", PROMPTS)
def test_prompt_says_keep_change_reference_point(name):
    assert "baseline" in PROMPTS[name].lower()


def test_synopsis_prompt_asks_for_plain_symbols():
    assert "not LaTeX" in engine.SYNOPSIS_PROMPT
