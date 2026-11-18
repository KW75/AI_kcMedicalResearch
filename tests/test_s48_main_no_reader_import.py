"""Session 48: main.py imported DocumentReader at startup but never used it;
its comment named document_reader as the slow part of startup (~7s cold).
The import is removed and the comment no longer makes that claim."""

import ast
from pathlib import Path

MAIN = Path(__file__).resolve().parent.parent / "SOURCE_CODE" / "main.py"


def test_main_does_not_import_document_reader():
    tree = ast.parse(MAIN.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert node.module != "utils.document_reader"
            assert "DocumentReader" not in {a.name for a in node.names}


def test_heavy_import_comment_not_stale():
    src = MAIN.read_text(encoding="utf-8")
    assert "document_reader (-> pytesseract" not in src
    assert "~7s cold" not in src
