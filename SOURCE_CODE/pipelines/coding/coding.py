"""
coding.py — Coding mode engine for AI kcMedicalResearch
Provides three sub-modes: Builder (pipeline), Reviewer (standalone), Tester (standalone)
"""

from __future__ import annotations

import re
import sys
import threading
import datetime
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def _project_root() -> Path:
    """Return the project root regardless of where the script is called from."""
    return Path(__file__).resolve().parent.parent.parent


def _ts() -> str:
    """Return a filesystem-safe timestamp string: YYYYMMDD_HHMMSS."""
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def _paths(root: Path) -> dict[str, Path]:
    """Return the standard paths dictionary for coding mode.
    Matches the folder conventions already established in src/main.py:
      docs/coding/   <- guidance .md files  (DOCS_CODING in main.py)
      input/coding/  <- code files to process
      output/coding/ <- final built code
      reports/coding/<- all reports and iteration logs
    """
    return {
        "doc":     root / "docs"    / "coding",
        "input":   root / "input"   / "coding",
        "output":  root / "output"  / "coding",
        "reports": root / "reports" / "coding",
    }


# ---------------------------------------------------------------------------
# File I/O helpers
# ---------------------------------------------------------------------------

def _load_md_guidelines(doc_path: Path) -> str:
    """
    Load all .md files from docs/coding/ and concatenate them as background
    guidelines context. Returns empty string if folder is empty or missing.
    """
    if not doc_path.exists():
        return ""
    md_files = sorted(doc_path.glob("*.md"))
    if not md_files:
        return ""
    sections = []
    for f in md_files:
        content = f.read_text(encoding="utf-8", errors="ignore").strip()
        if content:
            sections.append(f"### Guidelines from {f.name}\n\n{content}")
    return "\n\n---\n\n".join(sections)


def _load_code_files(input_path: Path) -> list[tuple[str, str, str]]:
    """
    Load all code files from input/coding/.
    Returns list of (filename_stem, file_content, original_suffix) tuples,
    sorted alphabetically.
    Returns empty list if folder is empty or missing.
    The original_suffix is preserved so Builder output uses the correct extension.
    """
    if not input_path.exists():
        return []
    
    extensions = {".py", ".js", ".ts", ".html", ".css", ".java", ".c",
                  ".cpp", ".cs", ".rb", ".go", ".rs", ".txt", ".md",
                  ".php", ".swift", ".kt", ".r", ".sh", ".sql", ".svg"}

    files = sorted([
        f for f in input_path.iterdir()
        if f.is_file() and f.suffix.lower() in extensions
    ])
    return [
        (f.stem.replace(" ", "_"),
         f.read_text(encoding="utf-8", errors="ignore"),
         f.suffix.lower())
        for f in files
    ]


def _write_file(path: Path, content: str) -> None:
    """Write content to path, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  [WRITTEN] {path}")


# ---------------------------------------------------------------------------
# Spinner — visible feedback during LLM calls
# ---------------------------------------------------------------------------

class _Spinner:
    """
    Simple terminal spinner that runs on a background thread.
    Shows the user the LLM is working and has not hung.
    Usage:
        with _Spinner("Reviewer agent thinking"):
            response = call_llm(...)
    """
    def __init__(self, message: str = "Processing"):
        self._message = message
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._spin, daemon=True)

    def _spin(self) -> None:
        frames = ["|", "/", "-", "\\"]
        idx = 0
        while not self._stop_event.is_set():
            frame = frames[idx % len(frames)]
            sys.stdout.write(f"\r  {frame}  {self._message}... ")
            sys.stdout.flush()
            self._stop_event.wait(0.15)
            idx += 1
        # Clear the spinner line
        sys.stdout.write(f"\r  ✓  {self._message} — done.          \n")
        sys.stdout.flush()

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, *_):
        self._stop_event.set()
        self._thread.join()


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

def _build_system_prompt(guidelines: str) -> str:
    """
    Build the system prompt from MD guidelines.
    Guidelines are background context; direct instructions come in the user prompt.
    """
    base = (
        "You are an expert software engineer and code assistant.\n"
        "You write clean, well-documented, production-quality code.\n"
        "You follow all coding standards and guidelines provided.\n"
        "When reviewing or testing code, you provide precise, actionable feedback.\n"
        "\n"
        "CRITICAL OUTPUT RULE: Never truncate, abbreviate, or summarise your code output.\n"
        "Never use placeholders such as '// ... rest of code', '# TODO', '[rest unchanged]',\n"
        "or any other shorthand. Always write every line of every function in full.\n"
        "If the file is long, keep writing until the final closing tag or brace.\n"
        "A response that ends mid-function or mid-file is considered a critical failure.\n"
    )
    if guidelines:
        return base + "\n\n## Background Guidelines and Standards\n\n" + guidelines
    return base


def _build_builder_user_prompt(
    direct_instructions: list[str],
    code_context: Optional[str],
    error_feedback: Optional[str],
    is_scratch: bool,
    iteration: int,
) -> str:
    """
    Build the Builder user prompt.
    direct_instructions are highest priority (from > CLI input).
    error_feedback from Reviewer/Tester is appended as context for regeneration.
    """
    parts = []

    # --- Highest priority: direct instructions ---
    if direct_instructions:
        parts.append("## Direct Task Instructions (Highest Priority)\n")
        for instr in direct_instructions:
            parts.append(f"- {instr}")
        parts.append("")

    # --- Code context or scratch build notice ---
    if is_scratch:
        parts.append(
            "## Task\n"
            "Build a complete, immediately runnable application implementing EVERY "
            "feature listed in the Direct Task Instructions above.\n"
            "STRICT RULES:\n"
            "1. Every button, input, and display element mentioned in the instructions "
            "   MUST exist as an HTML element with a matching id.\n"
            "2. Every HTML element id referenced in JavaScript MUST exist in the HTML "
            "   DOM. Never reference an id that is not in the HTML.\n"
            "3. All button click handlers MUST be wired with addEventListener in the "
            "   init() function called on DOMContentLoaded.\n"
            "4. Use the EXACT feature names from the instructions for button labels "
            "   and element ids (e.g. start-btn, stop-btn, beep-period).\n"
            "5. Do NOT invent features not listed in the instructions.\n"
            "6. Do NOT generate a generic template - implement the specific "
            "   application described.\n"
            "7. Write the ENTIRE file from first line to last line.\n"
            "8. Do NOT stop early, do NOT use placeholders.\n"
            "9. For HTML: last line must be </html>.\n"
            "10. For Python: last line must close all functions and classes.\n"
            "If running out of space, prioritise completing logic over comments."
        )
    else:
        parts.append("## Code Under Development\n")
        parts.append("```")
        parts.append(code_context or "")
        parts.append("```\n")
        parts.append(
            "## Task\n"
            "Review and improve the code above based on the direct task instructions "
            "and background guidelines. Produce the complete corrected code."
        )

    # --- Error feedback from previous iteration ---
    if error_feedback and iteration > 1:
        parts.append(
            f"\n## Feedback from Previous Iteration (Iteration {iteration - 1})\n"
            "The following errors or issues were identified. You MUST address ALL of "
            "them in your revised output:\n\n"
            + error_feedback
        )

    parts.append(
        "\n## Output Format\n"
        "Return ONLY the complete code for ONE single file. "
        "Do not include explanations, markdown prose, or commentary outside of code comments. "
        "Do not generate multiple files or multiple code blocks. "
        "Do not write a Python file AND an HTML file — pick the single best format. "
        "Begin your response with the very first line of the file (e.g. <!DOCTYPE html> or import ...). "
        "End your response with the very last line of the file (e.g. </html> or the last closing brace). "
        "Do not add any text after the closing line."
    )

    return "\n".join(parts)


def _build_reviewer_user_prompt(
    direct_instructions: list[str],
    code_content: str,
    stem: str,
) -> str:
    """Build the Reviewer agent user prompt."""
    parts = []
    if direct_instructions:
        parts.append("## Direct Review Instructions (Highest Priority)\n")
        for instr in direct_instructions:
            parts.append(f"- {instr}")
        parts.append("")

    parts.append(f"## Code to Review: {stem}\n")
    parts.append("```")
    parts.append(code_content)
    parts.append("```\n")
    parts.append(
        "## Review Task\n"
        "Perform a thorough code review. Identify ALL of the following:\n"
        "1. Syntax errors and logical bugs\n"
        "2. Security vulnerabilities\n"
        "3. Violations of the coding guidelines in the system prompt\n"
        "4. Missing error handling, edge cases, or input validation\n"
        "5. Code quality issues (naming, structure, documentation)\n\n"
        "## Output Format\n"
        "If the code passes review with no issues, begin your response with exactly:\n"
        "REVIEW_PASS\n\n"
        "If there are issues, begin your response with exactly:\n"
        "REVIEW_FAIL\n\n"
        "Then list every issue with its line number (if applicable) and a clear "
        "Then list every issue with its line number (if applicable) and a clear "
        "description. Be specific and actionable.\n\n"
        "TRUNCATION RULE: If the code submitted appears incomplete (ends mid-function, "
        "mid-string, or without a closing tag/brace), do NOT issue a REVIEW_FAIL for "
        "functional issues that cannot be verified. Instead begin your response with:\n"
        "REVIEW_FAIL\n\n"
        "## Issues Found\n"
        "### TRUNCATED OUTPUT\n"
        "- The code was cut off before completion. Request the Builder to continue "
        "from where it stopped and complete the file without rewriting from scratch."
    )
    return "\n".join(parts)


def _build_tester_user_prompt(
    direct_instructions: list[str],
    code_content: str,
    stem: str,
) -> str:
    """Build the Tester agent user prompt."""
    parts = []
    if direct_instructions:
        parts.append("## Direct Testing Instructions (Highest Priority)\n")
        for instr in direct_instructions:
            parts.append(f"- {instr}")
        parts.append("")

    parts.append(f"## Code to Test: {stem}\n")
    parts.append("```")
    parts.append(code_content)
    parts.append("```\n")
    parts.append(
        "## Testing Task\n"
        "Analyse the code above and produce a comprehensive test report:\n"
        "1. Identify all functions, classes, and entry points\n"
        "2. Write and mentally execute unit tests for each component\n"
        "3. Test boundary conditions, invalid inputs, and edge cases\n"
        "4. Identify any untested or untestable code paths\n"
        "5. Check for runtime errors, type errors, and exception handling gaps\n\n"
        "## Output Format\n"
        "If all tests pass with no issues, begin your response with exactly:\n"
        "TEST_PASS\n\n"
        "If there are test failures or issues, begin your response with exactly:\n"
        "TEST_FAIL\n\n"
        "Then list every failure with the test case, expected behaviour, and "
        "actual/predicted behaviour. Be specific and actionable."
    )
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# LLM call — thin wrapper with spinner feedback
# ---------------------------------------------------------------------------

def _call_llm(
    system_prompt: str,
    user_prompt: str,
    call_llm_fn,
    spinner_message: str = "LLM processing",
) -> str:
    """
    Thin wrapper around the project's existing call_llm function.
    Shows a spinner so the user knows the LLM is working.
    call_llm_fn is injected from src/main.py to keep this module decoupled
    from the LLM provider selection logic.
    """
    result_holder: list[str] = []
    error_holder:  list[Exception] = []

    def _run():
        try:
            result_holder.append(call_llm_fn(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            ))
        except Exception as exc:  # noqa: BLE001
            error_holder.append(exc)

    with _Spinner(spinner_message):
        t = threading.Thread(target=_run, daemon=True)
        t.start()
        t.join(timeout=300)  # 5-minute hard timeout per LLM call

    if t.is_alive():
        return (
            "[ERROR] LLM call timed out after 5 minutes. "
            "Check that Ollama is running and the model is pulled, "
            "or switch to a cloud provider with --provider."
        )
    if error_holder:
        return f"[ERROR] LLM call failed: {error_holder[0]}"
    if not result_holder:
        return "[ERROR] LLM returned no response."
    return result_holder[0]


# ---------------------------------------------------------------------------
# Pass/fail detection
# ---------------------------------------------------------------------------

def _reviewer_passed(response: str) -> bool:
    return response.strip().startswith("REVIEW_PASS")


def _tester_passed(response: str) -> bool:
    return response.strip().startswith("TEST_PASS")


# ---------------------------------------------------------------------------
# Report builders
# ---------------------------------------------------------------------------

def _build_iteration_report(
    sub_mode: str,
    stem: str,
    iteration: int,
    agent: str,
    code: str,
    feedback: str,
    passed: bool,
) -> str:
    """Build a markdown iteration report for a Builder pipeline pass."""
    status = "PASS" if passed else "FAIL"
    return (
        f"# Builder Pipeline Report\n\n"
        f"**Sub-mode:** {sub_mode}  \n"
        f"**Subproject:** {stem}  \n"
        f"**Agent:** {agent}  \n"
        f"**Iteration:** {iteration}  \n"
        f"**Status:** {status}  \n"
        f"**Timestamp:** {datetime.datetime.now().isoformat()}  \n\n"
        f"---\n\n"
        f"## Code Submitted\n\n```\n{code}\n```\n\n"
        f"---\n\n"
        f"## {agent} Feedback\n\n{feedback}\n"
    )


def _build_final_summary(
    stem: str,
    outcome: str,
    reviewer_iters: int,
    tester_iters: int,
    final_code: str,
) -> str:
    """Build a markdown final summary report for a completed Builder subproject."""
    return (
        f"# Builder Final Summary\n\n"
        f"**Subproject:** {stem}  \n"
        f"**Outcome:** {outcome}  \n"
        f"**Reviewer iterations used:** {reviewer_iters}  \n"
        f"**Tester iterations used:** {tester_iters}  \n"
        f"**Timestamp:** {datetime.datetime.now().isoformat()}  \n\n"
        f"---\n\n"
        f"## Final Code\n\n```\n{final_code}\n```\n"
    )


def _build_session_summary(
    sub_mode: str,
    results: list[dict],
) -> str:
    """Build a markdown session summary covering all subprojects in a run."""
    lines = [
        f"# {sub_mode} Session Summary\n",
        f"**Timestamp:** {datetime.datetime.now().isoformat()}  \n",
        f"**Total subprojects:** {len(results)}  \n\n",
        "---\n\n",
        "## Results\n\n",
        "| Subproject | Outcome | Reviewer Iters | Tester Iters |\n",
        "|---|---|---|---|\n",
    ]
    for r in results:
        lines.append(
            f"| {r['stem']} | {r['outcome']} "
            f"| {r.get('reviewer_iters', 'N/A')} "
            f"| {r.get('tester_iters', 'N/A')} |\n"
        )
    return "".join(lines)


def _build_standalone_report(
    sub_mode: str,
    stem: str,
    code_content: str,
    feedback: str,
) -> str:
    """Build a markdown report for Reviewer or Tester standalone runs."""
    return (
        f"# {sub_mode} Report\n\n"
        f"**Subproject:** {stem}  \n"
        f"**Timestamp:** {datetime.datetime.now().isoformat()}  \n\n"
        f"---\n\n"
        f"## Code Reviewed\n\n```\n{code_content}\n```\n\n"
        f"---\n\n"
        f"## {sub_mode} Output\n\n{feedback}\n"
    )


# ---------------------------------------------------------------------------
# MAX_ITERATIONS constant
# ---------------------------------------------------------------------------

MAX_ITERATIONS = 5


# ---------------------------------------------------------------------------
# Extension detection
# ---------------------------------------------------------------------------

def _detect_extension(
    stem: str,
    code: str,
) -> str:
    """
    Detect the correct file extension for Builder scratch output.
    Only called when input/coding/ was empty (no original_ext available).

    Detection is done by scanning the full content for reliable file-type
    signatures rather than just the first 500 chars, because LLMs sometimes
    add preamble text before the actual code.

    Priority order — most specific signatures checked first.
    Falls back to .py if nothing matches.
    """
    # Normalise for case-insensitive matching
    text = code.strip()
    text_lower = text.lower()

    # ---- HTML ----
    # <!DOCTYPE html> is the canonical HTML5 opening declaration.
    # Also catch files that open directly with <html without a doctype.
    if "<!doctype html" in text_lower or text_lower.lstrip().startswith("<html"):
        return ".html"

    # ---- SVG ----
    if "<svg" in text_lower and "xmlns" in text_lower:
        return ".svg"

    # ---- CSS ----
    # CSS files typically start with a selector or @import / @charset
    # and contain { } blocks but NO HTML tags
    if (
        "<" not in text_lower
        and "}" in text_lower
        and "{" in text_lower
        and (
            text_lower.lstrip().startswith("@")
            or text_lower.lstrip().startswith("/*")
            or re.match(r"^\s*[a-z#.\[*]", text_lower)
        )
    ):
        return ".css"

    # ---- SQL ----
    if re.search(r"\b(select|insert|update|delete|create\s+table|drop\s+table)\b",
                 text_lower):
        return ".sql"

    # ---- TypeScript (check before JS — TS is a superset) ----
    if re.search(r":\s*(string|number|boolean|void|any)\b", text) or \
       re.search(r"\binterface\s+\w+", text) or \
       re.search(r"\btype\s+\w+\s*=", text):
        return ".ts"

    # ---- JavaScript ----
    if re.search(r"\b(const|let|var)\s+\w+\s*=", text) and \
       "def " not in text and "import java" not in text_lower:
        return ".js"

    # ---- Java ----
    if re.search(r"\bpublic\s+class\s+\w+", text) or \
       re.search(r"\bimport\s+java\.", text):
        return ".java"

    # ---- C# ----
    if re.search(r"\busing\s+System", text) or \
       re.search(r"\bnamespace\s+\w+", text):
        return ".cs"

    # ---- Go ----
    if re.search(r"\bpackage\s+main\b", text) or \
       re.search(r"\bfunc\s+main\s*\(\s*\)", text):
        return ".go"

    # ---- C/C++ ----
    if re.search(r"#include\s*[<\"]", text):
        if "class " in text and "::" in text:
            return ".cpp"
        return ".c"

    # ---- Shell script ----
    if text.lstrip().startswith("#!/bin/bash") or \
       text.lstrip().startswith("#!/bin/sh"):
        return ".sh"

    # ---- Python signatures ----
    # def, class, import, if __name__ == "__main__" are all strong Python signals
    if re.search(r"^def\s+\w+\s*\(", text, re.MULTILINE) or \
       re.search(r"^class\s+\w+", text, re.MULTILINE) or \
       re.search(r"^import\s+\w+", text, re.MULTILINE) or \
       re.search(r"^from\s+\w+\s+import", text, re.MULTILINE) or \
       '__name__' in text:
        return ".py"

    # ---- Default fallback ----
    return ".py"


# ---------------------------------------------------------------------------
# BUILDER — pipeline sub-mode
# ---------------------------------------------------------------------------

def run_builder(
    direct_instructions: list[str],
    call_llm_fn,
    verbose: bool = True,
) -> None:
    """
    Run the Builder pipeline sub-mode.

    direct_instructions: list of strings entered via > at the CLI
    call_llm_fn: the project's call_llm function, injected from src/main.py
    verbose: print progress to stdout
    """
    root  = _project_root()
    paths = _paths(root)
    ts_session = _ts()

    if verbose:
        print("\n[BUILDER] Starting...")

    # --- Load guidelines ---
    guidelines    = _load_md_guidelines(paths["doc"])
    system_prompt = _build_system_prompt(guidelines)

    # --- Determine subprojects ---
    code_files = _load_code_files(paths["input"])
    is_scratch = len(code_files) == 0

    if is_scratch:
        subprojects = [("new_app", None, None)]
        if verbose:
            print("[BUILDER] No input files found — building new app from scratch.")
    else:
        subprojects = code_files
        if verbose:
            print(f"[BUILDER] Found {len(subprojects)} subproject(s) to process.")

    session_results = []

    # --- Process each subproject sequentially ---
    for idx, (stem, initial_code, original_ext) in enumerate(subprojects, start=1):
        ts = _ts()
        if verbose:
            print(f"\n[BUILDER] Subproject {idx}/{len(subprojects)}: {stem}")

        current_code = initial_code
        reviewer_iters_used = 0
        tester_iters_used   = 0
        error_feedback      = None
        outcome             = "UNKNOWN"

        # ---- REVIEWER LOOP ----
        reviewer_passed_flag = False
        for rev_iter in range(1, MAX_ITERATIONS + 1):
            reviewer_iters_used = rev_iter
            if verbose:
                print(f"\n  [REVIEWER LOOP] Iteration {rev_iter}/{MAX_ITERATIONS}")

            # Build code via Builder agent
            user_prompt  = _build_builder_user_prompt(
                direct_instructions=direct_instructions,
                code_context=current_code,
                error_feedback=error_feedback,
                is_scratch=is_scratch,
                iteration=rev_iter,
            )
            current_code = _call_llm(
                system_prompt, user_prompt, call_llm_fn,
                spinner_message=f"Builder generating code (iter {rev_iter})",
            )
            current_code = _strip_code_fences(current_code)
            current_code = _ensure_complete(
                current_code, system_prompt, call_llm_fn, max_continuations=5
            )

            # Pass to Reviewer agent
            reviewer_prompt   = _build_reviewer_user_prompt(
                direct_instructions=direct_instructions,
                code_content=current_code,
                stem=stem,
            )
            reviewer_response = _call_llm(
                system_prompt, reviewer_prompt, call_llm_fn,
                spinner_message=f"Reviewer checking code (iter {rev_iter})",
            )

            passed = _reviewer_passed(reviewer_response)

            # Write iteration report
            report_content = _build_iteration_report(
                sub_mode="Builder",
                stem=stem,
                iteration=rev_iter,
                agent="Reviewer",
                code=current_code,
                feedback=reviewer_response,
                passed=passed,
            )
            report_name = f"BUILDER_PASS_{stem}_{ts}_iter{rev_iter}_reviewer.md"
            _write_file(paths["reports"] / report_name, report_content)

            if passed:
                if verbose:
                    print(f"  [REVIEWER LOOP] PASSED at iteration {rev_iter}")
                reviewer_passed_flag = True
                error_feedback = None
                break
            else:
                error_feedback = reviewer_response
                if verbose:
                    print(f"  [REVIEWER LOOP] FAILED — feeding errors back to Builder")

        # ---- TESTER LOOP ----
        tester_passed_flag = False
        error_feedback     = None
        for test_iter in range(1, MAX_ITERATIONS + 1):
            tester_iters_used = test_iter
            if verbose:
                print(f"\n  [TESTER LOOP] Iteration {test_iter}/{MAX_ITERATIONS}")

            # Regenerate if there was tester feedback
            if error_feedback:
                user_prompt  = _build_builder_user_prompt(
                    direct_instructions=direct_instructions,
                    code_context=current_code,
                    error_feedback=error_feedback,
                    is_scratch=False,
                    iteration=test_iter,
                )
                current_code = _call_llm(
                    system_prompt, user_prompt, call_llm_fn,
                    spinner_message=f"Builder fixing code (iter {test_iter})",
                )
                current_code = _strip_code_fences(current_code)
                current_code = _ensure_complete(
                    current_code, system_prompt, call_llm_fn, max_continuations=5
                )

            # Pass to Tester agent
            tester_prompt   = _build_tester_user_prompt(
                direct_instructions=direct_instructions,
                code_content=current_code,
                stem=stem,
            )
            tester_response = _call_llm(
                system_prompt, tester_prompt, call_llm_fn,
                spinner_message=f"Tester checking code (iter {test_iter})",
            )

            passed = _tester_passed(tester_response)

            # Write iteration report
            report_content = _build_iteration_report(
                sub_mode="Builder",
                stem=stem,
                iteration=test_iter,
                agent="Tester",
                code=current_code,
                feedback=tester_response,
                passed=passed,
            )
            report_name = f"BUILDER_PASS_{stem}_{ts}_iter{test_iter}_tester.md"
            _write_file(paths["reports"] / report_name, report_content)

            if passed:
                if verbose:
                    print(f"  [TESTER LOOP] PASSED at iteration {test_iter}")
                tester_passed_flag = True
                error_feedback     = None
                break
            else:
                error_feedback = tester_response
                if verbose:
                    print(f"  [TESTER LOOP] FAILED — feeding errors back to Builder")

        # ---- Write final output ----
        fully_passed = reviewer_passed_flag and tester_passed_flag

        # Determine correct output extension
        if original_ext:
            ext = original_ext
            print(f"  [EXT] Preserving original extension: {ext}")
        else:
            ext = _detect_extension(stem=stem, code=current_code)
            print(f"  [EXT] Detected extension from content: {ext}")

        if fully_passed:
            outcome      = "FINAL"
            out_name     = f"BUILDER_{stem}_{ts}_FINAL{ext}"
            summary_name = f"BUILDER_{stem}_{ts}_FINAL_SUMMARY.md"
            if verbose:
                print(f"\n  [BUILDER] Subproject {stem} PASSED — writing final output.")
        else:
            outcome      = "MAXITER_WARNING"
            out_name     = f"BUILDER_{stem}_{ts}_MAXITER_WARNING{ext}"
            summary_name = f"BUILDER_{stem}_{ts}_MAXITER_SUMMARY.md"
            if verbose:
                print(f"\n  [BUILDER] WARNING: {stem} hit max iterations — writing best available output.")

        # Final truncation safety net before writing output
        current_code = _ensure_complete(
            current_code, system_prompt, call_llm_fn, max_continuations=5
        )
        _write_file(paths["output"] / out_name, current_code)

        summary_content = _build_final_summary(
            stem=stem,
            outcome=outcome,
            reviewer_iters=reviewer_iters_used,
            tester_iters=tester_iters_used,
            final_code=current_code,
        )
        _write_file(paths["reports"] / summary_name, summary_content)

        session_results.append({
            "stem":           stem,
            "outcome":        outcome,
            "reviewer_iters": reviewer_iters_used,
            "tester_iters":   tester_iters_used,
        })

    # ---- Write session summary ----
    session_summary = _build_session_summary("Builder", session_results)
    session_name    = f"BUILDER_SESSION_{ts_session}_SUMMARY.md"
    _write_file(paths["reports"] / session_name, session_summary)

    if verbose:
        print(f"\n[BUILDER] Session complete. {len(session_results)} subproject(s) processed.")


# ---------------------------------------------------------------------------
# REVIEWER — standalone sub-mode
# ---------------------------------------------------------------------------

def run_reviewer(
    direct_instructions: list[str],
    call_llm_fn,
    verbose: bool = True,
) -> None:
    """
    Run the Reviewer standalone sub-mode.
    Reviews each file in input/coding/ independently. No pipeline looping.
    """
    root       = _project_root()
    paths      = _paths(root)
    ts_session = _ts()

    if verbose:
        print("\n[REVIEWER] Starting...")

    guidelines    = _load_md_guidelines(paths["doc"])
    system_prompt = _build_system_prompt(guidelines)
    code_files    = _load_code_files(paths["input"])

    if not code_files:
        print("[REVIEWER] No code files found in input/coding/ — nothing to review.")
        return

    if verbose:
        print(f"[REVIEWER] Found {len(code_files)} file(s) to review.")

    session_results = []

    for idx, (stem, code_content, _ext) in enumerate(code_files, start=1):
        ts = _ts()
        if verbose:
            print(f"\n[REVIEWER] File {idx}/{len(code_files)}: {stem}")

        user_prompt = _build_reviewer_user_prompt(
            direct_instructions=direct_instructions,
            code_content=code_content,
            stem=stem,
        )
        response = _call_llm(
            system_prompt, user_prompt, call_llm_fn,
            spinner_message=f"Reviewer analysing {stem}",
        )

        passed  = _reviewer_passed(response)
        outcome = "REVIEW_PASS" if passed else "REVIEW_FAIL"

        report_content = _build_standalone_report(
            sub_mode="Reviewer",
            stem=stem,
            code_content=code_content,
            feedback=response,
        )
        report_name = f"REVIEWER_{stem}_{ts}.md"
        _write_file(paths["reports"] / report_name, report_content)

        session_results.append({"stem": stem, "outcome": outcome})

        if verbose:
            print(f"  [REVIEWER] {stem} → {outcome}")

    session_summary = _build_session_summary("Reviewer", session_results)
    session_name    = f"REVIEWER_SESSION_{ts_session}_SUMMARY.md"
    _write_file(paths["reports"] / session_name, session_summary)

    if verbose:
        print(f"\n[REVIEWER] Session complete. {len(session_results)} file(s) reviewed.")


# ---------------------------------------------------------------------------
# TESTER — standalone sub-mode
# ---------------------------------------------------------------------------

def run_tester(
    direct_instructions: list[str],
    call_llm_fn,
    verbose: bool = True,
) -> None:
    """
    Run the Tester standalone sub-mode.
    Tests each file in input/coding/ independently. No pipeline looping.
    """
    root       = _project_root()
    paths      = _paths(root)
    ts_session = _ts()

    if verbose:
        print("\n[TESTER] Starting...")

    guidelines    = _load_md_guidelines(paths["doc"])
    system_prompt = _build_system_prompt(guidelines)
    code_files    = _load_code_files(paths["input"])

    if not code_files:
        print("[TESTER] No code files found in input/coding/ — nothing to test.")
        return

    if verbose:
        print(f"[TESTER] Found {len(code_files)} file(s) to test.")

    session_results = []

    for idx, (stem, code_content, _ext) in enumerate(code_files, start=1):
        ts = _ts()
        if verbose:
            print(f"\n[TESTER] File {idx}/{len(code_files)}: {stem}")

        user_prompt = _build_tester_user_prompt(
            direct_instructions=direct_instructions,
            code_content=code_content,
            stem=stem,
        )
        response = _call_llm(
            system_prompt, user_prompt, call_llm_fn,
            spinner_message=f"Tester analysing {stem}",
        )

        passed  = _tester_passed(response)
        outcome = "TEST_PASS" if passed else "TEST_FAIL"

        report_content = _build_standalone_report(
            sub_mode="Tester",
            stem=stem,
            code_content=code_content,
            feedback=response,
        )
        report_name = f"TESTER_{stem}_{ts}.md"
        _write_file(paths["reports"] / report_name, report_content)

        session_results.append({"stem": stem, "outcome": outcome})

        if verbose:
            print(f"  [TESTER] {stem} → {outcome}")

    session_summary = _build_session_summary("Tester", session_results)
    session_name    = f"TESTER_SESSION_{ts_session}_SUMMARY.md"
    _write_file(paths["reports"] / session_name, session_summary)

    if verbose:
        print(f"\n[TESTER] Session complete. {len(session_results)} file(s) tested.")


# ---------------------------------------------------------------------------
# CLI instruction parser
# ---------------------------------------------------------------------------

def parse_direct_instructions(raw_input: str) -> list[str]:
    """
    Parse raw CLI input and extract lines beginning with >.
    Returns a list of instruction strings with the > prefix and leading
    whitespace stripped.

    Example:
        raw = "> Build a CSV parser\n> Add error handling\nSome other note"
        -> ["Build a CSV parser", "Add error handling"]
    """
    instructions = []
    for line in raw_input.splitlines():
        stripped = line.strip()
        if stripped.startswith(">"):
            instruction = stripped[1:].strip()
            if instruction:
                instructions.append(instruction)
    return instructions


# ---------------------------------------------------------------------------
# Code fence stripper
# ---------------------------------------------------------------------------



def _is_truncated(code: str) -> bool:
    """
    Detect whether the LLM output was cut off before the file was complete.
    Checks for missing closing tags/braces based on content type.
    """
    stripped = code.strip()
    if not stripped:
        return True

    is_html = stripped.lower().startswith("<!doctype") or "<html" in stripped.lower()[:200]

    if is_html:
        low = stripped.lower()
        # Must end with </html> as the very last non-empty content
        last_nonempty = stripped.rstrip().splitlines()[-1].strip().lower()
        if last_nonempty != "</html>":
            return True
        # If file has a <script> block, check braces are balanced inside it
        if "<script" in low:
            # Extract everything between first <script> and last </script>
            import re as _re
            script_blocks = _re.findall(r"<script[^>]*>(.*?)</script>", stripped, _re.DOTALL | _re.IGNORECASE)
            if not script_blocks:
                # <script> opened but </script> never closed
                return True
            for block in script_blocks:
                open_b  = block.count("{")
                close_b = block.count("}")
                if open_b > close_b + 2:
                    return True
        return False

    # Python files: last non-empty line should not be mid-expression
    last_line = stripped.splitlines()[-1].strip()
    bad_endings = (",", "(", "[", "{", "\\", "->", ":", "=", "+")
    if any(last_line.endswith(e) for e in bad_endings):
        return True

    # Generic JS/CSS: check for unclosed braces
    if stripped.startswith("{") or "function " in stripped or "const " in stripped:
        open_b  = stripped.count("{")
        close_b = stripped.count("}")
        if open_b > close_b + 2:
            return True

    return False


def _ensure_complete(
    code: str,
    system_prompt: str,
    call_llm_fn,
    max_continuations: int = 5,
) -> str:
    """
    If the Builder output appears truncated, fire continuation calls
    asking the LLM to complete the file from where it stopped.
    Rule 5 (close the file) is intentionally removed from the continuation
    prompt — the LLM must write ONLY the missing middle code; closing tags
    are appended by this function after all continuations finish.
    """
    is_html = "<!doctype" in code[:50].lower() or "<html" in code.lower()[:200]

    def _strip_closing_tags(text: str) -> str:
        """Remove closing wrapper tags the LLM may append to a continuation."""
        import re as _re
        # Strip </script></body></html> and variants from the end
        text = text.rstrip()
        for pattern in (
            r"(?i)</html>\s*$",
            r"(?i)</body>\s*$",
            r"(?i)</script>\s*$",
        ):
            text = _re.sub(pattern, "", text).rstrip()
        return text

    for attempt in range(1, max_continuations + 1):
        if not _is_truncated(code):
            break
        print(f"  [BUILDER] Output truncated — requesting continuation {attempt}/{max_continuations}...")
        continuation_prompt = (
            "The previous response was cut off before the file was complete.\n"
            "Continue EXACTLY from where you stopped.\n"
            "Rules:\n"
            "1. Do NOT repeat any code already written.\n"
            "2. Do NOT start from the beginning.\n"
            "3. Do NOT add any explanation or prose.\n"
            "4. Write ONLY the remaining lines of code needed — "
            "do NOT close the file, do NOT add </script>, </body>, or </html>.\n"
            "   Those closing tags will be added automatically after you finish.\n\n"
            f"## File type: {'HTML' if is_html else 'code'}\n\n"
            "## Last 800 characters of code written so far:\n"
            "```\n"
            f"{code[-800:]}\n"
            "```\n\n"
            "Now write ONLY the next lines of code (no closing tags):"
        )
        continuation = _call_llm(
            system_prompt, continuation_prompt, call_llm_fn,
            spinner_message=f"Builder continuing output (attempt {attempt})",
        )
        continuation = _strip_code_fences(continuation)
        if continuation and not continuation.startswith("[ERROR]"):
            # Strip any closing tags the LLM added despite instructions
            continuation = _strip_closing_tags(continuation)
            code = code.rstrip() + "\n" + continuation.lstrip()

    # After all continuations, append correct closing sequence if still missing
    if is_html:
        low = code.rstrip().lower()
        if not low.endswith("</html>"):
            # Check what closing tags are needed
            needs_script_close = "<script" in low and not low.endswith("</script>") and "</script>" not in low.split("<script")[-1]
            tail = ""
            if needs_script_close:
                tail += "\n    </script>"
            if not low.rstrip().endswith("</body>"):
                tail += "\n</body>"
            tail += "\n</html>"
            code = code.rstrip() + tail

    return code
def _strip_code_fences(text: str) -> str:
    """
    Remove markdown code fences that some LLMs wrap around their output.
    Handles ```python, ```py, ``` and similar variants.
    """
    text = text.strip()
    text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    return text.strip()
