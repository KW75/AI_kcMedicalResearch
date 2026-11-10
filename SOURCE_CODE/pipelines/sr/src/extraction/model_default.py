"""Default SR model when an extractor is built without model= (Session 37).

Replaces the hard-coded "qwen-vl-plus" defaults in DataExtractor and
HybridTableExtractor. The rule lives in providers.sr_default_model, the same
one main.py and pipelines/sr/main.resolve_model use.
"""
import sys
from pathlib import Path

# extraction -> src -> sr -> pipelines -> SOURCE_CODE
_SOURCE_CODE = Path(__file__).resolve().parents[4]


def sr_model_for(provider: str) -> str:
    if str(_SOURCE_CODE) not in sys.path:
        sys.path.insert(0, str(_SOURCE_CODE))
    from providers import sr_default_model
    return sr_default_model(provider)
