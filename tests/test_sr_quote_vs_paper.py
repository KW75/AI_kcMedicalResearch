# Session 39 (item 10): extraction passes paper_text to the source-quote check;
# branch 5 (verbatim_mismatch) matches words/numbers only, with a fallback for
# table rows the model quoted with cells skipped. Real cases, run 20261112_222233.
from pathlib import Path

from pipelines.sr.src.extraction.data_extractor import DataExtractor

SRC = (Path(__file__).resolve().parents[1] / "SOURCE_CODE" / "pipelines" / "sr"
       / "src" / "extraction" / "data_extractor.py")
VERB = "not found verbatim"

ANG_TEXT = ("Week 6 change\u2021\n15\n13\n4.4 [?] 13.7\n[?]10.2 [?] 9.9\n"
            "[?]20.2 [?] 23.9\n[?]14.9 [?] 16.4\nWeek 12 change\u2021\n15\n13\n")
ANG_Q = "Week 6 change\u2021     15      13      -20.2 \u00b1 23.9    -14.9 \u00b1 16.4"


def _check(quote_i, quote_c, mi, si, mc, sc, text):
    r = {"filename": "t.pdf", "primary_outcome": {
        "mean_intervention": mi, "sd_intervention": si,
        "mean_control": mc, "sd_control": sc,
        "source_quote_intervention": quote_i, "source_quote_control": quote_c}}
    DataExtractor.__new__(DataExtractor)._flag_suspect_source_quotes(r, source_text=text)
    return r.get("source_quote_warning") or ""


def test_ang_table_cells_skipped_no_false_alarm():
    assert VERB not in _check(ANG_Q, ANG_Q, -20.2, 23.9, -14.9, 16.4, ANG_TEXT)


def test_ocr_stray_dots_no_false_alarm():      # McCrae-style text layer
    q = "participants reported less morning pain at posttreatment (M = 47.14, SE = 2.36)"
    t = "participants. reported less. morning pain at. posttreatment (M = 47.14, SE = 2.36) relative"
    assert VERB not in _check(q, q, 47.14, 2.36, 47.14, 2.36, t)


def test_made_up_quote_warns():                # Lami
    t = "CBT-P 7.58 (1.75) 7.35 (2.08) UMC 7.40 (1.29)"
    w = _check("CBT-IP group: mean = 4.2 (SD = 2.1) at post-treatment",
               "UMC group: mean = 5.1 (SD = 2.3) at post-treatment",
               4.2, 2.1, 5.1, 2.3, t)
    assert "intervention source quote was " + VERB in w
    assert "control source quote was " + VERB in w


def test_extract_batch_passes_paper_text(monkeypatch):
    ex = DataExtractor.__new__(DataExtractor)
    ex.provider = "qwen"
    seen = {}

    def fake(pdf_path, filename="", paper_text=None):
        seen["paper_text"] = paper_text
        return {"filename": filename}

    monkeypatch.setattr(ex, "extract_by_pdf_path", fake)
    ex.extract_batch([{"filename": "a.pdf", "pdf_path": "a.pdf", "paper_text": "TXT"}])
    assert seen["paper_text"] == "TXT"


def test_both_paths_use_paper_text_as_source():
    src = SRC.read_text(encoding="utf-8")
    assert "source_text=text_payload or paper_text" in src
    assert "source_text=paper_text" in src
