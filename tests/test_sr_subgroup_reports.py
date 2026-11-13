"""Item 11 step 3 (Session 39): subgroup section in the HTML and Word
reports; lines come from subgroups.subgroup_report_lines (shared)."""
import re
from pathlib import Path

import docx

from pipelines.sr.src.analysis.subgroups import (
    subgroup_summary, subgroup_report_lines, WAITING_LIST, USUAL_CARE,
)
from pipelines.sr.src.reporting.html_report import HTMLReportGenerator
from pipelines.sr.src.reporting.report_generator import ReportGenerator

SR = Path(__file__).resolve().parents[1] / "SOURCE_CODE" / "pipelines" / "sr"
MA = {"k": 4, "pooled_effect": -0.4, "ci_lower": -0.8, "ci_upper": 0.0,
      "I2": 20.0}


def _summary():
    rows = [{"study": s, "comparator_type": t}
            for s, t in (("Jensen (2012)", WAITING_LIST),
                         ("Karlsson (2015)", WAITING_LIST),
                         ("Lami (2018)", USUAL_CARE),
                         ("McCrae (2019)", WAITING_LIST))]
    return subgroup_summary(rows, lambda m: {
        "pooled_effect": -0.5, "ci_lower": -0.9, "ci_upper": -0.1, "I2": 10.0})


def _html(tmp_path, subgroups):
    out = tmp_path / "r.html"
    HTMLReportGenerator().generate(
        title="T", authors="", pico={}, inclusion_criteria=[],
        exclusion_criteria=[], ma_result=MA, extraction_results=[],
        screening_results=[], rob_results=[], forest_plot_path="",
        effect_measure="SMD", output_path=str(out), subgroups=subgroups)
    return out.read_text(encoding="utf-8")


def _docx(tmp_path, subgroups):
    out = tmp_path / "r.docx"
    ReportGenerator().generate(
        title="T", authors="", pico={}, ma_result=MA, extraction_results=[],
        screening_results=[], forest_plot_path="", effect_measure="SMD",
        output_path=str(out), subgroups=subgroups)
    return "\n".join(p.text for p in docx.Document(str(out)).paragraphs)


def test_report_lines_run_222233():
    by = {l[0]: l for l in subgroup_report_lines(_summary(), "SMD")}
    wl = by["Waiting list (k=3)"]
    assert wl[1] == "Jensen (2012), Karlsson (2015), McCrae (2019)"
    assert wl[2] == "SMD -0.500 (95% CI -0.900 to -0.100); I\u00b2=10.0%"
    uc = by["Usual care (k=1)"]
    assert uc[2] == "" and uc[3] == "1 study - not pooled."
    assert "Excluding waiting-list trials (k=1)" in by
    assert subgroup_report_lines(None, "SMD") == []


def test_html_has_subgroup_section(tmp_path):
    html = _html(tmp_path, _summary())
    assert "Subgroups by control type" in html
    assert "Waiting list (k=3)" in html
    assert "1 study - not pooled." in html


def test_html_no_section_without_subgroups(tmp_path):
    assert "Subgroups by control type" not in _html(tmp_path, None)


def test_docx_subgroup_section(tmp_path):
    txt = _docx(tmp_path, _summary())
    assert "Subgroups by control type" in txt
    assert "Waiting list (k=3): Jensen (2012), Karlsson (2015), McCrae (2019)." in txt
    assert "Usual care (k=1): Lami (2018). 1 study - not pooled." in txt
    assert "Subgroups by control type" not in _docx(tmp_path, None)


def test_pdf_and_main_pass_subgroups():
    pdf = (SR / "src" / "reporting" / "pdf_report.py").read_text(encoding="utf-8")
    assert re.search(r"subgroups\s*=\s*None", pdf)
    assert re.search(r"subgroups\s*=\s*subgroups", pdf)
    main = (SR / "main.py").read_text(encoding="utf-8")
    # 2 report calls + generate_subgroups() in Stage 5 (item 11c)
    assert len(re.findall(r"subgroups\s*=\s*subgroups", main)) == 3

