"""Session 47 item (e): output/sr/ mirror never keeps a file the latest run did not produce.

Run 20261116_214126 pooled nothing and wrote only the HTML, but output/sr/ still
held the DOCX and forest plot of an earlier run: mirror_all() copied what existed
and never removed anything.
"""
import importlib
import logging

pl = importlib.import_module("SOURCE_CODE.pipelines.sr.src.utils.project_layout")


def _setup(tmp_path, monkeypatch, produced):
    out_fig = tmp_path / "mirror" / "figures"
    out_rep = tmp_path / "mirror" / "reports"
    monkeypatch.setattr(pl, "OUTPUT_FIGURES", out_fig)
    monkeypatch.setattr(pl, "OUTPUT_REPORTS", out_rep)
    lay = pl.SRProjectLayout(run_id="t_s47e")
    run = tmp_path / "run"
    lay.forest_png = run / "figures" / "forest_plot.png"
    lay.docx = run / "reports" / "systematic_review.docx"
    lay.html = run / "reports" / "systematic_review.html"
    lay.pdf = run / "reports" / "systematic_review.pdf"
    for name in produced:
        f = getattr(lay, name)
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("NEW " + name, encoding="utf-8")
    return lay, out_fig, out_rep


def _stale(out_fig, out_rep):
    out_fig.mkdir(parents=True, exist_ok=True)
    out_rep.mkdir(parents=True, exist_ok=True)
    for p in (out_fig / "forest_plot.png", out_rep / "systematic_review.docx",
              out_rep / "systematic_review.pdf", out_rep / "systematic_review.html"):
        p.write_text("OLD", encoding="utf-8")
    (out_fig / ".gitkeep").write_text("", encoding="utf-8")
    (out_fig / "other.png").write_text("KEEP", encoding="utf-8")


def _removed(caplog):
    return [m for m in caplog.messages if "[MIRROR] removed stale" in m]


def test_no_pool_run_removes_stale_docx_pdf_plot(tmp_path, monkeypatch):
    lay, f, r = _setup(tmp_path, monkeypatch, ["html"])
    _stale(f, r)
    lay.mirror_all()
    assert (r / "systematic_review.html").read_text(encoding="utf-8") == "NEW html"
    assert not (r / "systematic_review.docx").exists()
    assert not (r / "systematic_review.pdf").exists()
    assert not (f / "forest_plot.png").exists()


def test_each_removal_is_logged(tmp_path, monkeypatch, caplog):
    lay, f, r = _setup(tmp_path, monkeypatch, ["html"])
    _stale(f, r)
    with caplog.at_level(logging.INFO):
        lay.mirror_all()
    assert len(_removed(caplog)) == 3


def test_run_without_pdf_removes_only_stale_pdf(tmp_path, monkeypatch):
    lay, f, r = _setup(tmp_path, monkeypatch, ["forest_png", "docx", "html"])
    _stale(f, r)
    lay.mirror_all()
    assert not (r / "systematic_review.pdf").exists()
    assert (r / "systematic_review.docx").read_text(encoding="utf-8") == "NEW docx"
    assert (f / "forest_plot.png").read_text(encoding="utf-8") == "NEW forest_png"


def test_full_run_copies_all_removes_nothing(tmp_path, monkeypatch, caplog):
    lay, f, r = _setup(tmp_path, monkeypatch, ["forest_png", "docx", "html", "pdf"])
    _stale(f, r)
    with caplog.at_level(logging.INFO):
        lay.mirror_all()
    assert (r / "systematic_review.pdf").read_text(encoding="utf-8") == "NEW pdf"
    assert _removed(caplog) == []


def test_other_files_in_mirror_untouched(tmp_path, monkeypatch):
    lay, f, r = _setup(tmp_path, monkeypatch, ["html"])
    _stale(f, r)
    lay.mirror_all()
    assert (f / ".gitkeep").exists()
    assert (f / "other.png").read_text(encoding="utf-8") == "KEEP"


def test_nothing_stale_no_error_no_log(tmp_path, monkeypatch, caplog):
    lay, f, r = _setup(tmp_path, monkeypatch, ["html"])
    with caplog.at_level(logging.INFO):
        lay.mirror_all()
    assert (r / "systematic_review.html").exists()
    assert not (r / "systematic_review.docx").exists()
    assert _removed(caplog) == []
