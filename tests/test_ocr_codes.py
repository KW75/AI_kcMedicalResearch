"""OCR (B1): font:code per [?]; same code -> same symbol; ASCII fills normalised."""
from pipelines.ocr import engine, reader

F, G = "MathematicalPi-Four", "Universal-GreekwithMathP"


class _FakePage:
    def __init__(self, spans):
        self._spans = spans

    def get_text(self, mode="text"):
        return {"blocks": [{"lines": [{"spans": [
            {"font": f, "text": t} for f, t in self._spans]}]}]}


def test_symbol_codes_in_text_order():
    page = _FakePage([("Times", "(n "), (F, "\x01"),
                      ("Times", " 32) had 4.4 "), (G, "\x02"), ("Times", " 13.7")])
    text = "(n \x01 32) had 4.4 \x02 13.7"
    assert reader.symbol_codes(page, text) == [f"{F}:0x1", f"{G}:0x2"]


def test_symbol_codes_none_when_text_and_fonts_disagree():
    page = _FakePage([(F, "\x01")])
    assert reader.symbol_codes(page, "a \x01 b \x02 c") is None


def test_same_font_codes_need_different_symbols():
    # Ang p1 "versus [?]10.8 [?] 24.1": minus and ± are different codes
    hint = "versus [?]10.8 [?] 24.1"
    text, left, _ = engine.fill_lines(
        hint, lambda p: "1| versus ±10.8 ± 24.1", codes=[f"{G}:0x4", f"{G}:0x3"])
    assert text == hint and left == 2


def test_same_code_needs_the_same_symbol():
    hint = "mean [?] SD 4.4 [?] 13.7"
    text, left, _ = engine.fill_lines(
        hint, lambda p: "1| mean = SD 4.4 ± 13.7", codes=[f"{G}:0x3", f"{G}:0x3"])
    assert text == hint and left == 2


def test_consistent_fill_is_accepted_and_normalised():
    hint = "versus [?]10.8 [?] 24.1; P [?] 0.4"
    text, left, _ = engine.fill_lines(
        hint, lambda p: "1| versus -10.8 +/- 24.1; P = 0.4",
        codes=[f"{G}:0x4", f"{G}:0x3", f"{F}:0x1"])
    assert text == "versus \u221210.8 \u00b1 24.1; P = 0.4" and left == 0


def test_without_codes_ascii_stand_ins_are_normalised():
    text, left, _ = engine.fill_lines(
        "age 49 [?] 11; score [?]10", lambda p: "1| age 49 +/- 11; score >=10")
    assert text == "age 49 \u00b1 11; score \u226510" and left == 0


def test_codes_ignored_when_count_does_not_match():
    text, left, _ = engine.fill_lines(
        "P [?] 0.4", lambda p: "1| P = 0.4", codes=["a:0x1", "a:0x2"])
    assert text == "P = 0.4" and left == 0


def test_engine_passes_page_codes(tmp_path, monkeypatch):
    page = {"page": 1, "text": None, "png": b"PNG",
            "hint": "versus [?]10.8 [?] 24.1", "codes": [f"{G}:0x4", f"{G}:0x3"]}
    monkeypatch.setattr(engine.reader, "read_input", lambda p: [page])
    written = []
    monkeypatch.setattr(engine.output, "write_record",
                        lambda *a, **k: written.append(a[4]))

    def call(prompt, images=None):
        return "1| versus ±10.8 ± 24.1" if images else "SUM"

    engine.run_single(tmp_path / "ang.pdf", tmp_path, "t", "m",
                      call=call, log=lambda m: None)
    assert written[0][0]["text"] == "versus [?]10.8 [?] 24.1"
