"""
tests/test_sr.py
Unit tests for the SR pipeline — pure-Python logic only.
No Anthropic API calls, no real PDFs required.
"""
from __future__ import annotations
import sys
from pathlib import Path
import pytest
import pandas as pd
import numpy as np
import unittest.mock


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ---------------------------------------------------------------------------
# MetaAnalyzer
# ---------------------------------------------------------------------------

class TestMetaAnalyzer:
    def _df(self, effects, lowers, uppers):
        return pd.DataFrame({
            "study":           [f"Study {i+1}" for i in range(len(effects))],
            "effect_estimate": effects,
            "ci_lower":        lowers,
            "ci_upper":        uppers,
            "n_intervention":  [50]*len(effects),
            "n_control":       [50]*len(effects),
        })

    def test_md_returns_dict(self):
        from sr.src.analysis.meta_analysis import MetaAnalyzer
        r = MetaAnalyzer().run(self._df([-0.5,-0.6,-0.4],[-1.0,-1.1,-0.9],[0.0,-0.1,0.1]), "MD")
        assert isinstance(r, dict)
        assert "pooled_effect" in r

    def test_or_pooling_positive(self):
        from sr.src.analysis.meta_analysis import MetaAnalyzer
        r = MetaAnalyzer().run(self._df([1.5,1.8,1.6],[1.1,1.2,1.1],[2.1,2.7,2.4]), "OR")
        assert r["pooled_effect"] > 0

    def test_smd_has_all_keys(self):
        from sr.src.analysis.meta_analysis import MetaAnalyzer
        r = MetaAnalyzer().run(self._df([-0.4,-0.5,-0.3],[-0.9,-1.0,-0.8],[0.1,0.0,0.2]), "SMD")
        for key in ("pooled_effect","ci_lower","ci_upper","I2","tau2","Q","k","study_effects"):
            assert key in r

    def test_k_equals_study_count(self):
        from sr.src.analysis.meta_analysis import MetaAnalyzer
        r = MetaAnalyzer().run(self._df([-0.3,-0.4],[-0.8,-0.9],[0.2,0.1]), "MD")
        assert r["k"] == 2

    def test_ci_lower_less_than_upper(self):
        from sr.src.analysis.meta_analysis import MetaAnalyzer
        r = MetaAnalyzer().run(self._df([-0.5,-0.6,-0.4],[-1.0,-1.1,-0.9],[0.0,-0.1,0.1]), "MD")
        assert r["ci_lower"] < r["ci_upper"]

    def test_i2_in_range(self):
        from sr.src.analysis.meta_analysis import MetaAnalyzer
        r = MetaAnalyzer().run(self._df([-0.5,-0.6,-0.4],[-1.0,-1.1,-0.9],[0.0,-0.1,0.1]), "MD")
        assert 0.0 <= r["I2"] <= 100.0

    def test_tau2_non_negative(self):
        from sr.src.analysis.meta_analysis import MetaAnalyzer
        r = MetaAnalyzer().run(self._df([-0.5,-0.6,-0.4],[-1.0,-1.1,-0.9],[0.0,-0.1,0.1]), "MD")
        assert r["tau2"] >= 0.0

    def test_weight_pct_column_exists(self):
        from sr.src.analysis.meta_analysis import MetaAnalyzer
        r = MetaAnalyzer().run(self._df([-0.5,-0.6,-0.4],[-1.0,-1.1,-0.9],[0.0,-0.1,0.1]), "MD")
        assert "weight_pct" in r["study_effects"].columns

    def test_weight_pct_sums_to_100(self):
        from sr.src.analysis.meta_analysis import MetaAnalyzer
        r = MetaAnalyzer().run(self._df([-0.5,-0.6,-0.4],[-1.0,-1.1,-0.9],[0.0,-0.1,0.1]), "MD")
        assert abs(r["study_effects"]["weight_pct"].sum() - 100.0) < 0.01


# ---------------------------------------------------------------------------
# ForestPlotGenerator
# ---------------------------------------------------------------------------

class TestForestPlotGenerator:
    def _ma(self):
        from sr.src.analysis.meta_analysis import MetaAnalyzer
        df = pd.DataFrame({
            "study":           ["A (2020)","B (2021)","C (2022)"],
            "effect_estimate": [-0.5,-0.6,-0.4],
            "ci_lower":        [-1.0,-1.1,-0.9],
            "ci_upper":        [0.0,-0.1,0.1],
            "n_intervention":  [50,60,55],
            "n_control":       [50,60,55],
        })
        return MetaAnalyzer().run(df, "SMD")

    def test_generates_png(self, tmp_path):
        from sr.src.visualization.forest_plot import ForestPlotGenerator
        out = str(tmp_path / "forest.png")
        result = ForestPlotGenerator().generate(self._ma(), "SMD", out)
        assert Path(result).exists()
        assert Path(result).suffix == ".png"

    def test_png_non_empty(self, tmp_path):
        from sr.src.visualization.forest_plot import ForestPlotGenerator
        out = str(tmp_path / "forest.png")
        ForestPlotGenerator().generate(self._ma(), "SMD", out)
        assert Path(out).stat().st_size > 1000

    def test_or_log_scale_no_error(self, tmp_path):
        from sr.src.analysis.meta_analysis import MetaAnalyzer
        from sr.src.visualization.forest_plot import ForestPlotGenerator
        df = pd.DataFrame({
            "study":           ["A (2020)","B (2021)"],
            "effect_estimate": [1.5,1.8],
            "ci_lower":        [1.1,1.2],
            "ci_upper":        [2.1,2.7],
            "n_intervention":  [50,60],
            "n_control":       [50,60],
        })
        ma  = MetaAnalyzer().run(df, "OR")
        out = str(tmp_path / "forest_or.png")
        ForestPlotGenerator().generate(ma, "OR", out)
        assert Path(out).exists()


# ---------------------------------------------------------------------------
# HTMLReportGenerator
# ---------------------------------------------------------------------------

class TestHTMLReportGenerator:
    def _ma(self):
        return {"pooled_effect":0.5,"ci_lower":0.2,"ci_upper":0.8,
                "z_score":3.1,"p_value":0.002,"I2":45.0,"tau2":0.03,
                "Q":12.5,"Q_p":0.04,"k":3,
                "study_effects": pd.DataFrame({
                    "study":["A","B","C"],
                    "effect_estimate":[0.4,0.5,0.6],
                    "ci_lower":[0.1,0.2,0.3],
                    "ci_upper":[0.7,0.8,0.9],
                    "weight_pct":[33.3,33.3,33.4]})}

    def _screening(self):
        return [
            {"file_id":"f1","filename":"a.pdf","decision":"INCLUDE",
             "confidence":0.9,"pico_match":{},"rationale":"Good","is_rct":True,"error":None},
            {"file_id":"f2","filename":"b.pdf","decision":"EXCLUDE",
             "confidence":0.8,"pico_match":{},"rationale":"Wrong pop","is_rct":False,"error":None},
        ]

    def test_generates_html_file(self, tmp_path):
        from sr.src.reporting.html_report import HTMLReportGenerator
        out = str(tmp_path / "report.html")
        HTMLReportGenerator().generate(
            title="Test SR", authors="", pico={"population":"Adults"},
            inclusion_criteria=[], exclusion_criteria=[],
            ma_result=self._ma(), extraction_results=[],
            screening_results=self._screening(), rob_results=[],
            forest_plot_path=None, output_path=out)
        assert Path(out).exists()

    def test_html_contains_title(self, tmp_path):
        from sr.src.reporting.html_report import HTMLReportGenerator
        out = str(tmp_path / "report.html")
        HTMLReportGenerator().generate(
            title="My Review Title", authors="", pico={},
            inclusion_criteria=[], exclusion_criteria=[],
            ma_result=self._ma(), extraction_results=[],
            screening_results=[], rob_results=[],
            forest_plot_path=None, output_path=out)
        assert "My Review Title" in Path(out).read_text(encoding="utf-8")

    def test_html_contains_pooled_effect(self, tmp_path):
        from sr.src.reporting.html_report import HTMLReportGenerator
        out = str(tmp_path / "report.html")
        HTMLReportGenerator().generate(
            title="T", authors="", pico={},
            inclusion_criteria=[], exclusion_criteria=[],
            ma_result=self._ma(), extraction_results=[],
            screening_results=[], rob_results=[],
            forest_plot_path=None, output_path=out)
        assert "0.500" in Path(out).read_text(encoding="utf-8")

    def test_html_contains_screening_decisions(self, tmp_path):
        from sr.src.reporting.html_report import HTMLReportGenerator
        out = str(tmp_path / "report.html")
        HTMLReportGenerator().generate(
            title="T", authors="", pico={},
            inclusion_criteria=[], exclusion_criteria=[],
            ma_result=self._ma(), extraction_results=[],
            screening_results=self._screening(), rob_results=[],
            forest_plot_path=None, output_path=out)
        content = Path(out).read_text(encoding="utf-8")
        assert "INCLUDE" in content
        assert "EXCLUDE" in content

    def test_rob_not_available_when_empty(self, tmp_path):
        from sr.src.reporting.html_report import HTMLReportGenerator
        out = str(tmp_path / "report.html")
        HTMLReportGenerator().generate(
            title="T", authors="", pico={},
            inclusion_criteria=[], exclusion_criteria=[],
            ma_result=self._ma(), extraction_results=[],
            screening_results=[], rob_results=[],
            forest_plot_path=None, output_path=out)
        assert "not available" in Path(out).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# SR launcher stub (src/main.py integration)
# ---------------------------------------------------------------------------

class TestSRLauncher:
    def test_sr_in_parse_args(self):
        from src.main import parse_args
        args = parse_args(["--mode", "sr"])
        assert args.mode == "sr"

    def test_launcher_prints_pipeline_header(self, capsys):
        from src.main import run_sr_launcher
        run_sr_launcher()
        out = capsys.readouterr().out
        assert "SR Automation Pipeline" in out

    def test_launcher_prints_prisma_yaml(self, capsys):
        from src.main import run_sr_launcher
        with unittest.mock.patch("subprocess.Popen"):
            run_sr_launcher()
        out = capsys.readouterr().out
        assert "localhost:8501" in out

    def test_launcher_prints_output_files(self, capsys):
        from src.main import run_sr_launcher
        with unittest.mock.patch("subprocess.Popen"):
            run_sr_launcher()
        out = capsys.readouterr().out
        assert "SR Automation Pipeline" in out
        assert "Pipeline UI" in out
        assert "Pipeline UI launched" in out

