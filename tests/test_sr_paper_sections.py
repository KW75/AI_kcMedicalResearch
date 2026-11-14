"""Session 38: RoB2 reads Methods + Results of the shared paper text,
not the first 6000 characters (HANDOFF Session 37, NEXT item 1).

Session 37 runs 20261110_234448 / 20261111_001942: RoB2 justifications said
"in the abstract/excerpt"; McCrae missing data "not reported" though Figure 1
has 27/30/28. Cause: rob2_tool.py cut the text at MAX_ROB2_CHARS (6000).
Every paper here is built in the test: no PDFs, no AI.
"""
import importlib
import logging

import pytest

LIMIT = 20000
FALLBACK = 6000


@pytest.fixture
def ps():
    try:
        return importlib.import_module("pipelines.sr.src.utils.paper_sections")
    except ModuleNotFoundError as e:
        pytest.fail(f"paper_sections module missing: {e}")


def _body(tag, n):
    """About n characters of lines that all contain tag and are never a heading."""
    line = f"{tag} sentence about the trial and its participants."
    lines, total = [], 0
    while total < n:
        lines.append(line)
        total += len(line) + 1
    return "\n".join(lines)


def _paper(methods_heading="Methods", results_heading="Results",
           methods_n=6000, results_n=6000, abstract=None):
    abstract = abstract or (
        "Abstract\nBackground: chronic pain in women.\n" + _body("abstractbody", 900))
    return "\n".join([
        "--- page 1 ---",
        "Cognitive behavioural therapy for fibromyalgia: a randomised trial",
        abstract,
        "Introduction",
        _body("introbody", 8000),
        "--- page 2 ---",
        methods_heading,
        "Randomisation used sealed opaque envelopes.",
        _body("methodsbody", methods_n),
        results_heading,
        "Completed: 27/30/28 participants.",
        _body("resultsbody", results_n),
        "--- page 3 ---",
        "Discussion",
        _body("discussionbody", 8000),
        "References",
        _body("referencesbody", 8000),
    ])


def _pick(ps, text):
    return ps.rob2_text(text, limit=LIMIT, fallback_chars=FALLBACK)


# 1. Right sections
def test_sends_start_methods_and_results_not_discussion(ps):
    text = _paper()
    assert len(text) > 35000
    out, note = _pick(ps, text)
    assert out.startswith("--- page 1 ---\nCognitive behavioural therapy")
    for want in ("sealed opaque envelopes", "methodsbody", "27/30/28", "resultsbody"):
        assert want in out, want
    for unwanted in ("discussionbody", "referencesbody"):
        assert unwanted not in out, unwanted
    assert "no Methods heading" not in note


# 2. Structured abstract must not replace the full sections
LABEL_ABSTRACT = ("Abstract\nMethods: 60 women were randomised.\n"
                  "Results: pain fell.\nConclusions: CBT helps.")
LINE_ABSTRACT = ("Abstract\nMethods\n60 women were randomised.\n"
                 "Results\npain fell.\nConclusions\nCBT helps.")


@pytest.mark.parametrize("abstract", [LABEL_ABSTRACT, LINE_ABSTRACT],
                         ids=["labels", "own-line-headings"])
def test_structured_abstract_does_not_replace_full_sections(ps, abstract):
    out, _ = _pick(ps, _paper(abstract=abstract))
    assert "sealed opaque envelopes" in out
    assert "27/30/28" in out
    assert "discussionbody" not in out


# 3. Heading variants (Tesseract adds stray dots)
@pytest.mark.parametrize("heading", [
    "METHODS", "Methods", "Method", "Materials and methods",
    "Patients and Methods", "MATERIALS AND METHODS",
    "2. Methods", "2 Methods", "Methods.",
    # Session 38 real paper (Jensen, fMRI): reversed order
    "2. Methods and material", "Methods and materials", "METHODS AND MATERIALS"])
def test_methods_heading_variants(ps, heading):
    out, note = _pick(ps, _paper(methods_heading=heading))
    assert "sealed opaque envelopes" in out
    assert "27/30/28" in out
    assert "no Methods heading" not in note


@pytest.mark.parametrize("heading", ["RESULTS", "Results", "3. Results", "Results."])
def test_results_heading_variants(ps, heading):
    out, note = _pick(ps, _paper(results_heading=heading))
    assert "27/30/28" in out and "resultsbody" in out
    assert "discussionbody" not in out
    assert "no Results heading" not in note


# 4. Fallback: today's behaviour, never a failure
def test_no_methods_heading_falls_back_to_first_chars(ps):
    text = _body("nobody", 10000)
    out, note = _pick(ps, text)
    assert out == text[:FALLBACK] + "\n...[truncated]"
    assert "no Methods heading" in note


def test_short_text_without_heading_is_unchanged(ps):
    out, _ = _pick(ps, "short paper text")
    assert out == "short paper text"


def test_methods_without_results_heading(ps):
    out, note = _pick(ps, _paper(results_heading="Outcome data"))
    assert "sealed opaque envelopes" in out
    assert "27/30/28" in out          # inside the Methods span
    assert "discussionbody" not in out
    assert "no Results heading" in note


# 5. Limit
def test_long_sections_stay_within_limit_and_keep_both(ps):
    out, _ = _pick(ps, _paper(methods_n=30000, results_n=30000))
    assert len(out) <= LIMIT + 200
    assert "sealed opaque envelopes" in out
    assert "27/30/28" in out


def test_short_methods_leaves_space_for_results(ps):
    out, _ = _pick(ps, _paper(methods_n=2000, results_n=30000))
    assert len(out) <= LIMIT + 200
    # half-and-half without sharing would give about 1500 + 2000 + 9250
    assert len(out) > 15000


# 6. Wiring in rob2_tool.py
@pytest.fixture
def rob2(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-key")
    from pipelines.sr.src.screening.rob2_tool import RoB2Assessor
    return RoB2Assessor(model="m", provider="qwen")


def _capture(assessor):
    sent = []
    assessor._call_with_text = (lambda text, prompt: sent.append(text)
                                or '{"domains": {}, "overall_judgment": "Low"}')
    return sent


def test_rob2_sends_methods_and_results_of_shared_text(rob2):
    sent = _capture(rob2)
    rob2.assess_by_pdf_path("missing.pdf", "a.pdf", paper_text=_paper())
    assert len(sent) == 1
    assert "sealed opaque envelopes" in sent[0]
    assert "27/30/28" in sent[0]
    assert "discussionbody" not in sent[0]


def test_rob2_logs_when_no_methods_heading(rob2, caplog):
    sent = _capture(rob2)
    with caplog.at_level(logging.INFO):
        rob2.assess_by_pdf_path("missing.pdf", "a.pdf",
                                paper_text=_body("nobody", 10000))
    assert sent[0].endswith("...[truncated]")
    assert any("[ROB2 TEXT]" in r.getMessage() and "no Methods heading" in r.getMessage()
               for r in caplog.records)


# 7. Default limit fits the largest real paper (Session 38 check)
def test_default_section_limit_fits_largest_real_paper():
    """McCrae (zsy234): start 1500 + Methods 26298 + Results 20181 = 47979.
    At 20000 the half split dropped every 'drop' mention and the
    intention-to-treat text (Karlsson, Lami, McCrae)."""
    from pipelines.sr.src.screening import rob2_tool
    assert rob2_tool.MAX_ROB2_SECTION_CHARS >= 48000

# 8. Registration lines outside the sent sections (Session 38 rerun
#    20261111_081840: Ang NCT00965601 and Karlsson NCT01004458 no longer seen)
def _with(text, before, insert):
    assert before in text
    return text.replace(before, insert + before, 1)


def test_registration_line_before_methods_is_sent(ps):
    base, _ = _pick(ps, _paper())
    text = _with(_paper(), "--- page 2 ---",
                 "ClinicalTrials.gov identifier: NCT00965601.\n")
    out, note = _pick(ps, text)
    assert "NCT00965601" in out
    assert len(out) < len(base) + 200      # the line only, not the Introduction
    assert "registration" in note


def test_registration_in_end_matter_and_letter_o_are_sent(ps):
    text = _with(_paper(), "References\n",
                 "The trial is registered with Clinicaltrials.gov:\nNCTO1004458.\n")
    out, _ = _pick(ps, text)
    assert "registered with Clinicaltrials.gov:" in out
    assert "NCTO1004458" in out
    assert "referencesbody" not in out


def test_registered_without_registry_is_not_sent(ps):
    text = _with(_paper(), "References\n",
                 "Scored by a registered polysomnographic technologist.\n")
    out, _ = _pick(ps, text)
    assert "polysomnographic technologist" not in out


def test_registration_already_in_methods_is_not_repeated(ps):
    text = _with(_paper(), "Results\n",
                 "This trial is registered at www.clinicaltrials.gov (NCT02001077).\n")
    out, _ = _pick(ps, text)
    assert out.count("NCT02001077") == 1
