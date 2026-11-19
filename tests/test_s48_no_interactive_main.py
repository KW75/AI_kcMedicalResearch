"""Session 48: the interactive main() loop in SOURCE_CODE/main.py was
unreachable (run_cli sends every --mode to its own handler and raises
ValueError otherwise), and the RAG code (utils/rag.py) only ran inside it.
Both are removed, with the helpers only main() used. run_cli routing stays
pinned in tests/test_main_coverage.py::TestCliRouting."""

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
MAIN = ROOT / "SOURCE_CODE" / "main.py"
UTILS = ROOT / "SOURCE_CODE" / "utils"

REMOVED = ["main", "choose_role", "build_project_context", "truncate_context",
           "start_session_transcript", "append_to_transcript",
           "print_session_summary", "save_rct_search_links",
           "_read_article_files", "ARTICLE_EXTENSIONS", "ARTICLE_SIZE_LIMIT",
           "uuid"]


def _top_names():
    tree = ast.parse(MAIN.read_text(encoding="utf-8"))
    names = set()
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(n.name)
        elif isinstance(n, ast.Assign):
            names.update(t.id for t in n.targets if isinstance(t, ast.Name))
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            names.update((a.asname or a.name).split(".")[0] for a in n.names)
    return names


@pytest.mark.parametrize("name", REMOVED)
def test_removed_from_main_py(name):
    assert name not in _top_names()


def test_rag_module_removed():
    assert not (UTILS / "rag.py").exists()


def test_utils_init_has_no_rag_names():
    src = (UTILS / "__init__.py").read_text(encoding="utf-8")
    assert ".rag" not in src and "_LAZY" not in src


def test_kept_helpers_still_there():
    names = _top_names()
    for name in ("run_cli", "parse_args", "auto_load_input_files",
                 "role_color", "COLOURS", "RESET"):
        assert name in names, name
