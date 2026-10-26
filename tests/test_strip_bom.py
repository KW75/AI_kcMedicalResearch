"""Tests for scripts/strip_bom.py (Session 31).

strip_bom.py keeps its own copies of the scan lists from check_no_bom.py.
Its docstring said they were the same, but nothing checked that. When
check_no_bom.py learned to scan dotfiles, strip_bom.py still could not fix
the file the checker had just reported. The sync test pins the lists.
"""
import importlib.util
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _load(filename, module_name):
    spec = importlib.util.spec_from_file_location(module_name, _SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


strip_bom = _load("strip_bom.py", "strip_bom_under_test")
check_no_bom = _load("check_no_bom.py", "check_no_bom_for_sync")


def test_strip_bom_uses_the_same_lists_as_check_no_bom():
    assert strip_bom.CHECK_SUFFIXES == check_no_bom.CHECK_SUFFIXES
    assert strip_bom.IGNORE_DIRS == check_no_bom.IGNORE_DIRS
    assert getattr(strip_bom, "CHECK_NAMES", set()) == check_no_bom.CHECK_NAMES


def test_strip_removes_bom_from_dotfiles(tmp_path):
    names = [".gitattributes", ".gitignore", ".env.example"]
    for name in names:
        (tmp_path / name).write_bytes(strip_bom.BOM + b"# comment\n")
    clean = tmp_path / "clean"
    clean.mkdir()
    (clean / ".gitattributes").write_bytes(b"# comment\n")

    stripped = {p.relative_to(tmp_path).as_posix() for p in strip_bom.strip(tmp_path)}
    assert stripped == set(names)
    for name in names:
        assert (tmp_path / name).read_bytes() == b"# comment\n"
    assert (clean / ".gitattributes").read_bytes() == b"# comment\n"
