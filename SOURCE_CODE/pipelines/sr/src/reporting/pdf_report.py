# SOURCE_CODE/pipelines/sr/src/reporting/pdf_report.py
import logging, tempfile
from pathlib import Path
# Fix: Use relative import
from .html_report import HTMLReportGenerator
logger = logging.getLogger(__name__)

PDF_CSS = """
@page{size:A4;margin:18mm 16mm 20mm 16mm;
  @bottom-center{content:"SR Automation  |  Page " counter(page) " of " counter(pages);
    font-size:8pt;color:#9ca3af;font-family:"Segoe UI",Arial,sans-serif;}}
.section{break-inside:avoid;page-break-inside:avoid;}
.navbar{display:none!important;}
.fw img{max-width:100%;height:auto;}
table{font-size:8pt;}
"""

class PDFReportGenerator:
    def __init__(self):
        try:
            from weasyprint import HTML as WH, CSS
            self._HTML=WH; self._CSS=CSS; self._ok=True
        except Exception as e:
            logger.warning(f"WeasyPrint unavailable ({type(e).__name__}: {e}). HTML-only mode.")
            self._ok=False

    def generate(self, title, authors, pico, inclusion_criteria, exclusion_criteria,
                 ma_result, extraction_results, screening_results, rob_results,
                 forest_plot_path, effect_measure="OR", model_name="claude-opus-4-7",
                 output_path="outputs/reports/systematic_review.pdf",
                 also_save_html=True) -> dict:
        gen      = HTMLReportGenerator()
        html_path= str(Path(output_path).with_suffix(".html")) if also_save_html else None
        with tempfile.NamedTemporaryFile(suffix=".html",mode="w",encoding="utf-8",delete=False) as t:
            tmp=t.name
        rendered = gen.generate(title=title,authors=authors,pico=pico,
            inclusion_criteria=inclusion_criteria,exclusion_criteria=exclusion_criteria,
            ma_result=ma_result,extraction_results=extraction_results,
            screening_results=screening_results,rob_results=rob_results,
            forest_plot_path=forest_plot_path,effect_measure=effect_measure,
            model_name=model_name,output_path=html_path or tmp)
        result={}
        if also_save_html: result["html"]=rendered; logger.info(f"HTML: {rendered}")
        if not self._ok: result["pdf"]=None; return result
        pdf=Path(output_path); pdf.parent.mkdir(parents=True,exist_ok=True)
        try:
            self._HTML(filename=rendered).write_pdf(
                target=str(pdf),stylesheets=[self._CSS(string=PDF_CSS)],
                optimize_images=True,jpeg_quality=90)
            result["pdf"]=str(pdf.resolve()); logger.info(f"PDF: {result['pdf']}")
        except Exception as e:
            logger.error(f"WeasyPrint render failed: {e}"); result["pdf"]=None
        return result