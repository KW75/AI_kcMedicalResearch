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
