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
    assert ("Forest plot: all pooled studies and excluding waiting-list trials"
            in _gen(_plot(tmp_path)))
    assert "Forest plot by control type" not in _gen(_plot(tmp_path))
    assert "Forest plot: all pooled" not in _gen(None)


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



# --- Two-panel layout (Session 40): all pooled studies on top; the same
# studies with the wait-list taken off at the bottom. A study whose only
# control is a wait-list has no comparator left: it stays as a row with no
# effect. Its control is never filled in as 0.

def _panels(rows=ROWS):
    from pipelines.sr.src.visualization.forest_plot import build_panels
    ma = MetaAnalyzer().run(data=pd.DataFrame(rows), effect_measure="SMD")
    summ = subgroup_summary(rows, lambda m: MetaAnalyzer().run(
        data=pd.DataFrame(m), effect_measure="SMD"))
    return ma, build_panels(ma, summ)


def _names(panel):
    return [r["study"] for r in panel["rows"]]


def test_two_panels_all_pooled_on_top():
    ma, panels = _panels()
    assert [p["label"] for p in panels] == [
        "All pooled studies", "Excluding waiting-list trials"]
    top = panels[0]
    assert _names(top) == [str(s) for s in ma["study_effects"]["study"]]
    assert all(r["included"] for r in top["rows"])
    assert top["k"] == 4
    assert top["result"]["pooled_effect"] == ma["pooled_effect"]


def test_bottom_panel_keeps_every_study_in_same_order():
    _, panels = _panels()
    assert _names(panels[1]) == _names(panels[0])


def test_bottom_panel_waiting_list_rows_have_no_effect():
    _, panels = _panels()
    top = {r["study"]: r for r in panels[0]["rows"]}
    bottom = {r["study"]: r for r in panels[1]["rows"]}
    for s in ("Jensen (2012)", "Karlsson (2015)", "McCrae (2019)"):
        assert bottom[s]["included"] is False
        assert bottom[s]["effect_estimate"] is None
        assert "wait-list control only" in bottom[s]["note"]
    lami = bottom["Lami (2018)"]
    assert lami["included"] is True
    assert lami["effect_estimate"] == top["Lami (2018)"]["effect_estimate"]


def test_bottom_panel_one_study_not_pooled():
    _, panels = _panels()
    assert panels[1]["k"] == 1
    assert panels[1]["result"] is None
    assert panels[1]["note"].startswith("1 study - not pooled")


def test_bottom_panel_pools_when_two_non_waiting_list():
    rows = [dict(r) for r in ROWS]
    rows[0]["comparator_type"] = USUAL_CARE
    _, panels = _panels(rows)
    assert panels[1]["k"] == 2
    assert panels[1]["result"] is not None


def test_bottom_panel_unknown_control_marked():
    rows = [dict(r) for r in ROWS]
    rows[2]["comparator_type"] = None
    _, panels = _panels(rows)
    lami = {r["study"]: r for r in panels[1]["rows"]}["Lami (2018)"]
    assert lami["included"] is False
    assert "control type unknown" in lami["note"]
