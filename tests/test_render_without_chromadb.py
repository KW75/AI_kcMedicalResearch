"""Hosted app (Render) has no chromadb: requirements-render.txt omits it on purpose.

Session 31: utils/rag.py imported chromadb at module level, so importing main
(which the UI cloud gate does) failed on Render, and every hosted cloud run was
blocked with "Could not determine where this job's data would be sent (No module
named 'chromadb')". Local and CI both install chromadb, so only a test that hides
it can catch this. Runs in a subprocess so the hidden module can't leak into
other tests.
"""
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_CODE = REPO_ROOT / "SOURCE_CODE"

_PRELUDE = (
    "import sys\n"
    "sys.path[:0] = [{root!r}, {src!r}]\n"
    "sys.modules['chromadb'] = None  # as on Render\n"
)


def _run_without_chromadb(body: str) -> subprocess.CompletedProcess:
    code = _PRELUDE.format(root=str(REPO_ROOT), src=str(SOURCE_CODE)) + body
    return subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True, text=True, timeout=120, cwd=REPO_ROOT,
    )


def test_rag_module_imports_without_chromadb():
    result = _run_without_chromadb("import utils.rag\n")
    assert result.returncode == 0, result.stderr


def test_ui_cli_module_imports_without_chromadb():
    # Same import the UI's _cli_module() does before computing cloud destinations.
    result = _run_without_chromadb(
        "from SOURCE_CODE import main as cli\n"
        "assert callable(cli.data_destinations)\n"
        "assert isinstance(cli.SEARCH_SERVICES, dict)\n"
    )
    assert result.returncode == 0, result.stderr
