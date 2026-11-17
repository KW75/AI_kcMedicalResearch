"""Session 47 (item i): a study the reviewer excluded (exclude_from_meta) skips
AI extraction.

Run 20261117_201642: Ang went through ~10.6 min of vision extraction
(20:20:27-20:31:06) and was then left out of the meta-analysis anyway.
The skipped row still carries reviewer_exclusion (written by apply()) and
author/year in study_metadata, so [EXCLUDED], the report and the score work.
"""
import importlib
import logging

import pytest

REASON = "clinical pain reported only as Week 6 change scores"


def _import(*names):
    for cand in names:
        try:
            return importlib.import_module(cand)
        except ImportError:
            continue
    pytest.skip(f"none importable: {names}")


@pytest.fixture(scope="module")
def mods():
    de = _import("pipelines.sr.src.extraction.data_extractor",
                 "SOURCE_CODE.pipelines.sr.src.extraction.data_extractor")
    so = _import("pipelines.sr.src.extraction.study_overrides",
                 "SOURCE_CODE.pipelines.sr.src.extraction.study_overrides")
    al = _import("pipelines.sr.src.utils.audit_logger",
                 "SOURCE_CODE.pipelines.sr.src.utils.audit_logger")
    return de, so, al


def _extractor(de, overrides, monkeypatch):
    ex = de.DataExtractor.__new__(de.DataExtractor)
    ex.provider = "qwen"
    ex._study_overrides_cache = overrides
    calls = []

    def fake(pdf_path, filename="", paper_text=None):
        calls.append(filename)
        return {"filename": filename}

    monkeypatch.setattr(ex, "extract_by_pdf_path", fake)
    return ex, calls


def _yaml(tmp_path, so):
    p = tmp_path / "ovr.yaml"
    p.write_text(
        '"ang.pdf":\n'
        '  first_author: Ang\n'
        '  year: 2010\n'
        f'  exclude_from_meta: "{REASON}"\n'
        '"jensen.pdf":\n'
        '  first_author: Jensen\n'
        '  year: 2012\n'
        '  n_intervention: 19\n', encoding="utf-8")
    return so.StudyOverrides(str(p))


RECS = [{"filename": "ang.pdf", "pdf_path": "ang.pdf"},
        {"filename": "jensen.pdf", "pdf_path": "jensen.pdf"}]


def test_excluded_study_skips_the_model(mods, tmp_path, monkeypatch):
    de, so, _ = mods
    ex, calls = _extractor(de, _yaml(tmp_path, so), monkeypatch)
    out = ex.extract_batch(RECS, delay_seconds=0)
    assert calls == ["jensen.pdf"]
    assert len(out) == 2
    ang = out[0]
    assert ang["reviewer_exclusion"] == REASON
    assert ang["study_metadata"] == {"first_author": "Ang", "year": 2010}
    assert ang["extraction_method"] == "skipped_reviewer_exclusion"


def test_skip_is_logged(mods, tmp_path, monkeypatch, caplog):
    de, so, _ = mods
    ex, _ = _extractor(de, _yaml(tmp_path, so), monkeypatch)
    with caplog.at_level(logging.INFO):
        ex.extract_batch(RECS, delay_seconds=0)
    assert any("[EXCLUDED] Ang (2010): skipped AI extraction" in m for m in caplog.messages)


def test_skipped_row_gives_the_exclusion_reason(mods, tmp_path, monkeypatch):
    de, so, al = mods
    ex, _ = _extractor(de, _yaml(tmp_path, so), monkeypatch)
    ang = ex.extract_batch(RECS, delay_seconds=0)[0]
    assert al.reviewer_exclusion_reason(ang) == "excluded by reviewer: " + REASON


def test_no_overrides_extracts_everything(mods, tmp_path, monkeypatch):
    de, so, _ = mods
    ex, calls = _extractor(de, so.StudyOverrides(str(tmp_path / "none.yaml")), monkeypatch)
    ex.extract_batch(RECS, delay_seconds=0)
    assert calls == ["ang.pdf", "jensen.pdf"]


def test_broken_overrides_fall_back_to_extraction(mods, monkeypatch):
    de, _, _ = mods

    class Broken:
        def lookup(self, name):
            raise RuntimeError("boom")

    ex, calls = _extractor(de, Broken(), monkeypatch)
    ex.extract_batch(RECS, delay_seconds=0)
    assert calls == ["ang.pdf", "jensen.pdf"]
