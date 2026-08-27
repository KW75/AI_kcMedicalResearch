#!/usr/bin/env python3
"""
Fail if any tracked source file starts with a UTF-8 BOM.

Scans from the repository root, ignoring directories that legitimately
contain non-source content (VCS metadata, virtual environments, generated
artifacts). See Known Issue #60.
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


def scan(root: Path) -> list[Path]:
    offenders: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if is_ignored(path.relative_to(root)):
            continue
        if path.suffix.lower() not in CHECK_SUFFIXES:
            continue
        try:
            with path.open("rb") as fh:
                head = fh.read(3)
        except OSError:
            continue
        if head == BOM:
            offenders.append(path)
    return offenders


def main() -> int:
    offenders = scan(REPO_ROOT)
    if not offenders:
        print(f"[check_no_bom] OK - no UTF-8 BOMs found under {REPO_ROOT}")
        return 0
    print(f"[check_no_bom] FAIL - {len(offenders)} file(s) start with a UTF-8 BOM:")
    for path in offenders:
        print(f"  {path.relative_to(REPO_ROOT)}")
    print()
    print("Fix with: python scripts/strip_bom.py")
    return 1


if __name__ == "__main__":
    sys.exit(main())
