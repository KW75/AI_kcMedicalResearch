# Session 39: a missing PDF must say why in the run summary, not "PDF -> None".
# Run 20261112_222233 had no PDF: WeasyPrint not installed in .venv
# (HTML-only mode); the only reason was a warning lost in the console.
import sys
from pathlib import Path

import pipelines.sr.src.reporting.pdf_report as pr

MAIN_PY = Path(__file__).resolve().parents[1] / "SOURCE_CODE" / "pipelines" / "sr" / "main.py"


class _FakeHTML:
    def generate(self, **kw):
        p = Path(kw["output_path"])
        p.write_text("<html></html>", encoding="utf-8")
        return str(p)


class _BoomHTML:
    def __init__(self, filename):
        pass

    def write_pdf(self, **kw):
        raise RuntimeError("boom")


def _call(g, tmp_path):
    return g.generate(
        title="t", authors="", pico={}, inclusion_criteria=[], exclusion_criteria=[],
        ma_result=None, extraction_results=[], screening_results=[], rob_results=[],
        forest_plot_path=None, output_path=str(tmp_path / "r.pdf"), also_save_html=True)


def test_unavailable_weasyprint_records_reason(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "weasyprint", None)   # import now fails
    monkeypatch.setattr(pr, "HTMLReportGenerator", _FakeHTML)
    g = pr.PDFReportGenerator()
    assert g._ok is False
    res = _call(g, tmp_path)
    assert res["pdf"] is None
    assert "WeasyPrint unavailable" in res["pdf_error"]
    assert Path(res["html"]).exists()


def test_render_failure_records_reason(monkeypatch, tmp_path):
    monkeypatch.setattr(pr, "HTMLReportGenerator", _FakeHTML)
    g = pr.PDFReportGenerator.__new__(pr.PDFReportGenerator)
    g._ok, g._err, g._HTML, g._CSS = True, None, _BoomHTML, (lambda string: None)
    res = _call(g, tmp_path)
    assert res["pdf"] is None
    assert "WeasyPrint render failed" in res["pdf_error"]
    assert "boom" in res["pdf_error"]


def test_summary_line_names_reason():
    line = pr.pdf_summary_line({"pdf": None, "pdf_error": "WeasyPrint unavailable (X)"})
    assert "NOT WRITTEN" in line and "WeasyPrint unavailable (X)" in line
    assert "None" not in line
    assert pr.pdf_summary_line({"pdf": "C:/r.pdf"}) == "PDF      -> C:/r.pdf"
    assert "no reason recorded" in pr.pdf_summary_line({})


def test_main_uses_summary_line():
    src = MAIN_PY.read_text(encoding="utf-8")
    assert "pdf_summary_line(pdf_paths)" in src
    assert "pdf_paths.get('pdf',  'N/A')" not in src
