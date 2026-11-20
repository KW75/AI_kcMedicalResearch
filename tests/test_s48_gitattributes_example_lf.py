"""Session 48: *.example files are checked out with LF.

'* text=auto' with core.autocrlf=true checked .env.example and the
docs/*/topic.md.example files out as CRLF on Windows (repo copies LF).
"""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                          text=True, check=True).stdout


def test_gitattributes_has_example_rule():
    rules = [line.split() for line in
             (ROOT / ".gitattributes").read_text(encoding="utf-8").splitlines()]
    assert ["*.example", "text", "eol=lf"] in rules


def test_every_tracked_example_file_is_eol_lf():
    files = _git("ls-files", "--", "*.example").split()
    assert files
    for line in _git("check-attr", "eol", "--", *files).splitlines():
        assert line.endswith("eol: lf"), line
