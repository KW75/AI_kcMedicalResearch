"""time_limits.py - adjustable time limit per AI call (v2.5).

Choices: 15 min (default), 30 min, 1 hour, or no limit ("until finished").
Stdlib only, so scripts/launcher.py can import it (same rule as ollama_models).
main.py calls set_limit() once from --time-limit. coding.py, writing.py,
providers.py and streaming.py read get_limit() instead of a hard-coded 900 s.
Each launcher/UI job starts a fresh main.py process, so a module-level
setting is safe.
"""
from __future__ import annotations

import time

CHOICES = {"15": 900, "30": 1800, "60": 3600, "none": None}
DEFAULT = "15"
LABELS = {
    "15": "15 minutes (default)",
    "30": "30 minutes",
    "60": "1 hour",
    "none": "Until finished (no time limit - stop with Ctrl+C)",
}

_STEP = 1.0  # seconds per join; short steps keep Ctrl+C working on Windows
_limit = CHOICES[DEFAULT]


def parse(text):
    """'15' / '30' / '60' / 'none' -> seconds (None = no limit)."""
    key = str(text).strip().lower()
    if key not in CHOICES:
        raise ValueError(
            f"time limit must be one of {', '.join(CHOICES)}; got {text!r}")
    return CHOICES[key]


def set_limit(seconds):
    global _limit
    _limit = seconds


def get_limit():
    return _limit


def describe(seconds):
    """Human text for messages, e.g. 'timed out after 30 minutes'."""
    if seconds is None:
        return "no time limit"
    minutes = int(round(seconds / 60))
    if minutes % 60 == 0:
        hours = minutes // 60
        return "1 hour" if hours == 1 else f"{hours} hours"
    return f"{minutes} minutes"


def wait_for(thread, seconds):
    """Wait for a worker thread. True if it finished, False if the limit ran out.

    Never calls join() without a timeout: a bare join() can ignore Ctrl+C on
    Windows, which would make 'until finished' impossible to stop.
    """
    if seconds is None:
        while thread.is_alive():
            thread.join(_STEP)
        return True
    deadline = time.monotonic() + seconds
    while thread.is_alive():
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return False
        thread.join(min(_STEP, remaining))
    return True
