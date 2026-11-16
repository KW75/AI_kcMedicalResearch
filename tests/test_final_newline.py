"""Tracked text files end with a newline (Session 43).

Guarded edit scripts refuse a file without a final newline; two such files
blocked the item 6 edit. PowerShell here-strings drop the last newline, so
files written with WriteAllText from a here-string were the main source.
Readme/evidence/ is excluded: evidence files stay as recorded.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
EXTS = (".py", ".md", ".txt", ".yaml", ".yml", ".json", ".html", ".toml",
        ".cfg", ".ini", ".sh", ".bat", ".ps1")
EXCLUDE = ("Readme/evidence/",)


def _tracked():
    try:
        out = subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True,
                             text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("git not available")
    return [f for f in out.splitlines()
            if f.endswith(EXTS) and not f.startswith(EXCLUDE)]


def test_tracked_text_files_end_with_newline():
    files = _tracked()
    assert files, "no tracked text files found - the check did not run"
    bad = []
    for f in files:
        p = REPO / f
        if not p.is_file():
            continue
        raw = p.read_bytes()
        if raw and not raw.endswith(b"\n"):
            bad.append(f)
    assert bad == [], "no final newline: " + ", ".join(bad)
