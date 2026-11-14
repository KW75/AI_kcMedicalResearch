# tests/test_sr_metadata_precedence.py
"""Session 41 (bug 4a): which first_author / year the pooled row gets.

Run 20261114_133303: the model wrote "Kim" (2011) in study_metadata for the
Lami paper; the PDF lookup found Lami, 2017 (DOI 10.1007/s10608-017-9875-4),
but _mirror_study_metadata only filled empty fields, so the pooled row said
"Kim (2011)". Also, study_overrides.apply() ran after the PDF lookup and
fills metadata only when missing, so a reviewer's year lost to the lookup.
Rule: reviewer (study_overrides.yaml) > PDF lookup > model. A replaced
model value is logged as a [METADATA] warning naming both values.
"""
import logging

import pytest

from pipelines.sr.src.extraction import study_overrides as so_mod
from pipelines.sr.src.extraction.data_extractor import DataExtractor

DOI = "10.1007/s10608-017-9875-4"


def _extractor(monkeypatch, derived, entry=None):
    ex = DataExtractor.__new__(DataExtractor)
    ov = so_mod.StudyOverrides.__new__(so_mod.StudyOverrides)
    ov.lookup = lambda name: entry          # real apply(), fake yaml lookup
    ex._study_overrides_cache = ov
    monkeypatch.setattr(so_mod, "resolve_pdf_metadata",
                        lambda path: dict(derived))
    return ex


def _run(ex, author, year):
    r = {"filename": "s10608-017-9875-4.pdf",
         "study_metadata": {"first_author": author, "year": year}}
    return ex._apply_known_pdf_corrections(r, r["filename"], "x.pdf")


def _meta_warnings(caplog):
    return [m for m in caplog.messages if "[METADATA]" in m]


def test_pdf_lookup_author_and_year_beat_the_model(monkeypatch, caplog):
    caplog.set_level(logging.INFO)
    ex = _extractor(monkeypatch, {"first_author": "Lami", "year": 2017, "doi": DOI})
    r = _run(ex, "Kim", 2011)
    assert r["study_metadata"]["first_author"] == "Lami"
    assert int(r["study_metadata"]["year"]) == 2017
    w = " ".join(_meta_warnings(caplog))
    assert "Kim" in w and "Lami" in w


def test_reviewer_beats_pdf_lookup_and_model(monkeypatch, caplog):
    caplog.set_level(logging.INFO)
    ex = _extractor(monkeypatch, {"first_author": "Lami", "year": 2017, "doi": DOI},
                    entry={"first_author": "Lami", "year": 2018})
    r = _run(ex, "Kim", 2011)
    assert r["study_metadata"]["first_author"] == "Lami"
    assert int(r["study_metadata"]["year"]) == 2018


def test_no_lookup_result_keeps_the_model_author(monkeypatch, caplog):
    caplog.set_level(logging.INFO)
    ex = _extractor(monkeypatch, {})
    r = _run(ex, "Dennis C. Ang", 2010)
    assert r["study_metadata"]["first_author"] == "Dennis C. Ang"
    assert int(r["study_metadata"]["year"]) == 2010
    assert not _meta_warnings(caplog)


@pytest.mark.parametrize("year", [2017, "2017", 2017.0])
def test_same_value_is_not_reported(monkeypatch, caplog, year):
    caplog.set_level(logging.INFO)
    ex = _extractor(monkeypatch, {"first_author": "Lami", "year": 2017})
    _run(ex, "Lami", year)
    assert not _meta_warnings(caplog)


def test_empty_model_field_is_filled_without_warning(monkeypatch, caplog):
    caplog.set_level(logging.INFO)
    ex = _extractor(monkeypatch, {"first_author": "Lami", "year": 2017})
    r = _run(ex, None, None)
    assert r["study_metadata"]["first_author"] == "Lami"
    assert int(r["study_metadata"]["year"]) == 2017
    assert not _meta_warnings(caplog)
