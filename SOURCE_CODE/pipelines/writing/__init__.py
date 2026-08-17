# SOURCE_CODE/pipelines/writing/__init__.py
"""Writing pipeline for AI kcMedicalResearch"""

from .writing import run_writer, run_editor, run_qa

# For backward compatibility with main.py
def run_writing(*args, **kwargs):
    """Wrapper for writing pipeline (legacy)."""
    return run_writer(*args, **kwargs)

__all__ = ['run_writing', 'run_writer', 'run_editor', 'run_qa']
