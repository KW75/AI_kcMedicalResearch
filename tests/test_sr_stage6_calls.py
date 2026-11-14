"""Session 39: Stage 6 report calls in main.py, checked by a real call.
Keyword names are read from main.py (ast), so a keyword dropped from a
generate() signature (e.g. also_save_html, item 11c) fails here directly."""
import ast
import inspect
import sys
from pathlib import Path

import pandas as pd
import pytest

from pipelines.sr.src.analysis.meta_analysis import MetaAnalyzer
from pipelines.sr.src.analysis.subgroups import (
    subgroup_summary, WAITING_LIST, USUAL_CARE,
)
from pipelines.sr.src.reporting import pdf_report as pr
from pipelines.sr.src.reporting.report_generator import ReportGenerator

MAIN_PY = (Path(__file__).resolve().parents[1]
           / "SOURCE_CODE" / "pipelines" / "sr" / "main.py")
ROWS = [
    {"study": "A (2012)", "effect_estimate": -0.4, "ci_lower": -1.0,
     "ci_upper": 0.2, "comparator_type": WAITING_LIST},
    {"study": "B (2015)", "effect_estimate": -0.3, "ci_lower": -0.9,
     "ci_upper": 0.3, "comparator_type": WAITING_LIST},
    {"study": "C (2018)", "effect_estimate": 0.0, "ci_lower": -0.5,
     "ci_upper": 0.5, "comparator_type": USUAL_CARE},
]


def _main_keywords(cls_name):
    tree = ast.parse(MAIN_PY.read_text(encoding="utf-8"))
    found = []
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "generate"
                and isinstance(node.func.value, ast.Call)
                and isinstance(node.func.value.func, ast.Name)
                and node.func.value.func.id == cls_name):
            found.append([k.arg for k in node.keywords])
    assert len(found) == 1, f"expected one {cls_name}().generate( call, found {len(found)}"
    return found[0]


def _fake_kwargs(names, tmp_path, suffix):
    ma = MetaAnalyzer().run(data=pd.DataFrame(ROWS), effect_measure="SMD")
    sg = subgroup_summary(ROWS, lambda m: MetaAnalyzer().run(
        data=pd.DataFrame(m), effect_measure="SMD"))
    fake = {
        "title": "T", "authors": "", "pico": {}, "ma_result": ma,
        "extraction_results": [], "screening_results": [],
        "rob_results": [], "inclusion_criteria": [],
        "exclusion_criteria": [], "forest_plot_path": "",
        "effect_measure": "SMD", "meta_audit": [], "subgroups": sg,
        "subgroup_plot_path": None, "model_name": "test-model",
        "output_path": str(tmp_path / f"report{suffix}"),
        "also_save_html": True,
    }
    missing = [n for n in names if n not in fake]
    assert not missing, f"main.py passes new keyword(s) {missing}: add a fake value here"
    return {n: fake[n] for n in names}


@pytest.fixture
def no_weasy(monkeypatch):
    monkeypatch.setitem(sys.modules, "weasyprint", None)   # HTML-only, same in CI


def test_main_has_both_report_calls():
    assert "output_path" in _main_keywords("ReportGenerator")
    assert "also_save_html" in _main_keywords("PDFReportGenerator")


def test_signatures_accept_main_keywords(no_weasy):
    for obj, cls_name in ((ReportGenerator(), "ReportGenerator"),
                          (pr.PDFReportGenerator(), "PDFReportGenerator")):
        names = _main_keywords(cls_name)
        inspect.signature(obj.generate).bind(**{n: None for n in names})


def test_bind_detects_dropped_keyword():
    # the guard itself: an unknown keyword is a TypeError
    with pytest.raises(TypeError):
        inspect.signature(ReportGenerator().generate).bind(
            **{n: None for n in _main_keywords("ReportGenerator")},
            not_a_parameter=1)


def test_docx_call_runs(tmp_path):
    kw = _fake_kwargs(_main_keywords("ReportGenerator"), tmp_path, ".docx")
    ReportGenerator().generate(**kw)
    assert Path(kw["output_path"]).exists()


def test_pdf_call_runs_html_only(no_weasy, tmp_path):
    kw = _fake_kwargs(_main_keywords("PDFReportGenerator"), tmp_path, ".pdf")
    res = pr.PDFReportGenerator().generate(**kw)
    assert res["pdf"] is None
    assert Path(res["html"]).exists()
