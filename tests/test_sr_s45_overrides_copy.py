"""Session 45 (item c): the run folder keeps a copy of the overrides file the
run used. Run 20261117_155621 needed a hand copy to record the reviewer's values."""
import logging
import pathlib
import types

import SOURCE_CODE.pipelines.sr.main as M

SRC = pathlib.Path(__file__).resolve().parents[1] / "SOURCE_CODE" / "pipelines" / "sr" / "main.py"
YAML = '"a.pdf":\n  first_author: Lami\n"b.pdf":\n  first_author: Ang\n'


def _layout(tmp_path):
    return types.SimpleNamespace(extracted=tmp_path / "run" / "data" / "extracted")


def _ov(path, entries):
    return types.SimpleNamespace(path=path, entries=entries)


def test_copies_loaded_file(tmp_path, caplog):
    caplog.set_level(logging.INFO)
    src = tmp_path / "study_overrides.yaml"
    src.write_text(YAML, encoding="utf-8")
    dst = M._save_overrides_used(_layout(tmp_path), _ov(src, {"a.pdf": {}, "b.pdf": {}}))
    assert dst is not None and dst.name == "study_overrides_used.yaml"
    assert dst.read_text(encoding="utf-8") == YAML
    assert any("[OVERRIDES] copied" in r.getMessage() and "2 entries" in r.getMessage()
               for r in caplog.records)


def test_empty_template_writes_nothing(tmp_path, caplog):
    caplog.set_level(logging.INFO)
    src = tmp_path / "study_overrides.yaml"
    src.write_text("# template only\n", encoding="utf-8")
    assert M._save_overrides_used(_layout(tmp_path), _ov(src, {})) is None
    assert not (tmp_path / "run").exists()
    assert any("[OVERRIDES] none loaded" in r.getMessage() for r in caplog.records)


def test_no_overrides_object(tmp_path, caplog):
    caplog.set_level(logging.INFO)
    assert M._save_overrides_used(_layout(tmp_path), None) is None
    assert any("[OVERRIDES] none loaded" in r.getMessage() for r in caplog.records)


def test_copy_failure_warns_not_crashes(tmp_path, caplog):
    caplog.set_level(logging.INFO)
    gone = tmp_path / "deleted.yaml"
    assert M._save_overrides_used(_layout(tmp_path), _ov(gone, {"a.pdf": {}})) is None
    assert any(r.levelno == logging.WARNING and "[OVERRIDES] could not copy" in r.getMessage()
               for r in caplog.records)


def test_main_keeps_extractor_and_copies_after_extracts():
    src = SRC.read_text(encoding="utf-8")
    assert "extractor = DataExtractor(" in src
    assert "er = extractor.extract_batch(included)" in src
    w = src.index("write_extracts(layout.extracted_csv, er)")
    c = src.index('_save_overrides_used(layout, getattr(extractor, "_study_overrides", None))')
    r = src.index("STAGE 3.5")
    assert w < c < r
