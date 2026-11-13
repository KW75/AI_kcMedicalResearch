import logging
from pathlib import Path
logger = logging.getLogger(__name__)
from .override_summary import override_changed_values, override_confirmed_only, study_label
from .html_report import plain_skip_reason
from ..analysis.subgroups import subgroup_report_lines, SUBGROUP_INTRO

try:
    from docx import Document
    from docx.shared import Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    _OK = True
except ImportError:
    _OK = False

class ReportGenerator:
    def generate(self, title, authors, pico, ma_result, extraction_results,
                 screening_results, forest_plot_path, effect_measure="OR",
                 output_path="outputs/reports/systematic_review.docx",
                 meta_audit=None, subgroups=None):
        if not _OK:
            logger.error("python-docx required."); return
        doc = Document()
        h = doc.add_heading(title, 0); h.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if authors:
            p=doc.add_paragraph(authors); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        doc.add_heading("Abstract",1)
        doc.add_paragraph(
            f"k={ma_result.get('k','?')} RCTs included. "
            f"Pooled {effect_measure}={ma_result.get('pooled_effect',0):.3f} "
            f"(95% CI {ma_result.get('ci_lower',0):.3f}-{ma_result.get('ci_upper',0):.3f}). "
            f"I\u00b2={ma_result.get('I2',0):.1f}%, \u03c4\u00b2={ma_result.get('tau2',0):.4f}.")
        doc.add_heading("Methods",1)
        doc.add_heading("Eligibility Criteria",2)
        doc.add_paragraph(" | ".join(f"{k.upper()}: {v}" for k,v in pico.items()))
        # Session 37: reviewer-entered values (study_overrides.yaml) are stated
        # in the report, not only in the log and extracted_data.csv.
        # Session 39 (item 4c): count only entries that changed a value (same
        # rule as the HTML report, pipelines/sr/src/reporting/override_summary.py).
        _rows = [r for r in (extraction_results or []) if isinstance(r, dict)]
        _ov = [r for r in _rows if override_changed_values(r.get("override_fields"))]
        _conf = [r for r in _rows if override_confirmed_only(r.get("override_fields"))]
        if _ov or _conf:
            doc.add_heading("Reviewer-entered data", 2)
        if _ov:
            doc.add_paragraph(
                f"{len(_ov)} of {len(extraction_results)} extracted studies use values "
                f"entered by a reviewer from the source PDF (input/sr/study_overrides.yaml), "
                f"not values extracted by the model. Report them as manually extracted.")
            for r in _ov:
                parts = [study_label(r) + ":"]
                if r.get("override_note"):
                    parts.append(str(r["override_note"]))
                if r.get("override_fields"):
                    parts.append(f"Fields: {r['override_fields']}")
                doc.add_paragraph(" ".join(parts), style="List Bullet")
        if _conf:
            doc.add_paragraph(
                "Checked by a reviewer against the PDF, values unchanged (confirmed): "
                + ", ".join(study_label(r) for r in _conf) + ".")
        doc.add_heading("Results",1)
        doc.add_heading("Meta-Analysis",2)
        doc.add_paragraph(
            f"k={ma_result.get('k','?')} studies. "
            f"Pooled {effect_measure}={ma_result.get('pooled_effect',0):.3f} "
            f"(95% CI {ma_result.get('ci_lower',0):.3f}-{ma_result.get('ci_upper',0):.3f}; "
            f"p={ma_result.get('p_value',0):.4f}). "
            f"I\u00b2={ma_result.get('I2',0):.1f}%.")
        # Session 39 (item 4a): same not-pooled list as the HTML report
        # (html_report.py _not_pooled_html); reasons reworded by the same
        # plain_skip_reason(). PRISMA 2020 item 13a.
        _ma_rows = [r for r in (meta_audit or []) if isinstance(r, dict)]
        if _ma_rows:
            _out = [r for r in _ma_rows if not r.get("included_in_meta")]
            doc.add_heading("Studies included in the review but not in the meta-analysis", 2)
            doc.add_paragraph(f"{len(_ma_rows) - len(_out)} of {len(_ma_rows)} studies pooled."
                              + ("" if _out else " None left out."))
            for r in _out:
                reason = str(r.get("skip_reason") or "no reason recorded")
                who = "Reviewer" if reason.startswith("excluded by reviewer") else "Automatic"
                label = f"{r.get('first_author') or r.get('filename', '?')} ({r.get('year', '')})"
                doc.add_paragraph(f"{label}: {plain_skip_reason(reason)} [{who}]",
                                  style="List Bullet")
        # Session 39 (item 11): same rows as the HTML report.
        _sg = subgroup_report_lines(subgroups, effect_measure)
        if _sg:
            doc.add_heading("Subgroups by control type", 2)
            doc.add_paragraph(SUBGROUP_INTRO)
            for _g, _s, _est, _note in _sg:
                doc.add_paragraph(
                    " ".join(x for x in (f"{_g}: {_s}.",
                                         f"{_est}." if _est else "",
                                         _note) if x),
                    style="List Bullet")
        if forest_plot_path and Path(forest_plot_path).exists():
            doc.add_heading("Forest Plot",2)
            doc.add_picture(forest_plot_path, width=Inches(6.0))
        doc.add_heading("Discussion",1); doc.add_paragraph("[Author interpretation required]")
        doc.add_heading("Conclusion",1); doc.add_paragraph("[Author conclusion required]")
        out=Path(output_path); out.parent.mkdir(parents=True,exist_ok=True)
        doc.save(str(out)); logger.info(f"DOCX saved: {out}")
