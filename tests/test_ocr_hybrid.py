"""OCR hybrid read for PDF pages with broken symbol fonts.

The text layer is exact except for the broken characters, which become [?].
The model sees the page image plus that text and fills only the [?]; code
checks nothing else changed. Ang 2010: "4.4 \\x02 13.7" (±), "(n \\x01 32)" (=).
"""
import fitz

from pipelines.ocr import engine, reader


def _pdf(path):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Plain page text that is long enough to count.")
    doc.save(str(path))
    doc.close()


# --- reader -----------------------------------------------------------------

def test_mark_broken_replaces_each_broken_character():
    assert reader.mark_broken("(n \x01 32) had 4.4 \x02 13.7") == "(n [?] 32) had 4.4 [?] 13.7"


def test_broken_pdf_page_keeps_marked_text_and_image(tmp_path, monkeypatch):
    path = tmp_path / "ang.pdf"
    _pdf(path)
    broken = "Participants (n \x01 32) had 4.4 \x02 13.7 mA at baseline."
    monkeypatch.setattr(fitz.Page, "get_text", lambda self, *a, **k: broken)
    page = reader.read_input(path)[0]
    assert page["text"] is None
    assert page["png"]
    assert page["hint"] == "Participants (n [?] 32) had 4.4 [?] 13.7 mA at baseline."


def test_clean_pdf_page_has_no_hint(tmp_path):
    path = tmp_path / "clean.pdf"
    _pdf(path)
    page = reader.read_input(path)[0]
    assert page["text"]
    assert page.get("hint") is None


# --- fill check -------------------------------------------------------------

MARKED = "(n [?] 32) had\n4.4 [?] 13.7 mA"


def test_fill_keeps_original_line_breaks():
    answer = "(n = 32) had 4.4 \u00b1 13.7 mA"          # model joined the lines
    assert engine.fill_symbols(MARKED, answer) == "(n = 32) had\n4.4 \u00b1 13.7 mA"


def test_changed_digit_is_refused():
    assert engine.fill_symbols(MARKED, "(n = 33) had\n4.4 \u00b1 13.7 mA") is None


def test_letter_or_digit_fill_is_refused():
    assert engine.fill_symbols(MARKED, "(n x 32) had\n4.4 \u00b1 13.7 mA") is None
    assert engine.fill_symbols(MARKED, "(n 2 32) had\n4.4 \u00b1 13.7 mA") is None


def test_latex_fill_is_refused():
    assert engine.fill_symbols(MARKED, "(n $=$ 32) had\n4.4 $\\pm$ 13.7 mA") is None


def test_dropped_words_are_refused():
    assert engine.fill_symbols(MARKED, "(n = 32) had\n4.4 \u00b1 13.7") is None


# --- engine -----------------------------------------------------------------

HINT = "Participants (n [?] 32) had 4.4 [?] 13.7 mA at baseline."


def _run(tmp_path, monkeypatch, fill_answer):
    page = {"page": 1, "text": None, "png": b"PNG", "hint": HINT}
    monkeypatch.setattr(engine.reader, "read_input", lambda p: [page])
    pages_written, calls, logs = [], [], []
    monkeypatch.setattr(engine.output, "write_record",
                        lambda *a, **k: pages_written.append(a[4]))

    def call(prompt, images=None):
        calls.append((prompt, images))
        if images and "[?]" in prompt:
            return fill_answer
        return "VISION" if images else "SUM"

    result = engine.run_single(tmp_path / "ang.pdf", tmp_path, "t", "m",
                               call=call, log=logs.append)
    assert result["failed"] == []
    return pages_written[0][0], calls, logs


def test_good_fill_goes_into_the_record(tmp_path, monkeypatch):
    page, calls, logs = _run(
        tmp_path, monkeypatch,
        "Participants (n = 32) had 4.4 \u00b1 13.7 mA at baseline.")
    assert page["text"] == "Participants (n = 32) had 4.4 \u00b1 13.7 mA at baseline."
    assert calls[0][1] == [b"PNG"] and HINT in calls[0][0]
    assert not any("WARNING" in line for line in logs)


def test_bad_fill_keeps_visible_markers_and_warns(tmp_path, monkeypatch):
    page, calls, logs = _run(
        tmp_path, monkeypatch,
        "Participants (n = 33) had 4.4 \u00b1 13.7 mA at baseline.")
    assert page["text"] == HINT
    assert any("WARNING" in line and "[?]" in line for line in logs)
