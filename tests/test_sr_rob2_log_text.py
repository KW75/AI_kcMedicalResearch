# Session 39 (item 6a): rob2_tool.py OCR log had a note claiming a 6000-char
# prompt cut, stale since Session 38 - the prompt gets Methods + Results
# (rob2_text, up to MAX_ROB2_SECTION_CHARS); [ROB2 TEXT] logs what is sent.
from pathlib import Path

ROB2 = (Path(__file__).resolve().parents[1] / "SOURCE_CODE" / "pipelines"
        / "sr" / "src" / "screening" / "rob2_tool.py")


def test_no_stale_prompt_cut_note():
    assert "prompt uses first" not in ROB2.read_text(encoding="utf-8")


def test_rob2_text_line_still_logged():
    assert "[ROB2 TEXT]" in ROB2.read_text(encoding="utf-8")
