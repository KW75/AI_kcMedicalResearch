"""OCR per-line fill: only lines with [?] go to the model, each checked alone."""
from pipelines.ocr import engine

HINT = ("Results line without marks.\n"
        "SD 4.4 [?] 13.7 mA versus [?]10.2 [?] 9.9 mA; P [?] 0.005).\n"
        "Another clean line.\n"
        "Participants (n [?] 32) were randomized.")
GOOD_1 = "SD 4.4 \u00b1 13.7 mA versus \u221210.2 \u00b1 9.9 mA; P = 0.005)."
GOOD_2 = "Participants (n = 32) were randomized."
BAD_2 = "Participants (n = 33) were randomized."


def _asker(answers):
    prompts = []

    def ask(prompt):
        prompts.append(prompt)
        return answers.pop(0)
    return ask, prompts


def test_only_marked_lines_are_sent_numbered():
    ask, prompts = _asker(["1| x\n2| y"])
    engine.fill_lines(HINT, ask)
    assert len(prompts) == 1
    assert "1| SD 4.4 [?] 13.7" in prompts[0]
    assert "2| Participants (n [?] 32)" in prompts[0]
    assert "Another clean line." not in prompts[0]


def test_good_line_filled_bad_line_kept():
    ask, _ = _asker([f"1| {GOOD_1}\n2| {BAD_2}"])
    text, left, refused = engine.fill_lines(HINT, ask)
    assert GOOD_1 in text
    assert "Participants (n [?] 32) were randomized." in text
    assert "Results line without marks.\n" in text
    assert left == 1
    assert refused == [("Participants (n [?] 32) were randomized.", BAD_2)]


def test_missing_line_is_kept_and_reported():
    ask, _ = _asker([f"1| {GOOD_1}"])
    text, left, refused = engine.fill_lines(HINT, ask)
    assert left == 1
    assert refused == [("Participants (n [?] 32) were randomized.", None)]


def test_single_line_answer_without_number_is_accepted():
    ask, _ = _asker([GOOD_2])
    text, left, refused = engine.fill_lines("Participants (n [?] 32) were randomized.", ask)
    assert text == GOOD_2 and left == 0 and refused == []


def test_lines_are_sent_in_batches():
    hint = "\n".join(f"line {i} a [?] b" for i in range(20))
    ask, prompts = _asker(["", ""])
    text, left, refused = engine.fill_lines(hint, ask)
    assert len(prompts) == 2
    assert "15| line 14 a [?] b" in prompts[0]
    assert "1| line 15 a [?] b" in prompts[1]
    assert left == 20


# --- engine -----------------------------------------------------------------

def _run(tmp_path, monkeypatch, answer):
    page = {"page": 1, "text": None, "png": b"PNG", "hint": HINT}
    monkeypatch.setattr(engine.reader, "read_input", lambda p: [page])
    pages_written, logs = [], []
    monkeypatch.setattr(engine.output, "write_record",
                        lambda *a, **k: pages_written.append(a[4]))

    def call(prompt, images=None):
        return answer if images else "SUM"

    result = engine.run_single(tmp_path / "ang.pdf", tmp_path, "t", "m",
                               call=call, log=logs.append)
    assert result["failed"] == []
    return pages_written[0][0], logs


def test_partly_filled_page_is_labelled_and_debug_saved(tmp_path, monkeypatch):
    page, logs = _run(tmp_path, monkeypatch, f"1| {GOOD_1}\n2| {BAD_2}")
    assert page["method"] == "hybrid_partial"
    assert GOOD_1 in page["text"] and "(n [?] 32)" in page["text"]
    assert any("WARNING" in line and "1 of 5 [?]" in line for line in logs)
    debug = list(tmp_path.glob("*_FILL_DEBUG.txt"))
    assert len(debug) == 1 and "n = 33" in debug[0].read_text(encoding="utf-8")


def test_fully_filled_page_has_no_warning(tmp_path, monkeypatch):
    page, logs = _run(tmp_path, monkeypatch, f"1| {GOOD_1}\n2| {GOOD_2}")
    assert page["method"] == "hybrid"
    assert "[?]" not in page["text"]
    assert not any("WARNING" in line for line in logs)
    assert not list(tmp_path.glob("*_FILL_DEBUG.txt"))
