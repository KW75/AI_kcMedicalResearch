"""
Screening must send article text only to the provider the user chose.

RelevanceScreener.screen_by_pdf_path looked up the provider URL with a
DeepSeek default, so provider="anthropic" (or any name missing from the
table) POSTed the article text to api.deepseek.com. The normal SR
pipeline never reaches that path for Anthropic (Stage 1 uploads every
PDF and screen_batch routes by file_id), but direct calls could.
Pinned property: an unrouted provider sends the text nowhere, and the
refusal is recorded rather than silent.
"""
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "SOURCE_CODE"))

fitz = pytest.importorskip("fitz")

try:
    from SOURCE_CODE.pipelines.sr.src.screening.relevance_screener import RelevanceScreener
except ImportError:
    from pipelines.sr.src.screening.relevance_screener import RelevanceScreener


def _make_pdf(path: Path) -> None:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (72, 72),
        "Randomised controlled trial of cognitive behavioural therapy\n"
        "versus usual care in adults with fibromyalgia. The primary\n"
        "outcome was pain intensity at week twelve.",
    )
    doc.save(str(path))
    doc.close()


def _screener(provider: str) -> RelevanceScreener:
    return RelevanceScreener(
        pico_criteria={
            "population": "adults with fibromyalgia",
            "intervention": "cognitive behavioural therapy",
            "comparison": "usual care",
            "outcome": "pain",
        },
        inclusion_criteria=["randomised controlled trial"],
        exclusion_criteria=["animal study"],
        model="test-model",
        api_key="test-key",
        provider=provider,
    )


@pytest.mark.parametrize("provider", ["anthropic", "not_a_provider"])
def test_unrouted_provider_sends_article_text_nowhere(tmp_path, provider):
    pdf = tmp_path / "trial.pdf"
    _make_pdf(pdf)

    with patch("urllib.request.urlopen") as mock_open:
        mock_open.side_effect = AssertionError("network call attempted")
        result = _screener(provider).screen_by_pdf_path(str(pdf), "trial.pdf")

    sent_to = [c.args[0].full_url for c in mock_open.call_args_list]
    assert sent_to == [], f"provider={provider}: article text was sent to {sent_to}"
    assert result.get("error"), "the refusal must be recorded, not silent"
    assert provider in str(result["error"])
