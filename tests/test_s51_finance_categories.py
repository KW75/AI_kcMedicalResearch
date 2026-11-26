"""Session 51: OCR Finance category list extended at the user's request.

The user confirmed the eight Session 50 categories and added eleven.
Spellings are the user's. 'Other' stays last (unknown answers fall back
to it).
"""
import importlib
import re
from pathlib import Path

finance = importlib.import_module("pipelines.ocr.finance")

OLD = ('Travel', 'Accommodation', 'Meals', 'Conference/registration', 'Equipment', 'Software/subscriptions', 'Publication fees', 'Other')
ADDED = ('Utilities', 'Telecommunications', 'Maintenance', 'Cleaning', 'Miscellaneous', 'Entertainments', 'Insurance', 'Transportation', 'Parking Fees', 'Petrol', 'Car_maintenance')
MARKER = '"category": one of: '


def test_new_names_in_list():
    for name in ADDED:
        assert name in finance.CATEGORIES, name


def test_old_names_kept():
    for name in OLD:
        assert name in finance.CATEGORIES, name


def test_other_last_and_unique():
    cats = finance.CATEGORIES
    assert cats[-1] == "Other"
    lowered = [c.lower() for c in cats]
    assert len(lowered) == len(set(lowered))


def test_prompt_offers_all():
    prompts = [v for v in vars(finance).values()
               if isinstance(v, str) and MARKER in v]
    assert prompts, "no module-level prompt with the category line"
    for p in prompts:
        assert MARKER + "; ".join(finance.CATEGORIES) in p
        for name in ADDED:
            assert name in p, name


def test_readme_lists_all():
    path = Path(__file__).resolve().parents[1] / "Readme" / "readme_ocr_pipeline.txt"
    text = re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))
    for name in ADDED:
        assert name in text, name
    assert "Categories: " + ", ".join(finance.CATEGORIES) + "." in text
