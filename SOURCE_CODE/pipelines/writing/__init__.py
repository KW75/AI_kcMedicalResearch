# SOURCE_CODE/pipelines/writing/__init__.py
"""
Writing pipeline for AI kcMedicalResearch
"""

from .writing import main as run_writing
from .document_handler import WritingDocumentHandler

__all__ = ['run_writing', 'WritingDocumentHandler']