# SOURCE_CODE/pipelines/sr/__init__.py
"""
Systematic Review pipeline for AI kcMedicalResearch
"""
# Lazy re-export (PEP 562), for two reasons:
#   1. `python -m SOURCE_CODE.pipelines.sr.main` first imports this package;
#      an eager `from .main import main` puts sr.main into sys.modules
#      BEFORE runpy executes it as __main__, producing the RuntimeWarning
#      ("found in sys.modules after import of package ... prior to
#      execution") and two live instances of the module. Importing lazily
#      means package import no longer touches .main at all.
#   2. .main pulls scipy/matplotlib/pymupdf (~2.8s); consumers that only
#      import the package shouldn't pay for it (same treatment as
#      utils/__init__.py in Session 9).

__all__ = ['run_sr']


def __getattr__(name):
    if name == 'run_sr':
        from .main import main as run_sr
        return run_sr
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
