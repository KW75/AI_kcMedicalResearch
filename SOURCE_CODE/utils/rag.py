"""
rag.py  - Retrieval-Augmented Generation support for ai-automation-tool.

Design decisions:
- Per-session: ChromaDB collection is named {mode}_{session_id} and deleted
  at session end.  Nothing persists between runs.
- Mode-specific: only files under uploads/{mode}/ are indexed, so articles
  placed for rct_search never appear in a coding context.
- Small docs/ files continue to be injected directly by build_project_context();
  RAG chunks are appended after them.
- Embedding provider is controlled by EMBEDDING_PROVIDER in .env (default:
  ollama).  Switching to openai requires only a .env change.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

import chromadb

# ---------------------------------------------------------------------------
# Constants (overridden by .env via main.py at import time)
# ---------------------------------------------------------------------------
EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "ollama")
EMBEDDING_MODEL: str    = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
OLLAMA_HOST: str        = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OPENAI_API_KEY: str     = os.getenv("OPENAI_API_KEY", "")

CHUNK_SIZE: int    = 500   # characters per chunk
CHUNK_OVERLAP: int = 50    # characters shared between adjacent chunks
N_RESULTS: int     = 5     # chunks returned per retrieval query

# Persistent ChromaDB client (in-memory for tests; file-backed at runtime)
_chroma_client: Optional[chromadb.Client] = None


def _get_client() -> chromadb.Client:
    """Return (or lazily create) the module-level ChromaDB client."""
    global _chroma_client
    if _chroma_client is None:
        # Updated path: go up 3 levels from SOURCE_CODE/utils/ to project root
        db_path = Path(__file__).resolve().parent.parent.parent / "chroma_db"
        db_path.mkdir(parents=True, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=str(db_path))
    return _chroma_client


def set_client(client: chromadb.Client) -> None:
    """
    Inject a custom ChromaDB client (used in tests to pass an in-memory
    client without touching the file system).
    """
    global _chroma_client
    _chroma_client = client


# ---------------------------------------------------------------------------
# 1. chunk_text
# ---------------------------------------------------------------------------
def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    """
    Split *text* into overlapping chunks of *chunk_size* characters.

    Adjacent chunks share *overlap* characters so that a sentence split
    across a boundary is still retrievable from either chunk.

    Returns a list of non-empty strings.  If the text is shorter than
    *chunk_size* the whole text is returned as a single-element list.
    """
    if not text.strip():
        return []

    chunks: list[str] = []
    start = 0
    step  = chunk_size - overlap

    while start < len(text):
        end   = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += step

    return chunks


# ---------------------------------------------------------------------------
# 2. get_embeddings
# ---------------------------------------------------------------------------
def get_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Return an embedding vector for each string in *texts*.

    Routing logic (controlled by EMBEDDING_PROVIDER in .env):
      - "ollama"   - POST to {OLLAMA_HOST}/api/embed  (default, local, free)
      - "openai"   - POST to OpenAI embeddings endpoint (requires API key)

    Raises RuntimeError for unsupported providers or network failures.
    """
    if not texts:
        return []

    provider = EMBEDDING_PROVIDER.lower()

    if provider == "ollama":
        return _embed_ollama(texts)
    elif provider == "openai":
        return _embed_openai(texts)
    else:
        raise RuntimeError(
            f"Unsupported EMBEDDING_PROVIDER: '{provider}'. "
            "Choose 'ollama' or 'openai'."
        )


def _embed_ollama(texts: list[str]) -> list[list[float]]:
    """Call Ollama's /api/embed endpoint."""
    url     = f"{OLLAMA_HOST}/api/embed"
    payload = json.dumps({"model": EMBEDDING_MODEL, "input": texts}).encode()
    req     = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        # Ollama returns {"embeddings": [[...], ...]}
        return data["embeddings"]
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError) as exc:
        raise RuntimeError(f"Ollama embedding failed: {exc}") from exc


def _embed_openai(texts: list[str]) -> list[list[float]]:
    """Call OpenAI's embeddings endpoint."""
    if not OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add it to your .env file."
        )
    url     = "https://api.openai.com/v1/embeddings"
    payload = json.dumps({"model": EMBEDDING_MODEL, "input": texts}).encode()
    req     = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        # OpenAI returns {"data": [{"embedding": [...]}, ...]}
        return [item["embedding"] for item in data["data"]]
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError) as exc:
        raise RuntimeError(f"OpenAI embedding failed: {exc}") from exc


def _fetch_url(url: str) -> str:
    """
    Fetch a public URL and return its text content with HTML tags stripped.
    Returns an empty string on any network or parsing error.
    Respects a 10-second timeout to avoid blocking the session start.
    """
    import html
    import re as _re
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; ai-automation-tool/1.0)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        return ""

    # Strip <script> and <style> blocks first
    raw = _re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", "", raw)
    # Strip all remaining HTML tags
    raw = _re.sub(r"<[^>]+>", " ", raw)
    # Decode HTML entities
    raw = html.unescape(raw)
    # Collapse whitespace
    raw = _re.sub(r"\s+", " ", raw).strip()
    return raw


def _extract_urls(text: str) -> list[str]:
    """
    Return all lines in *text* that are bare URLs (start with http:// or
    https:// and contain no spaces). One URL per line is the expected format.
    """
    urls = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(("http://", "https://")) and " " not in stripped:
            urls.append(stripped)
    return urls


# ---------------------------------------------------------------------------
# 3. index_uploads
# ---------------------------------------------------------------------------
def index_uploads(mode: str, session_id: str, upload_base: str = "uploads") -> int:
    """
    Scan *upload_base/{mode}/* for supported files (.txt, .md, .pdf),
    chunk and embed each one, then store all chunks in a ChromaDB
    collection named ``{mode}_{session_id}``.

    Returns the total number of chunks indexed (0 if the folder is empty
    or contains no supported files).

    Supported formats
    -----------------
    - .txt / .md   - read as UTF-8 text (errors replaced)
    - .pdf         - text extracted page-by-page with pypdf
    """
    folder = Path(upload_base) / mode
    if not folder.exists():
        folder.mkdir(parents=True, exist_ok=True)
        return 0

    files = [
        f for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in {
            ".txt", ".md", ".pdf",
            ".py", ".js", ".ts", ".html", ".css", ".json", ".yaml", ".yml",
            ".sh", ".bat", ".ps1", ".sql", ".r", ".R",
        }
    ]
    if not files:
        return 0

    collection_name = f"{mode}_{session_id}"
    client     = _get_client()
    collection = client.get_or_create_collection(name=collection_name)

    total_chunks = 0
    for file_path in files:
        text = _read_file(file_path)
        if not text.strip():
            continue

        # Fetch any bare URLs found in the file and append their content
        urls = _extract_urls(text)
        for url in urls:
            fetched = _fetch_url(url)
            if fetched.strip():
                text += f"\n\n[Fetched from {url}]\n{fetched}"

        chunks = chunk_text(text)
        if not chunks:
            continue

        embeddings = get_embeddings(chunks)
        ids        = [
            f"{file_path.name}::{i}" for i in range(len(chunks))
        ]
        metadatas  = [
            {"source": file_path.name, "chunk_index": i}
            for i in range(len(chunks))
        ]

        collection.add(
            documents=chunks,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas,
        )
        total_chunks += len(chunks)

    return total_chunks


def _read_file(path: Path) -> str:
    """Read a .txt/.md file as UTF-8 or extract text from a .pdf."""
    if path.suffix.lower() == ".pdf":
        return _read_pdf(path)
    return path.read_text(encoding="utf-8", errors="replace")


def _read_pdf(path: Path) -> str:
    """
    Extract text from a PDF using a three-stage fallback chain:

    Stage 1  - PyMuPDF (fitz): fast, accurate for text-layer PDFs.
    Stage 2  - pypdf: fallback if fitz is not installed.
    Stage 3  - OCR (pytesseract + pdf2image): for scanned/image-only PDFs
              where stages 1 and 2 return empty text.

    OCR requires Tesseract binary and Poppler on PATH (or set via .env).
    If OCR dependencies are missing, returns empty string with a warning.
    """
    text = ""

    # Stage 1  - PyMuPDF
    try:
        import fitz  # PyMuPDF
        doc  = fitz.open(str(path))
        text = "\n\n".join(page.get_text() for page in doc)
        doc.close()
    except Exception:  # noqa: BLE001
        pass

    # Stage 2  - pypdf (if Stage 1 empty or failed)
    if not text.strip():
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            text   = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception:  # noqa: BLE001
            pass

    # Stage 3  - OCR fallback for scanned/image PDFs
    if not text.strip():
        text = _ocr_pdf(path)

    if not text.strip():
        print(f"[RAG] Warning: no text extracted from '{path.name}' "
              f"(text-layer empty and OCR returned nothing).")
    return text


def _ocr_pdf(path: Path) -> str:
    """
    Convert each PDF page to an image and run Tesseract OCR.
    Requires: pytesseract, pillow, pdf2image, Tesseract binary, Poppler.
    Paths are read from TESSERACT_PATH and POPPLER_PATH in .env.
    Returns empty string if any dependency is missing.
    """
    try:
        import pytesseract
        from pdf2image import convert_from_path

        # Configure Tesseract binary path if set in .env
        tesseract_path = os.getenv("TESSERACT_PATH", "")
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

        # Configure Poppler path if set in .env
        poppler_path = os.getenv("POPPLER_PATH", "") or None

        print(f"[RAG] OCR fallback activated for '{path.name}'...")
        images = convert_from_path(str(path), poppler_path=poppler_path)
        pages  = []
        for i, image in enumerate(images, start=1):
            page_text = pytesseract.image_to_string(image, lang="eng")
            if page_text.strip():
                pages.append(page_text)
            print(f"[RAG] OCR page {i}/{len(images)} complete.")

        result = "\n\n".join(pages)
        if result.strip():
            print(f"[RAG] OCR extracted {len(result)} chars from '{path.name}'.")
        return result

    except ImportError as exc:
        print(f"[RAG] OCR skipped  - missing dependency: {exc}")
        print("[RAG] Install: pip install pytesseract pillow pdf2image")
        print("[RAG] Then install Tesseract and Poppler binaries.")
        return ""
    except Exception as exc:  # noqa: BLE001
        print(f"[RAG] OCR failed for '{path.name}': {exc}")
        return ""


# ---------------------------------------------------------------------------
# 4. retrieve
# ---------------------------------------------------------------------------
def retrieve(
    query: str,
    mode: str,
    session_id: str,
    n_results: int = N_RESULTS,
) -> str:
    """
    Embed *query* and return the *n_results* most relevant chunks from the
    collection ``{mode}_{session_id}`` as a formatted string.

    Returns an empty string if the collection does not exist or is empty,
    so callers never need to guard against None.
    """
    collection_name = f"{mode}_{session_id}"
    client = _get_client()

    # Check collection exists
    existing = [c.name for c in client.list_collections()]
    if collection_name not in existing:
        return ""

    collection = client.get_collection(name=collection_name)
    if collection.count() == 0:
        return ""

    query_embeddings = get_embeddings([query])
    results = collection.query(
        query_embeddings=query_embeddings,
        n_results=min(n_results, collection.count()),
    )

    chunks: list[str] = results.get("documents", [[]])[0]
    sources: list[dict] = results.get("metadatas", [[]])[0]

    if not chunks:
        return ""

    lines = ["--- Relevant context from uploaded documents ---"]
    for chunk, meta in zip(chunks, sources):
        source = meta.get("source", "unknown")
        lines.append(f"[{source}]\n{chunk}")
    lines.append("--- End of retrieved context ---")

    return "\n\n".join(lines)


# ---------------------------------------------------------------------------
# 5. clear_session
# ---------------------------------------------------------------------------
def clear_session(mode: str, session_id: str) -> None:
    """
    Delete the ChromaDB collection for ``{mode}_{session_id}``.

    Called at session end to honour the per-session design decision.
    Safe to call even if the collection does not exist (no exception raised).
    """
    collection_name = f"{mode}_{session_id}"
    client = _get_client()

    existing = [c.name for c in client.list_collections()]
    if collection_name in existing:
        client.delete_collection(name=collection_name)
# ---------------------------------------------------------------------------
# RAGUtils wrapper class (for backward compatibility with coding.py)
# ---------------------------------------------------------------------------
class RAGUtils:
    """
    Wrapper class for RAG operations.
    Provides a unified interface for RAG functionality.
    """
    
    def __init__(self, mode: str = None, session_id: str = None):
        self.mode = mode
        self.session_id = session_id
        self.embedding_provider = EMBEDDING_PROVIDER
        self.embedding_model = EMBEDDING_MODEL
    
    def index_uploads(self, mode: str = None, session_id: str = None, upload_base: str = "uploads") -> int:
        """Index documents for the given mode and session."""
        mode = mode or self.mode
        session_id = session_id or self.session_id
        if mode is None or session_id is None:
            raise ValueError("mode and session_id are required")
        return index_uploads(mode, session_id, upload_base)
    
    def retrieve(self, query: str, mode: str = None, session_id: str = None, n_results: int = None) -> str:
        """Retrieve relevant chunks for a query."""
        mode = mode or self.mode
        session_id = session_id or self.session_id
        if mode is None or session_id is None:
            raise ValueError("mode and session_id are required")
        return retrieve(query, mode, session_id, n_results or N_RESULTS)
    
    def clear_session(self, mode: str = None, session_id: str = None) -> None:
        """Clear the session collection."""
        mode = mode or self.mode
        session_id = session_id or self.session_id
        if mode is None or session_id is None:
            raise ValueError("mode and session_id are required")
        clear_session(mode, session_id)
    
    def get_context(self, query: str, mode: str = None, session_id: str = None, n_results: int = None) -> str:
        """Get context for a query (alias for retrieve)."""
        return self.retrieve(query, mode, session_id, n_results)
