"""OCR B2: fills compared per font:code over the whole document."""
import re

from pipelines.ocr import engine


def test_majority_sign_is_agreed():
    agreed, keep = engine.code_votes([(["F:0x1"] * 5, ["=", "=", "=", "=", "<"])])
    assert agreed == {"F:0x1": "="} and keep == set()


def test_no_majority_agrees_nothing():
    agreed, keep = engine.code_votes([(["F:0x1"] * 5, ["=", "=", "=", "<", "<"])])
    assert agreed == {} and keep == set()


def test_single_vote_is_kept_not_copied():
    agreed, keep = engine.code_votes([(["F:0x2", "F:0x2"], ["=", None])])
    assert agreed == {} and keep == {"F:0x2"}


def test_two_codes_of_one_font_with_one_sign_are_not_trusted():
    agreed, keep = engine.code_votes([(["F:0x1"] * 2 + ["F:0x2"] * 2, ["="] * 4)])
    assert agreed == {} and keep == set()


def test_same_sign_in_different_fonts_is_fine():
    agreed, _ = engine.code_votes([(["F:0x1", "F:0x1", "G:0x1", "G:0x1"], ["="] * 4)])
    assert agreed == {"F:0x1": "=", "G:0x1": "="}


def test_fills_from_filled_text():
    assert engine._fills_from("a [?] b [?] c", "a = b [?] c") == ["=", None]
    assert engine._fills_from("a [?] b", "a = X") is None


def _run(tmp_path, monkeypatch, pages, answers):
    monkeypatch.setattr(engine.reader, "read_input", lambda path: pages)
    written = []

    def fake_write(*a, **k):
        written.append(next(x for x in list(a) + list(k.values()) if isinstance(x, list)))
        return tmp_path
    monkeypatch.setattr(engine.output, "write_record", fake_write)

    def call(prompt, images=None):
        if not images:
            return "SUM"
        rows = re.findall(r"^(\d+)\| (.*)$", prompt, re.M)
        return "\n".join(f"{k}| {answers.get(line, line)}" for k, line in rows)
    logs = []
    engine.run_single(tmp_path / "ang.pdf", tmp_path, "t", "m", call=call, log=logs.append)
    return written[0], logs


def _page(n, hint, codes=None):
    p = {"page": n, "text": None, "png": b"PNG", "hint": hint}
    if codes is not None:
        p["codes"] = codes
    return p


def test_vote_corrects_wrong_fill_and_fills_refused_line(tmp_path, monkeypatch):
    h1 = "a [?] 1; b [?] 2; c [?] 3; d [?] 4; e [?] 5"
    h2 = "adjusted P [?] 0.8\nx [?] y"
    pages = [_page(1, h1, ["F:0x1"] * 5), _page(2, h2, ["F:0x1"] * 2)]
    answers = {h1: "a = 1; b = 2; c = 3; d = 4; e = 5",
               "adjusted P [?] 0.8": "adjusted P > 0.8"}
    written, logs = _run(tmp_path, monkeypatch, pages, answers)
    assert written[0]["text"] == "a = 1; b = 2; c = 3; d = 4; e = 5"
    assert written[1]["text"] == "adjusted P = 0.8\nx = y"
    assert written[1]["method"] == "hybrid"
    assert any("document vote" in line for line in logs)
    assert not any("WARNING" in line for line in logs)


def test_vote_without_majority_puts_markers_back(tmp_path, monkeypatch):
    h = "a [?] 1; b [?] 2; c [?] 3\nd [?] 4; e [?] 5"
    answers = {"a [?] 1; b [?] 2; c [?] 3": "a = 1; b = 2; c = 3",
               "d [?] 4; e [?] 5": "d < 4; e < 5"}
    written, logs = _run(tmp_path, monkeypatch, [_page(1, h, ["F:0x1"] * 5)], answers)
    assert written[0]["text"] == h
    assert written[0]["method"] == "hybrid_unresolved"
    assert any("back to [?]" in line for line in logs)
    assert any("WARNING" in line and "5 of 5" in line for line in logs)


def test_page_without_codes_is_not_voted(tmp_path, monkeypatch):
    written, _ = _run(tmp_path, monkeypatch, [_page(1, "P [?] 1")], {"P [?] 1": "P < 1"})
    assert written[0]["text"] == "P < 1"
