"""Session 37: reviewer-entered values must be stated in the Word and HTML
reports, not only in the log and extracted_data.csv. StudyOverrides.apply puts
override_fields / override_note on each extraction result; Stage 6 passes
those results to both generators as extraction_results."""
import pytest

docx = pytest.importorskip("docx")

from pipelines.sr.src.reporting.report_generator import ReportGenerator
from pipelines.sr.src.reporting.html_report import HTMLReportGenerator

MCCRAE_NOTE = ("Multi-arm trial (CBT-I, CBT-P, WLC). CBT-I and CBT-P combined "
               "into one intervention arm (Cochrane Handbook 23.3.4).")

MCCRAE = {"filename": "zsy234.pdf",
          "study_metadata": {"first_author": "McCrae", "year": 2019},
          "participants": {"n_intervention": 57, "n_control": 28},
          "primary_outcome": {"name": "Morning pain"},
          "override_fields": "n_intervention(39->57); mean_control(46.72->52.38)",
          "override_note": MCCRAE_NOTE}
LAMI = {"filename": "s10608-017-9875-4.pdf",
        "study_metadata": {"first_author": "Lami", "year": 2018},
        "participants": {"n_intervention": 28, "n_control": 36},
        "primary_outcome": {"name": "Pain"},
        "override_fields": "mean_intervention(4.8->7.35); sd_intervention(confirmed 2.08)"}
KARLSSON = {"filename": "karlsson.pdf",
            "study_metadata": {"first_author": "Karlsson", "year": 2015},
            "participants": {"n_intervention": 24, "n_control": 24},
            "primary_outcome": {"name": "Pain"}}

PICO = {"population": "Adults with fibromyalgia", "intervention": "CBT"}
MA = {"k": 3, "pooled_effect": -0.1, "ci_lower": -0.4, "ci_upper": 0.2,
      "p_value": 0.5, "I2": 0.0, "tau2": 0.0}


def _docx_text(rows, tmp_path):
    out = tmp_path / "r.docx"
    ReportGenerator().generate(title="T", authors="", pico=PICO, ma_result=MA,
                               extraction_results=rows, screening_results=[],
                               forest_plot_path=None, effect_measure="SMD",
                               output_path=str(out))
    return "\n".join(p.text for p in docx.Document(str(out)).paragraphs)


def _html_text(rows, tmp_path):
    out = HTMLReportGenerator().generate(
        title="T", authors="", pico=PICO, inclusion_criteria=[],
        exclusion_criteria=[], ma_result=MA, extraction_results=rows,
        screening_results=[], rob_results=None, forest_plot_path=None,
        effect_measure="SMD", model_name="test", output_path=str(tmp_path / "r.html"))
    return open(out, encoding="utf-8").read()


def test_docx_lists_reviewer_entered_studies(tmp_path):
    t = _docx_text([MCCRAE, LAMI, KARLSSON], tmp_path)
    assert "Reviewer-entered data" in t
    assert "entered by a reviewer" in t
    assert "McCrae (2019)" in t and MCCRAE_NOTE in t
    assert "Lami (2018)" in t and "mean_intervention" in t
    assert "Karlsson" not in t          # no override -> not listed


def test_docx_no_section_without_overrides(tmp_path):
    assert "Reviewer-entered data" not in _docx_text([KARLSSON], tmp_path)


def test_html_lists_reviewer_entered_studies(tmp_path):
    h = _html_text([MCCRAE, LAMI, KARLSSON], tmp_path)
    assert "Reviewer-entered data" in h
    assert "entered by a reviewer" in h
    assert "McCrae (2019)" in h and MCCRAE_NOTE in h
    assert "Lami (2018)" in h and "mean_intervention" in h


def test_html_no_section_without_overrides(tmp_path):
    assert "Reviewer-entered data" not in _html_text([KARLSSON], tmp_path)


def test_html_escapes_note(tmp_path):
    row = dict(MCCRAE, override_note="SD <b>check</b> & verify")
    h = _html_text([row], tmp_path)
    assert "SD &lt;b&gt;check&lt;/b&gt; &amp; verify" in h
    assert "<b>check</b>" not in h

    
# --- Session 39 (item 4c): count only entries that changed a value ("old->new").
ANG = {"filename": "ang.pdf",
       "study_metadata": {"first_author": "Ang", "year": 2010},
       "participants": {"n_intervention": 15, "n_control": 13},
       "primary_outcome": {"name": "NFR pain rating"},
       "override_fields": "first_author; exclude_from_meta",
       "override_note": "Not pooled (reviewer decision)."}
KARLSSON_CONFIRMED = {"filename": "karlsson.pdf",
                      "study_metadata": {"first_author": "Karlsson", "year": 2015},
                      "participants": {"n_intervention": 24, "n_control": 24},
                      "primary_outcome": {"name": "Pain"},
                      "override_fields": "n_intervention(confirmed 24); n_control(confirmed 24)"}


def test_html_counts_only_studies_with_changed_values(tmp_path):
    h = _html_text([MCCRAE, LAMI, ANG, KARLSSON_CONFIRMED], tmp_path)
    assert "2 of 4 extracted studies use values entered by a reviewer" in h
    section = h.split("Reviewer-entered data", 1)[1].split("</div>", 1)[0]
    assert "Ang (2010)" not in section
    assert "Karlsson (2015)" in section and "confirmed" in section


def test_html_no_section_for_exclude_only(tmp_path):
    assert "Reviewer-entered data" not in _html_text([ANG, KARLSSON], tmp_path)

def test_docx_counts_only_studies_with_changed_values(tmp_path):
    t = _docx_text([MCCRAE, LAMI, ANG, KARLSSON_CONFIRMED], tmp_path)
    assert "2 of 4 extracted studies use values entered by a reviewer" in t
    assert "Ang (2010):" not in t
    assert "first_author; exclude_from_meta" not in t
    assert "Karlsson (2015)" in t and "confirmed" in t

def test_docx_no_section_for_exclude_only(tmp_path):
    assert "Reviewer-entered data" not in _docx_text([ANG, KARLSSON], tmp_path)
