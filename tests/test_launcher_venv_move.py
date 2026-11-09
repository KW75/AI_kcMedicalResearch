"""Pin that both CLI launchers survive a moved project folder.

Console-script stubs (pip.exe, .venv/bin/pip) store the absolute path of
the interpreter that created the venv. After the project folder is moved
or renamed they fail ("Fatal error in launcher"). So the launchers must:
  A. call pip as `python -m pip`, never through the stub;
  B. detect a moved folder via the `command` line in .venv/pyvenv.cfg and
     offer to rebuild .venv from requirements-local.txt, keeping the old
     tree as .venv.old until the new one is installed.
"""
import re
from pathlib import Path

import pytest


def _repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "scripts" / "launcher.py").exists():
            return parent
    raise RuntimeError("repo root with scripts/launcher.py not found")


ROOT = _repo_root()

LAUNCHERS = {
    "windows": ROOT / "scripts" / "windows" / "AI_kcMedicalResearch_CLI.bat",
    "macos": ROOT / "scripts" / "macos" / "Mac_kcMedicalResearch_CLI.sh",
}

# A pip call through the venv's console-script stub.
PIP_STUB = {
    "windows": r"(?i)Scripts\\pip",
    "macos": r"\.venv/bin/pip\b",
}

NAMES = sorted(LAUNCHERS)


def _text(name: str) -> str:
    return LAUNCHERS[name].read_text(encoding="utf-8")


@pytest.mark.parametrize("name", NAMES)
def test_launcher_file_exists(name):
    assert LAUNCHERS[name].is_file(), LAUNCHERS[name]


# --- A. pip through python, not through the stub ---------------------------

@pytest.mark.parametrize("name", NAMES)
def test_no_pip_stub_call(name):
    match = re.search(PIP_STUB[name], _text(name))
    assert match is None, f"{name} launcher still calls the pip stub: {match.group(0)!r}"


@pytest.mark.parametrize("name", NAMES)
def test_requirements_installed_with_python_m_pip(name):
    assert re.search(r"-m pip install -r requirements-local\.txt", _text(name)), (
        f"{name} launcher must install with `python -m pip install -r requirements-local.txt`"
    )


# --- B. moved-folder detection and safe rebuild ----------------------------

@pytest.mark.parametrize("name", NAMES)
def test_reads_pyvenv_cfg(name):
    assert "pyvenv.cfg" in _text(name), f"{name} launcher does not check .venv/pyvenv.cfg"


@pytest.mark.parametrize("name", NAMES)
def test_keeps_old_venv_until_rebuild_succeeds(name):
    assert ".venv.old" in _text(name), f"{name} launcher does not keep the old venv as .venv.old"


@pytest.mark.parametrize("name", NAMES)
def test_tells_user_the_folder_was_moved(name):
    assert "folder was moved" in _text(name).lower(), (
        f"{name} launcher does not tell the user the folder was moved"
    )
