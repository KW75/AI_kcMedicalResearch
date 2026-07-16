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

AI_DIR = PROJECT_ROOT / "ai"
DOCS_DIR = PROJECT_ROOT / "docs"
REPORTS_DIR = PROJECT_ROOT / "reports"

DEFAULT_OLLAMA_HOST = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "qwen2.5-coder:3b"
VERSION = "1.0.0"


ROLE_FILES = {
    "1": ("Builder", AI_DIR / "builder-prompt.md", REPORTS_DIR / "builder-output.md"),
    "2": ("Reviewer", AI_DIR / "reviewer-prompt.md", REPORTS_DIR / "review-log.md"),
    "3": ("Tester", AI_DIR / "tester-prompt.md", REPORTS_DIR / "test-report.md"),
}

DOC_FILES = [
    DOCS_DIR / "PRD.md",
    DOCS_DIR / "architecture.md",
    DOCS_DIR / "coding-standards.md",
    DOCS_DIR / "test-strategy.md",
    DOCS_DIR / "decision-log.md",
]


def role_color(role_name: str) -> str:
    """Return a colorama Fore colour code for the given role name."""
    colors = {
        "Builder": Fore.CYAN,
        "Reviewer": Fore.YELLOW,
        "Tester": Fore.GREEN,
    }
    return colors.get(role_name, Fore.WHITE)


def read_text_file(path: Path) -> str:
    """Read a file and return its content stripped of whitespace. Returns empty string if missing."""

    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def build_project_context() -> str:
    """Combine all project doc files into a single context string for the AI prompt."""

    sections = []
    for path in DOC_FILES:
        content = read_text_file(path)
        if content:
            sections.append(f"## {path.name}\n{content}")
    return "\n\n".join(sections)


def choose_role() -> tuple[str, Path, Path]:
    """Prompt the user to choose an AI role. Loops until a valid choice is made."""

    while True:
        print(f"\n{Fore.WHITE}Choose AI role:")
        print(f"{Fore.CYAN}1. Builder AI")
        print(f"{Fore.YELLOW}2. Reviewer AI")
        print(f"{Fore.GREEN}3. Tester AI")

        choice = input("\nEnter 1, 2, or 3: ").strip()

        if choice in ROLE_FILES:
            return ROLE_FILES[choice]

        print(f"{Fore.RED}Invalid choice. Please enter 1, 2, or 3.")

def call_ollama(model: str, prompt: str, host: str) -> str:
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

    # Strip common markdown symbols
    plain = content
    for symbol in ("##", "#", "**", "__", "---", "==="):
        plain = plain.replace(symbol, "")

    export_filename = Path(filename).stem + ".txt"
    export_path = reports_path / export_filename

    export_path.write_text(plain.strip(), encoding="utf-8")
    print(f"{Fore.GREEN}Exported: {export_path}")


def parse_args() -> argparse.Namespace:
    """Parse and return command line arguments."""
    parser = argparse.ArgumentParser(
        description="AI Automation Tool - local AI assistant using Ollama",
        epilog=(
            "Examples:\n"
            "  python src/main.py                        # start a session\n"
            "  python src/main.py --model llama3.2:3b    # use a different model\n"
            "  python src/main.py --list-sessions        # list past transcripts\n"
            "  python src/main.py --version              # show version\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Ollama model to use (overrides OLLAMA_MODEL in .env)",
    )
    parser.add_argument(
        "--list-sessions",
        action="store_true",
        default=False,
        help="List all past session transcripts in reports/ and exit",
    )
    parser.add_argument(
        "--read-session",
        type=str,
        default=None,
        metavar="FILENAME",
        help="Print a past session transcript to the terminal by filename",
    )

    parser.add_argument(
        "--delete-session",
        type=str,
        default=None,
        metavar="FILENAME",
        help="Delete a past session transcript by filename",
    )

    parser.add_argument(
        "--export-session",
        type=str,
        default=None,
        metavar="FILENAME",
        help="Export a session transcript as a plain text file",
    )


    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Run a session without calling Ollama - returns a fake response for testing",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"AI Automation Tool v{VERSION}",
        help="Show version and exit",
    )
    return parser.parse_args()


def main(model_override: str | None = None, dry_run: bool = False) -> None:
    """Run the main interactive AI automation session loop."""

    load_dotenv(PROJECT_ROOT / ".env")

    model = model_override or os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
    host = os.getenv("OLLAMA_HOST", DEFAULT_OLLAMA_HOST)

    print(f"\n{Fore.MAGENTA}{'=' * 42}")
    print(f"{Fore.MAGENTA}  AI Automation Tool  v{VERSION}")
    print(f"{Fore.MAGENTA}{'=' * 42}")
    print(f"  Model : {Fore.CYAN}{model}")
    print(f"{Fore.WHITE}  Host  : {host}")
    if dry_run:
        print(f"{Fore.YELLOW}  Mode  : DRY RUN - Ollama will not be called.")
    print(f"{Fore.MAGENTA}{'=' * 42}")
    print(f"{Fore.WHITE}  Type 'quit' or 'exit' at any prompt to stop.")
    print(f"{Fore.MAGENTA}{'=' * 42}\n")


    transcript_path = start_session_transcript(REPORTS_DIR)
    print(f"Session transcript: {transcript_path}\n")

    step = 0
    roles_used = []
    last_response = ""

    while True:
        role_name, prompt_path, report_path = choose_role()

        role_prompt = read_text_file(prompt_path)
        project_context = build_project_context()

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
            f"\n{color}Sending task to local {role_name} AI "
            f"using Ollama model {model}...\n"
        )

        if dry_run:
            response_text = (
                f"[DRY RUN] This is a simulated response from the {role_name} AI. "
                f"Ollama was not called. Model would have been: {model}"
            )
        else:
            try:
                response_text = call_ollama(model=model, prompt=full_prompt, host=host)
            except RuntimeError as error:
                print(f"\n{Fore.RED}Error: {error}")
                print(f"{Fore.RED}Please check Ollama is running and try again.\n")
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
    else:
        main(model_override=args.model, dry_run=args.dry_run)




