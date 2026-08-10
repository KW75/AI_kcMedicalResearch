# SOURCE_CODE/pipelines/search/__init__.py
"""Search pipeline for AI kcMedicalResearch"""

from .search import run_topic_search, run_article_search

# For backward compatibility
def run_search(*args, **kwargs):
    """Wrapper for search pipeline (legacy)."""
    # Default to topic search if no sub-mode specified
    return run_topic_search(*args, **kwargs)

__all__ = ['run_search', 'run_topic_search', 'run_article_search']
