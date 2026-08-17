# SOURCE_CODE/pipelines/coding/__init__.py
"""
Coding pipeline for AI kcMedicalResearch
"""

from .coding import run_builder, run_reviewer, run_tester

# For backward compatibility with main.py expecting 'run_coding'
# We'll map this to run_builder as the default
def run_coding(*args, **kwargs):
    """Wrapper for run_builder for backward compatibility."""
    return run_builder(*args, **kwargs)

__all__ = ['run_coding', 'run_builder', 'run_reviewer', 'run_tester']
