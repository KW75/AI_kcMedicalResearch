"""
PICO step (Next work item 1, Session 39): the comparator default reminds the
doctor that waiting-list controls are possible (analysed as a subgroup), and
inclusion/exclusion criteria are asked, saved with the PICO and written to
prisma_criteria.yaml instead of fixed lists.
"""
from pathlib import Path

import main


def _answers(monkeypatch, *values):
    it = iter(values)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(it))


# create: P, I, C, O, inclusion, exclusion

def test_comparator_default_mentions_waiting_list_trials(monkeypatch):
    _answers(monkeypatch, "Adults with fibromyalgia", "CBT", "", "Pain", "", "")
    pico = main._create_pico()
    assert pico["comparator"] == main.DEFAULT_COMPARATOR
    low = main.DEFAULT_COMPARATOR.lower()
    for word in ("usual care", "placebo", "waiting list"):
        assert word in low
    # active treatments are a separate comparison, not pooled with these
    assert "active" not in low


def test_typed_comparator_replaces_default(monkeypatch):
    _answers(monkeypatch, "P", "I", "Usual care", "O", "", "")
    assert main._create_pico()["comparator"] == "Usual care"


def test_create_enter_keeps_default_criteria(monkeypatch):
    _answers(monkeypatch, "P", "I", "", "O", "", "")
    pico = main._create_pico()
    assert pico["inclusion_criteria"] == main.DEFAULT_INCLUSION
    assert pico["exclusion_criteria"] == main.DEFAULT_EXCLUSION


def test_criteria_split_on_semicolon_and_keep_commas(monkeypatch):
    _answers(monkeypatch, "P", "I", "", "O",
             " RCT ; Children aged 6-12, both sexes ;", "Animal studies")
    pico = main._create_pico()
    assert pico["inclusion_criteria"] == ["RCT", "Children aged 6-12, both sexes"]
    assert pico["exclusion_criteria"] == ["Animal studies"]


def test_default_lists_are_copies(monkeypatch):
    _answers(monkeypatch, "P", "I", "", "O", "", "")
    pico = main._create_pico()
    pico["inclusion_criteria"].append("changed")
    assert "changed" not in main.DEFAULT_INCLUSION


# modify: P, I, C, O, inclusion, exclusion

def test_modify_enter_keeps_saved_values(monkeypatch):
    old = {"population": "P", "intervention": "I", "comparator": "Usual care",
           "outcome": "O", "inclusion_criteria": ["RCT", "Children"],
           "exclusion_criteria": ["Non-RCT"]}
    _answers(monkeypatch, "", "", "", "", "", "")
    pico = main._modify_pico(dict(old))
    assert pico["comparator"] == "Usual care"
    assert pico["inclusion_criteria"] == ["RCT", "Children"]
    assert pico["exclusion_criteria"] == ["Non-RCT"]


def test_modify_old_pico_gets_defaults(monkeypatch):
    old = {"population": "P", "intervention": "I", "comparator": "", "outcome": "O"}
    _answers(monkeypatch, "", "", "", "", "", "")
    pico = main._modify_pico(dict(old))
    assert pico["comparator"] == main.DEFAULT_COMPARATOR
    assert pico["inclusion_criteria"] == main.DEFAULT_INCLUSION
    assert pico["exclusion_criteria"] == main.DEFAULT_EXCLUSION


def test_modify_typed_criteria_replace(monkeypatch):
    old = {"population": "P", "intervention": "I", "comparator": "C", "outcome": "O"}
    _answers(monkeypatch, "", "", "", "", "RCT; Children aged 6-12", "Adults")
    pico = main._modify_pico(dict(old))
    assert pico["inclusion_criteria"] == ["RCT", "Children aged 6-12"]
    assert pico["exclusion_criteria"] == ["Adults"]


# step 3: prisma_criteria.yaml

def test_criteria_from_pico_uses_saved_or_defaults():
    inc, exc = main._criteria_from_pico(
        {"inclusion_criteria": ["RCT", "Children"], "exclusion_criteria": ["Adults"]})
    assert (inc, exc) == (["RCT", "Children"], ["Adults"])
    inc, exc = main._criteria_from_pico({})
    assert (inc, exc) == (main.DEFAULT_INCLUSION, main.DEFAULT_EXCLUSION)


def test_launcher_no_longer_hard_codes_criteria():
    src = Path(main.__file__).read_text(encoding="utf-8")
    assert '"inclusion_criteria": ["RCT", "Adult participants"]' not in src
    assert '"exclusion_criteria": ["Non-RCT", "Animal studies"]' not in src

# Exclude_WaitList keyword: the doctor types it, the saved comparator is plain text

def test_exclude_waitlist_keyword_on_create(monkeypatch):
    _answers(monkeypatch, "P", "I", "  exclude_waitlist ", "O", "", "")
    pico = main._create_pico()
    assert pico["comparator"] == main.EXCLUDE_WAITLIST_COMPARATOR
    assert pico["comparator"] == "Usual care or attention placebo"


def test_exclude_waitlist_keyword_on_modify(monkeypatch):
    old = {"population": "P", "intervention": "I",
           "comparator": main.DEFAULT_COMPARATOR, "outcome": "O"}
    _answers(monkeypatch, "", "", "Exclude_WaitList", "", "", "")
    pico = main._modify_pico(dict(old))
    assert pico["comparator"] == "Usual care or attention placebo"
