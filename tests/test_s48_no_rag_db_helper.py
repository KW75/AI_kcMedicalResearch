"""Session 48: the unused chroma_db/{mode}_rag_db helpers are removed.

PathManager.get_rag_db_path(mode) and get_rag_db(mode) built
chroma_db/<mode>_rag_db, but rag.py opens chroma_db directly
(_get_client) and nothing called them. chroma_db_dir stays: the folder
list created on import still uses it.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "SOURCE_CODE"))

import utils  # noqa: E402
import utils.path_utils as pu  # noqa: E402


def test_path_manager_has_no_get_rag_db_path():
    assert not hasattr(pu.PathManager, "get_rag_db_path")


def test_path_utils_has_no_get_rag_db():
    assert not hasattr(pu, "get_rag_db")


def test_utils_package_does_not_export_get_rag_db():
    assert not hasattr(utils, "get_rag_db")
    assert "get_rag_db" not in getattr(utils, "__all__", [])


def test_chroma_db_dir_kept():
    assert pu.PATH_MANAGER.chroma_db_dir.name == "chroma_db"
