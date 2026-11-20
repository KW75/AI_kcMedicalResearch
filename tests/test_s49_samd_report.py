"""Session 49 PR F: SaMD report.

Pinned:
- Lab lines are parsed by code (formats from the first real run, values
  only); status HIGH/LOW/normal/unclear/no range comes from the printed
  reference range, never from the AI.
- The answer is checked: an in-range value called abnormal is warned;
  a cited number not in the sources is warned.
- Report in output/samd/<run_id>/: report.md, report.html (opened in the
  browser), report.docx; a .docx failure keeps .md and .html.
- No answer -> no report, no browser.
"""
from datetime import datetime

import pytest

from SOURCE_CODE.pipelines.samd import cli, report

HDL_ZH = "\u9ad8\u5bc6\u5ea6\u81bd\u56fa\u9187"
A1C_ZH = "\u7cd6\u5316\u8840\u8272\u7d20"
NOW = datetime(2026, 11, 20, 17, 0, 0)
RUN = "20261120_170000"

LINES = {
    "Hemoglobin     13.7           g/dL         13.5 - 17.3":
        ("13.7", "g/dL", "13.5 - 17.3", "", "normal"),
    "MCV            94.6           fL           80.0 - 96.0":
        ("94.6", "fL", "80.0 - 96.0", "", "normal"),
    "LDH 149 IU/L 135 - 225": ("149", "IU/L", "135 - 225", "", "normal"),
    "Troponin I-hs              <10         ng/L    <34":
        ("<10", "ng/L", "<34", "", "normal"),
    "TSH                          5.77     mIU/L   0.27 - 4.20":
        ("5.77", "mIU/L", "0.27 - 4.20", "", "HIGH"),
    "Creatinine                94        umol/L     62 - 106":
        ("94", "umol/L", "62 - 106", "", "normal"),
    f"HDL Cholesterol {HDL_ZH} 0.93 L mmol/L 1.03 - 1.81":
        ("0.93", "mmol/L", "1.03 - 1.81", "L", "LOW"),
    f"HbA1c {A1C_ZH} 6.1 %": ("6.1", "%", "", "", "no range"),
}


@pytest.mark.parametrize("line", list(LINES))
def test_parse_known_lines(line):
    r = report.parse_line(line)
    assert (r["value"], r["unit"], r["ref"], r["flag"], r["status"]) == LINES[line]


@pytest.mark.parametrize("line", [
    "HDL >=1.81 - - <1.03",
    "Page 1 of 1",
    "Tel: 12345678    Fax: 87654321",
    "Age 70    Gender: F",
    "labs_2022-11.pdf (transcription)",
    "--- page 1 (transcription) ---",
])
def test_not_result_lines(line):
    assert report.parse_line(line) is None


@pytest.mark.parametrize("value, ref, expected", [
    ("34", "<34", "HIGH"), ("33.9", "<34", "normal"), ("<10", "<34", "normal"),
    ("13.5", "13.5 - 17.3", "normal"), ("13.4", "13.5 - 17.3", "LOW"),
    ("<5", "10 - 20", "LOW"), ("<15", "10 - 20", "unclear"),
    (">40", "10 - 20", "HIGH"), ("5", "", "no range"), ("1.0", ">=1.03", "LOW"),
])
def test_status_edges(value, ref, expected):
    assert report.status(value, ref) == expected


def test_names_kept():
    names = [report.parse_line(l)["test"] for l in LINES]
    assert names[0] == "Hemoglobin" and names[3] == "Troponin I-hs"
    assert names[6].startswith("HDL Cholesterol")


def test_parse_results_skips_photos():
    rows = report.parse_results([
        ("labs.pdf", "transcription",
         "Hemoglobin 13.7 g/dL 13.5 - 17.3\nTSH 5.77 mIU/L 0.27 - 4.20"),
        ("rash.jpg", "photo description", "Plaque 3 cm across"),
    ])
    assert [(r["test"], r["status"], r["source"]) for r in rows] == [
        ("Hemoglobin", "normal", "labs.pdf"), ("TSH", "HIGH", "labs.pdf")]


HB = report.parse_results([("labs.pdf", "transcription",
                            "Hemoglobin 13.7 g/dL 13.5 - 17.3\n"
                            "Troponin I-hs <10 ng/L <34")])
CASE = "Hemoglobin 13.7 g/dL 13.5 - 17.3\nTroponin I-hs <10 ng/L <34"


def test_flags_in_range_called_anaemia():
    # Run 20261120_142307, working diagnosis
    w = report.check_answer(HB, "His haemoglobin level is 13.7 g/dL (reference "
                            "range: 13.5-17.3 g/dL), indicating mild anaemia.", CASE)
    assert len(w) == 1 and "Hemoglobin 13.7" in w[0]


def test_normal_sentence_not_flagged():
    # Run 20261120_152500
    assert report.check_answer(HB, "The haemoglobin of 13.7 g/dL is within the "
                               "normal range, so there is no anaemia.", CASE) == []


def test_flags_elevated_troponin():
    w = report.check_answer(HB, "Elevated troponin I-hs (<10 ng/L) rules out "
                            "acute myocardial infarction.", CASE)
    assert len(w) == 1 and "Troponin I-hs <10" in w[0]


def test_numbers_not_in_sources():
    w = report.check_answer([], "Hb 13.7 g/dL; ferritin 8 ug/L; repeat in 5 "
                            "years.", CASE)
    assert len(w) == 1 and "8 ug/L" in w[0]
    assert "13.7" not in w[0] and "5 years" not in w[0]


ROWS = [
    {"test": "Hemoglobin", "value": "13.7", "unit": "g/dL", "ref": "13.5 - 17.3",
     "flag": "", "status": "normal", "source": "labs.pdf"},
    {"test": "TSH", "value": "5.77", "unit": "mIU/L", "ref": "0.27 - 4.20",
     "flag": "", "status": "HIGH", "source": "labs.pdf"},
]


def _md(warnings=()):
    return report.build_markdown(
        run_id=RUN, intended_use="Intended use: X.", doctor_text="62M tired",
        rows=ROWS, warnings=list(warnings),
        answer="## Working diagnosis\nSubclinical hypothyroidism.",
        sources=[("labs.pdf", "transcription")], ai_line="AI: Ollama m (local).")


def test_markdown_order_and_footnote():
    md = _md(["Check this."])
    assert md.index("Intended use: X.") < md.index("## Checks")
    assert md.index("| TSH") < md.index("| Hemoglobin")
    assert "**HIGH**" in md and "not by the AI" in md
    assert "- WARNING: Check this." in md
    assert "### Working diagnosis" in md
    for s in ("62M tired", "labs.pdf (transcription)", "AI: Ollama m (local)."):
        assert s in md


def test_markdown_no_warnings():
    assert "- No warnings." in _md()


def test_html_escapes_and_structure():
    md = "# T\n\n## Red flags\n\n- **HIGH** <script>x</script>\n\n| A | B |\n|---|---|\n| 1 | 2 |\n"
    page = report.md_to_html(md, "SaMD report")
    assert '<meta charset="utf-8">' in page
    assert "<h2>Red flags</h2>" in page and "<strong>HIGH</strong>" in page
    assert "&lt;script&gt;" in page and "<script>" not in page
    assert "<th>A</th>" in page and "<td>2</td>" in page


def test_write_report_three_files(tmp_path):
    import docx
    paths = report.write_report(tmp_path / "out", _md(), title="t", log=lambda m: None)
    for k in ("md", "html", "docx"):
        assert paths[k].exists()
    d = docx.Document(str(paths["docx"]))
    text = "\n".join(p.text for p in d.paragraphs)
    assert "Intended use: X." in text and "Working diagnosis" in text
    assert len(d.tables) == 1 and d.tables[0].cell(1, 0).text == "TSH"


def test_docx_failure_keeps_md_and_html(tmp_path, monkeypatch):
    def boom(path, md):
        raise RuntimeError("disk full")
    monkeypatch.setattr(report, "write_docx", boom)
    msgs = []
    paths = report.write_report(tmp_path, _md(), title="t", log=msgs.append)
    assert paths["docx"] is None and paths["html"].exists() and paths["md"].exists()
    assert "report.docx" in msgs[-1]


def _answers(*items):
    it = iter(items)
    return lambda _p="": next(it)


def _one_image(tmp_path, monkeypatch):
    d = tmp_path / "input" / "samd"
    d.mkdir(parents=True)
    (d / "labs.png").write_bytes(b"x")
    monkeypatch.setattr(cli, "read_pages",
                        lambda p: [{"number": 1, "text": None, "png": b"P"}])


def test_run_writes_report_and_opens_browser(tmp_path, monkeypatch):
    _one_image(tmp_path, monkeypatch)
    replies = iter(["TYPE: TEXT\nHemoglobin 13.7 g/dL 13.5 - 17.3\n"
                    "TSH 5.77 mIU/L 0.27 - 4.20",
                    "\n".join(f"{h}\nx" for h in cli.HEADINGS)
                    + "\nHb 13.7 g/dL indicates mild anaemia."])
    monkeypatch.setattr(cli, "choose_call",
                        lambda *a, **k: (lambda prompt, images=None: next(replies)))
    opened = []
    monkeypatch.setattr(cli, "open_browser", lambda p, log=print: opened.append(p))
    lines = []
    res = cli.run(tmp_path, input_fn=_answers("", "62M tired", ""),
                  log=lines.append, now=NOW)
    out = tmp_path / "output" / "samd" / RUN
    for n in ("report.md", "report.html", "report.docx"):
        assert (out / n).exists()
    assert opened == [out / "report.html"] and res["report"] == out / "report.html"
    assert any("Hemoglobin 13.7" in w for w in res["warnings"])
    assert (tmp_path / "reports" / "samd" / RUN / "results.json").exists()
    assert "WARNING" in "\n".join(lines)


def test_failed_answer_writes_no_report(tmp_path, monkeypatch):
    _one_image(tmp_path, monkeypatch)

    def call(prompt, images=None):
        if images:
            return "TYPE: TEXT\nHemoglobin 13.7 g/dL 13.5 - 17.3"
        raise RuntimeError("timeout")
    monkeypatch.setattr(cli, "choose_call", lambda *a, **k: call)
    opened = []
    monkeypatch.setattr(cli, "open_browser", lambda p, log=print: opened.append(p))
    res = cli.run(tmp_path, input_fn=_answers("", "62M", ""), log=lambda m: None, now=NOW)
    assert res["report"] is None and opened == []
    assert not (tmp_path / "output").exists()
