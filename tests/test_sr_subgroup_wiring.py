"""Item 11 step 2 (Session 39): comparator_type accepted from
study_overrides.yaml; main.py classifies each pooled row and logs
[SUBGROUP] lines."""
from pathlib import Path

from pipelines.sr.src.extraction import study_overrides as so
from pipelines.sr.src.analysis.subgroups import (
    subgroup_summary, WAITING_LIST, USUAL_CARE,
)

MAIN_PY = (Path(__file__).resolve().parents[1]
           / "SOURCE_CODE" / "pipelines" / "sr" / "main.py")


def test_comparator_type_is_allowed_field():
    assert "comparator_type" in so.ALLOWED_FIELDS


def test_apply_sets_comparator_type_as_bare_name():
    ov = so.StudyOverrides.__new__(so.StudyOverrides)
    ov.lookup = lambda filename: {"comparator_type": "waiting_list"}
    res = ov.apply({"study_metadata": {}, "primary_outcome": {},
                    "participants": {}}, "a.pdf")
    assert res["comparator_type"] == "waiting_list"
    assert "comparator_type" in res["override_fields"].split("; ")


def test_log_lines_run_222233():
    from pipelines.sr.src.analysis.subgroups import subgroup_log_lines
    rows = [{"study": s, "comparator_type": t, "comparator_source": "label"}
            for s, t in (("Jensen (2012)", WAITING_LIST),
                         ("Karlsson (2015)", WAITING_LIST),
                         ("Lami (2018)", USUAL_CARE),
                         ("McCrae (2019)", WAITING_LIST))]
    pool = lambda m: {"pooled_effect": -0.5, "ci_lower": -0.9,
                      "ci_upper": -0.1, "I2": 10.0}
    lines = subgroup_log_lines(subgroup_summary(rows, pool), "SMD", rows)
    txt = "\n".join(lines)
    assert all(l.startswith("[SUBGROUP]") for l in lines)
    assert "Jensen (2012): Waiting list (from label)" in txt
    assert "Waiting list (k=3" in txt
    assert "SMD -0.500 [-0.900,-0.100] I2=10.0%" in txt
    assert "Usual care (k=1" in txt and "1 study - not pooled." in txt
    assert "Excluding waiting-list trials (k=1" in txt


def test_main_wires_subgroups():
    src = MAIN_PY.read_text(encoding="utf-8")
    assert "classify_comparator(r)" in src
    assert '"comparator_type"' in src
    assert "subgroup_summary(" in src
    assert "subgroup_log_lines(" in src
