"""Session 37 decision (user): comparator = placebo, active comparator, or
waiting list; waiting-list trials are included and reported as a subgroup.

The screener and extractor prompts carry this wording. A sample config that
says only "placebo or active comparator" lets the AI exclude waiting-list
trials (Jensen 2012, Karlsson 2015, McCrae 2019). These tests stop the
wording from quietly going back.
"""
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
YAML_PATH = ROOT / "SOURCE_CODE" / "pipelines" / "sr" / "config" / "prisma_criteria.yaml"
PICO_PATH = ROOT / "input" / "sr" / "pico_sample.json"


def _find_key(obj, key):
    """First value stored under `key` anywhere in nested dicts/lists."""
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            found = _find_key(v, key)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for v in obj:
            found = _find_key(v, key)
            if found is not None:
                return found
    return None


def _covers_all_three(text):
    t = str(text or "").lower().replace("-", " ")
    has_wait = "waiting list" in t or "waitlist" in t
    return "placebo" in t and "active" in t and has_wait


def test_prisma_criteria_comparator_includes_waiting_list():
    cfg = yaml.safe_load(YAML_PATH.read_text(encoding="utf-8"))
    comp = _find_key(cfg, "comparator")
    assert comp is not None, "no comparator key in prisma_criteria.yaml"
    assert _covers_all_three(comp), f"prisma_criteria.yaml comparator is {comp!r}"


def test_pico_sample_comparator_includes_waiting_list():
    data = json.loads(PICO_PATH.read_text(encoding="utf-8"))
    comp = _find_key(data, "comparator")
    assert comp is not None, "no comparator key in pico_sample.json"
    assert _covers_all_three(comp), f"pico_sample.json comparator is {comp!r}"


def test_pico_sample_formulator_text_matches():
    data = json.loads(PICO_PATH.read_text(encoding="utf-8"))
    text = _find_key(data, "formulator_output")
    assert text, "no formulator_output in pico_sample.json"
    t = text.lower().replace("-", " ")
    assert "placebo or active comparator" not in t, (
        "formulator_output still says 'placebo or active comparator' only")
    assert "waiting list" in t or "waitlist" in t
