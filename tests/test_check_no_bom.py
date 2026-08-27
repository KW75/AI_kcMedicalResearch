"""
Regression tests for scripts/check_no_bom.py (Known Issue #49).

Session 17's handoff claimed check_no_bom.py "currently scans only
SOURCE_CODE/", but inspection at the top of Session 18 showed Session 16's
commit 32e0098 had already widened the scan root to the repository root and
0ede7bd had wired it into CI. This test file is the durable form of the
guard: rather than trusting CI-green as the verification (Session 15's
"verify the artifact, not the intent" lesson), it exercises scan() and
main() against a staged tree so a future refactor that silently narrows
the scan root, drops an entry from IGNORE_DIRS, or restricts
CHECK_SUFFIXES fails CI on the specific regression.

The tests monkeypatch check_no_bom.REPO_ROOT to tmp_path so they never
touch the real repository tree.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

# Load scripts/check_no_bom.py as a module without requiring scripts/ to be
# a package. tests/conftest.py already puts the repo root on sys.path, but
# scripts/ has no __init__.py so a bare `import check_no_bom` would only
# work by accident of sys.path ordering. spec_from_file_location makes the
# dependency explicit and matches the pattern Session 15 used for
# harness-style script testing.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPT_PATH = _REPO_ROOT / "scripts" / "check_no_bom.py"

_spec = importlib.util.spec_from_file_location("check_no_bom", _SCRIPT_PATH)
assert _spec is not None and _spec.loader is not None, (
    f"Could not load scripts/check_no_bom.py from {_SCRIPT_PATH}"
)
check_no_bom = importlib.util.module_from_spec(_spec)
sys.modules["check_no_bom"] = check_no_bom
_spec.loader.exec_module(check_no_bom)


BOM = b"\xef\xbb\xbf"


def _write(path: Path, data: bytes) -> None:
    """Write raw bytes to path, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as fh:
        fh.write(data)


@pytest.fixture
def staged_tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """
    Point check_no_bom.REPO_ROOT at a fresh tmp_path and return it.

    scan() and main() both read REPO_ROOT at call time, so patching it
    reroutes the scan without touching the real repo.
    """
    monkeypatch.setattr(check_no_bom, "REPO_ROOT", tmp_path)
    return tmp_path


def test_detects_bom_in_repo_root(staged_tree: Path) -> None:
    """A BOM'd .py at the tree root must be reported."""
    offender = staged_tree / "bad.py"
    _write(offender, BOM + b"print('hi')\n")

    offenders = check_no_bom.scan(staged_tree)

    assert offenders == [offender]


def test_detects_bom_in_tests_and_scripts_subdirs(staged_tree: Path) -> None:
    """
    BOMs under tests/ and scripts/ must be reported.

    This is the specific regression Session 17's handoff warned about
    (stale claim: "scans only SOURCE_CODE/"). A future refactor that
    narrows the scan root to SOURCE_CODE/ would fail here.
    """
    tests_offender = staged_tree / "tests" / "test_thing.py"
    scripts_offender = staged_tree / "scripts" / "launcher.py"
    source_offender = staged_tree / "SOURCE_CODE" / "main.py"
    _write(tests_offender, BOM + b"# test\n")
    _write(scripts_offender, BOM + b"# launcher\n")
    _write(source_offender, BOM + b"# main\n")

    offenders = set(check_no_bom.scan(staged_tree))

    assert offenders == {tests_offender, scripts_offender, source_offender}


def test_ignores_bom_under_ignored_dirs(staged_tree: Path) -> None:
    """
    BOMs under IGNORE_DIRS must not be reported.

    Files under .git/, .venv/, output/, reports/, input/, node_modules/
    are either not ours (.git, .venv, node_modules) or are
    pipeline-generated artifacts (output/, reports/) or reviewer input
    (input/). Flagging them would produce noise and, for .git,
    potentially corrupt the checkout.
    """
    for ignored in (".git", ".venv", "output", "reports", "input", "node_modules"):
        _write(staged_tree / ignored / "buried.py", BOM + b"pass\n")

    offenders = check_no_bom.scan(staged_tree)

    assert offenders == []


def test_ignores_non_source_suffixes(staged_tree: Path) -> None:
    """
    BOMs in binary or log files must not be reported.

    The check exists to catch UTF-8 encoding accidents in source files
    (PowerShell 5's Set-Content -Encoding UTF8 writes a BOM; see
    Session 10 lesson). PNGs, PDFs, and log files legitimately contain
    the same three bytes at other offsets and even at offset 0.
    """
    _write(staged_tree / "image.png", BOM + b"\x00\x00\x00fake png\n")
    _write(staged_tree / "debug.log", BOM + b"log line\n")
    _write(staged_tree / "report.pdf", BOM + b"%PDF-1.4\n")

    offenders = check_no_bom.scan(staged_tree)

    assert offenders == []


def test_clean_tree_returns_empty_and_main_returns_zero(
    staged_tree: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """
    A tree with no BOMs must produce scan() == [] and main() == 0.

    Pins the "silence is verification" contract: main() returning 0 is
    what CI reads as green. See lessons: "a tripwire that only fires on
    failure must also make silence auditable" (Session 14).
    """
    _write(staged_tree / "SOURCE_CODE" / "clean.py", b"print('clean')\n")
    _write(staged_tree / "tests" / "test_clean.py", b"# clean test\n")

    assert check_no_bom.scan(staged_tree) == []
    assert check_no_bom.main() == 0

    captured = capsys.readouterr()
    assert "OK" in captured.out
    assert "no UTF-8 BOMs found" in captured.out


def test_main_returns_1_and_names_offenders(
    staged_tree: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """
    main() must return 1 when offenders are found and print each path.

    This is what CI's `Check for UTF-8 BOMs` step gates on. If main()
    silently returned 0 on failure, the whole guard would be
    decorative - the exact failure mode Session 14's fieldnames bugs
    (#36, #44) exemplified elsewhere in the codebase.
    """
    offender = staged_tree / "scripts" / "buggy.py"
    _write(offender, BOM + b"import sys\n")

    exit_code = check_no_bom.main()

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "FAIL" in captured.out
    assert "scripts/buggy.py" in captured.out.replace("\\", "/")
    assert "python scripts/strip_bom.py" in captured.out
