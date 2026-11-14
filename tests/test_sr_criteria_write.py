"""Launcher must not rewrite prisma_criteria.yaml when the PICO is unchanged,
and must not wrap long lines when it does write (Session 37: the comparator
line was wrapped and left the tree modified after every launcher run)."""
import importlib
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "SOURCE_CODE" / "main.py"
LONG_C = ("Placebo, active comparator, or waiting list "
          "(waiting list reported as a subgroup)")


def _cfg(comparator=LONG_C):
    return {
        "review_title": "CBT for fibromyalgia pain",
        "effect_measure": "SMD",
        "pico": {
            "population": "Adults with fibromyalgia",
            "intervention": "Cognitive-Behavioral Therapy",
            "comparator": comparator,
            "outcome": "Pain intensity at post intervention",
        },
        "pubmed_query_cleaned": ("Adults with fibromyalgia AND Cognitive-Behavioral "
                                 "Therapy AND Pain intensity AND randomized "
                                 "controlled trial[pt]"),
        "inclusion_criteria": ["RCT", "Adult participants"],
        "exclusion_criteria": ["Non-RCT", "Animal studies"],
    }


@pytest.fixture(scope="module")
def cf():
    try:
        return importlib.import_module("pipelines.sr.src.utils.criteria_file")
    except ModuleNotFoundError:
        pytest.fail("pipelines/sr/src/utils/criteria_file.py missing (criteria write)")


def test_writes_new_file(cf, tmp_path):
    p = tmp_path / "prisma_criteria.yaml"
    assert cf.write_criteria_if_changed(p, _cfg()) is True
    assert yaml.safe_load(p.read_text(encoding="utf-8")) == _cfg()


def test_long_comparator_stays_on_one_line(cf, tmp_path):
    p = tmp_path / "prisma_criteria.yaml"
    cf.write_criteria_if_changed(p, _cfg())
    assert f"  comparator: {LONG_C}\n" in p.read_text(encoding="utf-8")


def test_unchanged_pico_does_not_touch_file(cf, tmp_path):
    p = tmp_path / "prisma_criteria.yaml"
    wrapped = yaml.dump(_cfg(), allow_unicode=True, sort_keys=False)  # old writer
    assert "\n    a subgroup)" in wrapped          # sanity: old writer wraps
    p.write_bytes(wrapped.replace("\n", "\r\n").encode("utf-8"))
    before = p.read_bytes()
    assert cf.write_criteria_if_changed(p, _cfg()) is False
    assert p.read_bytes() == before


def test_changed_pico_is_written(cf, tmp_path):
    p = tmp_path / "prisma_criteria.yaml"
    cf.write_criteria_if_changed(p, _cfg("Placebo or active comparator"))
    assert cf.write_criteria_if_changed(p, _cfg()) is True
    assert yaml.safe_load(p.read_text(encoding="utf-8"))["pico"]["comparator"] == LONG_C


def test_key_order_kept_and_no_bom(cf, tmp_path):
    p = tmp_path / "prisma_criteria.yaml"
    cf.write_criteria_if_changed(p, _cfg())
    raw = p.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf")
    assert raw.decode("utf-8").startswith("review_title:")


def test_unreadable_existing_file_is_replaced(cf, tmp_path):
    p = tmp_path / "prisma_criteria.yaml"
    p.write_text("pico: [unclosed", encoding="utf-8")
    assert cf.write_criteria_if_changed(p, _cfg()) is True
    assert yaml.safe_load(p.read_text(encoding="utf-8")) == _cfg()


def test_launcher_uses_helper():
    src = LAUNCHER.read_text(encoding="utf-8")
    assert "write_criteria_if_changed(" in src, "launcher must call the helper"
    assert "_yaml.dump(cfg_yaml" not in src, "old wrapping writer still in launcher"
