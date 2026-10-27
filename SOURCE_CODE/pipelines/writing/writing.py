"""
writing.py  - Writing Mode engine (v2.6 one-pass, three tracks)
Tracks:
  topic    - newspaper editorial / opinion, default 800 words
  article  - medical research (journal) article, default 3500 words
  report   - structured abstract / report, default 500 words
Main flow: run_one_pass - one AI call per input -> document + review.
Legacy (kept until cleanup): run_writer (Writer - Editor - QA), run_editor, run_qa.
"""

import sys
import threading
import datetime
from pathlib import Path
from typing import Callable

# Add SOURCE_CODE to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SOURCE_CODE_DIR = PROJECT_ROOT / "SOURCE_CODE"
sys.path.insert(0, str(SOURCE_CODE_DIR))

from utils.path_utils import PATH_MANAGER, get_input_dir, get_output_dir
from utils.document_reader import DocumentReader
from utils.rag import RAGUtils
import time_limits

try:
    from docx import Document
    from docx.shared import Pt
    _DOCX_AVAILABLE = True
except ImportError:
    _DOCX_AVAILABLE = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TRACK_TOPIC   = "topic"
TRACK_ARTICLE = "article"
TRACK_REPORT  = "report"

DEFAULT_WORDS = {
    TRACK_TOPIC:   800,
    TRACK_ARTICLE: 3500,
    TRACK_REPORT:  500,
}

# What each track is called inside the prompt. A missing track raises an
# error instead of silently being treated as a journal article.
_TRACK_LABELS = {
    TRACK_TOPIC:   "newspaper editorial / opinion piece",
    TRACK_ARTICLE: "medical journal article",
    TRACK_REPORT:  "structured abstract / report",
}

DISCLOSURE = (
    "AI Involvement Disclosure: This document was produced with the assistance "
    "of an AI language model. All factual claims should be independently verified "
    "before clinical or public use."
)

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------
def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent.parent


def _ts() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def _paths(root: Path) -> dict:
    return {
        "doc_root": PROJECT_ROOT / "docs"    / "writing",
        "input":    PROJECT_ROOT / "input"   / "writing",
        "output":   PROJECT_ROOT / "output"  / "writing",
        "reports":  PROJECT_ROOT / "reports" / "writing",
    }


def _track_doc_path(root: Path, track: str) -> Path:
    return SOURCE_CODE_DIR / "docs" / "modes" / "writing.md" / track


# ---------------------------------------------------------------------------
# Spinner
# ---------------------------------------------------------------------------
class _Spinner:
    def __init__(self, message: str = "Processing"):
        self._message = message
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._spin, daemon=True)

    def _spin(self) -> None:
        frames = ["|", "/", "-", "\\"]
        idx = 0
        while not self._stop_event.is_set():
            sys.stdout.write(f"\r  {frames[idx % len(frames)]}  {self._message}... ")
            sys.stdout.flush()
            self._stop_event.wait(0.15)
            idx += 1
        sys.stdout.write(f"\r  OK  {self._message} -- done.          \n")
        sys.stdout.flush()

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, *_):
        self._stop_event.set()
        self._thread.join()


# ---------------------------------------------------------------------------
# LLM wrapper
# ---------------------------------------------------------------------------
def _call_llm(
    system_prompt: str,
    user_prompt: str,
    call_llm_fn: Callable,
    spinner_message: str = "LLM processing",
) -> str:
    result_holder: list = []
    error_holder: list  = []

    def _run() -> None:
        try:
            result_holder.append(
                call_llm_fn(system_prompt=system_prompt, user_prompt=user_prompt)
            )
        except Exception as exc:
            error_holder.append(exc)

    limit = time_limits.get_limit()
    with _Spinner(spinner_message):
        t = threading.Thread(target=_run, daemon=True)
        t.start()
        finished = time_limits.wait_for(t, limit)  # v2.5: --time-limit 15/30/60/none

    if not finished:
        return f"[ERROR] LLM call timed out after {time_limits.describe(limit)}."
    if error_holder:
        return f"[ERROR] LLM call failed: {error_holder[0]}"
    if not result_holder:
        return "[ERROR] LLM returned no response."
    return result_holder[0]


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------
def _load_guidelines(track_doc_path: Path, shared_doc_path: Path) -> str:
    """
    Load all .md files from the track subfolder plus project-brief.md
    from the shared root if present.
    """
    parts = []

    # Shared root: project-brief.md only (if still at root)
    brief = shared_doc_path / "project-brief.md"
    if brief.exists():
        parts.append(f"### project-brief.md\n{brief.read_text(encoding='utf-8')}")

    # Track-specific docs
    if track_doc_path.exists():
        for f in sorted(track_doc_path.glob("*.md")):
            parts.append(f"### {f.name}\n{f.read_text(encoding='utf-8')}")

    return "\n\n".join(parts)


# File types Writing mode can read from input/writing/
_INPUT_EXTENSIONS = {".md", ".txt", ".docx", ".html", ".tex", ".rst", ".pdf"}


def list_input_names(input_dir: Path) -> list:
    """Names of files in input_dir that Writing mode would read, sorted.
    Does not open the files (fast; used by the menu to ask the user).
    """
    if not input_dir.exists():
        return []
    return [
        f.name for f in sorted(input_dir.iterdir())
        if f.is_file() and f.suffix.lower() in _INPUT_EXTENSIONS
    ]


def _load_input_files(input_dir: Path) -> list:
    """Load all supported files from input_dir.
    Returns list of (stem, content, suffix) tuples.
    """
    extensions = _INPUT_EXTENSIONS
    results: list = []
    if not input_dir.exists():
        return results
    for f in sorted(input_dir.iterdir()):
        if not f.is_file() or f.suffix.lower() not in extensions:
            continue
        suffix = f.suffix.lower()
        stem   = f.stem
        if suffix == ".docx":
            try:
                doc = Document(str(f))
                content = "\n".join(p.text for p in doc.paragraphs)
            except Exception:
                content = f"[Could not read {f.name}]"
        elif suffix == ".pdf":
            try:
                import fitz
                pdf = fitz.open(str(f))
                content = "\n\n".join(page.get_text() for page in pdf)
                pdf.close()
                if not content.strip():
                    content = f"[PDF {f.name} contained no extractable text]"
            except ImportError:
                content = "[PDF reading requires PyMuPDF: pip install pymupdf]"
            except Exception as exc:
                content = f"[Could not read PDF {f.name}: {exc}]"
        else:
            content = f.read_text(encoding="utf-8", errors="replace")
        results.append((stem, content, suffix))
    return results


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _add_inline_runs(paragraph, text: str) -> None:
    import re
    pattern = re.compile(r"(\*\*(.+?)\*\*|\*(.+?)\*|([^*]+))")
    for match in pattern.finditer(text):
        if match.group(2):
            paragraph.add_run(match.group(2)).bold = True
        elif match.group(3):
            paragraph.add_run(match.group(3)).italic = True
        elif match.group(4):
            paragraph.add_run(match.group(4))


def _write_docx(path: Path, content: str, title: str = "") -> None:
    if not _DOCX_AVAILABLE:
        print("  [WARN] python-docx not available -- skipping .docx export.")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = Document()
    if title:
        doc.add_heading(title, level=0)
    for line in content.splitlines():
        s = line.rstrip()
        if s.startswith("#### "):
            doc.add_heading(s[5:], level=4)
        elif s.startswith("### "):
            doc.add_heading(s[4:], level=3)
        elif s.startswith("## "):
            doc.add_heading(s[3:], level=2)
        elif s.startswith("# "):
            doc.add_heading(s[2:], level=1)
        elif s.startswith("- ") or s.startswith("* "):
            doc.add_paragraph(s[2:], style="List Bullet")
        elif len(s) > 2 and s[0].isdigit() and s[1] in ".)":
            doc.add_paragraph(s[2:].strip(), style="List Number")
        elif s.startswith("---"):
            doc.add_paragraph("")
        else:
            _add_inline_runs(doc.add_paragraph(), s)
    disc = doc.add_paragraph()
    run  = disc.add_run(DISCLOSURE)
    run.italic = True
    run.font.size = Pt(9)
    doc.save(str(path))
    print(f"  [DOCX] {path.name}")


def _strip_fences(text: str) -> str:
    import re
    text = re.sub(r"^```[a-zA-Z]*\n", "", text.strip())
    text = re.sub(r"\n```$", "", text.strip())
    return text.strip()

# Markers that indicate the LLM has started copying guideline boilerplate
_BOILERPLATE_MARKERS = [
    "## QA Checklist",
    "## Checklist Before Submission",
    "## Footnotes",
    "## Language and Style",
    "## Accuracy and Ethics",
    "## Supporting Points\n\n1.",  # only if repeated verbatim
    "[ ] Opening sentence",
    "[ ] Single clear position",
    "[ ] Plain English",
]


def _strip_boilerplate(text: str) -> str:
    """
    Remove guideline boilerplate that the LLM copied into the document output.
    Truncates at the first occurrence of any known boundary marker.
    """
    for marker in _BOILERPLATE_MARKERS:
        idx = text.find(marker)
        if idx != -1:
            text = text[:idx].rstrip()
            break
    return text


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------
_WRITER_PERSONA = {
    TRACK_TOPIC: (
        "You are a senior newspaper columnist and editorial writer with 20 years of "
        "experience writing for national broadsheets. You write with authority, clarity, "
        "and wit. You take clear positions, use plain English, and never hide behind "
        "jargon. Your pieces have a strong hook, a clear argument, and a memorable close."
    ),
    TRACK_ARTICLE: (
        "You are an experienced medical academic writer and researcher. You produce "
        "rigorous, clearly structured journal articles following IMRAD format. You cite "
        "evidence precisely, report effect sizes and confidence intervals, name study "
        "designs correctly, and write in formal academic prose suitable for peer review."
    ),
    TRACK_REPORT: (
        "You are a medical report writer who produces clear, factual, structured "
        "abstracts and reports. You state the purpose, sources or methods, key "
        "findings and conclusions in a neutral tone, use headings where helpful, and "
        "never add opinion, persuasion, or claims not supported by the input or the "
        "instructions."
    ),
}

_EDITOR_PERSONA = {
    TRACK_TOPIC: (
        "You are a senior newspaper and magazine editor. You sharpen arguments, improve "
        "sentence rhythm, cut padding, strengthen hooks, and ensure every paragraph "
        "earns its place. You preserve the writer's voice while making the piece tighter, "
        "clearer, and more engaging. You apply newspaper editorial standards rigorously."
    ),
    TRACK_ARTICLE: (
        "You are a medical journal editor and peer reviewer with expertise across clinical "
        "medicine and research methodology. You check structure (IMRAD), verify that "
        "claims are supported by cited evidence, ensure statistical reporting is complete "
        "(effect sizes, CIs, p-values), flag unsupported assertions, and improve academic "
        "prose without altering the scientific content."
    ),
    TRACK_REPORT: (
        "You are a medical report editor. You check that the abstract or report is "
        "accurate, concise and logically structured (for example Background, Methods, "
        "Results, Conclusions), remove opinion and unsupported statements, tighten "
        "wording, keep terminology consistent, and keep within the word count without "
        "changing the factual content."
    ),
}

_QA_PERSONA = {
    TRACK_TOPIC: (
        "You are a quality assurance reviewer for editorial and opinion writing. You "
        "review documents against the editorial QA checklist: hook quality, argument "
        "clarity, logical flow, plain language, word count, accuracy, and ethics. "
        "Produce a structured QA report with PASS items, FAIL items with specific "
        "references, and a RECOMMENDATION: APPROVE / REVISE MINOR / REVISE MAJOR."
    ),
    TRACK_ARTICLE: (
        "You are a quality assurance reviewer for medical journal articles. You "
        "systematically review the document against the medical article QA checklist: "
        "IMRAD structure, citation completeness, statistical reporting, word count, "
        "ethical compliance, and formatting. Produce a structured QA report with "
        "PASS items, FAIL items with specific section references, and a "
        "RECOMMENDATION: APPROVE / REVISE MINOR / REVISE MAJOR."
    ),
    TRACK_REPORT: (
        "You are a quality assurance reviewer for medical abstracts and reports. You "
        "review the document for structure, factual accuracy against the source, "
        "neutral tone, completeness of key findings, clarity, and word count. "
        "Produce a structured QA report with PASS items, FAIL items with specific "
        "references, and a RECOMMENDATION: APPROVE / REVISE MINOR / REVISE MAJOR."
    ),
}


# ---------------------------------------------------------------------------
# One-pass Writing mode: split the single AI answer into document + review
# ---------------------------------------------------------------------------

REVIEW_MARKER = "=== REVIEW ==="
REVIEW_MISSING = (
    "Review missing: the model did not separate the review from the document."
)


# Headings a model may write when it echoes the stages instead of using the
# marker. Only headings (lines starting with #) count, so ordinary text such
# as "## Review of the literature" never triggers a split.
_STAGE_HEADING = r"^\s*#{1,6}\s*stage\s*\d"
_EDITOR_STAGE_HEADING = r"^\s*#{1,6}\s*stage\s*2\b"
_REVIEW_STAGE_HEADING = r"^\s*#{1,6}\s*(stage\s*3\b|(reviewer\s+)?qa\s+report\b)"


def _clean_staged_document(document: str) -> str:
    """If the model wrote a draft and a polished version under 'Stage'
    headings, keep only the polished (Stage 2) text, and drop any leftover
    stage heading lines."""
    import re
    lines = document.splitlines()
    for i, line in enumerate(lines):
        if re.match(_EDITOR_STAGE_HEADING, line, re.I):
            lines = lines[i + 1:]
            break
    lines = [l for l in lines if not re.match(_STAGE_HEADING, l, re.I)]
    return "\n".join(lines).strip()


def _split_document_and_review(text: str) -> tuple[str, str]:
    """Cut the AI answer into (document, review).

    1. The REVIEW_MARKER line wins (on a line of its own, spaces allowed).
    2. Fallback: a 'Stage 3' or 'QA Report' heading starts the review.
    3. Otherwise no text is lost: the document keeps the text and the
       review says the review is missing.
    In cases 1 and 2, a duplicated draft under 'Stage' headings is dropped.
    """
    import re
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == REVIEW_MARKER:
            document = _clean_staged_document("\n".join(lines[:i]))
            review = "\n".join(lines[i + 1:]).strip()
            return document, (review or REVIEW_MISSING)
    for i, line in enumerate(lines):
        if re.match(_REVIEW_STAGE_HEADING, line, re.I):
            document = _clean_staged_document("\n".join(lines[:i]))
            review = "\n".join(lines[i + 1:]).strip()
            if document and review:
                return document, review
            break
    return text, REVIEW_MISSING


def _one_pass_system_prompt(guidelines: str, track: str) -> str:
    """One system prompt for one-pass Writing mode: writer, editor and reviewer.

    Reuses the three existing persona texts for the track, so any later
    improvement to a persona also reaches one-pass mode.
    """
    base = (
        "Work in three steps inside a single answer, silently: write the "
        "document, polish it as its editor, then review the final version.\n"
        "Do NOT write stage headings (such as 'Stage 1', 'Writer Draft' or "
        "'Editor Polish') and do NOT include your draft. Output only the final "
        "polished document, then the review marker line, then the review, "
        "exactly as the Output Format in the user message says.\n\n"
        "### Writer role\n"
        f"{_WRITER_PERSONA[track]}\n\n"
        "### Editor role\n"
        f"{_EDITOR_PERSONA[track]}\n\n"
        "### Reviewer role\n"
        f"{_QA_PERSONA[track]}"
    )

    if guidelines:
        return (
            f"{base}\n\n"
            "## Guidelines\n"
            "Apply the following guidelines throughout your work.\n\n"
            f"{guidelines}"
        )
    return base


def _one_pass_user_prompt(
    direct_instructions: list,
    original_content: str,
    is_scratch: bool,
    track: str,
    word_limit: int,
) -> str:
    """User prompt for one-pass Writing mode: document, marker line, review."""
    track_label = _TRACK_LABELS[track]
    parts = []
    if direct_instructions:
        parts.append("## DIRECT TASK INSTRUCTIONS (highest priority)")
        for inst in direct_instructions:
            parts.append(f"- {inst.lstrip('>').strip()}")
        parts.append("")
    if is_scratch:
        parts.append(
            f"## Task\n"
            f"No input document was provided. Using the instructions above, produce a "
            f"complete {track_label}. Target word count: {word_limit} words. "
            f"Follow all style and editorial guidelines provided."
        )
    else:
        parts.append("## Source Document")
        parts.append(original_content)
        parts.append(
            f"\n## Task\n"
            f"Using the source document above and the instructions, produce a complete "
            f"{track_label}. Target word count: {word_limit} words. "
            f"Follow all style and editorial guidelines."
        )
    parts.append(
        "\n## Output Format\n"
        "1. Write the complete final document in Markdown, already edited and "
        "polished. Do not truncate. Do not include drafts or meta-commentary.\n"
        "2. Then write this line on its own, exactly as shown:\n\n"
        f"{REVIEW_MARKER}\n\n"
        "3. After that line, write a short review of the final document: PASS "
        "items, FAIL items with specific references, and a RECOMMENDATION: "
        "APPROVE / REVISE MINOR / REVISE MAJOR.\n\n"
        f"The target word count ({word_limit} words) applies to the document only, "
        "not to the review."
    )
    return "\n".join(parts)


def _system_prompt(guidelines: str, role: str, track: str) -> str:
    personas = {
        "Writer": _WRITER_PERSONA,
        "Editor": _EDITOR_PERSONA,
        "QA":     _QA_PERSONA,
    }
    base = personas[role][track]
    if guidelines:
        return (
            f"{base}\n\n"
            "## Guidelines\n"
            "Apply the following guidelines throughout your work.\n\n"
            f"{guidelines}"
        )
    return base


def _writer_user_prompt(
    direct_instructions: list,
    original_content: str,
    is_scratch: bool,
    track: str,
    word_limit: int,
) -> str:
    track_label = "newspaper editorial / opinion piece" if track == TRACK_TOPIC \
        else "medical journal article"
    parts = []
    if direct_instructions:
        parts.append("## DIRECT TASK INSTRUCTIONS (highest priority)")
        for inst in direct_instructions:
            parts.append(f"- {inst.lstrip('>').strip()}")
        parts.append("")
    if is_scratch:
        parts.append(
            f"## Task\n"
            f"No input document was provided. Using the instructions above, produce a "
            f"complete {track_label}. Target word count: {word_limit} words. "
            f"Follow all style and editorial guidelines provided."
        )
    else:
        parts.append("## Source Document")
        parts.append(original_content)
        parts.append(
            f"\n## Task\n"
            f"Using the source document above and the instructions, produce a complete "
            f"{track_label}. Target word count: {word_limit} words. "
            f"Follow all style and editorial guidelines."
        )
    parts.append(
        "\n## Output Format\n"
        "Return the complete document in Markdown. Do not truncate. "
        "Do not add meta-commentary -- output only the document itself."
    )
    return "\n".join(parts)


def _editor_user_prompt(
    direct_instructions: list,
    writer_output: str,
    original_content: str,
    track: str,
    word_limit: int,
) -> str:
    track_label = "editorial/opinion piece" if track == TRACK_TOPIC \
        else "medical journal article"
    parts = []
    if direct_instructions:
        parts.append("## DIRECT TASK INSTRUCTIONS (highest priority)")
        for inst in direct_instructions:
            parts.append(f"- {inst.lstrip('>').strip()}")
        parts.append("")
    parts.append("## Original Source (for reference)")
    parts.append(original_content if original_content else "(No original source.)")
    parts.append("")
    parts.append("## Writer Draft (edit this)")
    parts.append(writer_output)
    parts.append(
        f"\n## Task\n"
        f"Edit the Writer Draft above as a {track_label} editor. "
        f"Target word count: {word_limit} words. "
        f"Return the complete edited document in Markdown. Do not truncate."
    )
    return "\n".join(parts)


def _qa_user_prompt(editor_output: str, track: str) -> str:
    track_label = "editorial/opinion" if track == TRACK_TOPIC else "medical journal article"
    return (
        f"## Document to Review ({track_label})\n\n"
        f"{editor_output}\n\n"
        "## Task\n"
        "Review the document against the QA checklist in your guidelines. "
        "Produce a structured report:\n\n"
        "### PASS\nList every checklist item satisfied.\n\n"
        "### FAIL\nList every unsatisfied item with specific section or line reference.\n\n"
        "### RECOMMENDATION\nState: APPROVE / REVISE MINOR / REVISE MAJOR "
        "with a one-paragraph justification."
    )


# ---------------------------------------------------------------------------
# Report helpers
# ---------------------------------------------------------------------------
def _write_report(
    reports_path: Path,
    role: str,
    track: str,
    stem: str,
    timestamp: str,
    content: str,
    extra_meta: str = "",
) -> Path:
    """
    Write a process log to reports/writing/.
    For Writer and Editor: logs word count and first 300 chars as preview.
    For QA: logs the full QA report (it has no output/ deliverable).
    """
    track_upper = track.upper()
    filename    = f"{role.upper()}_{track_upper}_{stem}_{timestamp}.md"
    word_count  = len(content.split())

    header = (
        f"# {role} Process Log ({track_upper}) -- {stem}\n"
        f"**Timestamp:** {timestamp}  \n"
        f"**Track:** {track_upper}  \n"
        f"**Role:** {role}  \n"
        f"**Word count:** {word_count}  \n"
    )
    if extra_meta:
        header += f"{extra_meta}  \n"
    header += "\n---\n\n"

    if role.upper() == "QA":
        # QA has no output/ file  - write full report here
        body = content
    else:
        # Writer and Editor  - write preview only; full doc is in output/writing/
        preview = content[:300].replace("\n", " ").strip()
        if len(content) > 300:
            preview += "..."
        body = (
            f"## Preview (first 300 characters)\n\n"
            f"{preview}\n\n"
            f"---\n\n"
            f"*Full document saved to output/writing/{role.upper()}_{track_upper}_{stem}_{timestamp}.docx*\n"
        )

    path = reports_path / filename
    _write_text(path, header + body)
    print(f"  [REPORT] {filename}")
    return path


def _write_session_summary(
    reports_path: Path,
    timestamp: str,
    track: str,
    subprojects: list,
) -> None:
    filename = f"WRITER_SESSION_{track.upper()}_{timestamp}_SUMMARY.md"
    lines = [
        f"# Writing Session Summary ({track.upper()})\n",
        f"**Timestamp:** {timestamp}  ",
        f"**Track:** {track.upper()}  ",
        f"**Sub-projects:** {len(subprojects)}\n",
        "---\n",
    ]
    for sp in subprojects:
        lines.append(f"## {sp['stem']}")
        lines.append(f"- Writer:  `{sp.get('writer_docx', 'N/A')}`")
        lines.append(f"- Editor:  `{sp.get('editor_docx', 'N/A')}`")
        lines.append(f"- QA:      `{sp.get('qa_report',   'N/A')}`")
        lines.append(f"- Status:  {sp.get('status', 'unknown')}\n")
    _write_text(reports_path / filename, "\n".join(lines))
    print(f"\n  [SESSION] {filename}")


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------
def parse_direct_instructions(raw_text: str) -> list:
    return [
        line.strip()
        for line in raw_text.splitlines()
        if line.strip().startswith(">")
    ]


def _prompt_word_limit(track: str) -> int:
    default = DEFAULT_WORDS[track]
    try:
        raw = input(
            f"  Word limit [{default}]: "
        ).strip()
    except (EOFError, KeyboardInterrupt):
        return default
    if raw.isdigit() and int(raw) > 0:
        return int(raw)
    return default


# ---------------------------------------------------------------------------
# Pipeline: Writer  - Editor  - QA
# ---------------------------------------------------------------------------
def run_writer(
    direct_instructions: list,
    call_llm_fn: Callable,
    track: str = TRACK_TOPIC,
    word_limit: int | None = None,
    verbose: bool = True,
) -> None:
    root      = _project_root()
    paths     = _paths(root)
    timestamp = _ts()

    for p in [paths["input"], paths["output"], paths["reports"]]:
        p.mkdir(parents=True, exist_ok=True)

    if word_limit is None:
        word_limit = DEFAULT_WORDS[track]

    guidelines   = _load_guidelines(paths["doc_root"], paths["doc_root"])
    input_files  = _load_input_files(paths["input"])
    is_scratch   = len(input_files) == 0
    subprojects  = [("new_doc", "", ".md")] if is_scratch else input_files
    session_log  = []

    for stem, original_content, original_suffix in subprojects:
        if verbose:
            print(f"\n{'='*60}")
            print(f"  [WRITER PIPELINE | {track.upper()}] {stem}")
            print(f"  Word limit: {word_limit}")
            print(f"{'='*60}")

        sp = {"stem": stem, "status": "started"}

        # -- WRITER --
        if verbose:
            print(f"\n  [WRITER] Generating draft...")
        writer_out = _call_llm(
            _system_prompt(guidelines, "Writer", track),
            _writer_user_prompt(direct_instructions, original_content,
                                is_scratch, track, word_limit),
            call_llm_fn, "Writer generating",
        )
        writer_out = _strip_boilerplate(_strip_fences(writer_out))


        _write_report(paths["reports"], "WRITER", track, stem, timestamp,
                      writer_out,
                      extra_meta=f"**Source:** {'scratch' if is_scratch else stem}")

        w_md   = paths["output"] / f"WRITER_{track.upper()}_{stem}_{timestamp}.md"
        w_docx = paths["output"] / f"WRITER_{track.upper()}_{stem}_{timestamp}.docx"
        _write_text(w_md, writer_out)
        print(f"  [MD]   {w_md.name}")
        _write_docx(w_docx, writer_out, title=f"Writer Draft ({track.upper()}) -- {stem}")
        sp["writer_docx"] = w_docx.name

        # -- EDITOR --
        if verbose:
            print(f"\n  [EDITOR] Editing draft...")
        editor_out = _call_llm(
            _system_prompt(guidelines, "Editor", track),
            _editor_user_prompt(direct_instructions, writer_out,
                                original_content, track, word_limit),
            call_llm_fn, "Editor revising",
        )
        editor_out = _strip_boilerplate(_strip_fences(editor_out))


        _write_report(paths["reports"], "EDITOR", track, stem, timestamp, editor_out)

        e_md   = paths["output"] / f"EDITOR_{track.upper()}_{stem}_{timestamp}.md"
        e_docx = paths["output"] / f"EDITOR_{track.upper()}_{stem}_{timestamp}.docx"
        _write_text(e_md, editor_out)
        print(f"  [MD]   {e_md.name}")
        _write_docx(e_docx, editor_out,
                    title=f"Edited Document ({track.upper()}) -- {stem}")
        sp["editor_docx"] = e_docx.name

        # -- QA --
        if verbose:
            print(f"\n  [QA] Running quality check...")
        qa_out = _call_llm(
            _system_prompt(guidelines, "QA", track),
            _qa_user_prompt(editor_out, track),
            call_llm_fn, "QA reviewing",
        )
        qa_out = _strip_fences(qa_out)

        qa_path = _write_report(paths["reports"], "QA", track, stem, timestamp, qa_out)
        sp["qa_report"] = qa_path.name
        sp["status"]    = "complete"

        if verbose:
            print(f"\n  Done: {stem}")
            print(f"    Writer:  output/writing/{w_docx.name}")
            print(f"    Editor:  output/writing/{e_docx.name}")
            print(f"    QA:      reports/writing/{qa_path.name}")

        session_log.append(sp)

    _write_session_summary(paths["reports"], timestamp, track, session_log)


# ---------------------------------------------------------------------------
# One-pass Writing mode: one AI call per input -> document + review
# ---------------------------------------------------------------------------

def run_one_pass(
    direct_instructions: list,
    call_llm_fn: Callable,
    track: str = TRACK_TOPIC,
    word_limit: int | None = None,
    verbose: bool = True,
    use_files: bool = True,
) -> None:
    
    """Write (or revise) and review in a single AI call per input.

    With files in input/writing/, each file is revised on its own. With an
    empty folder, or use_files=False, one document is written from the
    instructions alone (files are ignored, never moved or deleted).
    Saves to output/writing/: the document (.docx + .md) and the review
    (_REVIEW.md). Nothing is written to reports/writing/.
    """
    root      = _project_root()
    paths     = _paths(root)
    timestamp = _ts()

    for p in [paths["input"], paths["output"]]:
        p.mkdir(parents=True, exist_ok=True)

    if word_limit is None:
        word_limit = DEFAULT_WORDS[track]

    guidelines  = _load_guidelines(paths["doc_root"], paths["doc_root"])
    input_files = _load_input_files(paths["input"]) if use_files else []
    is_scratch  = len(input_files) == 0
    subprojects = [("new_doc", "", ".md")] if is_scratch else input_files

    for stem, original_content, _suffix in subprojects:
        if verbose:
            print(f"\n{'='*60}")
            print(f"  [WRITING | {track.upper()}] {stem}")
            print(f"  Word limit: {word_limit}")
            print(f"{'='*60}")
            print("\n  Writing, editing and reviewing (one AI call)...")

        answer = _call_llm(
            _one_pass_system_prompt(guidelines, track),
            _one_pass_user_prompt(direct_instructions, original_content,
                                  is_scratch, track, word_limit),
            call_llm_fn, "Writing (one pass)",
        )
        document, review = _split_document_and_review(_strip_fences(answer))
        document = _strip_boilerplate(_strip_fences(document))
        review   = _strip_fences(review)

        base     = f"WRITING_{track.upper()}_{stem}_{timestamp}"
        doc_md   = paths["output"] / f"{base}.md"
        doc_docx = paths["output"] / f"{base}.docx"
        rev_md   = paths["output"] / f"{base}_REVIEW.md"

        _write_text(doc_md, document)
        _write_docx(doc_docx, document, title=f"{track.upper()} -- {stem}")
        _write_text(rev_md, f"# Review ({track.upper()}) -- {stem}\n\n{review}\n")

        if verbose:
            print(f"\n  Done: {stem}")
            print(f"    Document: output/writing/{doc_docx.name}")
            print(f"    Review:   output/writing/{rev_md.name}")


# ---------------------------------------------------------------------------
# Standalone: Editor
# ---------------------------------------------------------------------------
def run_editor(
    direct_instructions: list,
    call_llm_fn: Callable,
    track: str = TRACK_TOPIC,
    word_limit: int | None = None,
    verbose: bool = True,
) -> None:
    root  = _project_root()
    paths = _paths(root)
    timestamp = _ts()

    for p in [paths["input"], paths["output"], paths["reports"]]:
        p.mkdir(parents=True, exist_ok=True)

    if word_limit is None:
        word_limit = DEFAULT_WORDS[track]

    input_files = _load_input_files(paths["input"])
    if not input_files:
        print("  [EDITOR] No files in input/writing/ -- place documents there first.")
        return

    guidelines = _load_guidelines(paths["doc_root"], paths["doc_root"])

    for stem, content, suffix in input_files:
        if verbose:
            print(f"\n  [EDITOR STANDALONE | {track.upper()}] {stem}{suffix}")
        editor_out = _call_llm(
            _system_prompt(guidelines, "Editor", track),
            _editor_user_prompt(direct_instructions, content, content,
                                track, word_limit),
            call_llm_fn, "Editor processing",
        )
        editor_out = _strip_fences(editor_out)

        _write_report(paths["reports"], "EDITOR", track, stem, timestamp, editor_out)

        e_md   = paths["output"] / f"EDITOR_{track.upper()}_{stem}_{timestamp}.md"
        e_docx = paths["output"] / f"EDITOR_{track.upper()}_{stem}_{timestamp}.docx"
        _write_text(e_md, editor_out)
        _write_docx(e_docx, editor_out,
                    title=f"Edited ({track.upper()}) -- {stem}")


# ---------------------------------------------------------------------------
# Standalone: QA
# ---------------------------------------------------------------------------
def run_qa(
    direct_instructions: list,
    call_llm_fn: Callable,
    track: str = TRACK_TOPIC,
    verbose: bool = True,
) -> None:
    root  = _project_root()
    paths = _paths(root)
    timestamp = _ts()

    for p in [paths["input"], paths["reports"]]:
        p.mkdir(parents=True, exist_ok=True)

    input_files = _load_input_files(paths["input"])
    if not input_files:
        print("  [QA] No files in input/writing/ -- place documents there first.")
        return

    guidelines = _load_guidelines(paths["doc_root"], paths["doc_root"])

    for stem, content, suffix in input_files:
        if verbose:
            print(f"\n  [QA STANDALONE | {track.upper()}] {stem}{suffix}")
        qa_out = _call_llm(
            _system_prompt(guidelines, "QA", track),
            _qa_user_prompt(content, track),
            call_llm_fn, "QA reviewing",
        )
        qa_out = _strip_fences(qa_out)
        _write_report(paths["reports"], "QA", track, stem, timestamp, qa_out)



# ---------------------------------------------------------------------------
# Synopsis track: ONE document summarising ALL files in input/writing/
# ---------------------------------------------------------------------------
TRACK_SYNOPSIS = "synopsis"

# Register the Synopsis track in the shared tables defined near the top.
DEFAULT_WORDS[TRACK_SYNOPSIS] = 1500
_TRACK_LABELS[TRACK_SYNOPSIS] = "synopsis of multiple source documents"

_WRITER_PERSONA[TRACK_SYNOPSIS] = (
    "You are a medical writer who synthesises several source documents "
    "(for example research papers, or one patient's clinical records) into "
    "one clear, accurate synopsis. You cover every source, group related "
    "findings, note where sources agree or conflict, keep figures, dates and "
    "medication details exactly as written, and never add facts that are not "
    "in the sources."
)
_EDITOR_PERSONA[TRACK_SYNOPSIS] = (
    "You are a medical editor checking a multi-source synopsis. You make sure "
    "every source is represented, facts, numbers and dates match the sources, "
    "nothing is invented, duplicated points are merged, the structure is "
    "logical, the language is plain and clear, and the word limit is met."
)
_QA_PERSONA[TRACK_SYNOPSIS] = (
    "You are a quality assurance reviewer for multi-document synopses. You "
    "check coverage of every source, factual fidelity (numbers, dates, "
    "medications, findings), absence of fabricated content, handling of "
    "conflicting information, clarity, structure, word count, and "
    "confidentiality (no unnecessary patient identifiers). You produce a "
    "structured QA report with PASS items, FAIL items with specific "
    "references, and a final RECOMMENDATION: APPROVE / REVISE MINOR / "
    "REVISE MAJOR."
)

# Ollama's context (num_ctx, default 32768 tokens) holds prompt + answer.
# With up to 8192 tokens kept for the answer, ~24,500 tokens (~90,000
# characters) are left; 80,000 characters of source text leaves room for
# the guidelines and instructions. Above this, a local run stops.
SYNOPSIS_LOCAL_MAX_CHARS = 80_000

_UNREADABLE_SIGNS = ("could not read", "no extractable text", "requires pymupdf")


def _unreadable_reason(content: str) -> str | None:
    """Return why a loaded file is unusable, or None if it has real text.

    _load_input_files puts a one-line placeholder such as
    "[PDF x.pdf contained no extractable text]" in place of unreadable
    files; those must not be sent to the AI as if they were content.
    """
    stripped = (content or "").strip()
    if not stripped:
        return "empty file"
    if (stripped.startswith("[") and stripped.endswith("]")
            and any(s in stripped.lower() for s in _UNREADABLE_SIGNS)):
        return stripped[1:-1]
    return None


def _synopsis_user_prompt(
    direct_instructions: list,
    sources: list,
    word_limit: int,
) -> str:
    """User prompt for the Synopsis track. sources = [(name, text), ...]."""
    parts = []
    if direct_instructions:
        parts.append("## Direct Task Instructions (highest priority)")
        parts.extend(f"> {str(i).lstrip('> ').strip()}" for i in direct_instructions)
        parts.append("")
    parts.append("## Task")
    parts.append(
        f"Write ONE {_TRACK_LABELS[TRACK_SYNOPSIS]} that summarises ALL "
        f"{len(sources)} source document(s) below together. Cover every "
        "source, group related points, note where sources agree or "
        "conflict, and name the source file for key points. Use only "
        "information from the sources."
    )
    parts.append(f"Target word count: {word_limit} words (the synopsis only).")
    parts.append("")
    for i, (name, text) in enumerate(sources, 1):
        parts.append(f"## Source {i}: {name}")
        parts.append(text.strip())
        parts.append("")
    parts.append("## Output Format")
    parts.append("1. The final polished synopsis in Markdown (no draft, no stage headings).")
    parts.append("2. Then this line on its own:")
    parts.append(REVIEW_MARKER)
    parts.append(
        "3. Then the review: PASS items, FAIL items with specific references, "
        "and a final line RECOMMENDATION: APPROVE / REVISE MINOR / REVISE MAJOR."
    )
    return "\n".join(parts)


def run_synopsis(
    direct_instructions: list,
    call_llm_fn: Callable,
    word_limit: int | None = None,
    verbose: bool = True,
    local: bool = True,
) -> None:
    """Read ALL files in input/writing/ and write ONE synopsis + review
    in a single AI call.

    Unreadable files are skipped with a [SKIP] line. With no files, or no
    readable files, nothing is sent and nothing is written. local=True
    (Ollama) stops if the files are too large for the context window.
    Files are never moved or deleted. Stop/skip messages always print.
    """
    root      = _project_root()
    paths     = _paths(root)
    timestamp = _ts()

    for p in [paths["input"], paths["output"]]:
        p.mkdir(parents=True, exist_ok=True)

    if word_limit is None:
        word_limit = DEFAULT_WORDS[TRACK_SYNOPSIS]

    input_files = _load_input_files(paths["input"])
    if not input_files:
        print("  [SYNOPSIS] Synopsis needs files in input/writing/ -- nothing was written.")
        return

    sources = []
    for stem, content, suffix in input_files:
        reason = _unreadable_reason(content)
        if reason:
            print(f"  [SKIP] {stem}{suffix}: {reason}")
            continue
        sources.append((f"{stem}{suffix}", content))

    if not sources:
        print("  [SYNOPSIS] No readable files in input/writing/ -- nothing was written.")
        return

    total = sum(len(text) for _, text in sources)
    if total > SYNOPSIS_LOCAL_MAX_CHARS:
        if local:
            print(f"  [SYNOPSIS] Files too large for local AI: {total:,} characters "
                  f"(limit {SYNOPSIS_LOCAL_MAX_CHARS:,}). Nothing was written.")
            print("  Remove some files from input/writing/ or change to a cloud provider.")
            return
        print(f"  [SYNOPSIS] Note: {total:,} characters of source text; "
              "large inputs may be slow or costly on cloud providers.")

    guidelines = _load_guidelines(paths["doc_root"], paths["doc_root"])

    if verbose:
        print(f"\n{'='*60}")
        print(f"  [WRITING | SYNOPSIS] {len(sources)} file(s)")
        for name, _ in sources:
            print(f"    - {name}")
        print(f"  Word limit: {word_limit}")
        print(f"{'='*60}")
        print("\n  Writing, editing and reviewing the synopsis (one AI call)...")

    answer = _call_llm(
        _one_pass_system_prompt(guidelines, TRACK_SYNOPSIS),
        _synopsis_user_prompt(direct_instructions, sources, word_limit),
        call_llm_fn, "Synopsis (one pass)",
    )
    document, review = _split_document_and_review(_strip_fences(answer))
    document = _strip_boilerplate(_strip_fences(document))
    review   = _strip_fences(review)

    base     = f"WRITING_SYNOPSIS_{timestamp}"
    doc_md   = paths["output"] / f"{base}.md"
    doc_docx = paths["output"] / f"{base}.docx"
    rev_md   = paths["output"] / f"{base}_REVIEW.md"

    _write_text(doc_md, document)
    _write_docx(doc_docx, document, title=f"SYNOPSIS -- {len(sources)} file(s)")
    _write_text(rev_md, f"# Review (SYNOPSIS) -- {len(sources)} file(s)\n\n{review}\n")

    if verbose:
        print("\n  Done: synopsis")
        print(f"    Document: output/writing/{doc_docx.name}")
        print(f"    Review:   output/writing/{rev_md.name}")
