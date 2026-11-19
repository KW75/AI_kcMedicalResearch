"""Session 48: tracked .txt files are checked out with LF line endings.

.gitattributes had no *.txt rule, so on Windows (core.autocrlf=true)
"* text=auto" checked the readme and requirements .txt files out as
CRLF, while the .md and .py files were LF. Edit scripts that stop on CR
then needed a CRLF exception. The repo copies were already LF.
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_gitattributes_has_txt_eol_lf_rule():
    text = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    assert re.search(r"(?m)^\*\.txt\s+text\s+eol=lf\s*$", text)


@pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")
def test_git_reports_eol_lf_for_txt_files():
    out = subprocess.run(
        ["git", "check-attr", "eol", "--",
         "requirements.txt", "Readme/readme_rct_search_pipeline.txt"],
        cwd=ROOT, capture_output=True, text=True, check=True).stdout
    lines = out.strip().splitlines()
    assert len(lines) == 2
    for ln in lines:
        assert ln.endswith(": eol: lf"), ln
