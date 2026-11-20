"""Session 49 PR A: SaMD mode docs.

Pins the SaMD decision, folder map and intended-use statement in
docs/project before any code, so later edits cannot silently drop them.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "project"


def _read(name):
    return (DOCS / name).read_text(encoding="utf-8")


def test_decision_log_has_samd_entry():
    text = _read("decision-log.md")
    assert "## 2026-11-20: SaMD mode replaces launcher menu 9" in text
    for s in ("--mode samd", "input/samd/", "reports/samd/",
              "output/samd/", "Intended use"):
        assert s in text, s


def test_architecture_names_samd_folders():
    text = _read("architecture.md")
    for s in ("input/samd/", "reports/samd/", "output/samd/"):
        assert s in text, s


def test_architecture_describes_reference_and_assets():
    text = _read("architecture.md")
    assert re.search(r"reference/.*standard", text, re.I)
    assert re.search(r"assets/.*(icon|shortcut)", text, re.I)


def test_prd_has_ocr_and_samd_modes():
    text = _read("PRD.md")
    assert re.search(r"^### \d+\. OCR Mode", text, re.M)
    assert re.search(r"^### \d+\. SaMD Mode", text, re.M)
    assert "not a cleared or certified medical device" in text


def test_prd_no_session_transcripts():
    text = _read("PRD.md")
    assert not re.search(r"session[ _]transcript|session_", text, re.I)
