from __future__ import annotations

import json
import os
import argparse
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from colorama import Fore, init as colorama_init
from dotenv import load_dotenv

colorama_init(autoreset=True)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

AI_DIR        = PROJECT_ROOT / "ai"
DOCS_DIR      = PROJECT_ROOT / "docs"
DOCS_CODING   = DOCS_DIR / "coding"
DOCS_WRITING  = DOCS_DIR / "writing"
DOCS_RCT_SEARCH = DOCS_DIR / "rct_search"
REPORTS_DIR   = PROJECT_ROOT / "reports"

DEFAULT_OLLAMA_HOST  = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "qwen2.5-coder:3b"
DEFAULT_PROVIDER     = "ollama"
DEFAULT_MODE         = "coding"

VERSION = "2.0.0"

# ---------------------------------------------------------------------------
# Role file sets - one dictionary per mode
# ---------------------------------------------------------------------------

ROLE_FILES_CODING = {
    "1": ("Builder",  AI_DIR / "builder-prompt.md",  REPORTS_DIR / "builder-output.md"),
    "2": ("Reviewer", AI_DIR / "reviewer-prompt.md", REPORTS_DIR / "review-log.md"),
    "3": ("Tester",   AI_DIR / "tester-prompt.md",   REPORTS_DIR / "test-report.md"),
}

ROLE_FILES_WRITING = {
    "1": ("Writer", AI_DIR / "writer-prompt.md", REPORTS_DIR / "writer-output.md"),
    "2": ("Editor", AI_DIR / "editor-prompt.md", REPORTS_DIR / "editor-log.md"),
    "3": ("QA",     AI_DIR / "qa-prompt.md",     REPORTS_DIR / "qa-report.md"),
}

ROLE_FILES_RCT_SEARCH = {
    "1": ("Formulator", AI_DIR / "formulator-prompt.md", REPORTS_DIR / "formulator-output.md"),
    "2": ("Searcher",   AI_DIR / "searcher-prompt.md",   REPORTS_DIR / "searcher-output.md"),
    "3": ("Validator",  AI_DIR / "validator-prompt.md",  REPORTS_DIR / "validator-output.md"),
}

ALL_MODES = {
    "coding":     ROLE_FILES_CODING,
    "writing":    ROLE_FILES_WRITING,
    "rct_search": ROLE_FILES_RCT_SEARCH,
}


# ---------------------------------------------------------------------------
# Role-aware documentation files
# Each role receives only the docs relevant to its specific job.
# ---------------------------------------------------------------------------

DOC_FILES_BY_ROLE = {
    # Coding roles
    "Builder":  [
        DOCS_CODING / "PRD.md",
        DOCS_CODING / "architecture.md",
        DOCS_CODING / "coding-standards.md",
    ],
    "Reviewer": [
        DOCS_CODING / "PRD.md",
        DOCS_CODING / "architecture.md",
        DOCS_CODING / "decision-log.md",
    ],
    "Tester": [
        DOCS_CODING / "PRD.md",
        DOCS_CODING / "architecture.md",
        DOCS_CODING / "test-strategy.md",
    ],
    # Writing roles
    "Writer": [
        DOCS_WRITING / "project-brief.md",
        DOCS_WRITING / "style-guide.md",
    ],
    "Editor": [
        DOCS_WRITING / "project-brief.md",
        DOCS_WRITING / "editorial-standards.md",
    ],
    "QA": [
        DOCS_WRITING / "project-brief.md",
        DOCS_WRITING / "qa-checklist.md",
    ],
    # RCT search roles
    "Formulator": [
        DOCS_RCT_SEARCH / "pico-framework.md",
    ],
    "Searcher": [
        DOCS_RCT_SEARCH / "pico-framework.md",
        DOCS_RCT_SEARCH / "database-guide.md",
    ],
    "Validator": [
        DOCS_RCT_SEARCH / "pico-framework.md",
        DOCS_RCT_SEARCH / "validation-criteria.md",
    ],
}

def list_roles(mode: str = "coding") -> None:
    """Print the roles for the given mode and the doc files each role receives."""
    role_files = ALL_MODES.get(mode, ROLE_FILES_CODING)

    print(f"\n{Fore.MAGENTA}{'=' * 42}")
    print(f"{Fore.MAGENTA}  Roles — {mode} mode")
    print(f"{Fore.MAGENTA}{'=' * 42}")

    for key, (role_name, prompt_path, _) in role_files.items():
        color = role_color(role_name)
        doc_files = DOC_FILES_BY_ROLE.get(role_name, [])
        doc_names = [f.name for f in doc_files] if doc_files else ["(none)"]
        print(f"\n{color}{key}. {role_name} AI")
        print(f"   Prompt : {prompt_path.relative_to(PROJECT_ROOT)}")
        print(f"   Docs   : {', '.join(doc_names)}")

    print(f"\n{Fore.MAGENTA}{'=' * 42}\n")


def role_color(role_name: str) -> str:
    """Return a colorama Fore colour code for the given role name."""
    colors = {
        "Builder":    Fore.CYAN,
        "Reviewer":   Fore.YELLOW,
        "Tester":     Fore.GREEN,
        "Writer":     Fore.CYAN,
        "Editor":     Fore.YELLOW,
        "QA":         Fore.GREEN,
        "Formulator": Fore.CYAN,
        "Searcher":   Fore.YELLOW,
        "Validator":  Fore.GREEN,
    }
    return colors.get(role_name, Fore.WHITE)


def read_text_file(path: Path) -> str:
    """Read a file and return its content stripped of whitespace. Returns empty string if missing."""
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def build_project_context(role_name: str) -> str:
    """Combine doc files for the given role into a context string.
    Each role receives only the documentation relevant to its specific job."""
    doc_files = DOC_FILES_BY_ROLE.get(role_name, [])
    sections = []
    for path in doc_files:
        content = read_text_file(path)
        if content:
            sections.append(f"## {path.name}\n{content}")
    return "\n\n".join(sections)


def choose_role(mode: str = "coding") -> tuple[str, Path, Path]:
    """Prompt the user to choose an AI role for the active mode. Loops until a valid choice is made."""
    role_files = ALL_MODES.get(mode, ROLE_FILES_CODING)
    while True:
        print(f"\n{Fore.WHITE}Choose AI role:")
        for key, (role_name, _, _) in role_files.items():
            color = role_color(role_name)
            print(f"{color}{key}. {role_name} AI")

        choice = input("\nEnter 1, 2, or 3: ").strip()

        if choice in role_files:
            return role_files[choice]

        print(f"{Fore.RED}Invalid choice. Please enter 1, 2, or 3.")


# ---------------------------------------------------------------------------
# Provider caller functions
# ---------------------------------------------------------------------------

def call_ollama_provider(model: str, prompt: str, host: str) -> str:
    """Send a prompt to the Ollama API and return the response text."""
    url = host.rstrip("/") + "/api/generate"

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }

    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=180) as response:
            raw_response = response.read().decode("utf-8")
    except HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Ollama HTTP error {error.code}: {body}") from error
    except URLError as error:
        raise RuntimeError(
            "Could not connect to Ollama. Make sure Ollama is running, then try: ollama list"
        ) from error
    except TimeoutError as error:
        raise RuntimeError(
            "Ollama took too long to respond. Try again or use a smaller model."
        ) from error

    result = json.loads(raw_response)

    if "error" in result:
        raise RuntimeError(f"Ollama error: {result['error']}")

    response_text = result.get("response", "").strip()

    if not response_text:
        raise RuntimeError(f"Ollama returned no response. Raw result: {result}")

    return response_text


def call_openai_provider(model: str, prompt: str, host: str) -> str:
    """Send a prompt to the OpenAI API and return the response text."""
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add it to your .env file."
        )

    url = "https://api.openai.com/v1/chat/completions"

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }

    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=180) as response:
            raw_response = response.read().decode("utf-8")
    except HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI HTTP error {error.code}: {body}") from error
    except URLError as error:
        raise RuntimeError(
            "Could not connect to OpenAI. Check your internet connection."
        ) from error
    except TimeoutError as error:
        raise RuntimeError(
            "OpenAI took too long to respond. Try again."
        ) from error

    result = json.loads(raw_response)

    if "error" in result:
        raise RuntimeError(f"OpenAI error: {result['error']}")

    response_text = result["choices"][0]["message"]["content"].strip()

    if not response_text:
        raise RuntimeError(f"OpenAI returned no response. Raw result: {result}")

    return response_text


def call_anthropic_provider(model: str, prompt: str, host: str) -> str:
    """Send a prompt to the Anthropic API and return the response text."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Add it to your .env file."
        )

    url = "https://api.anthropic.com/v1/messages"

    payload = {
        "model": model,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }

    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=180) as response:
            raw_response = response.read().decode("utf-8")
    except HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Anthropic HTTP error {error.code}: {body}") from error
    except URLError as error:
        raise RuntimeError(
            "Could not connect to Anthropic. Check your internet connection."
        ) from error
    except TimeoutError as error:
        raise RuntimeError(
            "Anthropic took too long to respond. Try again."
        ) from error

    result = json.loads(raw_response)

    if "error" in result:
        raise RuntimeError(f"Anthropic error: {result['error']}")

    response_text = result["content"][0]["text"].strip()

    if not response_text:
        raise RuntimeError(f"Anthropic returned no response. Raw result: {result}")

    return response_text


PROVIDERS = {
    "ollama":    call_ollama_provider,
    "openai":    call_openai_provider,
    "anthropic": call_anthropic_provider,
}


def call_ai(model: str, prompt: str, host: str, provider: str = "ollama") -> str:
    """Universal AI caller. Dispatches to the correct provider function."""
    caller = PROVIDERS.get(provider, call_ollama_provider)
    return caller(model, prompt, host)


def save_report(
    report_path: Path, role_name: str, model: str, task: str, response_text: str
) -> None:
    """Append a formatted AI response entry to the role report file."""
    report_path.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    entry = f"""
# {role_name} AI Response

Time: {timestamp}
Model: {model}

## User Task

{task}

## AI Response

{response_text}

---
"""

    with report_path.open("a", encoding="utf-8") as file:
        file.write(entry)


def start_session_transcript(reports_dir: Path) -> Path:
    """Create a timestamped session transcript file and return its path."""
    reports_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    transcript_path = reports_dir / f"session_{timestamp}.md"
    header = (
        f"# Session Transcript\n\n"
        f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n"
    )
    transcript_path.write_text(header, encoding="utf-8")
    return transcript_path


def append_to_transcript(
    transcript_path: Path, step: int, role_name: str, task: str, response_text: str
) -> None:
    """Append a step entry to the session transcript file."""
    entry = (
        f"## Step {step} - {role_name} AI\n\n"
        f"**Task:** {task}\n\n"
        f"**Response:**\n\n{response_text}\n\n---\n"
    )
    with transcript_path.open("a", encoding="utf-8") as file:
        file.write(entry)


def truncate_context(text: str, max_chars: int = 2000) -> str:
    """Truncate text to max_chars. Appends a notice if truncation occurred."""
    if len(text) <= max_chars:
        return text
    return (
        text[:max_chars]
        + f"\n\n[Response truncated at {max_chars} characters to keep prompt size manageable.]"
    )


def print_session_summary(
    step: int, roles_used: list[str], transcript_path: Path
) -> None:
    """Print a formatted session summary showing steps completed, roles used, and transcript path."""
    role_counts = Counter(roles_used)
    roles_str = ", ".join(
        f"{role} ({count})" for role, count in role_counts.items()
    )
    print("\n" + f"{Fore.MAGENTA}" + "=" * 42)
    print(f"{Fore.MAGENTA}Session Summary")
    print(f"{Fore.MAGENTA}" + "=" * 42)
    print(f"Steps completed : {step}")
    print(f"Roles used      : {roles_str if roles_str else 'none'}")
    print(f"Transcript saved: {transcript_path}")
    print(f"{Fore.MAGENTA}" + "=" * 42 + "\n")


def list_sessions(reports_dir: str = "reports") -> None:
    """List all past session transcripts in reports/, sorted newest first."""
    reports_path = Path(reports_dir)

    if not reports_path.exists():
        print("No reports folder found. No sessions have been run yet.")
        return

    session_files = sorted(
        reports_path.glob("session_*.md"),
        reverse=True,
    )

    if not session_files:
        print("No session transcripts found in reports/.")
        return

    print(f"\nFound {len(session_files)} session transcript(s):\n")
    for i, f in enumerate(session_files, start=1):
        print(f"  {i:>3}.  {f.name}")
    print()


def read_session(filename: str, reports_dir: str = "reports") -> None:
    """Print the contents of a named session transcript to the terminal."""
    reports_path = Path(reports_dir)
    session_path = reports_path / filename

    if not session_path.exists():
        print(f"{Fore.RED}Session file not found: {session_path}")
        print(f"{Fore.YELLOW}Use --list-sessions to see available transcripts.")
        return

    content = session_path.read_text(encoding="utf-8")
    print(f"\n{Fore.MAGENTA}{'=' * 42}")
    print(f"{Fore.MAGENTA}  Session: {filename}")
    print(f"{Fore.MAGENTA}{'=' * 42}\n")
    print(content)
    print(f"{Fore.MAGENTA}{'=' * 42}\n")


def delete_session(filename: str, reports_dir: str = "reports") -> None:
    """Delete a named session transcript after confirmation."""
    reports_path = Path(reports_dir)
    session_path = reports_path / filename

    if not session_path.exists():
        print(f"{Fore.RED}Session file not found: {session_path}")
        print(f"{Fore.YELLOW}Use --list-sessions to see available transcripts.")
        return

    confirm = input(
        f"{Fore.YELLOW}Delete {filename}? This cannot be undone. Type 'yes' to confirm: "
    ).strip().lower()

    if confirm != "yes":
        print(f"{Fore.WHITE}Delete cancelled.")
        return

    session_path.unlink()
    print(f"{Fore.GREEN}Deleted: {filename}")


def export_session(filename: str, reports_dir: str = "reports") -> None:
    """Export a session transcript as a plain text file with markdown stripped."""
    reports_path = Path(reports_dir)
    session_path = reports_path / filename

    if not session_path.exists():
        print(f"{Fore.RED}Session file not found: {session_path}")
        print(f"{Fore.YELLOW}Use --list-sessions to see available transcripts.")
        return

    content = session_path.read_text(encoding="utf-8")

    plain = content
    for symbol in ("##", "#", "**", "__", "---", "==="):
        plain = plain.replace(symbol, "")

    export_filename = Path(filename).stem + ".txt"
    export_path = reports_path / export_filename

    export_path.write_text(plain.strip(), encoding="utf-8")
    print(f"{Fore.GREEN}Exported: {export_path}")


def show_stats(reports_dir: str = "reports") -> None:
    """Scan all session transcripts and print summary statistics."""
    reports_path = Path(reports_dir)

    if not reports_path.exists():
        print("No reports folder found. No sessions have been run yet.")
        return

    session_files = sorted(
        reports_path.glob("session_*.md"),
        reverse=True,
    )

    if not session_files:
        print("No session transcripts found in reports/.")
        return

    total_sessions = len(session_files)
    most_recent = session_files[0].name
    role_counts: dict[str, int] = {}

    for session_file in session_files:
        content = session_file.read_text(encoding="utf-8")
        for line in content.splitlines():
            for role in (
                "Builder", "Reviewer", "Tester",
                "Writer", "Editor", "QA",
                "Formulator", "Searcher", "Validator",
            ):
                if "## Step" in line and f"{role} AI" in line:
                    role_counts[role] = role_counts.get(role, 0) + 1

    print(f"\n{Fore.MAGENTA}{'=' * 42}")
    print(f"{Fore.MAGENTA}  Session Statistics")
    print(f"{Fore.MAGENTA}{'=' * 42}")
    print(f"  Total sessions    : {total_sessions}")
    print(f"  Most recent       : {most_recent}")
    print(f"  Role usage across all sessions:")
    for role, count in role_counts.items():
        color = role_color(role)
        print(f"    {color}{role:<10}: {count} step(s)")
    if not role_counts:
        print(f"  No steps recorded.")
    print(f"{Fore.MAGENTA}{'=' * 42}\n")


def rename_session(filename: str, reports_dir: str = "reports") -> None:
    """Rename a session transcript file to a user-supplied name."""
    reports_path = Path(reports_dir)
    session_path = reports_path / filename

    if not session_path.exists():
        print(f"{Fore.RED}Session file not found: {session_path}")
        print(f"{Fore.YELLOW}Use --list-sessions to see available transcripts.")
        return

    new_name = input(
        f"{Fore.WHITE}Enter new name for '{filename}' (without extension): "
    ).strip()

    if not new_name:
        print(f"{Fore.RED}Name cannot be empty. Rename cancelled.")
        return

    new_filename = new_name + ".md"
    new_path = reports_path / new_filename

    if new_path.exists():
        print(f"{Fore.RED}A file named '{new_filename}' already exists. Rename cancelled.")
        return

    session_path.rename(new_path)
    print(f"{Fore.GREEN}Renamed: {filename} -> {new_filename}")

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="AI Automation Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python src/main.py                        # start a session\n"
            "  python src/main.py --mode writing         # writing mode\n"
            "  python src/main.py --mode rct_search      # RCT search mode\n"
            "  python src/main.py --model llama3.2:3b    # different model\n"
            "  python src/main.py --provider openai      # use OpenAI\n"
            "  python src/main.py --list-sessions        # list transcripts\n"
            "  python src/main.py --list-roles           # show roles and docs\n"
            "  python src/main.py --list-roles --mode writing\n"
            "  python src/main.py --dry-run              # simulate session\n"
            "  python src/main.py --version              # show version\n"
        ),
    )
    parser.add_argument("--model",          type=str,  default=None)
    parser.add_argument("--mode",           type=str,  default="coding", choices=["coding", "writing", "rct_search"])
    parser.add_argument("--provider",       type=str,  default="ollama", choices=["ollama", "openai", "anthropic"])
    parser.add_argument("--list-sessions",  action="store_true", default=False)
    parser.add_argument("--read-session",   type=str,  default=None, metavar="FILENAME")
    parser.add_argument("--delete-session", type=str,  default=None, metavar="FILENAME")
    parser.add_argument("--export-session", type=str,  default=None, metavar="FILENAME")
    parser.add_argument("--rename-session", type=str,  default=None, metavar="FILENAME")
    parser.add_argument("--stats",          action="store_true", default=False)
    parser.add_argument("--dry-run",        action="store_true", default=False)
    parser.add_argument("--version",        action="version", version=f"AI Automation Tool v{VERSION}")
    parser.add_argument("--list-roles",     action="store_true", default=False)
    return parser.parse_args()


def main(
    model_override: str | None = None,
    dry_run: bool = False,
    mode: str = DEFAULT_MODE,
    provider: str = DEFAULT_PROVIDER,
) -> None:
    """Run the main interactive AI automation session loop."""

    load_dotenv(PROJECT_ROOT / ".env")

    # Resolve model based on active provider
    if model_override:
        model = model_override
    elif provider == "openai":
        model = os.getenv("OPENAI_MODEL", "gpt-4o")
    elif provider == "anthropic":
        model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    else:
        model = os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)

    host = os.getenv("OLLAMA_HOST", DEFAULT_OLLAMA_HOST)

    print(f"\n{Fore.MAGENTA}{'=' * 42}")
    print(f"{Fore.MAGENTA}  AI Automation Tool  v{VERSION}")
    print(f"{Fore.MAGENTA}{'=' * 42}")
    print(f"  Mode     : {Fore.CYAN}{mode}")
    print(f"  Provider : {Fore.CYAN}{provider}")
    print(f"  Model    : {Fore.CYAN}{model}")
    print(f"{Fore.WHITE}  Host     : {host}")
    if dry_run:
        print(f"{Fore.YELLOW}  DRY RUN  : AI will not be called.")
    print(f"{Fore.MAGENTA}{'=' * 42}")
    print(f"{Fore.WHITE}  Type 'quit' or 'exit' at any prompt to stop.")
    print(f"{Fore.MAGENTA}{'=' * 42}\n")

    transcript_path = start_session_transcript(REPORTS_DIR)
    print(f"Session transcript: {transcript_path}\n")

    step = 0
    roles_used = []
    last_response = ""

    while True:
        role_name, prompt_path, report_path = choose_role(mode=mode)

        role_prompt       = read_text_file(prompt_path)
        project_context   = build_project_context(role_name=role_name)

        task = input("\nEnter your task for the AI: ").strip()

        if task.lower() in ("quit", "exit"):
            print("\nGoodbye.")
            break

        if not task:
            print("Task cannot be empty. Please try again.")
            continue

        safety_rules = """
Safety rules:
- Do not include secrets, passwords, or API keys.
- Do not create malware, spyware, keyloggers, credential theft tools, exploit payloads, reverse shells, or unauthorized scanning tools.
- If a task is unsafe, refuse and suggest a safe defensive alternative.
"""

        previous_context = (
            f"\nPrevious AI output:\n\n{truncate_context(last_response)}\n"
            if last_response
            else ""
        )

        full_prompt = f"""
{role_prompt}

{safety_rules}

Project context:

{project_context}

{previous_context}User task:

{task}

Respond as the {role_name} AI.
"""

        color = role_color(role_name)

        print(
            f"\n{color}Sending task to {role_name} AI "
            f"using {provider} model {model}...\n"
        )

        if dry_run:
            response_text = (
                f"[DRY RUN] Simulated response from {role_name} AI. "
                f"Provider: {provider}. Model: {model}. Mode: {mode}."
            )
        else:
            try:
                response_text = call_ai(
                    model=model,
                    prompt=full_prompt,
                    host=host,
                    provider=provider,
                )
            except RuntimeError as error:
                print(f"\n{Fore.RED}Error: {error}")
                print(f"{Fore.RED}Please check your provider settings and try again.\n")
                continue

        step += 1
        roles_used.append(role_name)
        last_response = response_text

        print(f"\n{color}AI RESPONSE")
        print(color + "=" * 60)
        print(response_text)
        print(color + "=" * 60)

        save_report(report_path, role_name, model, task, response_text)
        append_to_transcript(transcript_path, step, role_name, task, response_text)

        print(f"\nSaved response to: {report_path}")
        print(f"Session transcript updated: {transcript_path}")

        again = (
            input(
                "\nSend another task? (yes to continue, anything else to quit): "
            )
            .strip()
            .lower()
        )
        if again != "yes":
            print_session_summary(step, roles_used, transcript_path)
            print("Goodbye.")
            break


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
        main(model_override=args.model, dry_run=args.dry_run, mode=args.mode, provider=args.provider)
