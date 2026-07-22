"""
test_rag.py — Unit tests for src/rag.py

All tests use mocks or an in-memory ChromaDB client so no files are written
to disk and Ollama does not need to be running.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import chromadb
import pytest

import src.rag as rag


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_in_memory_client() -> chromadb.Client:
    """Return a fresh ephemeral ChromaDB client for test isolation."""
    return chromadb.EphemeralClient()


def _fake_embeddings(texts: list[str]) -> list[list[float]]:
    """Return a deterministic 4-dimensional embedding for each text."""
    return [[float(i), float(len(t)), 0.0, 1.0] for i, t in enumerate(texts)]


# ---------------------------------------------------------------------------
# 1. chunk_text
# ---------------------------------------------------------------------------
class TestChunkText:

    def test_basic_chunk_count(self):
        """Text longer than chunk_size should produce multiple chunks."""
        text   = "a" * 1200
        chunks = rag.chunk_text(text, chunk_size=500, overlap=50)
        assert len(chunks) >= 2

    def test_overlap_shared_content(self):
        """Adjacent chunks must share *overlap* characters."""
        text    = "x" * 600
        overlap = 50
        chunks  = rag.chunk_text(text, chunk_size=300, overlap=overlap)
        assert len(chunks) >= 2
        # The tail of chunk[0] and the head of chunk[1] must overlap
        tail = chunks[0][-overlap:]
        head = chunks[1][:overlap]
        assert tail == head

    def test_short_input_returns_single_chunk(self):
        """Text shorter than chunk_size must be returned as one chunk."""
        text   = "short text"
        chunks = rag.chunk_text(text, chunk_size=500, overlap=50)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_empty_input_returns_empty_list(self):
        """Empty or whitespace-only input must return an empty list."""
        assert rag.chunk_text("") == []
        assert rag.chunk_text("   ") == []


# ---------------------------------------------------------------------------
# 2. get_embeddings
# ---------------------------------------------------------------------------
class TestGetEmbeddings:

    def test_empty_list_returns_empty(self):
        """No network call should be made for an empty list."""
        result = rag.get_embeddings([])
        assert result == []

    def test_ollama_provider_calls_correct_endpoint(self):
        """get_embeddings with EMBEDDING_PROVIDER=ollama must POST to /api/embed."""
        fake_response_body = json.dumps(
            {"embeddings": [[0.1, 0.2, 0.3]]}
        ).encode()

        mock_resp = MagicMock()
        mock_resp.read.return_value = fake_response_body
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__  = MagicMock(return_value=False)

        with patch("src.rag.EMBEDDING_PROVIDER", "ollama"), \
             patch("urllib.request.urlopen", return_value=mock_resp) as mock_open:
            result = rag.get_embeddings(["hello"])

        called_url = mock_open.call_args[0][0].full_url
        assert "/api/embed" in called_url
        assert result == [[0.1, 0.2, 0.3]]

    def test_openai_provider_calls_correct_endpoint(self):
        """get_embeddings with EMBEDDING_PROVIDER=openai must POST to OpenAI."""
        fake_response_body = json.dumps(
            {"data": [{"embedding": [0.4, 0.5, 0.6]}]}
        ).encode()

        mock_resp = MagicMock()
        mock_resp.read.return_value = fake_response_body
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__  = MagicMock(return_value=False)

        with patch("src.rag.EMBEDDING_PROVIDER", "openai"), \
             patch("src.rag.OPENAI_API_KEY", "sk-test"), \
             patch("urllib.request.urlopen", return_value=mock_resp) as mock_open:
            result = rag.get_embeddings(["hello"])

        called_url = mock_open.call_args[0][0].full_url
        assert "openai.com" in called_url
        assert result == [[0.4, 0.5, 0.6]]

    def test_unsupported_provider_raises(self):
        """An unknown EMBEDDING_PROVIDER must raise RuntimeError."""
        with patch("src.rag.EMBEDDING_PROVIDER", "unknown_llm"):
            with pytest.raises(RuntimeError, match="Unsupported EMBEDDING_PROVIDER"):
                rag.get_embeddings(["test"])


# ---------------------------------------------------------------------------
# 3. index_uploads
# ---------------------------------------------------------------------------
class TestIndexUploads:

    def test_empty_folder_returns_zero(self, tmp_path):
        """index_uploads must return 0 when the upload folder has no files."""
        client = _make_in_memory_client()
        rag.set_client(client)

        result = rag.index_uploads(
            mode="coding",
            session_id="abc123",
            upload_base=str(tmp_path),
        )
        assert result == 0

    def test_txt_file_is_indexed(self, tmp_path):
        """A .txt file placed in uploads/mode/ must be chunked and indexed."""
        folder = tmp_path / "coding"
        folder.mkdir()
        (folder / "notes.txt").write_text("word " * 300, encoding="utf-8")

        client = _make_in_memory_client()
        rag.set_client(client)

        with patch("src.rag.get_embeddings", side_effect=_fake_embeddings):
            n = rag.index_uploads(
                mode="coding",
                session_id="sess01",
                upload_base=str(tmp_path),
            )

        assert n > 0
        col = client.get_collection("coding_sess01")
        assert col.count() == n

    def test_unsupported_file_type_ignored(self, tmp_path):
        """Files with unsupported extensions must not be indexed."""
        folder = tmp_path / "coding"
        folder.mkdir()
        (folder / "image.png").write_bytes(b"\x89PNG\r\n")

        client = _make_in_memory_client()
        rag.set_client(client)

        result = rag.index_uploads(
            mode="coding",
            session_id="sess02",
            upload_base=str(tmp_path),
        )
        assert result == 0


# ---------------------------------------------------------------------------
# 4. retrieve
# ---------------------------------------------------------------------------
class TestRetrieve:

    def test_retrieve_returns_formatted_string(self, tmp_path):
        """retrieve must return a non-empty formatted string after indexing."""
        folder = tmp_path / "rct_search"
        folder.mkdir()
        (folder / "article.txt").write_text(
            "Randomised controlled trial of aspirin. " * 50,
            encoding="utf-8",
        )

        client = _make_in_memory_client()
        rag.set_client(client)

        with patch("src.rag.get_embeddings", side_effect=_fake_embeddings):
            rag.index_uploads(
                mode="rct_search",
                session_id="s99",
                upload_base=str(tmp_path),
            )
            result = rag.retrieve(
                query="aspirin trial",
                mode="rct_search",
                session_id="s99",
                n_results=3,
            )

        assert "Relevant context" in result
        assert "article.txt" in result

    def test_retrieve_missing_collection_returns_empty(self):
        """retrieve must return '' when the collection does not exist."""
        client = _make_in_memory_client()
        rag.set_client(client)

        result = rag.retrieve(
            query="anything",
            mode="writing",
            session_id="nonexistent",
        )
        assert result == ""


# ---------------------------------------------------------------------------
# 5. clear_session
# ---------------------------------------------------------------------------
class TestClearSession:

    def test_clear_session_deletes_collection(self, tmp_path):
        """clear_session must delete the named ChromaDB collection."""
        folder = tmp_path / "coding"
        folder.mkdir()
        (folder / "code.txt").write_text("def foo(): pass\n" * 100, encoding="utf-8")

        client = _make_in_memory_client()
        rag.set_client(client)

        with patch("src.rag.get_embeddings", side_effect=_fake_embeddings):
            rag.index_uploads(
                mode="coding",
                session_id="del01",
                upload_base=str(tmp_path),
            )

        names_before = [c.name for c in client.list_collections()]
        assert "coding_del01" in names_before

        rag.clear_session(mode="coding", session_id="del01")

        names_after = [c.name for c in client.list_collections()]
        assert "coding_del01" not in names_after

    def test_clear_session_safe_when_missing(self):
        """clear_session must not raise if the collection does not exist."""
        client = _make_in_memory_client()
        rag.set_client(client)

        # Should complete without exception
        rag.clear_session(mode="coding", session_id="ghost")
