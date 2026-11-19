"""Session 48: Search turns AI LaTeX into plain text before saving.

Before, $\\text{FeNO}$, $\\pm$ and 50\\% from the AI were saved as they
were in the .md, the .docx and the report log. strip_latex (moved from
pipelines/ocr/output.py to pipelines/shared/latex.py) now runs on the AI
text; money such as "$5 and $10" and the reference URLs stay as they are.
search.py must not import the OCR package (output.py needs python-docx).
"""
import sys
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "SOURCE_CODE"))

import pipelines.search.search as s  # noqa: E402

RESULTS = [{"title": "T1", "url": "https://pubmed.ncbi.nlm.nih.gov/1/",
            "snippet": "snippet"}]
ARTICLES = [{"uid": "1", "title": "T1", "url": "https://x/1", "doi": ""}]
AI_TEXT = (r"## Overview" "\n"
           r"$\text{FeNO}$ fell by 50\% ($\pm$ 3). Cost $5 and $10.")
CLEAN = "FeNO fell by 50% (\u00b1 3). Cost $5 and $10."


def _paths(tmp_path):
    return {k: tmp_path / k for k in ("docs", "input", "output", "reports")}


def _latex_ai(system_prompt="", user_prompt=""):
    return AI_TEXT


def _run_topic(tmp_path):
    paths = _paths(tmp_path)
    with patch.object(s, "_paths", return_value=paths), \
         patch.object(s, "_Spinner", lambda *a, **k: nullcontext()), \
         patch.object(s, "_europepmc_search", return_value=RESULTS):
        s.run_topic_search(["cbt fibromyalgia"], _latex_ai, verbose=False)
    return paths


def _run_article(tmp_path, monkeypatch):
    paths = _paths(tmp_path)
    monkeypatch.setattr("builtins.input", lambda *a: "3")
    with patch.object(s, "_paths", return_value=paths), \
         patch.object(s, "_Spinner", lambda *a, **k: nullcontext()), \
         patch.object(s, "_pubmed_search", return_value=ARTICLES), \
         patch.object(s, "_pubmed_fetch_abstracts",
                      side_effect=lambda a, **k: a), \
         patch.object(s, "_article_user_prompt", return_value="prompt"):
        s.run_article_search(["cbt fibromyalgia"], _latex_ai, verbose=False)
    return paths


def _one(paths, key, suffix):
    files = list(paths[key].glob("*" + suffix))
    assert len(files) == 1, files
    return files[0]


def _docx_text(path):
    docx = pytest.importorskip("docx")
    return "\n".join(p.text for p in docx.Document(str(path)).paragraphs)


def _assert_clean(text):
    assert CLEAN in text
    assert "\\text" not in text
    assert "$\\pm$" not in text


def test_shared_module_and_ocr_use_one_copy():
    from pipelines.shared.latex import strip_latex
    import pipelines.ocr.output as output
    assert output.strip_latex is strip_latex


def test_search_imports_shared_not_ocr():
    src = (ROOT / "SOURCE_CODE" / "pipelines" / "search" / "search.py"
           ).read_text(encoding="utf-8")
    assert "from pipelines.shared.latex import strip_latex" in src
    assert "pipelines.ocr" not in src


def test_topic_md_and_report_have_no_latex(tmp_path):
    paths = _run_topic(tmp_path)
    md = _one(paths, "output", ".md").read_text(encoding="utf-8")
    _assert_clean(md)
    assert "https://pubmed.ncbi.nlm.nih.gov/1/" in md
    _assert_clean(_one(paths, "reports", ".md").read_text(encoding="utf-8"))


def test_topic_docx_has_no_latex(tmp_path):
    paths = _run_topic(tmp_path)
    _assert_clean(_docx_text(_one(paths, "output", ".docx")))


def test_article_md_and_report_have_no_latex(tmp_path, monkeypatch):
    paths = _run_article(tmp_path, monkeypatch)
    _assert_clean(_one(paths, "output", ".md").read_text(encoding="utf-8"))
    _assert_clean(_one(paths, "reports", ".md").read_text(encoding="utf-8"))


def test_article_docx_has_no_latex(tmp_path, monkeypatch):
    paths = _run_article(tmp_path, monkeypatch)
    _assert_clean(_docx_text(_one(paths, "output", ".docx")))
