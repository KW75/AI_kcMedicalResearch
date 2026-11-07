"""OCR step 4: engine (reader -> vision model -> record -> SUMMARY/SYNOPSIS).

Uses a fake model, so Ollama never needs to run.
"""
from datetime import datetime

import fitz
import pytest
from PIL import Image

from pipelines.ocr import engine

NOW = datetime(2026, 11, 7, 14, 30)


class FakeModel:
    """Stands in for the AI. Calls with images = transcription; others = summaries."""

    def __init__(self):
        self.calls = []

    def __call__(self, prompt, images=None):
        self.calls.append({"prompt": prompt, "images": images})
        if images:
            return "OCR TEXT line 1\n3) BP 140/90"
        if prompt.startswith(engine.SYNOPSIS_PROMPT):
            return "FAKE SYNOPSIS"
        n = len([c for c in self.calls if not c["images"]
                 and not c["prompt"].startswith(engine.SYNOPSIS_PROMPT)])
        return f"FAKE SUMMARY {n}"


def _text_pdf(path):
    doc = fitz.open()
    doc.new_page().insert_text((72, 72), "Blood pressure 140/90 mmHg recorded today")
    doc.save(str(path))
    doc.close()
    return path


def _png(path):
    Image.new("RGB", (40, 20), "white").save(path)
    return path


def _md_records(out_dir):
    return sorted((out_dir / "records").glob("*.md"))


def test_text_layer_pdf_needs_no_vision_call(tmp_path):
    src = _text_pdf(tmp_path / "note.pdf")
    fake = FakeModel()
    engine.run_single(src, tmp_path / "out", "Test", "fake-model", call=fake, now=NOW)
    assert all(not c["images"] for c in fake.calls)
    md = _md_records(tmp_path / "out")[0].read_text(encoding="utf-8")
    assert "Page 1 (text layer)" in md
    assert "Blood pressure 140/90 mmHg recorded today" in md


def test_image_page_is_sent_to_the_model_and_labelled_ai_read(tmp_path):
    src = _png(tmp_path / "scan.png")
    fake = FakeModel()
    engine.run_single(src, tmp_path / "out", "Test", "fake-model", call=fake, now=NOW)
    image_calls = [c for c in fake.calls if c["images"]]
    assert len(image_calls) == 1
    assert len(image_calls[0]["images"]) == 1
    assert image_calls[0]["prompt"] == engine.TRANSCRIBE_PROMPT
    md = _md_records(tmp_path / "out")[0].read_text(encoding="utf-8")
    assert "Page 1 (AI read)" in md
    assert "3) BP 140/90" in md


def test_single_file_writes_record_and_summary(tmp_path):
    src = _png(tmp_path / "scan.png")
    out = tmp_path / "out"
    result = engine.run_single(src, out, "Test", "fake-model", call=FakeModel(), now=NOW)
    records = _md_records(out)
    assert len(records) == 1
    md = records[0].read_text(encoding="utf-8")
    assert md.index("FAKE SUMMARY 1") < md.index("## Full text")
    summaries = list(out.glob("*_SUMMARY.md"))
    assert len(summaries) == 1
    assert "FAKE SUMMARY 1" in summaries[0].read_text(encoding="utf-8")
    assert result["failed"] == []


def test_set_writes_one_record_per_file_and_one_synopsis(tmp_path):
    inp, out = tmp_path / "in", tmp_path / "out"
    inp.mkdir()
    _text_pdf(inp / "a_note.pdf")
    _png(inp / "b_scan.png")
    fake = FakeModel()
    engine.run_set(inp, out, "Test", "fake-model", call=fake, now=NOW)
    assert len(_md_records(out)) == 2
    assert len(list(out.glob("*_SYNOPSIS.md"))) == 1
    assert not list(out.glob("*_SUMMARY.md"))
    syn = [c["prompt"] for c in fake.calls
           if c["prompt"].startswith(engine.SYNOPSIS_PROMPT)]
    assert len(syn) == 1
    for s in ("a_note.pdf", "b_scan.png", "FAKE SUMMARY 1", "FAKE SUMMARY 2"):
        assert s in syn[0]


def test_one_bad_file_does_not_stop_the_set(tmp_path):
    inp, out = tmp_path / "in", tmp_path / "out"
    inp.mkdir()
    _png(inp / "a_good.png")
    (inp / "b_broken.png").write_bytes(b"not an image")
    result = engine.run_set(inp, out, "Test", "fake-model", call=FakeModel(), now=NOW)
    assert len(_md_records(out)) == 1
    assert [name for name, _ in result["failed"]] == ["b_broken.png"]
    assert list(out.glob("*_SYNOPSIS.md"))


def test_no_synopsis_when_every_file_fails(tmp_path):
    inp, out = tmp_path / "in", tmp_path / "out"
    inp.mkdir()
    (inp / "broken.png").write_bytes(b"not an image")
    result = engine.run_set(inp, out, "Test", "fake-model", call=FakeModel(), now=NOW)
    assert result["summary"] is None
    assert not list(out.glob("*_SYNOPSIS.md"))


def test_empty_folder_raises(tmp_path):
    inp = tmp_path / "in"
    inp.mkdir()
    with pytest.raises(ValueError):
        engine.run_set(inp, tmp_path / "out", "Test", "fake-model",
                       call=FakeModel(), now=NOW)


def test_transcribe_prompt_forbids_summarising():
    assert "do not summarise" in engine.TRANSCRIBE_PROMPT.lower()
