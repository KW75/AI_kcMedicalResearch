"""Session 43: when < 2 studies pool, the log says DOCX/PDF are skipped on purpose.

Run 20261116_214126: the launcher printed 'PDF -> not generated (see pipeline
log above)', but the log said nothing about DOCX or PDF.
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
SR = ROOT / "SOURCE_CODE" / "pipelines" / "sr"
MARK = "HTML report written without a pooled estimate"
NOTE = "DOCX and PDF are not written when nothing pools"


def _hits():
    out = []
    for p in sorted(SR.rglob("*.py")):
        lines = p.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines):
            if MARK in line:
                out.append((p, lines, i))
    return out


def test_no_pool_html_line_found_once():
    assert len(_hits()) == 1


def test_skip_note_logged_right_after_html_line():
    p, lines, i = _hits()[0]
    assert NOTE in "\n".join(lines[i:i + 6]), f"{p}: no DOCX/PDF note after the no-pool HTML line"
