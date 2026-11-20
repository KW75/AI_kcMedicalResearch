"""Session 49: the launcher banner and the main.py docstring list every mode,
and the docstring every provider with the code default first. Read from code,
so a new mode or provider fails here until both texts name it."""
import re
from pathlib import Path

import main
import providers

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts" / "launcher.py"
MAIN = ROOT / "SOURCE_CODE" / "main.py"


def _word(name, text):
    return re.search(r"(?<![\w-])" + re.escape(name) + r"(?![\w-])", text) is not None


def _choices(flag):
    """The choices of an argparse flag in main.py."""
    src = MAIN.read_text(encoding="utf-8")
    m = re.search(r"add_argument\((?:\s*[\"']-\w[\"']\s*,)?\s*[\"']" + flag + r"[\"']", src)
    assert m, f"add_argument for {flag} not found in main.py"
    block = src[m.start():m.start() + 800]
    lit = re.search(r"choices\s*=\s*[\[(]([^\])]*)[\])]", block)
    if lit:
        return re.findall(r"[\"']([\w-]+)[\"']", lit.group(1))
    ref = re.search(r"choices\s*=\s*([\w.]+(?:\([\w.]*\))?)", block)
    assert ref, f"no choices= for {flag}"
    return [str(v) for v in eval(ref.group(1), vars(main))]


def _doc_line(start):
    lines = [l.strip() for l in (main.__doc__ or "").splitlines()
             if l.strip().startswith(start)]
    assert len(lines) == 1, f"main.py docstring: expected 1 line starting {start!r}, found {len(lines)}"
    return lines[0]


def test_launcher_banner_lists_every_menu_mode():
    src = LAUNCHER.read_text(encoding="utf-8")
    menu = src[src.index("MODES = ["):]
    menu = menu[:menu.index("\n]")]
    modes = re.findall(r"--mode (\w+)", menu)
    assert "samd" in modes and "ocr" in modes  # guard: menu read right
    start = src.index("Modes  :")
    banner = src[start:src.index("Providers", start)]
    assert [m for m in modes if not _word(m, banner)] == []


def test_docstring_lists_every_mode():
    line = _doc_line("Workflow modes")
    assert [m for m in _choices("--mode") if not _word(m, line)] == []


def test_docstring_lists_every_provider():
    line = _doc_line("AI providers")
    assert [p for p in _choices("--provider") if not _word(p, line)] == []


def test_docstring_names_code_default_provider():
    line = _doc_line("AI providers")
    assert re.search(r"providers:\s*" + re.escape(providers.CODE_DEFAULT_PROVIDER)
                     + r" \(default", line)
