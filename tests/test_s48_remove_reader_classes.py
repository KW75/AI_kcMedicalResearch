"""Session 48: utils/document_reader.DocumentReader and utils/rag.RAGUtils
were never used. The module and the class are removed, the utils lazy map
no longer lists DocumentReader, and every remaining lazy name still exists."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UTILS = ROOT / "SOURCE_CODE" / "utils"


def _top_names(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {n.name for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.ClassDef))}


def test_document_reader_module_removed():
    assert not (UTILS / "document_reader.py").exists()


def test_ragutils_class_removed():
    assert "RAGUtils" not in _top_names(UTILS / "rag.py")


def test_utils_init_does_not_list_document_reader():
    assert '"DocumentReader"' not in (UTILS / "__init__.py").read_text(encoding="utf-8")


def test_every_lazy_name_still_exists():
    tree = ast.parse((UTILS / "__init__.py").read_text(encoding="utf-8"))
    lazy = next(ast.literal_eval(n.value) for n in tree.body
                if isinstance(n, ast.Assign)
                and getattr(n.targets[0], "id", "") == "_LAZY")
    for name, module in lazy.items():
        assert name in _top_names(UTILS / (module.lstrip(".") + ".py")), name


def test_main_has_no_ragutils_comment():
    src = (ROOT / "SOURCE_CODE" / "main.py").read_text(encoding="utf-8")
    assert "RAGUtils" not in src


def test_requirements_do_not_point_to_removed_file():
    for name in ("requirements.txt", "requirements-ocr.txt"):
        assert "document_reader.py" not in (ROOT / name).read_text(encoding="utf-8")
