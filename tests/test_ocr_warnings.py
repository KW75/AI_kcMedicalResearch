"""Session 36: the [?]-left warning must not blame the AI for every leftover."""
from pipelines.ocr import engine


def test_vote_warning_says_not_confirmed():
    logs = []
    done = [{"text": "P [?] 0.01", "method": "hybrid"}]
    engine._vote_pages(done, [(0, 1, "P [?] 0.01", None)], logs.append)
    warn = [m for m in logs if "WARNING" in m]
    assert len(warn) == 1
    assert "1 of 1 [?] left" in warn[0]
    assert "could not be confirmed" in warn[0]
    assert "check against the PDF" in warn[0]
    assert "AI changed other text" not in warn[0]
    assert done[0]["method"] == "hybrid_unresolved"

def test_fill_debug_also_keeps_vote_and_warning_lines(tmp_path, monkeypatch):
    from pathlib import Path
    page = {"page": 1, "text": None, "hint": "P [?] 0.01", "png": b"x",
            "codes": None}
    monkeypatch.setattr(engine.reader, "read_input", lambda path: [page])

    def call(prompt, images=None):
        return "1| P 0.01"  # the model drops the sign -> line refused

    logs = []
    engine._process_file(Path("a.pdf"), tmp_path, "H", "m", call, logs.append)
    dbg = (tmp_path / "H_FILL_DEBUG.txt").read_text(encoding="utf-8")
    assert "TEXT: P [?] 0.01" in dbg  # refused line still there
    assert "WARNING: page 1: 1 of 1 [?] left" in dbg  # vote/warning now saved too
    assert any("WARNING: page 1" in m for m in logs)  # still shown on screen
