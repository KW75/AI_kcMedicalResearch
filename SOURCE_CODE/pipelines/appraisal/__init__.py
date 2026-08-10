# SOURCE_CODE/pipelines/appraisal/__init__.py
"""
Appraisal pipeline for AI kcMedicalResearch
"""

from .appraisal import main as run_appraisal
from .document_handler import AppraisalDocumentHandler

__all__ = ['run_appraisal', 'AppraisalDocumentHandler']