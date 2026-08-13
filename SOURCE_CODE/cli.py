"""
CLI argument parsing and dispatch for AI kcMedicalResearch.
Separates command-line interface logic from the core engine.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Lazy imports to avoid circular dependencies
def _get_providers():
    from providers import DEFAULT_PROVIDER, PROVIDERS
    return DEFAULT_PROVIDER, PROVIDERS


VERSION = "2.3.2"


def build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser."""
    DEFAULT_PROVIDER, PROVIDERS = _get_providers()
    parser = argparse.ArgumentParser(
        prog="AI kcMedicalResearch",
        description="Multi-mode AI assistant for medical research workflows.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python SOURCE_CODE/main.py --mode coding
  python SOURCE_CODE/main.py --mode writing --provider qwen
  python SOURCE_CODE/main.py --mode sr --provider qwen
  python SOURCE_CODE/main.py --mode rct_search --dry-run
  python SOURCE_CODE/main.py --provider ollama --mode coding
  python SOURCE_CODE/main.py --list-sessions
  python SOURCE_CODE/main.py --stats
        """,
    )

    parser.add_argument(
        "--mode", "-m",
        choices=["coding", "writing", "rct_search", "search", "appraisal", "sr"],
        default="coding",
        help="Pipeline mode to run (default: coding)",
    )
    parser.add_argument(
        "--provider", "-p",
        choices=list(PROVIDERS.keys()),
        default=None,
        help=f"AI provider (default: {DEFAULT_PROVIDER})",
    )
    parser.add_argument("--model", default=None,
                        help="Override the default model for the selected provider")
    parser.add_argument("--report", action="store_true",
                        help="Writing mode: generate report from input files")
    parser.add_argument("--revise", action="store_true",
                        help="Coding mode: run full Builder>Reviewer>Tester pipeline")
    parser.add_argument("--role", help="Override starting role for coding mode")
    parser.add_argument("--sub", type=int, choices=[1, 2],
                        help="Search sub-mode: 1=Topic, 2=Article")
    parser.add_argument("--dry-run", action="store_true",
                        help="Run without making real API calls")
    parser.add_argument("--help-guide", action="store_true",
                        help="Open interactive HTML help in browser")
    parser.add_argument("--ui", action="store_true",
                        help="Launch Streamlit web UI")
    parser.add_argument("--list-sessions", action="store_true",
                        help="List all saved session transcripts")
    parser.add_argument("--list-roles", action="store_true",
                        help="Show available roles and their docs")
    parser.add_argument("--stats", action="store_true",
                        help="Show session statistics")
    parser.add_argument("--version", "-v", action="version",
                        version=f"%(prog)s {VERSION}")

    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments."""
    DEFAULT_PROVIDER, _ = _get_providers()
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.provider is None:
        args.provider = DEFAULT_PROVIDER
    return args


def preflight_check(args: argparse.Namespace) -> tuple[bool, list[str]]:
    """
    Run pre-flight checks before starting a pipeline.
    Returns (all_passed, list_of_error_messages).
    """
    from providers import validate_provider, supports_vision

    errors = []

    valid, msg = validate_provider(args.provider)
    if not valid:
        errors.append(f"Provider check failed: {msg}")

    if args.mode == "sr" and not supports_vision(args.provider):
        errors.append(
            f"SR pipeline requires a vision-capable provider. "
            f"'{args.provider}' does not support vision. "
            f"Use --provider qwen, --provider openai, or --provider anthropic."
        )

    input_dir = Path(__file__).resolve().parent.parent / "input" / args.mode
    if input_dir.exists():
        files = [f for f in input_dir.iterdir() if f.is_file() and not f.name.startswith(".")]
        if not files and args.mode not in ("search", "coding"):
            errors.append(
                f"No input files found in input/{args.mode}/. "
                f"Add files before running the {args.mode} pipeline."
            )

    return len(errors) == 0, errors


def print_roles() -> None:
    """Print available roles for each mode."""
    roles_by_mode = {
        "coding": ["Builder", "Reviewer", "Tester"],
        "writing": ["Writer", "Editor", "QA"],
        "appraisal": ["Appraiser", "Methodologist", "Summariser"],
        "search": ["Researcher"],
        "rct_search": ["Formulator", "Searcher", "Validator"],
        "sr": ["SR Methodologist"],
    }
    print("\nAvailable roles by mode:\n")
    for mode, roles in roles_by_mode.items():
        print(f"  {mode}:")
        for role in roles:
            print(f"    - {role}")
    print()
