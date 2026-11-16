"""[SENSITIVITY] names each needs-review study's own reason (F13 a, item 6).

Run 20261116_080329 said the runs disagreed for every needs-review study,
also for Jensen and Karlsson, which only the quote gate held back.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import SOURCE_CODE.pipelines.sr.main as main_mod

AL = sys.modules[main_mod.review_skip_reason.__module__]
DISAGREE = AL.review_skip_reason("table_shift")


class _FakeMA:
    data = None

    def run(self, data, effect_measure):
        _FakeMA.data = data
        return {"pooled_effect": -0.1, "ci_lower": -0.5, "ci_upper": 0.3, "I2": 10.0}


def _log(monkeypatch, caplog, rows, review):
    monkeypatch.setattr(main_mod, "MetaAnalyzer", _FakeMA)
    with caplog.at_level(logging.INFO):
        main_mod._log_review_sensitivity(rows, review, "SMD")
    return "\n".join(caplog.messages)


def test_labels_match_audit_logger_reasons():
    assert DISAGREE.startswith("needs review: runs disagree (table_shift)")
    assert main_mod._review_labels(DISAGREE) == ["runs disagree"]
    assert main_mod._review_labels(AL.TOO_FEW_RUNS_REASON) == ["too few usable runs"]
    assert main_mod._review_labels(AL.QUOTE_GATE_REASON) == ["quote not found"]
    assert main_mod._review_labels(AL.NUMBER_GATE_REASON) == ["number not in quote"]
    assert main_mod._review_labels(None) == []


def test_combined_reason_gets_both_labels():
    reason = AL.review_skip_reason("table_shift",
                                   quote_warning="x was not found verbatim y",
                                   extraction_method="vision")
    assert main_mod._review_labels(reason) == ["runs disagree", "quote not found"]


def test_quote_only_studies_not_called_disagreed(monkeypatch, caplog):
    review = [{"study": "Jensen (2012)", "review_reason": AL.QUOTE_GATE_REASON},
              {"study": "Karlsson (2015)", "review_reason": AL.QUOTE_GATE_REASON}]
    txt = _log(monkeypatch, caplog, [], review)
    assert "Jensen (2012) [quote not found]" in txt
    assert "Karlsson (2015) [quote not found]" in txt
    assert "disagree" not in txt.lower()
    assert "primary estimate excludes them" in txt


def test_disagreeing_study_still_says_so(monkeypatch, caplog):
    review = [{"study": "Lami (2017)", "review_reason": DISAGREE}]
    txt = _log(monkeypatch, caplog, [{"study": "Ang (2010)"}], review)
    assert "Lami (2017) [runs disagree]" in txt


def test_reason_not_passed_to_meta_analyzer(monkeypatch, caplog):
    review = [{"study": "Jensen (2012)", "review_reason": AL.QUOTE_GATE_REASON}]
    _log(monkeypatch, caplog, [{"study": "Ang (2010)"}], review)
    assert len(_FakeMA.data) == 2
    assert "review_reason" not in _FakeMA.data.columns


def test_loop_stores_reason_on_review_row():
    src = Path(main_mod.__file__).read_text(encoding="utf-8")
    assert '_row["review_reason"] = _review' in src