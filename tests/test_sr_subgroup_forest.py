"""Item 11c (Session 39): second forest plot grouped by control type
(forest_plot_subgroups.png). The main forest_plot.png is unchanged."""
import re
from pathlib import Path

import docx
import pandas as pd

from pipelines.sr.src.analysis.meta_analysis import MetaAnalyzer
from pipelines.sr.src.analysis.subgroups import (
    subgroup_summary, WAITING_LIST, USUAL_CARE,
)
from pipelines.sr.src.visualization.forest_plot import ForestPlotGenerator
from pipelines.sr.src.reporting.html_report import HTMLReportGenerator
from pipelines.sr.src.reporting.report_generator import ReportGenerator

SR = Path(__file__).resolve().parents[1] / "SOURCE_CODE" / "pipelines" / "sr"
ROWS = [
    {"study": "Jensen (2012)", "effect_estimate": -0.43, "ci_lower": -1.10,
     "ci_upper": 0.25, "comparator_type": WAITING_LIST},
    {"study": "Karlsson (2015)", "effect_estimate": -0.30, "ci_lower": -0.87,
     "ci_upper": 0.27, "comparator_type": WAITING_LIST},
    {"study": "Lami (2018)", "effect_estimate": -0.03, "ci_lower": -0.52,
     "ci_upper": 0.46, "comparator_type": USUAL_CARE},
    {"study": "McCrae (2019)", "effect_estimate": -0.20, "ci_lower": -0.66,
     "ci_upper": 0.26, "comparator_type": WAITING_LIST},
]


def _ma():
    return MetaAnalyzer().run(data=pd.DataFrame(ROWS), effect_measure="SMD")


def _summary():
    return subgroup_summary(ROWS, lambda m: MetaAnalyzer().run(
        data=pd.DataFrame(m), effect_measure="SMD"))


def _plot(tmp_path):
    return ForestPlotGenerator().generate_subgroups(
        _ma(), _summary(), "SMD", str(tmp_path / "forest_plot_subgroups.png"))


def test_subgroup_plot_written(tmp_path):
    p = _plot(tmp_path)
    assert p and Path(p).exists()
    assert Path(p).read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_no_subgroups_no_plot(tmp_path):
    out = tmp_path / "x.png"
    assert ForestPlotGenerator().generate_subgroups(_ma(), None, "SMD", str(out)) is None
    assert not out.exists()


def test_main_forest_plot_still_drawn(tmp_path):
    p = ForestPlotGenerator().generate(_ma(), "SMD", str(tmp_path / "fp.png"))
    assert Path(p).exists()


def test_html_embeds_subgroup_plot(tmp_path):
    def _gen(plot):
        out = tmp_path / "r.html"
        HTMLReportGenerator().generate(
            title="T", authors="", pico={}, inclusion_criteria=[],
            exclusion_criteria=[], ma_result=_ma(), extraction_results=[],
            screening_results=[], rob_results=[], forest_plot_path="",
            effect_measure="SMD", output_path=str(out),
            subgroups=_summary(), subgroup_plot_path=plot)
        return out.read_text(encoding="utf-8")
    assert "Forest plot by control type" in _gen(_plot(tmp_path))
    assert "Forest plot by control type" not in _gen(None)


def test_docx_embeds_subgroup_plot(tmp_path):
    def _shapes(plot):
        out = tmp_path / "r.docx"
        ReportGenerator().generate(
            title="T", authors="", pico={}, ma_result=_ma(),
            extraction_results=[], screening_results=[], forest_plot_path="",
            effect_measure="SMD", output_path=str(out),
            subgroups=_summary(), subgroup_plot_path=plot)
        return len(docx.Document(str(out)).inline_shapes)
    assert _shapes(_plot(tmp_path)) == 1
    assert _shapes(None) == 0


def test_pdf_and_main_pass_subgroup_plot():
    pdf = (SR / "src" / "reporting" / "pdf_report.py").read_text(encoding="utf-8")
    assert re.search(r"subgroup_plot_path\s*=\s*None", pdf)
    assert re.search(r"subgroup_plot_path\s*=\s*subgroup_plot_path", pdf)
    main = (SR / "main.py").read_text(encoding="utf-8")
    assert "generate_subgroups(" in main
    assert len(re.findall(r"subgroup_plot_path\s*=\s*fp_sg", main)) == 2
