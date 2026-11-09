"""Small, safe edits to the project's .env file (standard library only).

Used by the launcher's Setup -> API keys screen. Rules:
- set_value changes only the lines for the key being set; comments, blank
  lines, ordering and every other key stay exactly as they were
- the file's existing line endings (CRLF or LF) are kept; no BOM is written
- if .env is missing, it starts from a copy of .env.example (template)
- saves go to a temp file in the same folder, then os.replace swaps it in,
  so a failed save leaves the old .env intact. The temp name
  (.env.<random>.tmp) is covered by the '.env.*' line in .gitignore
- read_values follows python-dotenv: comments skipped, quotes stripped,
  the last duplicate wins
- error messages never include the value (it may be an API key)
"""
from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

_KEY_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_LINE_RE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=(.*)$")
_SPLIT_RE = re.compile(r"\r\n|\r|\n")


def _read_text(path: Path) -> str | None:
    """File text without a BOM, or None if the file does not exist."""
    try:
        return path.read_bytes().decode("utf-8-sig")
    except FileNotFoundError:
        return None


def _unquote(raw: str) -> str:
    v = raw.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    # Unquoted value: drop an inline comment (" # ...") like python-dotenv.
    m = re.search(r"\s#", v)
    return v[:m.start()].rstrip() if m else v


def read_values(path) -> dict[str, str]:
    """Return {NAME: value} for every active line. Missing file -> {}."""
    text = _read_text(Path(path))
    if text is None:
        return {}
    values: dict[str, str] = {}
    for line in _SPLIT_RE.split(text):
        if line.lstrip().startswith("#"):
            continue
        m = _LINE_RE.match(line)
        if m:
            values[m.group(1)] = _unquote(m.group(2))
    return values


def _validate(key: str, value: str) -> str:
    if not isinstance(key, str) or not _KEY_RE.fullmatch(key):
        raise ValueError(f"Not a valid .env key name: {key!r}")
    value = value.strip()
    if any(c.isspace() or c in "\"'" for c in value):
        raise ValueError(f"Value for {key} must not contain spaces, line breaks or quotes.")
    return value


def _atomic_write(path: Path, data: bytes) -> None:
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def set_value(path, key: str, value: str, template=None) -> None:
    """Set KEY=value in .env, changing nothing else.

    Every active line for KEY is updated (python-dotenv uses the last one, so
    the new value wins wherever it is). If KEY is not present, it is added at
    the end. Commented-out lines are left alone.
    """
    path = Path(path)
    value = _validate(key, value)

    text = _read_text(path)
    if text is None and template is not None:
        text = _read_text(Path(template))
    text = text or ""

    newline = "\r\n" if "\r\n" in text else "\n"
    lines = _SPLIT_RE.split(text)
    if lines and lines[-1] == "":
        lines.pop()

    new_line = f"{key}={value}"
    found = False
    for i, line in enumerate(lines):
        m = _LINE_RE.match(line)
        if m and m.group(1) == key:
            lines[i] = new_line
            found = True
    if not found:
        lines.append(new_line)

    _atomic_write(path, (newline.join(lines) + newline).encode("utf-8"))


def mask(value: str) -> str:
    """Show only enough of a key to recognise it: '****abcd'."""
    if not value:
        return "(not set)"
    if len(value) < 8:
        return "****"
    return "****" + value[-4:]
