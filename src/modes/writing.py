"""
writing.py — Writing Mode engine for AI_kcMedicalResearch
Pipeline: Writer → Editor → QA (linear, no feedback loops)
Standalone: Editor, QA
All docs/writing/ .md files loaded as background for every role.
Writer and Editor outputs: .docx (primary) + .md (companion)
QA output: .md report only
"""

import sys
import threading
import datetime
from pathlib import Path
from typing import Optional, Callable

try:
    from docx import Document
    from docx.shared import Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    _DOCX_AVAILABLE = True
except ImportError:
    _DOCX_AVAILABLE = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DISCLOSURE = (
    "AI Involvement Disclosure: This document was produced with the assistance "
    "of an AI language model. All factual claims should be independently verified "
    "before clinical or public use."
)

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------
def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _ts() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def _paths(root: Path) -> dict:
    return {
        "doc":     root / "docs"    / "writing",
        "input":   root / "input"   / "writing",
        "output":  root / "output"  / "writing",
        "reports": root / "reports" / "writing",
    }


# ---------------------------------------------------------------------------
# Spinner (identical pattern to coding.py)
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
        sys.stdout.write(f"\r  ✓  {self._message} — done.          \n")
        sys.stdout.flush()

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, *_):
        self._stop_event.set()
        self._thread.join()


# ---------------------------------------------------------------------------
# LLM wrapper with spinner + 5-minute timeout
# ---------------------------------------------------------------------------
def _call_llm(
    system_prompt: str,
    user_prompt: str,
    call_llm_fn: Callable,
    spinner_message: str = "LLM processing",
) -> str:
    result_holder: list = []
    error_holder: list = []

    def _run() -> None:
        try:
            result_holder.append(
                call_llm_fn(system_prompt=system_prompt, user_prompt=user_prompt)
            )
        except Exception as exc:
            error_holder.append(exc)

    with _Spinner(spinner_message):
        t = threading.Thread(target=_run, daemon=True)
        t.start()
        t.join(timeout=300)

    if t.is_alive():
        return "[ERROR] LLM call timed out after 5 minutes. Check Ollama or switch provider."
    if error_holder:
        return f"[ERROR] LLM call failed: {error_holder[0]}"
    if not result_holder:
        return "[ERROR] LLM returned no response."
    return result_holder[0]


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------
def _load_guidelines(doc_path: Path) -> str:
    """Load all .md files from docs/writing/ as a single string."""
    if not doc_path.exists():
        return ""
    parts = []
    for f in sorted(doc_path.glob("*.md")):
        parts.append(f"### {f.name}\n{f.read_text(encoding='utf-8')}")
    return "\n\n".join(parts)


def _load_input_files(input_path: Path) -> list:
    """
    Return list of (stem, content, suffix) tuples for every file in input/writing/.
    Supported text extensions only.
    """
    extensions = {
        ".md", ".txt", ".docx", ".html", ".tex", ".rst",
        ".csv", ".json", ".xml",
    }
    if not input_path.exists():
        return []
    results = []
    for f in sorted(input_path.iterdir()):
        if f.suffix.lower() not in extensions:
            continue
        if f.suffix.lower() == ".docx":
            try:
                doc = Document(str(f))
                content = "\n".join(p.text for p in doc.paragraphs)
            except Exception:
                content = f"[Could not read {f.name}]"
        else:
            content = f.read_text(encoding="utf-8", errors="replace")
        results.append((f.stem, content, f.suffix.lower()))
    return results


def _write_text_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_docx_file(path: Path, content: str, title: str = "") -> None:
    """Convert markdown-flavoured text to a .docx file using python-docx."""
    if not _DOCX_AVAILABLE:
        print("  [WARN] python-docx not available — skipping .docx export.")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = Document()

    if title:
        doc.add_heading(title, level=0)

    for line in content.splitlines():
        stripped = line.rstrip()

        # Headings
        if stripped.startswith("#### "):
            doc.add_heading(stripped[5:], level=4)
        elif stripped.startswith("### "):
            doc.add_heading(stripped[4:], level=3)
        elif stripped.startswith("## "):
            doc.add_heading(stripped[3:], level=2)
        elif stripped.startswith("# "):
            doc.add_heading(stripped[2:], level=1)

        # Bullet list items
        elif stripped.startswith("- ") or stripped.startswith("* "):
            doc.add_paragraph(stripped[2:], style="List Bullet")

        # Numbered list items
        elif len(stripped) > 2 and stripped[0].isdigit() and stripped[1] in ".)" :
            doc.add_paragraph(stripped[2:].strip(), style="List Number")

        # Horizontal rule — skip
        elif stripped.startswith("---"):
            doc.add_paragraph("")

        # Normal paragraph
        else:
            p = doc.add_paragraph()
            # Inline bold/italic (simple pass)
            _add_inline_runs(p, stripped)

    # Disclosure statement
    doc.add_paragraph("")
    disc = doc.add_paragraph()
    run = disc.add_run(DISCLOSURE)
    run.italic = True
    run.font.size = Pt(9)

    doc.save(str(path))
    print(f"  [DOCX] Saved: {path.name}")


def _add_inline_runs(paragraph, text: str) -> None:
    """Very lightweight bold/italic inline parser for python-docx paragraphs."""
    import re
    # Pattern captures **bold**, *italic*, and plain text segments
    pattern = re.compile(r"(\*\*(.+?)\*\*|\*(.+?)\*|([^*]+))")
    for match in pattern.finditer(text):
        if match.group(2):
            run = paragraph.add_run(match.group(2))
            run.bold = True
        elif match.group(3):
            run = paragraph.add_run(match.group(3))
            run.italic = True
        elif match.group(4):
            paragraph.add_run(match.group(4))


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------
def _system_prompt(guidelines: str, role: str) -> str:
    role_descriptions = {
        "Writer": (
            "You are an expert medical writer. Your task is to produce clear, "
            "accurate, well-structured written content according to the project brief "
            "and style guidelines provided. Always cite sources when making clinical claims. "
            "Produce complete documents — never truncate or use placeholder text."
        ),
        "Editor": (
            "You are a professional medical editor. Your task is to improve the draft "
            "provided to you: enhance clarity, fix structure, ensure consistency, correct "
            "errors, and verify it meets editorial standards. Return the full improved document. "
            "Do not summarise or truncate — output the complete revised text."
        ),
        "QA": (
            "You are a quality assurance reviewer for medical writing. Your task is to "
            "systematically review the document provided against the QA checklist and "
            "editorial standards. Produce a structured QA report listing: (1) items that "
            "PASS, (2) items that FAIL with specific line references, (3) a recommendation "
            "(APPROVE / REVISE MINOR / REVISE MAJOR). Be specific and actionable."
        ),
    }
    base = role_descriptions.get(role, "You are a professional writing assistant.")
    if guidelines:
        return (
            f"{base}\n\n"
            "## Background Guidelines\n"
            "The following guidelines govern all writing in this project. "
            "Apply them throughout your work.\n\n"
            f"{guidelines}"
        )
    return base


def _writer_user_prompt(
    direct_instructions: list,
    original_content: str,
    is_scratch: bool,
) -> str:
    parts = []

    if direct_instructions:
        parts.append("## DIRECT TASK INSTRUCTIONS (highest priority — follow exactly)")
        for inst in direct_instructions:
            clean = inst.lstrip(">").strip()
            parts.append(f"- {clean}")
        parts.append("")

    if is_scratch:
        parts.append(
            "## Task\n"
            "No input document was provided. Using the direct instructions above, "
            "produce a complete, well-structured document. Include all required sections, "
            "citations, and formatting as specified in the style guide."
        )
    else:
        parts.append("## Source Document (use as reference and starting point)")
        parts.append(original_content)
        parts.append("")
        parts.append(
            "## Task\n"
            "Using the source document above and the direct instructions, produce a "
            "complete, polished written output that meets all style and editorial guidelines."
        )

    parts.append(
        "\n## Output Format\n"
        "Return the complete document in Markdown. Use ## for main section headings "
        "and ### for subsections. Do not truncate. Do not add meta-commentary — "
        "output only the document itself."
    )
    return "\n".join(parts)


def _editor_user_prompt(
    direct_instructions: list,
    writer_output: str,
    original_content: str,
) -> str:
    parts = []

    if direct_instructions:
        parts.append("## DIRECT TASK INSTRUCTIONS (highest priority — follow exactly)")
        for inst in direct_instructions:
            clean = inst.lstrip(">").strip()
            parts.append(f"- {clean}")
        parts.append("")

    parts.append("## Original Source Document (for reference)")
    parts.append(original_content if original_content else "(No original source provided.)")
    parts.append("")
    parts.append("## Writer Draft (edit this document)")
    parts.append(writer_output)
    parts.append(
        "\n## Task\n"
        "Edit the Writer Draft above. Improve clarity, structure, and accuracy. "
        "Ensure it meets all editorial standards and style guidelines. "
        "Return the complete edited document in Markdown. Do not truncate."
    )
    return "\n".join(parts)


def _qa_user_prompt(editor_output: str) -> str:
    return (
        "## Document to Review\n\n"
        f"{editor_output}\n\n"
        "## Task\n"
        "Review the document above against the QA checklist and editorial standards "
        "provided in your guidelines. Produce a structured QA report with three sections:\n\n"
        "### PASS\nList every checklist item that is satisfied.\n\n"
        "### FAIL\nList every checklist item that is NOT satisfied, with a specific "
        "description of the issue and the relevant section or line.\n\n"
        "### RECOMMENDATION\nState one of: APPROVE / REVISE MINOR / REVISE MAJOR. "
        "Provide a one-paragraph justification."
    )


# ---------------------------------------------------------------------------
# Report builders
# ---------------------------------------------------------------------------
def _write_role_report(
    reports_path: Path,
    role: str,
    stem: str,
    timestamp: str,
    content: str,
    extra_meta: str = "",
) -> Path:
    filename = f"{role.upper()}_{stem}_{timestamp}.md"
    report_path = reports_path / filename
    header = (
        f"# {role} Report — {stem}\n"
        f"**Timestamp:** {timestamp}\n"
        f"**Role:** {role}\n"
    )
    if extra_meta:
        header += f"{extra_meta}\n"
    header += "\n---\n\n"
    _write_text_file(report_path, header + content)
    print(f"  [REPORT] {filename}")
    return report_path


def _write_session_summary(
    reports_path: Path,
    timestamp: str,
    subprojects: list,
    mode: str = "WRITER",
) -> None:
    filename = f"{mode}_SESSION_{timestamp}_SUMMARY.md"
    lines = [
        f"# Writing Mode Session Summary\n",
        f"**Session timestamp:** {timestamp}  ",
        f"**Sub-projects processed:** {len(subprojects)}\n",
        "---\n",
    ]
    for sp in subprojects:
        lines.append(f"## {sp['stem']}")
        lines.append(f"- Writer output: `{sp.get('writer_out', 'N/A')}`")
        lines.append(f"- Editor output: `{sp.get('editor_out', 'N/A')}`")
        lines.append(f"- QA report:     `{sp.get('qa_report', 'N/A')}`")
        lines.append(f"- Status:        {sp.get('status', 'unknown')}\n")
    _write_text_file(reports_path / filename, "\n".join(lines))
    print(f"\n  [SESSION SUMMARY] {filename}")


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------
def parse_direct_instructions(raw_text: str) -> list:
    """Return lines that start with > (direct task instructions)."""
    return [
        line.strip()
        for line in raw_text.splitlines()
        if line.strip().startswith(">")
    ]


def _strip_fences(text: str) -> str:
    """Remove markdown code fences if the LLM wrapped output in them."""
    import re
    text = re.sub(r"^```[a-zA-Z]*\n", "", text.strip())
    text = re.sub(r"\n```$", "", text.strip())
    return text.strip()


# ---------------------------------------------------------------------------
# Main pipeline: Writer → Editor → QA
# ---------------------------------------------------------------------------
def run_writer(
    direct_instructions: list,
    call_llm_fn: Callable,
    verbose: bool = True,
) -> None:
    root = _project_root()
    paths = _paths(root)
    timestamp = _ts()

    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)

    guidelines = _load_guidelines(paths["doc"])
    input_files = _load_input_files(paths["input"])
    is_scratch = len(input_files) == 0

    if is_scratch:
        subprojects = [("new_doc", "", ".md")]
    else:
        subprojects = [(stem, content, suffix) for stem, content, suffix in input_files]

    session_log = []

    for stem, original_content, original_suffix in subprojects:
        if verbose:
            print(f"\n{'='*60}")
            print(f"  [WRITER PIPELINE] Sub-project: {stem}")
            print(f"{'='*60}")

        sp_log = {"stem": stem, "status": "started"}

        # ── WRITER ──────────────────────────────────────────────
        if verbose:
            print(f"\n  [WRITER] Generating draft...")

        sys_prompt = _system_prompt(guidelines, "Writer")
        usr_prompt = _writer_user_prompt(
            direct_instructions=direct_instructions,
            original_content=original_content,
            is_scratch=is_scratch,
        )
        writer_output = _call_llm(sys_prompt, usr_prompt, call_llm_fn, "Writer generating")
        writer_output = _strip_fences(writer_output)

        # Write Writer report
        _write_role_report(
            paths["reports"], "WRITER", stem, timestamp,
            writer_output,
            extra_meta=f"**Source:** {'scratch' if is_scratch else stem + original_suffix}",
        )

        # Save Writer outputs
        writer_md_path = paths["output"] / f"WRITER_{stem}_{timestamp}.md"
        _write_text_file(writer_md_path, writer_output)
        print(f"  [MD]   Saved: {writer_md_path.name}")
        sp_log["writer_out"] = writer_md_path.name

        writer_docx_path = paths["output"] / f"WRITER_{stem}_{timestamp}.docx"
        _write_docx_file(writer_docx_path, writer_output, title=f"Writer Draft — {stem}")
        sp_log["writer_docx"] = writer_docx_path.name

        # ── EDITOR ──────────────────────────────────────────────
        if verbose:
            print(f"\n  [EDITOR] Editing draft...")

        sys_prompt = _system_prompt(guidelines, "Editor")
        usr_prompt = _editor_user_prompt(
            direct_instructions=direct_instructions,
            writer_output=writer_output,
            original_content=original_content,
        )
        editor_output = _call_llm(sys_prompt, usr_prompt, call_llm_fn, "Editor revising")
        editor_output = _strip_fences(editor_output)

        # Write Editor report
        _write_role_report(
            paths["reports"], "EDITOR", stem, timestamp,
            editor_output,
        )

        # Save Editor outputs
        editor_md_path = paths["output"] / f"EDITOR_{stem}_{timestamp}.md"
        _write_text_file(editor_md_path, editor_output)
        print(f"  [MD]   Saved: {editor_md_path.name}")
        sp_log["editor_out"] = editor_md_path.name

        editor_docx_path = paths["output"] / f"EDITOR_{stem}_{timestamp}.docx"
        _write_docx_file(editor_docx_path, editor_output, title=f"Edited Document — {stem}")
        sp_log["editor_docx"] = editor_docx_path.name

        # ── QA ──────────────────────────────────────────────────
        if verbose:
            print(f"\n  [QA] Running quality check...")

        sys_prompt = _system_prompt(guidelines, "QA")
        usr_prompt = _qa_user_prompt(editor_output)
        qa_output = _call_llm(sys_prompt, usr_prompt, call_llm_fn, "QA reviewing")
        qa_output = _strip_fences(qa_output)

        qa_report_path = _write_role_report(
            paths["reports"], "QA", stem, timestamp,
            qa_output,
        )
        sp_log["qa_report"] = qa_report_path.name
        sp_log["status"] = "complete"

        if verbose:
            print(f"\n  ✓ Sub-project '{stem}' complete.")
            print(f"    Writer:  output/writing/WRITER_{stem}_{timestamp}.docx")
            print(f"    Editor:  output/writing/EDITOR_{stem}_{timestamp}.docx")
            print(f"    QA:      reports/writing/QA_{stem}_{timestamp}.md")

        session_log.append(sp_log)

    _write_session_summary(paths["reports"], timestamp, session_log, mode="WRITER")


# ---------------------------------------------------------------------------
# Standalone: Editor only
# ---------------------------------------------------------------------------
def run_editor(
    direct_instructions: list,
    call_llm_fn: Callable,
    verbose: bool = True,
) -> None:
    root = _project_root()
    paths = _paths(root)
    timestamp = _ts()

    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)

    guidelines = _load_guidelines(paths["doc"])
    input_files = _load_input_files(paths["input"])

    if not input_files:
        print("  [EDITOR] No files found in input/writing/. Place documents there first.")
        return

    for stem, content, suffix in input_files:
        if verbose:
            print(f"\n  [EDITOR STANDALONE] Processing: {stem}{suffix}")

        sys_prompt = _system_prompt(guidelines, "Editor")
        usr_prompt = _editor_user_prompt(
            direct_instructions=direct_instructions,
            writer_output=content,
            original_content=content,
        )
        editor_output = _call_llm(sys_prompt, usr_prompt, call_llm_fn, "Editor processing")
        editor_output = _strip_fences(editor_output)

        _write_role_report(paths["reports"], "EDITOR", stem, timestamp, editor_output)

        md_path = paths["output"] / f"EDITOR_{stem}_{timestamp}.md"
        _write_text_file(md_path, editor_output)
        print(f"  [MD]   Saved: {md_path.name}")

        docx_path = paths["output"] / f"EDITOR_{stem}_{timestamp}.docx"
        _write_docx_file(docx_path, editor_output, title=f"Edited — {stem}")


# ---------------------------------------------------------------------------
# Standalone: QA only
# ---------------------------------------------------------------------------
def run_qa(
    direct_instructions: list,
    call_llm_fn: Callable,
    verbose: bool = True,
) -> None:
    root = _project_root()
    paths = _paths(root)
    timestamp = _ts()

    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)

    guidelines = _load_guidelines(paths["doc"])
    input_files = _load_input_files(paths["input"])

    if not input_files:
        print("  [QA] No files found in input/writing/. Place documents there first.")
        return

    for stem, content, suffix in input_files:
        if verbose:
            print(f"\n  [QA STANDALONE] Reviewing: {stem}{suffix}")

        sys_prompt = _system_prompt(guidelines, "QA")
        usr_prompt = _qa_user_prompt(content)
        qa_output = _call_llm(sys_prompt, usr_prompt, call_llm_fn, "QA reviewing")
        qa_output = _strip_fences(qa_output)

        _write_role_report(paths["reports"], "QA", stem, timestamp, qa_output)
        print(f"  [QA STANDALONE] Report saved to reports/writing/")
