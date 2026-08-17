"""
Utility modules for AI kcMedicalResearch
"""
from .path_utils import PATH_MANAGER, get_input_dir, get_output_dir, get_reports_dir, get_rag_db

# Heavy dependencies (chromadb, pymupdf, docx2txt) are imported on first use
# rather than at package import. "from utils.path_utils import ..." previously
# pulled in the entire RAG and document stack, costing ~2s on every run.
_LAZY = {
    "DocumentReader": ".document_reader",
    "chunk_text": ".rag",
    "get_embeddings": ".rag",
    "index_uploads": ".rag",
    "retrieve": ".rag",
    "clear_session": ".rag",
    "set_client": ".rag",
    "_get_client": ".rag",
}


def __getattr__(name):
    module = _LAZY.get(name)
    if module is None:
        raise AttributeError("module {!r} has no attribute {!r}".format(__name__, name))
    from importlib import import_module
    return getattr(import_module(module, __name__), name)


def __dir__():
    return sorted(list(globals()) + list(_LAZY))


__all__ = [
    "PATH_MANAGER",
    "get_input_dir",
    "get_output_dir",
    "get_reports_dir",
    "get_rag_db",
    "DocumentReader",
    "chunk_text",
    "get_embeddings",
    "index_uploads",
    "retrieve",
    "clear_session",
    "set_client",
]
