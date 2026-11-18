"""The subgroup forest plot (forest_plot_subgroups.png) is mirrored to
output/sr/figures like forest_plot.png, and a stale copy is removed when the
run did not draw it (too few studies, or a drawing error).

Before: mirror_all() handled only forest_plot.png, DOCX, HTML and PDF, so the
subgroup plot stayed in the run folder and an old copy was never cleaned.
"""
import importlib
import logging
from pathlib import Path

pl = importlib.import_module("SOURCE_CODE.pipelines.sr.src.utils.project_layout")
SR_MAIN = (Path(__file__).resolve().parents[1]
           / "SOURCE_CODE" / "pipelines" / "sr" / "main.py")


def _setup(tmp_path, monkeypatch, produced):
    out_fig = tmp_path / "mirror" / "figures"
    out_rep = tmp_path / "mirror" / "reports"
    monkeypatch.setattr(pl, "OUTPUT_FIGURES", out_fig)
    monkeypatch.setattr(pl, "OUTPUT_REPORTS", out_rep)
    lay = pl.SRProjectLayout(run_id="t_mirror_sg")
    run = tmp_path / "run"
    lay.forest_png = run / "figures" / "forest_plot.png"
    lay.forest_subgroups_png = run / "figures" / "forest_plot_subgroups.png"
    lay.docx = run / "reports" / "systematic_review.docx"
    lay.html = run / "reports" / "systematic_review.html"
    lay.pdf = run / "reports" / "systematic_review.pdf"
    for name in produced:
        f = getattr(lay, name)
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("NEW " + name, encoding="utf-8")
    return lay, out_fig, out_rep


def test_layout_names_the_subgroup_plot():
    lay = pl.SRProjectLayout(run_id="t_mirror_sg")
    assert lay.forest_subgroups_png == lay.figures / "forest_plot_subgroups.png"


def test_subgroup_plot_copied_when_drawn(tmp_path, monkeypatch):
    lay, f, r = _setup(tmp_path, monkeypatch,
                       ["forest_png", "forest_subgroups_png", "html"])
    lay.mirror_all()
    dst = f / "forest_plot_subgroups.png"
    assert dst.exists()
    assert dst.read_text(encoding="utf-8") == "NEW forest_subgroups_png"


def test_stale_subgroup_plot_removed_and_logged(tmp_path, monkeypatch, caplog):
    lay, f, r = _setup(tmp_path, monkeypatch, ["forest_png", "html"])
    f.mkdir(parents=True, exist_ok=True)
    stale = f / "forest_plot_subgroups.png"
    stale.write_text("OLD", encoding="utf-8")
    with caplog.at_level(logging.INFO):
        lay.mirror_all()
    assert not stale.exists()
    assert any("[MIRROR] removed stale" in m and "forest_plot_subgroups.png" in m
               for m in caplog.messages)


def test_sr_main_uses_the_layout_path():
    src = SR_MAIN.read_text(encoding="utf-8")
    assert "layout.forest_subgroups_png" in src
    assert '"forest_plot_subgroups.png"' not in src
