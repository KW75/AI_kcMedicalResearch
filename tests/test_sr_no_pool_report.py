"""Session 43: SR writes the HTML report when < 2 studies pool.

Run 20261116_181723 pooled 0 of 5 and wrote no HTML, so the reviewer never
saw the not-pooled reasons or the RoB 2 D4 'reviewer to confirm' marks.
Now a no-pool report is written: banner, no pooled numbers (n/a, never
0.000), no forest plot; RoB 2 table and the not-pooled list kept.
"""
import importlib
from pathlib import Path

hr = importlib.import_module("SOURCE_CODE.pipelines.sr.src.reporting.html_report")
m = importlib.import_module("SOURCE_CODE.pipelines.sr.main")

MAIN = Path(__file__).resolve().parents[1] / "SOURCE_CODE" / "pipelines" / "sr" / "main.py"


def _gen(tmp_path):
    out = tmp_path / "r.html"
    hr.HTMLReportGenerator().generate(
        title="T", authors="", pico={}, inclusion_criteria=[], exclusion_criteria=[],
        ma_result={}, extraction_results=[], screening_results=[], rob_results=[],
        forest_plot_path=None, effect_measure="SMD", model_name="m",
        output_path=str(out), no_pool=True)
    return out.read_text(encoding="utf-8")


def test_no_pool_banner_and_no_numbers(tmp_path):
    h = _gen(tmp_path)
    assert "No pooled estimate in this run" in h
    assert "0.000" not in h
    assert "Pooled SMD =" not in h


def test_no_pool_has_no_forest_or_heterogeneity(tmp_path):
    h = _gen(tmp_path)
    assert 'id="fp"' not in h
    assert "Cochran Q" not in h


def test_no_pool_keeps_rob_and_d4_note(tmp_path):
    h = _gen(tmp_path)
    assert 'id="rob"' in h and "reviewer judgement" in h
    assert 'id="ma"' in h


def test_helper_writes_report(tmp_path):
    out = tmp_path / "reports" / "systematic_review.html"
    got = m._write_no_pool_html(out, {"pico": {"population": "Adults"}}, [], [], [], None, "SMD", "qwen")
    assert got and out.exists()
    assert "No pooled estimate in this run" in out.read_text(encoding="utf-8")


def test_helper_error_does_not_stop_run(tmp_path, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("x")
    monkeypatch.setattr(hr.HTMLReportGenerator, "generate", boom)
    assert m._write_no_pool_html(tmp_path / "r.html", {}, [], [], [], None, "SMD", "m") is None


def test_main_writes_report_before_abort_return():
    src = MAIN.read_text(encoding="utf-8")
    i = src.index("Aborting meta-analysis")
    j = src.index("return", i)
    block = src[i:j]
    assert "_write_no_pool_html(" in block
    assert block.index("_write_no_pool_html(") < block.index("layout.mirror_all()")
