# SOURCE_CODE/__init__.py
"""
AI kcMedicalResearch - Core AI Module
Version: 2.3.0
"""

from .utils.path_utils import PATH_MANAGER, get_input_dir, get_output_dir
from .utils.document_reader import DocumentReader
from .utils.rag import RAGUtils

__version__ = "2.3.0"
__all__ = [
    'PATH_MANAGER',
    'get_input_dir',
    'get_output_dir',
    'DocumentReader',
    'RAGUtils',
]