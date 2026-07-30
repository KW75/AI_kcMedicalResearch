"""
project_layout.py
-----------------
Single source of truth for all runtime paths used by the SR pipeline.

Directory contract
──────────────────
input\sr\                          ← user drops PDFs + PICO here
output\sr\figures\                 ← mirror: latest forest plot
output\sr\reports\                 ← mirror: latest DOCX / HTML
reports\sr\<RUN_ID>\
    uploads\                       ← copy of every input PDF
    data\screened\                 ← screening_log.csv
    data\extracted\                ← extracted_data.csv, rob2_assessment.csv
    data\results\                  ← meta_analysis_results.csv
    output\figures\                ← forest plot (primary copy)
    output\reports\                ← DOCX, HTML (primary copy)
"""

import os
import shutil
from datetime import datetime
from pathlib import Path

# ── Root ──────────────────────────────────────────────────────────────────────
ROOT = Path(os.environ.get("KC_ROOT", r"D:\AI_kcMedicalResearch"))

# ── Input (read-only by pipeline) ─────────────────────────────────────────────
INPUT_SR        = ROOT / "input" / "sr"

# ── Mirror output (always reflects latest run) ────────────────────────────────
OUTPUT_SR       = ROOT / "output" / "sr"
OUTPUT_FIGURES  = OUTPUT_SR / "figures"
OUTPUT_REPORTS  = OUTPUT_SR / "reports"

# ── Legacy sr\data paths (kept for backward compat during transition) ─────────
LEGACY_UPLOADS  = ROOT / "sr" / "data" / "uploads"
LEGACY_SCREENED = ROOT / "sr" / "data" / "screened"
LEGACY_EXTRACTED= ROOT / "sr" / "data" / "extracted"
LEGACY_RESULTS  = ROOT / "sr" / "data" / "results"
LEGACY_FIGURES  = ROOT / "sr" / "outputs" / "figures"
LEGACY_REPORTS  = ROOT / "sr" / "outputs" / "reports"


def make_run_id() -> str:
    """Return a timestamp string used as the project folder name."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


class SRProjectLayout:
    """
    Created once per pipeline run.  Builds the full reports\sr\<RUN_ID>\
    tree, copies input PDFs into uploads\, and exposes every path the
    pipeline needs as a plain pathlib.Path attribute.
    """

    def __init__(self, run_id: str | None = None):
        self.run_id     = run_id or make_run_id()
        self.project    = ROOT / "reports" / "sr" / self.run_id

        # ── Sub-paths ─────────────────────────────────────────────────────────
        self.uploads        = self.project / "uploads"
        self.screened       = self.project / "data" / "screened"
        self.extracted      = self.project / "data" / "extracted"
        self.results        = self.project / "data" / "results"
        self.figures        = self.project / "output" / "figures"
        self.reports        = self.project / "output" / "reports"

        # ── Audit CSV paths ───────────────────────────────────────────────────
        self.screens_csv    = self.screened  / "screening_log.csv"
        self.extracted_csv  = self.extracted / "extracted_data.csv"
        self.rob2_csv       = self.extracted / "rob2_assessment.csv"
        self.results_csv    = self.results   / "meta_analysis_results.csv"
        self.forest_png     = self.figures   / "forest_plot.png"
        self.docx           = self.reports   / "systematic_review.docx"
        self.html           = self.reports   / "systematic_review.html"
        self.pdf            = self.reports   / "systematic_review.pdf"

    def initialise(self, pdf_sources: list[Path]) -> list[Path]:
        """
        Create all directories, copy input PDFs into uploads\,
        and return the list of paths inside uploads\.
        """
        for d in (self.uploads, self.screened, self.extracted,
                  self.results, self.figures, self.reports,
                  OUTPUT_FIGURES, OUTPUT_REPORTS):
            d.mkdir(parents=True, exist_ok=True)

        copied = []
        for src in pdf_sources:
            dst = self.uploads / src.name
            if not dst.exists():
                shutil.copy2(src, dst)
            copied.append(dst)
        return copied

    def mirror(self, src: Path) -> None:
        """
        Copy a finished output file into the output\sr\ mirror folder.
        Silently skips if src does not exist.
        """
        if not src.exists():
            return
        if src.suffix.lower() == ".png":
            dst_dir = OUTPUT_FIGURES
        else:
            dst_dir = OUTPUT_REPORTS
        dst_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst_dir / src.name)

    def mirror_all(self) -> None:
        """Mirror every finished output file to output\sr\."""
        for f in (self.forest_png, self.docx, self.html, self.pdf):
            self.mirror(f)
