#!/usr/bin/env python3
"""
Strip UTF-8 BOMs from source files under the repository root.

Uses the same scan-root and ignore rules as check_no_bom.py. See Known
Issue #60.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

IGNORE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "output",
    "reports",
    "input",
    ".idea",
    ".vscode",
    "htmlcov",
    "dist",
    "build",
    ".egg-info",
}

CHECK_SUFFIXES = {
    ".py", ".pyi",
    ".md", ".txt", ".rst",
    ".yml", ".yaml",
    ".toml", ".ini", ".cfg",
    ".json",
    ".sh", ".bat", ".ps1", ".cmd",
    ".html", ".css", ".js",
}

BOM = b"\xef\xbb\xbf"


def is_ignored(path: Path) -> bool:
    return any(part in IGNORE_DIRS for part in path.parts)


def strip(root: Path) -> list[Path]:
    stripped: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if is_ignored(path.relative_to(root)):
            continue
        if path.suffix.lower() not in CHECK_SUFFIXES:
            continue
        try:
            with path.open("rb") as fh:
                data = fh.read()
        except OSError:
            continue
        if data.startswith(BOM):
            with path.open("wb") as fh:
                fh.write(data[len(BOM):])
            stripped.append(path)
    return stripped


def main() -> int:
    stripped = strip(REPO_ROOT)
    if not stripped:
        print("No BOMs found; nothing to do.")
        return 0
    print(f"Stripped BOM from {len(stripped)} file(s):")
    for path in stripped:
        print(f"  {path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
