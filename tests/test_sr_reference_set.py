"""Session 38 (7h): the fibromyalgia trial set is an example, not an app default.

The papers, PICO and reviewer overrides used to sit in input/sr and the SR
config, so a doctor's run started from someone else's review. They now live in
reference/sr_cbt_fibromyalgia/ (PDFs and paper_text git-ignored). The config is
a sample with <...> placeholders and the run stops until they are replaced;
input/sr/study_overrides.yaml is a comments-only template.
"""
from pathlib import Path

import pytest
import yaml

try:
    import pipelines.sr.src.utils.criteria_file as cf
except ImportError:
    import SOURCE_CODE.pipelines.sr.src.utils.criteria_file as cf

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "SOURCE_CODE" / "pipelines" / "sr" / "config" / "prisma_criteria.yaml"
INPUT_OVR = ROOT / "input" / "sr" / "study_overrides.yaml"
REF = ROOT / "reference" / "sr_cbt_fibromyalgia"
MAIN_SRC = ROOT / "SOURCE_CODE" / "pipelines" / "sr" / "main.py"


def _load(p):
    return yaml.safe_load(p.read_text(encoding="utf-8-sig"))


def test_default_criteria_is_a_sample_not_fibromyalgia():
    assert "fibromyalgia" not in str(_load(CONFIG)).lower()
    assert cf.placeholder_fields(_load(CONFIG)), "sample has no <...> placeholders"


def test_placeholder_fields_names_unfilled_fields():
    cfg = {"review_title": "<Review title>", "effect_measure": "SMD",
           "pico": {"population": "Adults", "intervention": "<Treatment X>",
                    "comparator": "Usual care", "outcome": "Pain"}}
    assert cf.placeholder_fields(cfg) == ["review_title", "pico.intervention"]


def test_placeholder_fields_empty_for_real_criteria():
    assert cf.placeholder_fields(_load(REF / "prisma_criteria.yaml")) == []


def test_main_stops_while_placeholders_remain():
    src = MAIN_SRC.read_text(encoding="utf-8")
    i = src.find("cfg = load_config(")
    j = src.find("placeholder_fields(", i)
    assert i != -1 and j != -1, "main.py does not check <...> placeholders after load_config"
    assert "SystemExit" in src[j:j + 600]


def test_input_overrides_is_an_empty_template():
    assert not _load(INPUT_OVR), "input/sr/study_overrides.yaml still holds entries"
    assert "#" in INPUT_OVR.read_text(encoding="utf-8-sig")


@pytest.mark.parametrize("name", [
    "prisma_criteria.yaml", "pico_sample.json", "study_overrides.yaml",
])
def test_reference_set_files_exist(name):
    assert (REF / name).is_file()


def test_reference_overrides_keep_the_reviewer_entries():
    authors = {e.get("first_author") for e in _load(REF / "study_overrides.yaml").values()}
    assert {"Ang", "Karlsson", "Lami", "McCrae"} <= authors
