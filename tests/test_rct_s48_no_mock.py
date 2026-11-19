"""Session 48: menu 5 call_ai never returns a made-up [MOCK] answer.

Before: if main could not be imported, or the AI call raised ImportError
or AttributeError, call_ai returned "[MOCK] ... response for: ..." and the
pipeline used it as a real Formulator, Searcher, Validator or ranking
answer. Now it raises RuntimeError, which both callers already catch.
"""
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "SOURCE_CODE"))

import pipelines.rct_search.rct_search as rs  # noqa: E402


@pytest.mark.parametrize("provider", ["ollama", "deepseek"])
def test_no_main_module_raises(provider):
    with patch.dict(sys.modules, {"main": None}):
        with pytest.raises(RuntimeError) as info:
            rs.call_ai("Test prompt", provider=provider)
    assert "[MOCK]" not in str(info.value)


def test_attribute_error_in_ai_call_raises():
    with patch("main.call_ai", side_effect=AttributeError("no such attr")):
        with pytest.raises(RuntimeError) as info:
            rs.call_ai("Test prompt", provider="ollama")
    assert "no such attr" in str(info.value)


def test_source_has_no_mock_answer():
    text = Path(rs.__file__).read_text(encoding="utf-8")
    assert text.count("[MOCK]") == 0
