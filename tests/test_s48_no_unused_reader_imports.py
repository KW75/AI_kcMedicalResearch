"""Session 48: the pipelines imported DocumentReader and RAGUtils but never
used them (all reading goes through each pipeline's loader and the shared
doc_reader). The unused imports are removed."""

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PIPELINES = [
    "SOURCE_CODE/pipelines/appraisal/appraisal.py",
    "SOURCE_CODE/pipelines/coding/coding.py",
    "SOURCE_CODE/pipelines/rct_search/rct_search.py",
    "SOURCE_CODE/pipelines/search/search.py",
    "SOURCE_CODE/pipelines/writing/writing.py",
]


@pytest.mark.parametrize("rel", PIPELINES)
def test_pipeline_does_not_import_unused_readers(rel):
    tree = ast.parse((ROOT / rel).read_text(encoding="utf-8"))
    imported = {
        alias.name
        for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    assert "DocumentReader" not in imported
    assert "RAGUtils" not in imported
