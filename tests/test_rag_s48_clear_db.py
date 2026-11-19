"""Session 48: chroma_db is emptied once, before the RAG client opens it.

Each run uses a new random session_id (main.py uuid4), so no run reads
the collection of an earlier run. Leftovers built up: collections of
runs that crashed or were closed (clear_session not reached) and segment
folders that delete_collection leaves on disk. A failed delete prints a
warning and the run goes on. An injected client (set_client) never
clears anything.
"""
import sys
import types
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "SOURCE_CODE"))

import utils.rag as rag  # noqa: E402


def _fake_chromadb(seen):
    mod = types.ModuleType("chromadb")

    def PersistentClient(path):
        p = Path(path)
        seen.append((p, sorted(x.name for x in p.iterdir())))
        return object()

    mod.PersistentClient = PersistentClient
    return mod


def _old_db(tmp_path):
    db = tmp_path / "chroma_db"
    (db / "0b1c-orphan").mkdir(parents=True)
    (db / "0b1c-orphan" / "data_level0.bin").write_bytes(b"x")
    (db / "chroma.sqlite3").write_bytes(b"old")
    return db


def _use(monkeypatch, db, client=None):
    monkeypatch.setattr(rag, "_DB_PATH", db, raising=False)
    monkeypatch.setattr(rag, "_chroma_client", client)


def test_get_client_empties_old_chroma_db(tmp_path, monkeypatch, capsys):
    db = _old_db(tmp_path)
    _use(monkeypatch, db)
    seen = []
    with patch.dict(sys.modules, {"chromadb": _fake_chromadb(seen)}):
        rag._get_client()
    assert seen == [(db, [])]
    assert "[RAG] Cleared old chroma_db (2 items)." in capsys.readouterr().out


def test_injected_client_never_clears(tmp_path, monkeypatch):
    db = _old_db(tmp_path)
    _use(monkeypatch, db, client=object())
    rag._get_client()
    assert (db / "chroma.sqlite3").exists()
    assert (db / "0b1c-orphan" / "data_level0.bin").exists()


def test_clear_failure_warns_and_continues(tmp_path, monkeypatch, capsys):
    db = _old_db(tmp_path)
    _use(monkeypatch, db)
    seen = []
    with patch("shutil.rmtree", side_effect=PermissionError("locked")), \
         patch.dict(sys.modules, {"chromadb": _fake_chromadb(seen)}):
        rag._get_client()
    assert "[RAG] Could not clear old chroma_db: locked" in capsys.readouterr().out
    assert seen and seen[0][0] == db


def test_no_old_folder_creates_it_quietly(tmp_path, monkeypatch, capsys):
    db = tmp_path / "chroma_db"
    _use(monkeypatch, db)
    seen = []
    with patch.dict(sys.modules, {"chromadb": _fake_chromadb(seen)}):
        rag._get_client()
    assert db.is_dir()
    assert seen == [(db, [])]
    assert "chroma_db" not in capsys.readouterr().out
