"""
main.py — AI Automation Tool
Supports three workflow modes: coding, writing, rct_search.
Supports three AI providers: ollama (default), openai, anthropic.
RAG layer: per-session, mode-specific uploads/ folder indexing via rag.py.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from urllib.request import urlopen  # bare name so tests can patch src.main.urlopen
import uuid
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------
VERSION = "2.0.0"

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR        = Path(__file__).parent.parent
REPORTS_DIR     = BASE_DIR / "reports"
DOCS_DIR        = BASE_DIR / "docs"
DOCS_CODING     = DOCS_DIR / "coding"
DOCS_WRITING    = DOCS_DIR / "writing"
DOCS_RCT_SEARCH = DOCS_DIR / "rct_search"
AI_DIR          = BASE_DIR / "ai"
UPLOAD_DIR      = BASE_DIR / os.getenv("UPLOAD_DIR", "uploads")
UPLOADS_CODING      = UPLOAD_DIR / "coding"
UPLOADS_WRITING     = UPLOAD_DIR / "writing"
UPLOADS_RCT_SEARCH  = UPLOAD_DIR / "rct_search"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Environment / provider config
# ---------------------------------------------------------------------------
OLLAMA_HOST         = os.getenv("OLLAMA_HOST",         "http://localhost:11434")
OLLAMA_MODEL        = os.getenv("OLLAMA_MODEL",        "qwen2.5-coder:3b")
OPENAI_API_KEY      = os.getenv("OPENAI_API_KEY",      "")
OPENAI_MODEL        = os.getenv("OPENAI_MODEL",        "gpt-4o-mini")
ANTHROPIC_API_KEY   = os.getenv("ANTHROPIC_API_KEY",   "")
ANTHROPIC_MODEL     = os.getenv("ANTHROPIC_MODEL",     "claude-sonnet-4-6")
EMBEDDING_PROVIDER  = os.getenv("EMBEDDING_PROVIDER",  "ollama")
EMBEDDING_MODEL     = os.getenv("EMBEDDING_MODEL",     "nomic-embed-text")

# ---------------------------------------------------------------------------
# Role / mode definitions
# ---------------------------------------------------------------------------
ROLE_FILES_CODING = {
    "Builder":  {"prompt": AI_DIR / "builder-prompt.md",  "report": "builder-report.md"},
    "Reviewer": {"prompt": AI_DIR / "reviewer-prompt.md", "report": "reviewer-report.md"},
    "Tester":   {"prompt": AI_DIR / "tester-prompt.md",   "report": "tester-report.md"},
}

ROLE_FILES_WRITING = {
    "Writer": {"prompt": AI_DIR / "writer-prompt.md", "report": "writer-report.md"},
    "Editor": {"prompt": AI_DIR / "editor-prompt.md", "report": "editor-report.md"},
    "QA":     {"prompt": AI_DIR / "qa-prompt.md",     "report": "qa-report.md"},
}

ROLE_FILES_RCT_SEARCH = {
    "Formulator": {"prompt": AI_DIR / "formulator-prompt.md", "report": "formulator-report.md"},
    "Searcher":   {"prompt": AI_DIR / "searcher-prompt.md",   "report": "searcher-report.md"},
    "Validator":  {"prompt": AI_DIR / "validator-prompt.md",  "report": "validator-report.md"},
}

ALL_MODES: dict[str, dict] = {
    "coding":     ROLE_FILES_CODING,
    "writing":    ROLE_FILES_WRITING,
    "rct_search": ROLE_FILES_RCT_SEARCH,
}

# ---------------------------------------------------------------------------
# Role-specific documentation injection (least-privilege)
# ---------------------------------------------------------------------------
DOC_FILES_BY_ROLE: dict[str, list[Path]] = {
    "Builder":  [DOCS_CODING / "PRD.md",
                 DOCS_CODING / "architecture.md",
                 DOCS_CODING / "coding-standards.md"],
    "Reviewer": [DOCS_CODING / "PRD.md",
                 DOCS_CODING / "architecture.md",
                 DOCS_CODING / "decision-log.md"],
    "Tester":   [DOCS_CODING / "PRD.md",
                 DOCS_CODING / "architecture.md",
                 DOCS_CODING / "test-strategy.md"],
    "Writer": [DOCS_WRITING / "project-brief.md",
               DOCS_WRITING / "style-guide.md"],
    "Editor": [DOCS_WRITING / "project-brief.md",
               DOCS_WRITING / "editorial-standards.md"],
    "QA":     [DOCS_WRITING / "project-brief.md",
               DOCS_WRITING / "qa-checklist.md"],
    "Formulator": [DOCS_RCT_SEARCH / "pico-framework.md"],
    "Searcher":   [DOCS_RCT_SEARCH / "pico-framework.md",
                   DOCS_RCT_SEARCH / "database-guide.md"],
    "Validator":  [DOCS_RCT_SEARCH / "pico-framework.md",
                   DOCS_RCT_SEARCH / "validation-criteria.md"],
}

# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------
def call_openai_provider(
    prompt: str,
    model: str | None = None,
    max_tokens: int = 2048,
) -> str:
    """Send a prompt to the OpenAI chat completions endpoint."""
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to your .env file.")
    model = model or OPENAI_MODEL
    url   = "https://api.openai.com/v1/chat/completions"
    payload = json.dumps({
        "model":      model,
        "messages":   [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
    }).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}",
        },
        method="POST",
    )
    try:
        with urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
        choices = data.get("choices", [])
        if not choices or not choices[0].get("message", {}).get("content"):
            raise RuntimeError("OpenAI returned an empty response.")
        return choices[0]["message"]["content"]
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"OpenAI HTTP error {exc.code}: {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"OpenAI connection error: {exc.reason}") from exc
    except (KeyError, IndexError) as exc:
        raise RuntimeError(f"OpenAI unexpected response format: {exc}") from exc


def call_anthropic_provider(
    prompt: str,
    model: str | None = None,
    max_tokens: int = 2048,
) -> str:
    """Send a prompt to the Anthropic messages endpoint."""
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY is not set. Add it to your .env file.")
    model = model or ANTHROPIC_MODEL
    url   = "https://api.anthropic.com/v1/messages"
    payload = json.dumps({
        "model":      model,
        "messages":   [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
    }).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type":      "application/json",
            "x-api-key":         ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    try:
        with urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
        content = data.get("content", [])
        if not content or not content[0].get("text"):
            raise RuntimeError("Anthropic returned an empty response.")
        return content[0]["text"]
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Anthropic HTTP error {exc.code}: {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Anthropic connection error: {exc.reason}") from exc
    except (KeyError, IndexError) as exc:
        raise RuntimeError(f"Anthropic unexpected response format: {exc}") from exc


def call_ollama_provider(
    prompt: str,
    model: str | None = None,
    max_tokens: int = 2048,
) -> str:
    """Send a prompt to the local Ollama generate endpoint."""
    model = model or OLLAMA_MODEL
    url   = f"{OLLAMA_HOST}/api/generate"
    payload = json.dumps({
        "model":   model,
        "prompt":  prompt,
        "stream":  False,
        "options": {"num_predict": max_tokens},
    }).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
        response_text = data.get("response", "")
        if not response_text:
            raise RuntimeError("Ollama returned an empty response.")
        return response_text
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Ollama HTTP error {exc.code}: {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Ollama connection error: {exc.reason}") from exc


PROVIDERS: dict[str, callable] = {
    "ollama":    call_ollama_provider,
    "openai":    call_openai_provider,
    "anthropic": call_anthropic_provider,
}


def call_ai(
    prompt: str,
    provider: str = "ollama",
    model: str | None = None,
) -> str:
    """Dispatch an AI call to the correct provider function."""
    fn = PROVIDERS.get(provider, call_ollama_provider)
    return fn(prompt, model=model)


# ---------------------------------------------------------------------------
# Context builder (with optional RAG)
# ---------------------------------------------------------------------------
def build_project_context(
    role_name: str,
    query: str = "",
    mode: str = "",
    session_id: str = "",
) -> str:
    """
    Build the project context string injected into every AI prompt.
    Reads small docs/ files for the role, then optionally appends RAG chunks.
    """
    doc_files = DOC_FILES_BY_ROLE.get(role_name, [])
    sections: list[str] = []

    for doc_path in doc_files:
        if doc_path.exists():
            content = doc_path.read_text(encoding="utf-8", errors="replace").strip()
            if content:
                sections.append(f"### {doc_path.name}\n{content}")

    if query and mode and session_id:
        try:
            from src import rag
            rag_context = rag.retrieve(query, mode, session_id)
            if rag_context:
                sections.append(rag_context)
        except Exception as exc:  # noqa: BLE001
            print(f"[RAG] Retrieval warning: {exc}")

    return "\n\n".join(sections)


def truncate_context(text: str, max_chars: int = 2000) -> str:
    """
    Return *text* unchanged if it fits within *max_chars*, otherwise
    truncate and append an ellipsis character.
    """
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "…"


# ---------------------------------------------------------------------------
# File utilities
# ---------------------------------------------------------------------------
def read_text_file(path: Path) -> str:
    """Read a text file, strip whitespace. Returns '' if missing."""
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except (FileNotFoundError, OSError):
        return ""


def save_report(
    path: Path,
    role_name: str,
    model: str,
    task: str,
    response: str,
) -> None:
    """Append a role interaction to a markdown report file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = (
        f"\n## {role_name}\n"
        f"**Model:** {model}\n\n"
        f"**Task:** {task}\n\n"
        f"**Response:**\n{response}\n"
    )
    with path.open("a", encoding="utf-8") as fh:
        fh.write(entry)


def start_session_transcript(reports_dir: Path) -> Path:
    """
    Create a new timestamped session transcript file with a header.
    Returns the Path of the newly created file.
    """
    reports_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path      = reports_dir / f"session_{timestamp}.md"
    path.write_text(
        f"# Session Transcript\nStarted: {timestamp}\n",
        encoding="utf-8",
    )
    return path


def append_to_transcript(
    path: Path,
    role_name: str,
    step: int,
    task: str,
    response: str,
) -> None:
    """Append one interaction step to an existing transcript file."""
    entry = (
        f"\n## Step {step} — {role_name}\n"
        f"**Task:** {task}\n\n"
        f"**Response:**\n{response}\n"
    )
    with path.open("a", encoding="utf-8") as fh:
        fh.write(entry)


def print_session_summary(
    transcript_path: Path,
    step_count: int,
    role_counts: dict[str, int],
) -> None:
    """Print a summary of the completed session to stdout."""
    print(f"\n{'='*55}")
    print(f"  Session complete")
    print(f"  Transcript : {transcript_path.name}")
    print(f"  Total steps: {step_count}")
    if step_count == 0:
        print("  No steps recorded.")
    else:
        print("\n  Role usage:")
        for role, count in role_counts.items():
            if count > 0:
                print(f"    {role}: {count} step(s)")
    print(f"{'='*55}\n")


# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------
COLOURS = {
    "Builder":    "\033[94m",
    "Reviewer":   "\033[93m",
    "Tester":     "\033[92m",
    "Writer":     "\033[95m",
    "Editor":     "\033[96m",
    "QA":         "\033[91m",
    "Formulator": "\033[94m",
    "Searcher":   "\033[92m",
    "Validator":  "\033[93m",
}
RESET = "\033[0m"


def role_color(role_name: str) -> str:
    return COLOURS.get(role_name, RESET)


def choose_role(mode: str = "coding") -> tuple[str, dict]:
    """Prompt the user to pick a role and return (role_name, role_config)."""
    roles      = ALL_MODES[mode]
    role_names = list(roles.keys())

    print(f"\nSelect a role for {mode} mode:")
    for i, name in enumerate(role_names, start=1):
        colour = role_color(name)
        print(f"  {colour}{i}. {name}{RESET}")

    while True:
        choice = input("Enter number: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(role_names):
            name = role_names[int(choice) - 1]
            return name, roles[name]
        print(f"Please enter a number between 1 and {len(role_names)}.")


# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------
def list_sessions(reports_dir: str = str(REPORTS_DIR)) -> None:
    """Print all saved session transcript files, newest first."""
    path = Path(reports_dir)
    if not path.exists():
        print("No reports folder found.")
        return
    files = sorted(path.glob("session_*.md"), reverse=True)
    if not files:
        print("No session transcripts found.")
        return
    print(f"\n{'#':<4} {'Filename':<45} {'Size':>8}")
    print("-" * 60)
    for i, f in enumerate(files, start=1):
        print(f"{i:<4} {f.name:<45} {f.stat().st_size:>6} B")


def read_session(filename: str, reports_dir: str = str(REPORTS_DIR)) -> None:
    """Print the contents of a saved session transcript."""
    path = Path(reports_dir) / filename
    if not path.exists():
        print(f"File not found: {filename}. Use --list-sessions to see available files.")
        return
    print(f"--- {filename} ---")
    print(path.read_text(encoding="utf-8"))


def delete_session(filename: str, reports_dir: str = str(REPORTS_DIR)) -> None:
    """Delete a saved session transcript after confirmation."""
    path = Path(reports_dir) / filename
    if not path.exists():
        print(f"File not found: {filename}. Use --list-sessions to see available files.")
        return
    confirm = input(f"Delete '{filename}'? [y/N]: ").strip().lower()
    if confirm == "y":
        path.unlink()
        print(f"Deleted: {filename}")
    else:
        print("cancelled.")


def export_session(filename: str, reports_dir: str = str(REPORTS_DIR)) -> None:
    """Export a session transcript as a plain-text .txt file in the CWD."""
    src = Path(reports_dir) / filename
    if not src.exists():
        print(f"File not found: {filename}. Use --list-sessions to see available files.")
        return
    # Strip markdown and write as .txt
    raw     = src.read_text(encoding="utf-8")
    cleaned = re.sub(r"#{1,6}\s*", "", raw)          # remove headings
    cleaned = re.sub(r"\*\*(.+?)\*\*", r"\1", cleaned)  # remove bold
    cleaned = re.sub(r"\*(.+?)\*",   r"\1", cleaned)    # remove italic
    txt_name = Path(filename).stem + ".txt"
    dest     = Path(reports_dir) / txt_name
    dest.write_text(cleaned, encoding="utf-8")
    print(f"Exported to: {dest}")


def rename_session(filename: str, reports_dir: str = str(REPORTS_DIR)) -> None:
    """Rename a session transcript file, appending .md automatically."""
    src = Path(reports_dir) / filename
    if not src.exists():
        print(f"File not found: {filename}. Use --list-sessions to see available files.")
        return
    raw_name = input("New filename (without extension): ").strip()
    if not raw_name:
        print("Name cannot be empty. Cancelled.")
        return
    new_name = raw_name if raw_name.endswith(".md") else raw_name + ".md"
    dest = Path(reports_dir) / new_name
    if dest.exists():
        print(f"A file named '{new_name}' already exists. Cancelled.")
        return
    src.rename(dest)
    print(f"Renamed to: {new_name}")


def show_stats(reports_dir: str = str(REPORTS_DIR)) -> None:
    """Print session statistics for all saved transcripts."""
    path = Path(reports_dir)
    if not path.exists():
        print("No reports folder found.")
        return
    files = sorted(path.glob("session_*.md"))
    if not files:
        print("No session transcripts found.")
        return

    total_size  = 0
    role_counts: dict[str, int] = {}
    all_role_names = [r for mode_roles in ALL_MODES.values() for r in mode_roles]
    for role in all_role_names:
        role_counts[role] = 0

    for f in files:
        total_size += f.stat().st_size
        content     = f.read_text(encoding="utf-8", errors="replace")
        for role in all_role_names:
            role_counts[role] += content.count(f"## {role}")

    print(f"\nTotal sessions    : {len(files)}")
    print(f"Total size        : {total_size} bytes")
    print("\nRole usage across all sessions:")
    for role, count in role_counts.items():
        colour = role_color(role)
        print(f"  {colour}{role:<14}{RESET}: {count} interaction(s)")


# ---------------------------------------------------------------------------
# --list-roles
# ---------------------------------------------------------------------------
def list_roles(mode: str = "coding") -> None:
    """Print each role's prompt file and injected documentation for a mode."""
    roles = ALL_MODES.get(mode, {})
    print(f"\n{'='*55}")
    print(f"  Roles for mode: {mode}")
    print(f"{'='*55}")
    for role_name, role_cfg in roles.items():
        colour    = role_color(role_name)
        prompt    = Path(role_cfg["prompt"]).relative_to(BASE_DIR)
        doc_files = DOC_FILES_BY_ROLE.get(role_name, [])
        doc_names = [d.name for d in doc_files]
        print(f"\n{colour}{role_name}{RESET}")
        print(f"  Prompt : {prompt}")
        print(f"  Docs   : {', '.join(doc_names) if doc_names else 'none'}")
    print(f"\n{'='*55}\n")


# ---------------------------------------------------------------------------
# Main session loop
# ---------------------------------------------------------------------------
def main(
    model_override: str | None = None,
    dry_run: bool = False,
    mode: str = "coding",
    provider: str = "ollama",
) -> None:
    """Run an interactive AI session."""
    session_id   = uuid.uuid4().hex[:8]
    transcript   = start_session_transcript(REPORTS_DIR)
    step_count   = 0
    role_counts: dict[str, int] = {
        r: 0 for mode_roles in ALL_MODES.values() for r in mode_roles
    }

    print(f"\n{'='*55}")
    print(f"  AI Automation Tool  v{VERSION}")
    print(f"  Mode    : {mode}")
    print(f"  Provider: {provider}")
    print(f"  Session : {session_id}")
    if dry_run:
        print("  DRY RUN — AI calls will be skipped")
    print(f"{'='*55}\n")

    # --- Index uploads (RAG) ------------------------------------------------
    rag_enabled   = False
    upload_folder = UPLOAD_DIR / mode
    upload_folder.mkdir(parents=True, exist_ok=True)

    if not dry_run:
        try:
            from src import rag as rag_module
            n_chunks = rag_module.index_uploads(
                mode=mode,
                session_id=session_id,
                upload_base=str(UPLOAD_DIR),
            )
            if n_chunks > 0:
                rag_enabled = True
                print(f"[RAG] Indexed {n_chunks} chunk(s) from uploads/{mode}/\n")
        except Exception as exc:  # noqa: BLE001
            print(f"[RAG] Indexing skipped: {exc}\n")

    # --- Role selection ------------------------------------------------------
    role_name, role_cfg = choose_role(mode)
    colour      = role_color(role_name)
    prompt_path = Path(role_cfg["prompt"])

    if not prompt_path.exists():
        print(f"Prompt file not found: {prompt_path}")
        sys.exit(1)

    role_prompt = prompt_path.read_text(encoding="utf-8", errors="replace")
    print(f"\n{colour}Starting session as {role_name}{RESET}")
    print("Type your task below. Press Ctrl+C to end the session.\n")

    previous_response = ""

    try:
        while True:
            task = input(f"{colour}{role_name} >{RESET} ").strip()
            if not task:
                continue

            context = build_project_context(
                role_name=role_name,
                query=task if rag_enabled else "",
                mode=mode,
                session_id=session_id,
            )

            parts = [role_prompt]
            if context:
                parts.append(f"## Project Context\n{context}")
            if previous_response:
                parts.append(
                    f"## Previous Response\n{truncate_context(previous_response)}"
                )
            parts.append(f"## Task\n{task}")
            full_prompt = "\n\n".join(parts)

            start = time.time()
            if dry_run:
                response = f"[DRY RUN] {role_name} would respond here."
            else:
                try:
                    response = call_ai(
                        prompt=full_prompt,
                        provider=provider,
                        model=model_override,
                    )
                except RuntimeError as exc:
                    response = f"[ERROR] {exc}"

            elapsed = time.time() - start
            step_count += 1
            role_counts[role_name] = role_counts.get(role_name, 0) + 1

            print(f"\n{colour}--- {role_name} response ({elapsed:.1f}s) ---{RESET}")
            print(response)
            print()

            append_to_transcript(
                path=transcript,
                role_name=role_name,
                step=step_count,
                task=task,
                response=response,
            )
            previous_response = response

    except KeyboardInterrupt:
        print(f"\n\n{colour}Session ended.{RESET}")

    finally:
        print_session_summary(transcript, step_count, role_counts)

        if rag_enabled and not dry_run:
            try:
                from src import rag as rag_module
                rag_module.clear_session(mode=mode, session_id=session_id)
                print("[RAG] Session collection cleared.")
            except Exception as exc:  # noqa: BLE001
                print(f"[RAG] Clear warning: {exc}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="AI Automation Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python src/main.py                           # coding session\n"
            "  python src/main.py --mode writing            # writing mode\n"
            "  python src/main.py --mode rct_search         # RCT search mode\n"
            "  python src/main.py --model llama3.2:3b       # different model\n"
            "  python src/main.py --provider openai         # use OpenAI\n"
            "  python src/main.py --list-sessions           # list transcripts\n"
            "  python src/main.py --list-roles              # show roles/docs\n"
            "  python src/main.py --list-roles --mode rct_search\n"
            "  python src/main.py --dry-run                 # simulate session\n"
            "  python src/main.py --version                 # show version\n"
        ),
    )
    parser.add_argument("--model",          type=str,  default=None)
    parser.add_argument("--mode",           type=str,  default="coding",
                        choices=["coding", "writing", "rct_search"])
    parser.add_argument("--provider",       type=str,  default="ollama",
                        choices=["ollama", "openai", "anthropic"])
    parser.add_argument("--list-sessions",  action="store_true", default=False)
    parser.add_argument("--read-session",   type=str,  default=None, metavar="FILENAME")
    parser.add_argument("--delete-session", type=str,  default=None, metavar="FILENAME")
    parser.add_argument("--export-session", type=str,  default=None, metavar="FILENAME")
    parser.add_argument("--rename-session", type=str,  default=None, metavar="FILENAME")
    parser.add_argument("--stats",          action="store_true", default=False)
    parser.add_argument("--dry-run",        action="store_true", default=False)
    parser.add_argument("--version",        action="version",
                        version=f"AI Automation Tool v{VERSION}")
    parser.add_argument("--list-roles",     action="store_true", default=False)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.list_sessions:
        list_sessions(reports_dir=str(REPORTS_DIR))
    elif args.read_session:
        read_session(filename=args.read_session, reports_dir=str(REPORTS_DIR))
    elif args.delete_session:
        delete_session(filename=args.delete_session, reports_dir=str(REPORTS_DIR))
    elif args.export_session:
        export_session(filename=args.export_session, reports_dir=str(REPORTS_DIR))
    elif args.rename_session:
        rename_session(filename=args.rename_session, reports_dir=str(REPORTS_DIR))
    elif args.stats:
        show_stats(reports_dir=str(REPORTS_DIR))
    elif args.list_roles:
        list_roles(mode=args.mode)
    else:
        main(
            model_override=args.model,
            dry_run=args.dry_run,
            mode=args.mode,
            provider=args.provider,
        )
