"""OCR fill_lines: AI lines matched by content, not by number (Ang p4 drift)."""
from pipelines.ocr import engine


def _ask(answer, calls=None):
    def ask(prompt):
        if calls is not None:
            calls.append(prompt)
        return answer
    return ask


def test_answers_under_wrong_numbers_still_fill():
    hint = "SD 4.4 [?] 13.7 mA\nP [?] 0.005"
    text, left, refused = engine.fill_lines(
        hint, _ask("1| P = 0.005\n2| SD 4.4 ± 13.7 mA"))
    assert text == "SD 4.4 ± 13.7 mA\nP = 0.005"
    assert left == 0 and refused == []


def test_unnumbered_line_starting_with_a_number_fills():
    hint = "1.6; adjusted P [?] 0.8)"
    text, left, _ = engine.fill_lines(hint, _ask("1.6; adjusted P = 0.8)"))
    assert text == "1.6; adjusted P = 0.8)" and left == 0


def test_line_filled_early_is_not_asked_again(monkeypatch):
    monkeypatch.setattr(engine, "LINES_PER_CALL", 1)
    calls = []
    hint = "P [?] 0.005\nSD 4.4 [?] 13.7 mA"
    text, left, _ = engine.fill_lines(
        hint, _ask("1| P = 0.005\n2| SD 4.4 ± 13.7 mA", calls))
    assert left == 0 and len(calls) == 1


def test_dropped_minus_is_still_refused_and_reported():
    hint = "([?]65 to [?]5 msec)"
    text, left, refused = engine.fill_lines(hint, _ask("1| (65 to 5 msec)"))
    assert text == hint and left == 2
    assert refused == [(hint, "(65 to 5 msec)")]


def test_five_lines_per_call():
    assert engine.LINES_PER_CALL == 5
