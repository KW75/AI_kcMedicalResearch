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


def test_records_go_to_their_own_header_folder(tmp_path):
    src = _png(tmp_path / "scan.png")
    out, rep = tmp_path / "out", tmp_path / "reports" / "ocr"
    engine.run_single(src, out, "Test scan", "fake-model", call=FakeModel(),
                      now=NOW, records_root=rep)
    assert len(list((rep / "Test_scan_2026-11-07").glob("*.md"))) == 1
    assert not (out / "records").exists()
    assert list(out.glob("Test_scan_2026-11-07_SUMMARY.md"))


def test_second_scan_same_name_same_day_does_not_overwrite(tmp_path):
    src = _png(tmp_path / "scan.png")
    out, rep = tmp_path / "out", tmp_path / "reports" / "ocr"
    r1 = engine.run_single(src, out, "Test scan", "fake-model", call=FakeModel(),
                           now=NOW, records_root=rep)
    r2 = engine.run_single(src, out, "Test scan", "fake-model", call=FakeModel(),
                           now=NOW, records_root=rep)
    assert r1["header"] == "Test_scan_2026-11-07"
    assert r2["header"] == "Test_scan_2026-11-07_2"
    assert (rep / "Test_scan_2026-11-07_2").is_dir()
    assert len(list(out.glob("*_SUMMARY.md"))) == 2

def test_repeat_scan_with_empty_name_gets_a_number(tmp_path):
    src = _png(tmp_path / "scan.png")
    out, rep = tmp_path / "out", tmp_path / "reports" / "ocr"
    r1 = engine.run_single(src, out, "", "fake-model", call=FakeModel(),
                           now=NOW, records_root=rep)
    r2 = engine.run_single(src, out, "", "fake-model", call=FakeModel(),
                           now=NOW, records_root=rep)
    assert r1["header"] == "OCR_2026-11-07_1430"
    assert r2["header"] == "OCR_2026-11-07_1430_2"
    assert (rep / "OCR_2026-11-07_1430").is_dir()
    assert (rep / "OCR_2026-11-07_1430_2").is_dir()

# --- Long text: summarised in parts, nothing cut silently -------------------

def _ctx_call(answer="note"):
    prompts = []

    def call(prompt, images=None):
        prompts.append(prompt)
        return answer
    call.prompts = prompts
    return call


def _ctx_txt(folder, name, text):
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    path.write_text(text, encoding="utf-8")
    return path


def test_short_document_is_still_one_call(tmp_path, monkeypatch):
    monkeypatch.setattr(engine, "_budget_chars", lambda: 2000)
    path = _ctx_txt(tmp_path / "in", "short.txt", "Hb 13.2 g/dL. " * 20)
    call = _ctx_call()
    engine.run_single(path, tmp_path / "out", "t", "fake", call=call,
                      log=lambda m: None)
    assert len(call.prompts) == 1
    assert engine.PART_PROMPT not in call.prompts[0]


def test_long_document_is_summarised_in_parts_and_nothing_is_lost(tmp_path, monkeypatch):
    monkeypatch.setattr(engine, "_budget_chars", lambda: 2000)
    words = [f"W{i:04d}" for i in range(1200)]          # about 7,200 characters
    path = _ctx_txt(tmp_path / "in", "long.txt", " ".join(words))
    call = _ctx_call()
    logs = []
    engine.run_single(path, tmp_path / "out", "t", "fake", call=call,
                      log=logs.append)
    parts = [p for p in call.prompts if engine.PART_PROMPT in p]
    assert len(parts) >= 3
    sent = "".join(parts)
    assert all(w in sent for w in words)                # every word reached the model
    assert all(len(p) <= 2000 + len(engine.PART_PROMPT) + 200 for p in parts)
    assert any(engine.COMBINE_PROMPT in p for p in call.prompts)
    assert any("summarised in" in m for m in logs)


def test_long_synopsis_is_combined_in_parts(tmp_path, monkeypatch):
    monkeypatch.setattr(engine, "_budget_chars", lambda: 2000)
    folder = tmp_path / "in"
    for name in ["a.txt", "b.txt", "c.txt", "d.txt"]:
        _ctx_txt(folder, name, f"Text of {name}, BP 140/90 mmHg.")
    call = _ctx_call(answer="x" * 900)                  # long per-file summaries
    result = engine.run_set(folder, tmp_path / "out", "t", "fake", call=call,
                            log=lambda m: None)
    assert len(result["records"]) == 4
    parts = "".join(p for p in call.prompts if engine.PART_PROMPT in p)
    assert all(f"### {n}" in parts for n in ["a.txt", "b.txt", "c.txt", "d.txt"])
    assert any(engine.COMBINE_PROMPT in p and engine.SYNOPSIS_PROMPT in p
               for p in call.prompts)

# --- Notes that do not shrink: stop early, still write the record -----------

def _echo_call():
    prompts = []

    def call(prompt, images=None):
        prompts.append(prompt)
        return prompt                                   # notes never get shorter
    call.prompts = prompts
    return call


def test_summary_failure_still_writes_the_record(tmp_path, monkeypatch):
    monkeypatch.setattr(engine, "_budget_chars", lambda: 2000)
    words = " ".join(f"W{i:04d}" for i in range(1200))
    path = _ctx_txt(tmp_path / "in", "long.txt", words)
    logs = []
    result = engine.run_single(path, tmp_path / "out", "t", "fake",
                               call=_echo_call(), log=logs.append,
                               records_root=tmp_path / "rep")
    assert result["failed"] == []
    md = list((tmp_path / "rep").rglob("*.md"))
    assert len(md) == 1
    text = md[0].read_text(encoding="utf-8")
    assert "Summary not written" in text
    assert "W1199" in text                              # full text is kept
    assert any("WARNING" in m for m in logs)


def test_notes_that_do_not_shrink_stop_after_one_round(tmp_path, monkeypatch):
    monkeypatch.setattr(engine, "_budget_chars", lambda: 2000)
    words = " ".join(f"W{i:04d}" for i in range(1200))
    path = _ctx_txt(tmp_path / "in", "long.txt", words)
    logs = []
    engine.run_single(path, tmp_path / "out", "t", "fake", call=_echo_call(),
                      log=logs.append, records_root=tmp_path / "rep")
    assert sum("summarised in" in m for m in logs) == 1


def test_synopsis_failure_keeps_each_file_summary(tmp_path, monkeypatch):
    monkeypatch.setattr(engine, "_budget_chars", lambda: 2000)
    folder = tmp_path / "in"
    for name in ["a.txt", "b.txt", "c.txt", "d.txt"]:
        _ctx_txt(folder, name, f"{name} " + "BP 140/90 mmHg. " * 50)
    result = engine.run_set(folder, tmp_path / "out", "t", "fake",
                            call=_echo_call(), log=lambda m: None,
                            records_root=tmp_path / "rep")
    assert len(result["records"]) == 4
    syn = list((tmp_path / "out").glob("*_SYNOPSIS.md"))
    assert len(syn) == 1
    text = syn[0].read_text(encoding="utf-8")
    assert "Synopsis not written" in text
    assert "### d.txt" in text
