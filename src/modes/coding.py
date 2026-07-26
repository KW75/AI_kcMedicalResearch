"""
coding.py — Coding mode engine for AI kcMedicalResearch
Provides three sub-modes: Builder (pipeline), Reviewer (standalone), Tester (standalone)
"""

from __future__ import annotations

import os
import re
import glob
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


def _stem(filepath: str | Path) -> str:
    """Return the filename stem (no extension, spaces replaced with underscores)."""
    return Path(filepath).stem.replace(" ", "_")


def _paths(root: Path) -> dict[str, Path]:
    """Return the standard paths dictionary for coding mode."""
    return {
        "doc":     root / "doc"     / "coding",
        "input":   root / "input"   / "coding",
        "output":  root / "output"  / "coding",
        "reports": root / "reports" / "coding",
    }


# ---------------------------------------------------------------------------
# File I/O helpers
# ---------------------------------------------------------------------------

def _load_md_guidelines(doc_path: Path) -> str:
    """
    Load all .md files from doc/coding/ and concatenate them as background
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


def _load_code_files(input_path: Path) -> list[tuple[str, str]]:
    """
    Load all code files from input/coding/.
    Returns list of (filename_stem, file_content) tuples, sorted alphabetically.
    Returns empty list if folder is empty or missing.
    """
    if not input_path.exists():
        return []
    extensions = {".py", ".js", ".ts", ".java", ".c", ".cpp", ".cs", ".go",
                  ".rb", ".php", ".rs", ".swift", ".kt", ".r", ".sh", ".sql"}
    files = sorted([
        f for f in input_path.iterdir()
        if f.is_file() and f.suffix.lower() in extensions
    ])
    return [(f.stem.replace(" ", "_"), f.read_text(encoding="utf-8", errors="ignore"))
            for f in files]


def _write_file(path: Path, content: str) -> None:
    """Write content to path, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  [WRITTEN] {path}")


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
            "Build a complete, well-structured application based on the direct task "
            "instructions above and the background guidelines in the system prompt.\n"
            "Each instruction represents a feature, function, or component of ONE "
            "single application. Produce the complete application as a single coherent "
            "Python file unless the guidelines specify otherwise."
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
        "Return ONLY the complete code. Do not include explanations outside of "
        "code comments. Begin your response with the first line of code."
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
        "description. Be specific and actionable."
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
# LLM call — thin wrapper (plugs into existing call_llm in src/main.py)
# ---------------------------------------------------------------------------

def _call_llm(system_prompt: str, user_prompt: str, call_llm_fn) -> str:
    """
    Thin wrapper around the project's existing call_llm function.
    call_llm_fn is injected from src/main.py to keep this module decoupled
    from the LLM provider selection logic.
    """
    return call_llm_fn(system_prompt=system_prompt, user_prompt=user_prompt)


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
        f"## Code Submitted\n\n```python\n{code}\n```\n\n"
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
        f"## Final Code\n\n```python\n{final_code}\n```\n"
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
        f"## Code Reviewed\n\n```python\n{code_content}\n```\n\n"
        f"---\n\n"
        f"## {sub_mode} Output\n\n{feedback}\n"
    )


# ---------------------------------------------------------------------------
# MAX_ITERATIONS constant
# ---------------------------------------------------------------------------

MAX_ITERATIONS = 5


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
    root = _project_root()
    paths = _paths(root)
    ts_session = _ts()

    if verbose:
        print("\n[BUILDER] Starting...")

    # --- Load guidelines ---
    guidelines = _load_md_guidelines(paths["doc"])
    system_prompt = _build_system_prompt(guidelines)

    # --- Determine subprojects ---
    code_files = _load_code_files(paths["input"])
    is_scratch = len(code_files) == 0

    if is_scratch:
        subprojects = [("new_app", None)]
        if verbose:
            print("[BUILDER] No input files found — building new app from scratch.")
    else:
        subprojects = code_files
        if verbose:
            print(f"[BUILDER] Found {len(subprojects)} subproject(s) to process.")

    session_results = []

    # --- Process each subproject sequentially ---
    for idx, (stem, initial_code) in enumerate(subprojects, start=1):
        ts = _ts()
        if verbose:
            print(f"\n[BUILDER] Subproject {idx}/{len(subprojects)}: {stem}")

        current_code = initial_code  # None if scratch
        reviewer_iters_used = 0
        tester_iters_used = 0
        error_feedback = None
        outcome = "UNKNOWN"

        # ---- REVIEWER LOOP ----
        reviewer_passed_flag = False
        for rev_iter in range(1, MAX_ITERATIONS + 1):
            reviewer_iters_used = rev_iter
            if verbose:
                print(f"  [REVIEWER LOOP] Iteration {rev_iter}/{MAX_ITERATIONS}")

            # Build and call Builder to generate/regenerate code
            user_prompt = _build_builder_user_prompt(
                direct_instructions=direct_instructions,
                code_context=current_code,
                error_feedback=error_feedback,
                is_scratch=is_scratch,
                iteration=rev_iter,
            )
            current_code = _call_llm(system_prompt, user_prompt, call_llm_fn)

            # Strip markdown code fences if LLM wraps output
            current_code = _strip_code_fences(current_code)

            # Pass to Reviewer agent
            reviewer_prompt = _build_reviewer_user_prompt(
                direct_instructions=direct_instructions,
                code_content=current_code,
                stem=stem,
            )
            reviewer_response = _call_llm(system_prompt, reviewer_prompt, call_llm_fn)

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
        error_feedback = None
        for test_iter in range(1, MAX_ITERATIONS + 1):
            tester_iters_used = test_iter
            if verbose:
                print(f"  [TESTER LOOP] Iteration {test_iter}/{MAX_ITERATIONS}")

            # Regenerate if there was tester feedback (not first iteration)
            if error_feedback:
                user_prompt = _build_builder_user_prompt(
                    direct_instructions=direct_instructions,
                    code_context=current_code,
                    error_feedback=error_feedback,
                    is_scratch=False,
                    iteration=test_iter,
                )
                current_code = _call_llm(system_prompt, user_prompt, call_llm_fn)
                current_code = _strip_code_fences(current_code)

            # Pass to Tester agent
            tester_prompt = _build_tester_user_prompt(
                direct_instructions=direct_instructions,
                code_content=current_code,
                stem=stem,
            )
            tester_response = _call_llm(system_prompt, tester_prompt, call_llm_fn)

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
                error_feedback = None
                break
            else:
                error_feedback = tester_response
                if verbose:
                    print(f"  [TESTER LOOP] FAILED — feeding errors back to Builder")

        # ---- Write final output ----
        fully_passed = reviewer_passed_flag and tester_passed_flag

        if fully_passed:
            outcome = "FINAL"
            out_name = f"BUILDER_{stem}_{ts}_FINAL.py"
            summary_name = f"BUILDER_{stem}_{ts}_FINAL_SUMMARY.md"
            if verbose:
                print(f"  [BUILDER] Subproject {stem} PASSED — writing final output.")
        else:
            outcome = "MAXITER_WARNING"
            out_name = f"BUILDER_{stem}_{ts}_MAXITER_WARNING.py"
            summary_name = f"BUILDER_{stem}_{ts}_MAXITER_SUMMARY.md"
            if verbose:
                print(f"  [BUILDER] WARNING: {stem} hit max iterations — writing best available output.")

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
            "stem": stem,
            "outcome": outcome,
            "reviewer_iters": reviewer_iters_used,
            "tester_iters": tester_iters_used,
        })

    # ---- Write session summary ----
    session_summary = _build_session_summary("Builder", session_results)
    session_name = f"BUILDER_SESSION_{ts_session}_SUMMARY.md"
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
    root = _project_root()
    paths = _paths(root)
    ts_session = _ts()

    if verbose:
        print("\n[REVIEWER] Starting...")

    guidelines = _load_md_guidelines(paths["doc"])
    system_prompt = _build_system_prompt(guidelines)
    code_files = _load_code_files(paths["input"])

    if not code_files:
        print("[REVIEWER] No code files found in input/coding/ — nothing to review.")
        return

    if verbose:
        print(f"[REVIEWER] Found {len(code_files)} file(s) to review.")

    session_results = []

    for idx, (stem, code_content) in enumerate(code_files, start=1):
        ts = _ts()
        if verbose:
            print(f"\n[REVIEWER] File {idx}/{len(code_files)}: {stem}")

        user_prompt = _build_reviewer_user_prompt(
            direct_instructions=direct_instructions,
            code_content=code_content,
            stem=stem,
        )
        response = _call_llm(system_prompt, user_prompt, call_llm_fn)

        passed = _reviewer_passed(response)
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
    session_name = f"REVIEWER_SESSION_{ts_session}_SUMMARY.md"
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
    root = _project_root()
    paths = _paths(root)
    ts_session = _ts()

    if verbose:
        print("\n[TESTER] Starting...")

    guidelines = _load_md_guidelines(paths["doc"])
    system_prompt = _build_system_prompt(guidelines)
    code_files = _load_code_files(paths["input"])

    if not code_files:
        print("[TESTER] No code files found in input/coding/ — nothing to test.")
        return

    if verbose:
        print(f"[TESTER] Found {len(code_files)} file(s) to test.")

    session_results = []

    for idx, (stem, code_content) in enumerate(code_files, start=1):
        ts = _ts()
        if verbose:
            print(f"\n[TESTER] File {idx}/{len(code_files)}: {stem}")

        user_prompt = _build_tester_user_prompt(
            direct_instructions=direct_instructions,
            code_content=code_content,
            stem=stem,
        )
        response = _call_llm(system_prompt, user_prompt, call_llm_fn)

        passed = _tester_passed(response)
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
    session_name = f"TESTER_SESSION_{ts_session}_SUMMARY.md"
    _write_file(paths["reports"] / session_name, session_summary)

    if verbose:
        print(f"\n[TESTER] Session complete. {len(session_results)} file(s) tested.")


# ---------------------------------------------------------------------------
# CLI instruction parser — strips leading > from user input lines
# ---------------------------------------------------------------------------

def parse_direct_instructions(raw_input: str) -> list[str]:
    """
    Parse raw CLI input and extract lines beginning with >.
    Returns a list of instruction strings with the > prefix and leading
    whitespace stripped.

    Example:
        raw = "> Build a CSV parser\n> Add error handling\nSome other note"
        → ["Build a CSV parser", "Add error handling"]
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
# Code fence stripper — removes ```python ... ``` wrapping from LLM output
# ---------------------------------------------------------------------------

def _strip_code_fences(text: str) -> str:
    """
    Remove markdown code fences that some LLMs wrap around their output.
    Handles ```python, ```py, ``` and similar variants.
    """
    text = text.strip()
    # Remove opening fence with optional language tag
    text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
    # Remove closing fence
    text = re.sub(r"\n?```$", "", text)
    return text.strip()
