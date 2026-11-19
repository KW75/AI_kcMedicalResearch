"""Session 48: version 2.7.0, and every place that shows it agrees.

The version is written in seven places: main.py VERSION (used by
--version and the launcher banner), pipelines/__init__.py __version__,
README line 6, and two lines each in the Windows .bat and macOS .sh
launchers. This test keeps them in step.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXPECTED = "2.7.0"
OLD = "2.6.0"
LAUNCHERS = [
    ROOT / "scripts" / "windows" / "AI_kcMedicalResearch_CLI.bat",
    ROOT / "scripts" / "macos" / "Mac_kcMedicalResearch_CLI.sh",
]


def _read(p):
    p = p if isinstance(p, Path) else ROOT / p
    return p.read_bytes().decode("utf-8", errors="replace")


def _main_version():
    m = re.search(r'^VERSION = "([^"]+)"', _read("SOURCE_CODE/main.py"), re.M)
    assert m, "VERSION line not found in main.py"
    return m.group(1)


def test_main_version_is_2_7_0():
    assert _main_version() == EXPECTED


def test_pipelines_version_matches_main():
    m = re.search(r'^__version__ = "([^"]+)"',
                  _read("SOURCE_CODE/pipelines/__init__.py"), re.M)
    assert m and m.group(1) == _main_version()


def test_readme_version_matches_main():
    assert re.search(rf"^\s*Version: {re.escape(_main_version())}\s*$",
                     _read("README.md"), re.M)


def test_launcher_banners_match_main():
    tag = "v" + _main_version()
    for p in LAUNCHERS:
        assert _read(p).count(tag) == 2, p.name


def test_old_version_not_left():
    files = [ROOT / "SOURCE_CODE" / "main.py",
             ROOT / "SOURCE_CODE" / "pipelines" / "__init__.py",
             ROOT / "README.md", *LAUNCHERS]
    left = [p.name for p in files if OLD in _read(p)]
    assert left == []
