"""Item 11 (Session 39): control-type subgroups. Option C: the reviewer's
comparator_type (study_overrides.yaml) wins, else the extracted
control_group label; unknown -> unclassified, listed, never pooled."""
import pytest

from pipelines.sr.src.analysis.subgroups import (
    classify_comparator, subgroup_summary,
    WAITING_LIST, USUAL_CARE, UNCLASSIFIED,
)


def _r(study, ctype):
    return {"study": study, "comparator_type": ctype}


class _Pool:
    def __init__(self):
        self.calls = []

    def __call__(self, members):
        self.calls.append([m["study"] for m in members])
        return {"pooled_effect": -0.5, "ci_lower": -0.9,
                "ci_upper": -0.1, "I2": 10.0}


def test_run_222233_labels_classify():
    # control_group labels from run 20261112_222233
    cases = {"UC": USUAL_CARE, "waitinglist": WAITING_LIST,
             "Wait-list group": WAITING_LIST,
             "Usual Medical Care (UMC)": USUAL_CARE, "WLC": WAITING_LIST}
    for label, want in cases.items():
        assert classify_comparator({"control_group": label}) == (want, "label"), label


def test_unknown_or_empty_label_is_unclassified():
    for label in ("Exercise", "", None):
        assert classify_comparator({"control_group": label}) == (UNCLASSIFIED, "label")


def test_reviewer_value_wins_over_label():
    r = {"comparator_type": " Usual_Care ", "control_group": "WLC"}
    assert classify_comparator(r) == (USUAL_CARE, "reviewer")


def test_unrecognised_reviewer_value_is_unclassified_not_silent():
    ctype, source = classify_comparator(
        {"comparator_type": "waitlist", "control_group": "WLC"})
    assert ctype == UNCLASSIFIED
    assert "not recognised" in source


def test_run_222233_shape():
    # Ang is not pooled (reviewer decision), so usual care = Lami only
    pool = _Pool()
    rows = [_r("Jensen", WAITING_LIST), _r("Karlsson", WAITING_LIST),
            _r("Lami", USUAL_CARE), _r("McCrae", WAITING_LIST)]
    by = {e["key"]: e for e in subgroup_summary(rows, pool)}
    assert by[WAITING_LIST]["k"] == 3
    assert by[WAITING_LIST]["result"] is not None
    assert by[WAITING_LIST]["note"] == ""
    assert by[USUAL_CARE]["k"] == 1
    assert by[USUAL_CARE]["result"] is None
    assert "1 study - not pooled" in by[USUAL_CARE]["note"]
    ex = by["excluding_waiting_list"]
    assert ex["k"] == 1 and ex["result"] is None
    assert UNCLASSIFIED not in by and "attention_placebo" not in by
    assert pool.calls == [["Jensen", "Karlsson", "McCrae"]]


def test_two_studies_pooled_with_caution():
    by = {e["key"]: e for e in subgroup_summary(
        [_r("A", USUAL_CARE), _r("B", USUAL_CARE)], _Pool())}
    assert by[USUAL_CARE]["result"] is not None
    assert "< 3" in by[USUAL_CARE]["note"]


def test_unclassified_not_pooled_named_and_left_out_of_excluding_wl():
    pool = _Pool()
    rows = [_r("A", WAITING_LIST), _r("B", WAITING_LIST),
            _r("C", USUAL_CARE), _r("D", USUAL_CARE), _r("E", UNCLASSIFIED)]
    by = {e["key"]: e for e in subgroup_summary(rows, pool)}
    assert by[UNCLASSIFIED]["studies"] == ["E"]
    assert by[UNCLASSIFIED]["result"] is None
    assert "comparator_type" in by[UNCLASSIFIED]["note"]
    ex = by["excluding_waiting_list"]
    assert ex["studies"] == ["C", "D"]
    assert "E" in ex["note"]
    assert pool.calls == [["A", "B"], ["C", "D"], ["C", "D"]]


def test_pool_failure_is_reported_not_raised():
    def boom(members):
        raise ValueError("pooled SD is zero")
    rows = [_r(s, WAITING_LIST) for s in ("A", "B", "C")]
    by = {e["key"]: e for e in subgroup_summary(rows, boom)}
    assert by[WAITING_LIST]["result"] is None
    assert "pooled SD is zero" in by[WAITING_LIST]["note"]
