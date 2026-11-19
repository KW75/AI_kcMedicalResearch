"""Session 48: menu 5 Validator gate needs one clear verdict.

Before: status was APPROVED FOR DOWNLOAD whenever the last stage answer
contained that text anywhere - also "NOT APPROVED FOR DOWNLOAD", the
prompt template line "[APPROVED FOR DOWNLOAD / REQUIRES REFINEMENT]",
or the Searcher answer when the Validator was skipped. Now
_validator_verdict reads the line after the last "Overall decision:" of
the Validator answer itself (or the whole answer if there is none).
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "SOURCE_CODE"))

import pipelines.rct_search.rct_search as rs  # noqa: E402

APPROVED = "APPROVED FOR DOWNLOAD"
REFINE = "REQUIRES REFINEMENT"


@pytest.mark.parametrize("answer", [
    "**Overall decision:** APPROVED FOR DOWNLOAD",
    "**Overall decision:**\nAPPROVED FOR DOWNLOAD\n",
    "All checks pass.\nOverall decision: [APPROVED FOR DOWNLOAD]",
    "overall decision: approved for download",
    "APPROVED FOR DOWNLOAD",
])
def test_clear_approval(answer):
    assert rs._validator_verdict(answer) == APPROVED


@pytest.mark.parametrize("answer", [
    "**Overall decision:** [APPROVED FOR DOWNLOAD / REQUIRES REFINEMENT]",
    "**Overall decision:** NOT APPROVED FOR DOWNLOAD",
    "**Overall decision:** REQUIRES REFINEMENT\nOnce fixed: APPROVED FOR DOWNLOAD.",
    "Overall decision: APPROVED FOR DOWNLOAD\n\nOverall decision: REQUIRES REFINEMENT",
    "The strategy is not approved for download.",
    "[ERROR in Validator: Ollama timed out]",
    "[DRY RUN] Validator would respond here.",
    "",
    None,
])
def test_not_approved(answer):
    assert rs._validator_verdict(answer) == REFINE


def test_gate_uses_validator_answer_not_last_stage():
    text = Path(rs.__file__).read_text(encoding="utf-8")
    assert "previous_response.upper()" not in text
    assert "_validator_verdict(validator_response)" in text
