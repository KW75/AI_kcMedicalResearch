"""Session 50: version 3.0.0 carries the author's signature, Dr. Keith KW CHAN
and https://kw75.github.io/Credential/, below the version line in the launcher
banner, both launchers and the venv shell banner (user request).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SIG = "Dr. Keith KW CHAN"
URL = "https://kw75.github.io/Credential/"


def _lines(rel):
    raw = (ROOT / rel).read_bytes().decode("utf-8", errors="replace")
    return raw.replace("\r\n", "\n").split("\n")


def _line_after(rel, marker):
    lines = _lines(rel)
    hits = [i for i, line in enumerate(lines) if marker in line]
    assert len(hits) == 1, (rel, marker, len(hits))
    return lines[hits[0] + 1]


def _banner_src():
    src = "\n".join(_lines("scripts/launcher.py"))
    start = src.index("def banner(")
    return src[start:src.index("\ndef ", start + 1)]


def test_launcher_banner_signature_below_version():
    b = _banner_src()
    assert SIG in b
    assert b.index("Version  ") < b.index(SIG) < b.index("Python   ")


def test_launcher_banner_has_credential_link():
    b = _banner_src()
    assert URL in b
    assert b.index(SIG) < b.index(URL) < b.index("Medical Research  -")


def test_credential_link_is_magenta():
    b = _banner_src()
    assert "{_mag}{_web}" in b
    assert "\\033[95m" in b and "\\033[35m" in b


def test_windows_launcher_signature_below_version():
    nxt = _line_after("scripts/windows/AI_kcMedicalResearch_CLI.bat",
                      "CLI Launcher  ^|  v")
    assert nxt.startswith("echo ") and SIG in nxt and URL in nxt and "^|" in nxt


def test_mac_launcher_signature_below_version():
    nxt = _line_after("scripts/macos/Mac_kcMedicalResearch_CLI.sh",
                      "CLI Launcher  |  v")
    assert nxt.startswith('echo "') and SIG in nxt and URL in nxt


def test_venv_shell_banner_signature_below_version():
    nxt = _line_after("scripts/windows/activate_venv.bat", "venv shell  |  v")
    assert "Write-Host" in nxt and SIG in nxt and URL in nxt
    assert nxt.rstrip().endswith("^")
    assert "-ForegroundColor Magenta" in nxt
