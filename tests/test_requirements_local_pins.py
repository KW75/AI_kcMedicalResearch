"""Pin httpx in requirements-local.txt (the file the launchers install).

requirements-local.txt pins old SDKs (openai==1.43.0, anthropic==0.34.2)
for colleagues. Those versions pass `proxies=` to httpx.Client, which
httpx 0.28 removed, so every OpenAI-compatible and Anthropic call crashed
on a fresh install ("unexpected keyword argument 'proxies'"). CI and dev
installs use requirements-base.txt with the newest SDKs, so nothing else
catches this. Session 34: 89 errors/failures on a fresh install,
0 after pinning httpx==0.27.2.
"""
import re
from pathlib import Path


def _repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "requirements-local.txt").exists():
            return parent
    raise RuntimeError("repo root with requirements-local.txt not found")


REQ = _repo_root() / "requirements-local.txt"


def _pins() -> dict:
    """Return {lowercased package name: line} for active requirement lines."""
    pins = {}
    for raw in REQ.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue
        name = re.split(r"[<>=!~\[; ]", line, maxsplit=1)[0].lower()
        pins[name] = line
    return pins


def test_httpx_is_pinned_exactly():
    line = _pins().get("httpx")
    assert line is not None, "requirements-local.txt must pin httpx (unpinned gets 0.28+)"
    assert re.fullmatch(r"httpx==\d+\.\d+\.\d+", line), f"httpx must be pinned with ==, got {line!r}"


def test_httpx_pin_is_below_0_28():
    line = _pins().get("httpx")
    assert line is not None, "requirements-local.txt must pin httpx (unpinned gets 0.28+)"
    major, minor, _ = (int(p) for p in line.split("==", 1)[1].split("."))
    assert (major, minor) < (0, 28), (
        f"{line!r}: httpx 0.28 removed `proxies`, which openai 1.43.0 / anthropic 0.34.2 still pass"
    )
