"""OCR output files (Session 35 design).

Records: summary on top, full OCR text below, one heading per page saying how
it was read. OCR text is written verbatim: no markdown -> Word list or heading
conversion, so "3) BP 140/90" is never renumbered. Every file names the model
and says the content is AI-produced. Files go to tmp_path only.
"""
from datetime import datetime

import docx
import pytest

from pipelines.ocr import output

NOW = datetime(2026, 11, 7, 14, 30)
PAGES = [
    {"page": 1, "text": "Typed page one.", "method": "text"},
    {"page": 2, "text": "3) BP 140/90\n- not a bullet\n# not a heading",
     "method": "vision"},
]


def _docx_paragraphs(path):
    return [(p.text, p.style.name) for p in docx.Document(str(path)).paragraphs]


def test_header_from_typed_name():
    assert output.make_header("Cardio lectures", NOW) == "Cardio_lectures_2026-11-07"


def test_header_default_when_blank():
    assert output.make_header("", NOW) == "OCR_2026-11-07_1430"
    assert output.make_header("   ", NOW) == "OCR_2026-11-07_1430"


def test_header_drops_unsafe_characters():
    assert output.make_header("PT/01:a", NOW) == "PT01a_2026-11-07"
    assert output.make_header("///", NOW) == "OCR_2026-11-07_1430"


def test_record_paths_keep_extension_so_names_cannot_clash(tmp_path):
    header = "PT0123_2026-11-07"
    a = output.write_record(tmp_path, header, "scan01.pdf", "S", PAGES, "gemma4:e4b")
    b = output.write_record(tmp_path, header, "scan01.png", "S", PAGES, "gemma4:e4b")
    assert a[0] == tmp_path / "records" / "PT0123_2026-11-07_scan01_pdf.docx"
    assert a[1] == tmp_path / "records" / "PT0123_2026-11-07_scan01_pdf.md"
    assert b[0].name == "PT0123_2026-11-07_scan01_png.docx"
    assert all(p.exists() for p in (*a, *b))


def test_record_md_has_summary_then_full_text_verbatim(tmp_path):
    _, md = output.write_record(tmp_path, "H", "scan.pdf", "Short summary.",
                                PAGES, "gemma4:e4b")
    text = md.read_text(encoding="utf-8")
    assert text.index("## Summary") < text.index("Short summary.") < text.index("## Full text")
    assert "### Page 1 (text layer)" in text
    assert "### Page 2 (AI read)" in text
    assert "3) BP 140/90\n- not a bullet\n# not a heading" in text


def test_record_docx_keeps_ocr_lines_as_plain_text(tmp_path):
    path, _ = output.write_record(tmp_path, "H", "scan.pdf", "Short summary.",
                                  PAGES, "gemma4:e4b")
    paras = _docx_paragraphs(path)
    for line in ("3) BP 140/90", "- not a bullet", "# not a heading"):
        assert (line, "Normal") in paras
    assert ("Page 2 (AI read)", "Heading 3") in paras


def test_every_file_names_the_model_and_says_ai(tmp_path):
    rec = output.write_record(tmp_path, "H", "scan.pdf", "S", PAGES, "gemma4:e4b")
    summ = output.write_summary(tmp_path, "H", "SYNOPSIS", "All files.", "gemma4:e4b")
    for md in (rec[1], summ[1]):
        note = md.read_text(encoding="utf-8")
        assert "gemma4:e4b" in note and "AI" in note
    for path in (rec[0], summ[0]):
        assert any("gemma4:e4b" in t for t, _ in _docx_paragraphs(path))


def test_summary_and_synopsis_file_names(tmp_path):
    s = output.write_summary(tmp_path, "H", "SUMMARY", "One file.", "m")
    y = output.write_summary(tmp_path, "H", "SYNOPSIS", "All files.", "m")
    assert s[0] == tmp_path / "H_SUMMARY.docx" and s[1] == tmp_path / "H_SUMMARY.md"
    assert y[0] == tmp_path / "H_SYNOPSIS.docx"


def test_summary_kind_must_be_known(tmp_path):
    with pytest.raises(ValueError):
        output.write_summary(tmp_path, "H", "REPORT", "x", "m")

def test_control_characters_do_not_break_the_docx(tmp_path):
    import docx
    pages = [{"page": 1, "text": "BP 140/90\x00 mm\x0bHg\x1f ok", "method": "text"}]
    output.write_record(tmp_path, "H", "a.pdf", "sum\x07mary", pages, "m")
    docx_path = next((tmp_path / "records").glob("*.docx"))
    text = "\n".join(p.text for p in docx.Document(str(docx_path)).paragraphs)
    assert "BP 140/90 mmHg ok" in text
    assert "summary" in text



# --- Next work item 1: LaTeX in AI-written summaries (Session 36) ----------
# The prompts ask for plain symbols, but models still write $\pm$ etc.
# strip_latex() turns known commands into Unicode in code. It leaves money
# ($5), [?] marks and unknown commands exactly as they are.

@pytest.mark.parametrize("raw, want", [
    (r"mean $\pm$ SD", "mean ± SD"),
    (r"age $\geq$ 18 and $\leq$ 65", "age ≥ 18 and ≤ 65"),
    (r"week 6 $\rightarrow$ week 12", "week 6 → week 12"),
    (r"2 $\times$ 3", "2 × 3"),
    (r"$-20.2 \pm 23.9$", "-20.2 ± 23.9"),
    (r"37$^\circ$C", "37°C"),
    (r"50\% reduction", "50% reduction"),
    (r"P $\le$ 0.05, $\leq$ and $\leftarrow$", "P ≤ 0.05, ≤ and ←"),
    (r"bare \pm in text", "bare ± in text"),
])
def test_strip_latex_gives_plain_symbols(raw, want):
    assert output.strip_latex(raw) == want


@pytest.mark.parametrize("raw", [
    "costs $5 and $10",
    "P [?] 0.01 and [?]10.8",
    "no latex here",
    r"$\unknowncmd$ stays",
    "",
])
def test_strip_latex_leaves_other_text_alone(raw):
    assert output.strip_latex(raw) == raw


def test_strip_latex_none_stays_none():
    assert output.strip_latex(None) is None

def test_summary_files_have_no_latex(tmp_path):
    text = (r"## Results" "\n"
            r"- Pain $-20.2 \pm 23.9$ vs $-14.9 \pm 16.4$" "\n"
            r"- P [?] 0.01")
    docx_path, md_path = output.write_summary(tmp_path, "H", "SUMMARY", text,
                                              "gemma4:e4b")
    md = md_path.read_text(encoding="utf-8")
    assert "$" not in md and r"\pm" not in md
    assert "-20.2 ± 23.9" in md and "P [?] 0.01" in md
    paras = " ".join(t for t, _ in _docx_paragraphs(docx_path))
    assert r"\pm" not in paras and "-20.2 ± 23.9" in paras

def test_record_summary_has_no_latex_but_page_text_is_verbatim(tmp_path):
    pages = [{"page": 1, "text": r"Raw $\pm$ stays as read", "method": "text"}]
    docx_path, md_path = output.write_record(
        tmp_path, "H", "a.pdf", r"Pain $-20.2 \pm 23.9$", pages, "gemma4:e4b")
    md = md_path.read_text(encoding="utf-8")
    assert "Pain -20.2 ± 23.9" in md
    assert r"Raw $\pm$ stays as read" in md
    paras = [t for t, _ in _docx_paragraphs(docx_path)]
    assert "Pain -20.2 ± 23.9" in paras
    assert r"Raw $\pm$ stays as read" in paras


# Statistics in $...$ with no backslash (Ang SUMMARY: "($P = 0.8$)").
# Only "letter, comparison, number" loses its $; money stays (Session 36).
@pytest.mark.parametrize("raw, want", [
    ("($P = 0.8$)", "(P = 0.8)"),
    ("adjusted $P = 0.005$", "adjusted P = 0.005"),
    ("$P < 0.01$", "P < 0.01"),
    ("$n = 15$ per arm", "n = 15 per arm"),
    ("$r = -0.45$", "r = -0.45"),
])
def test_strip_latex_plain_statistic_in_dollars(raw, want):
    assert output.strip_latex(raw) == want


@pytest.mark.parametrize("raw", [
    "from $5 < $10",
    "costs $5 and $10",
    "$5 = $5",
])
def test_strip_latex_money_with_comparison_stays(raw):
    assert output.strip_latex(raw) == raw

# --- Session 36: AI summary Markdown becomes Word formatting; page text stays plain
MD_SUMMARY = (
    "## Key Results\n"
    "*   **Baseline to Week 6:**\n"
    "    *   CBT group: 4.4 ± 13.7 mA\n"
    "- UC group: −10.2 ± 9.9 mA\n"
    "Plain closing line."
)


def _paras(path):
    import docx
    return docx.Document(str(path)).paragraphs


def test_summary_docx_turns_markdown_into_word_formatting(tmp_path):
    docx_path, md_path = output.write_summary(tmp_path, "H", "SUMMARY", MD_SUMMARY, "m")
    paras = {p.text: p for p in _paras(docx_path)}
    assert paras["Key Results"].style.name.startswith("Heading")
    assert paras["Baseline to Week 6:"].style.name == "List Bullet"
    assert any(r.bold for r in paras["Baseline to Week 6:"].runs)
    assert paras["CBT group: 4.4 ± 13.7 mA"].style.name == "List Bullet 2"
    assert paras["UC group: −10.2 ± 9.9 mA"].style.name == "List Bullet"
    assert paras["Plain closing line."].style.name == "Normal"
    assert not any("*" in t or t.startswith("#") for t in paras)
    # the .md keeps the Markdown as the model wrote it
    assert "**Baseline to Week 6:**" in md_path.read_text(encoding="utf-8")


def test_record_docx_summary_formatted_but_page_text_stays_plain(tmp_path):
    pages = [{**PAGES[0], "text": "* Values are the mean ± SD\n- 0.3 not a bullet"}]
    docx_path, _ = output.write_record(tmp_path, "H", "a.pdf", MD_SUMMARY, pages, "m")
    paras = {p.text: p for p in _paras(docx_path)}
    assert paras["Baseline to Week 6:"].style.name == "List Bullet"
    assert paras["* Values are the mean ± SD"].style.name == "Normal"
    assert paras["- 0.3 not a bullet"].style.name == "Normal"
