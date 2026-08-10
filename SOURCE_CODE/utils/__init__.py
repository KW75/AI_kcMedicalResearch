"""
Utility modules for AI kcMedicalResearch
"""

from .path_utils import PATH_MANAGER, get_input_dir, get_output_dir, get_reports_dir, get_rag_db
from .document_reader import DocumentReader
from .rag import (
    chunk_text,
    get_embeddings,
    index_uploads,
    retrieve,
    clear_session,
    set_client,
    _get_client,
)

__all__ = [
    'PATH_MANAGER',
    'get_input_dir',
    'get_output_dir',
    'get_reports_dir',
    'get_rag_db',
    'DocumentReader',
    'chunk_text',
    'get_embeddings',
    'index_uploads',
    'retrieve',
    'clear_session',
    'set_client',
]
