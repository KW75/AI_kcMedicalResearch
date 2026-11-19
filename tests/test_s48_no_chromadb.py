"""Session 48, option A step A2: chromadb is removed now that utils/rag.py
is gone (step A1, PR #66), with everything kept only for it: the pysqlite3
sqlite3 override in tests/conftest.py, the pyarrow==12.0.1 pin (only
chromadb needed it), the EMBEDDING_* settings, PathManager.chroma_db_dir and
the chroma_db/ .gitignore line. Streamlit and Render leftovers in the docs
go too (the UI itself was removed in Session 33)."""

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "SOURCE_CODE"))

REQUIREMENTS = [
    "requirements.txt",
    "requirements-base.txt",
    "requirements-local.txt",
    "requirements-ci.txt",
    "SOURCE_CODE/pipelines/sr/requirements.txt",
]
SETUP_DOCS = [
    ".env.example",
    "README.md",
    "Readme/Setup_Instructions_for_Users.txt",
    "Readme/flashcard-help.html",
]


def _text(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def _packages(rel):
    path = ROOT / rel
    if not path.exists():
        return []
    names = []
    for line in path.read_text(encoding="utf-8").splitlines():
        spec = line.split("#", 1)[0].strip().lower()
        if spec and not spec.startswith("-"):
            names.append(re.split(r"[<>=!~;\[\s]", spec, maxsplit=1)[0])
    return names


@pytest.mark.parametrize("rel", REQUIREMENTS)
def test_requirements_have_no_chromadb_pysqlite3_or_pyarrow(rel):
    names = _packages(rel)
    for pkg in ("chromadb", "pysqlite3-binary", "pyarrow"):
        assert pkg not in names, f"{rel}: {pkg}"


def test_conftest_has_no_sqlite3_override():
    assert "pysqlite3" not in _text("tests/conftest.py")


def test_main_has_no_embedding_settings_or_chromadb():
    text = _text("SOURCE_CODE/main.py")
    assert "EMBEDDING_" not in text
    assert "chromadb" not in text


def test_path_manager_does_not_create_chroma_db(tmp_path):
    import utils.path_utils as pu
    pm = pu.PathManager(tmp_path)
    assert not hasattr(pm, "chroma_db_dir")
    assert not (tmp_path / "chroma_db").exists()


def test_gitignore_has_no_chroma_db_line():
    assert not any("chroma_db" in ln for ln in _text(".gitignore").splitlines())


@pytest.mark.parametrize("rel", SETUP_DOCS)
def test_setup_docs_have_no_embedding_setup(rel):
    text = _text(rel)
    assert "EMBEDDING_" not in text
    assert "ollama pull nomic-embed-text" not in text


def test_flashcard_has_no_streamlit_or_render_card():
    text = _text("Readme/flashcard-help.html").lower()
    for banned in ("streamlit", "<code>--ui</code>", "_stcore", "h-deploy"):
        assert banned not in text, banned


@pytest.mark.parametrize("rel", ["docs/project/PRD.md",
                                 "docs/project/architecture.md",
                                 "SOURCE_CODE/streaming.py"])
def test_no_streamlit_mention(rel):
    assert "streamlit" not in _text(rel).lower()
