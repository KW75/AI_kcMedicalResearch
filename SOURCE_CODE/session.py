"""
Session management for AI kcMedicalResearch.
Handles session transcripts, stats, export, rename, and deletion.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
def _get_reports_dir() -> Path:
    """Get reports directory, avoiding circular imports."""
    return Path(__file__).resolve().parent.parent / "reports"


# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------
COLOURS = {
    "Builder": "\033[94m",
    "Reviewer": "\033[93m",
    "Tester": "\033[92m",
    "Writer": "\033[95m",
    "Editor": "\033[96m",
    "QA": "\033[91m",
    "Formulator": "\033[94m",
    "Searcher": "\033[92m",
    "Validator": "\033[93m",
    "Appraiser": "\033[95m",
    "Methodologist": "\033[96m",
    "Summariser": "\033[92m",
    "Researcher": "\033[94m",
}
RESET = "\033[0m"


def role_color(role_name: str) -> str:
    return COLOURS.get(role_name, RESET)


# ---------------------------------------------------------------------------
# Transcript management
# ---------------------------------------------------------------------------
def start_session_transcript(reports_dir: Path = None) -> Path:
    """Create a new timestamped session transcript file. Returns its Path."""
    reports_dir = reports_dir or _get_reports_dir()
    reports_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = reports_dir / f"session_{timestamp}.md"
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
        f"\n## Step {step}  - {role_name}\n"
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
    print(f"\n{'=' * 55}")
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
    print(f"{'=' * 55}\n")


# ---------------------------------------------------------------------------
# Session listing and management
# ---------------------------------------------------------------------------
def list_sessions(reports_dir=None) -> None:
    """Print all saved session transcript files, newest first."""
    path = Path(reports_dir) if reports_dir else _get_reports_dir()
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


def read_session(filename: str, reports_dir=None) -> None:
    """Print the contents of a saved session transcript."""
    path = (Path(reports_dir) if reports_dir else _get_reports_dir()) / filename
    if not path.exists():
        print(f"File not found: {filename}. Use --list-sessions to see available files.")
        return
    print(f"--- {filename} ---")
    print(path.read_text(encoding="utf-8"))


def delete_session(filename: str, reports_dir=None) -> None:
    """Delete a saved session transcript after confirmation."""
    path = (Path(reports_dir) if reports_dir else _get_reports_dir()) / filename
    if not path.exists():
        print(f"File not found: {filename}. Use --list-sessions to see available files.")
        return
    try:
        confirm = input(f"Delete '{filename}'? [y/N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        confirm = "n"
    if confirm == "y":
        path.unlink()
        print(f"Deleted: {filename}")
    else:
        print("Cancelled.")


def export_session(filename: str, reports_dir=None) -> None:
    """Export a session transcript as a plain-text .txt file."""
    src = (Path(reports_dir) if reports_dir else _get_reports_dir()) / filename
    if not src.exists():
        print(f"File not found: {filename}. Use --list-sessions to see available files.")
        return
    raw = src.read_text(encoding="utf-8")
    cleaned = re.sub(r"#{1,6}\s*", "", raw)
    cleaned = re.sub(r"\*\*(.+?)\*\*", r"\1", cleaned)
    cleaned = re.sub(r"\*(.+?)\*", r"\1", cleaned)
    txt_name = Path(filename).stem + ".txt"
    dest = (Path(reports_dir) if reports_dir else _get_reports_dir()) / txt_name
    dest.write_text(cleaned, encoding="utf-8")
    print(f"Exported to: {dest}")


def rename_session(filename: str, reports_dir=None) -> None:
    """Rename a session transcript file."""
    src = (Path(reports_dir) if reports_dir else _get_reports_dir()) / filename
    if not src.exists():
        print(f"File not found: {filename}. Use --list-sessions to see available files.")
        return
    try:
        raw_name = input("New filename (without extension): ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        raw_name = ""
    if not raw_name:
        print("Name cannot be empty. Cancelled.")
        return
    new_name = raw_name if raw_name.endswith(".md") else raw_name + ".md"
    dest = (Path(reports_dir) if reports_dir else _get_reports_dir()) / new_name
    if dest.exists():
        print(f"A file named '{new_name}' already exists. Cancelled.")
        return
    src.rename(dest)
    print(f"Renamed to: {new_name}")


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------
ALL_ROLE_NAMES = [
    "Builder", "Reviewer", "Tester",
    "Writer", "Editor", "QA",
    "Formulator", "Searcher", "Validator",
    "Appraiser", "Methodologist", "Summariser",
    "Researcher",
]


def show_stats(reports_dir=None) -> None:
    """Print session statistics for all saved transcripts."""
    path = Path(reports_dir) if reports_dir else _get_reports_dir()
    if not path.exists():
        print("No reports folder found.")
        return
    files = sorted(path.glob("session_*.md"))
    if not files:
        print("No session transcripts found.")
        return

    total_size = 0
    role_counts: dict[str, int] = {role: 0 for role in ALL_ROLE_NAMES}

    for f in files:
        total_size += f.stat().st_size
        content = f.read_text(encoding="utf-8", errors="replace")
        for role in ALL_ROLE_NAMES:
            role_counts[role] += content.count(f"## {role}")

    print(f"\nTotal sessions    : {len(files)}")
    print(f"Total size        : {total_size} bytes")
    print("\nRole usage across all sessions:")
    for role, count in role_counts.items():
        colour = role_color(role)
        print(f"  {colour}{role:<14}{RESET}: {count} interaction(s)")


# ---------------------------------------------------------------------------
# Report saving
# ---------------------------------------------------------------------------
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
