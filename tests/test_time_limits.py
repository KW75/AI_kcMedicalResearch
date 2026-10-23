"""v2.5: adjustable time limit per AI call (15 min / 30 min / 1 hr / until finished).
Replaces the hard-coded 900 s in coding.py, writing.py, providers.py, streaming.py."""
import ast
import importlib
import sys
import threading
import time
from pathlib import Path

import pytest

import time_limits as tl


@pytest.fixture(autouse=True)
def _reset_limit():
    yield
    tl.set_limit(tl.parse(tl.DEFAULT))


def test_choices_and_default():
    assert list(tl.CHOICES) == ["15", "30", "60", "none"]
    assert tl.DEFAULT == "15"


@pytest.mark.parametrize("text,seconds", [
    ("15", 900), ("30", 1800), ("60", 3600),
    ("none", None), ("NONE", None), (" 30 ", 1800),
])
def test_parse(text, seconds):
    assert tl.parse(text) == seconds


@pytest.mark.parametrize("bad", ["", "10", "1h", "abc", "0"])
def test_parse_rejects_other_values(bad):
    with pytest.raises(ValueError):
        tl.parse(bad)


def test_fresh_process_starts_at_15_minutes():
    fresh = importlib.reload(tl)
    assert fresh.get_limit() == 900


def test_set_and_get():
    tl.set_limit(3600)
    assert tl.get_limit() == 3600
    tl.set_limit(None)
    assert tl.get_limit() is None


@pytest.mark.parametrize("seconds,text", [
    (900, "15 minutes"), (1800, "30 minutes"),
    (3600, "1 hour"), (None, "no time limit"),
])
def test_describe(seconds, text):
    assert tl.describe(seconds) == text


def test_labels_cover_every_choice_and_are_ascii():
    assert list(tl.LABELS) == list(tl.CHOICES)
    assert "default" in tl.LABELS[tl.DEFAULT]
    for label in tl.LABELS.values():
        label.encode("ascii")  # launcher runs in CJK-locale consoles


def test_wait_returns_true_when_call_finishes():
    t = threading.Thread(target=time.sleep, args=(0.05,), daemon=True)
    t.start()
    assert tl.wait_for(t, 5) is True


def test_wait_returns_false_after_limit():
    stop = threading.Event()
    t = threading.Thread(target=stop.wait, daemon=True)
    t.start()
    start = time.monotonic()
    assert tl.wait_for(t, 0.2) is False
    assert time.monotonic() - start < 2
    stop.set()


def test_no_limit_waits_in_short_steps_so_ctrl_c_still_works():
    joins = []

    class FakeThread:
        n = 0
        def join(self, timeout=None):
            joins.append(timeout)
            self.n += 1
        def is_alive(self):
            return self.n < 3

    assert tl.wait_for(FakeThread(), None) is True
    assert joins and all(j is not None and j <= 1 for j in joins)


def test_module_is_stdlib_only_so_the_launcher_can_import_it():
    src = Path(tl.__file__).read_text(encoding="utf-8")
    names = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Import):
            names |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    assert names <= set(sys.stdlib_module_names) | {"__future__"}
