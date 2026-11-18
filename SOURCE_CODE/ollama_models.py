"""
ollama_models.py - Local Ollama model list and picker information.

Shared by scripts/launcher.py (model picker) and providers.py (default model).

Standard library only: the launcher imports this file directly.

Everything about a model is read live from Ollama, never hard-coded:
- Disk size and parameter count: /api/tags.
- Version (Setup -> Local AI status line): /api/version.
- Capabilities (completion, vision, embedding, ...): /api/show.
  The launcher lists only models with 'completion', which hides
  embedding models without matching their names.
"""
from __future__ import annotations

import json
import os
import urllib.request

OLLAMA_HOST_DEFAULT = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

# Default local model, used when .env has no OLLAMA_MODEL (Session 33 rule,
# no auto-detection). gemma4:e4b reads images, which OCR mode will need.
# README and .env.example must name the same model (test_providers.py).
OLLAMA_DEFAULT_MODEL = "gemma4:e4b"

# Default vision model for SR extraction (Session 42) and OCR (Session 48).
# gemma4:e4b is too small for SR: on Karlsson it read 3 of 4 means/SDs wrong
# and all 3 runs agreed on the misread. qwen3-vl:30b-a3b-instruct read all
# six values right, AI alone (run k20261116_070736). Use an -instruct tag: the
# thinking tag (qwen3-vl:30b) ignores think=false and gave 21 of 21 unusable
# runs (20261115_230933). About 20 GB; runs CPU-only (slow).
# OCR (Session 48, input/ocr test: Ang PDF + 3 images): gemma4:e4b left most
# [?] unfilled and misread table values; qwen3-vl filled every [?] on Ang
# correctly and read every checked value right. It may guess covered text.
# Not pulled -> SR and OCR fall back to the rule below, with a warning.
# Text modes and .env keep OLLAMA_DEFAULT_MODEL.
VISION_MODEL = "qwen3-vl:30b-a3b-instruct"
SR_VISION_MODEL = VISION_MODEL  # Session 42 name, kept for SR code and tests


def ollama_version(host: str | None = None) -> str:
    """Ollama's version from /api/version, e.g. '0.40.11'. '' if not reachable."""
    host = host or OLLAMA_HOST_DEFAULT
    try:
        req = urllib.request.Request(f"{host}/api/version", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
    except Exception:
        return ""
    return str(data.get("version") or "")


def _parse_params(text: str) -> float:
    """'7.5B' -> 7.5, '137M' -> 0.137. Unreadable -> 0.0."""
    text = (text or "").strip().upper()
    scale = {"B": 1.0, "M": 1e-3, "K": 1e-6}
    try:
        if text and text[-1] in scale:
            return float(text[:-1]) * scale[text[-1]]
        return float(text)
    except ValueError:
        return 0.0


def list_ollama_models(host: str | None = None) -> list[dict]:
    """Every pulled model (chat and embedding), smallest first: [{name, size_gb, params_b}].

    Returns [] if Ollama is not reachable.
    """
    host = host or OLLAMA_HOST_DEFAULT
    try:
        req = urllib.request.Request(f"{host}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
    except Exception:
        return []
    models = []
    for m in data.get("models", []):
        name = m.get("name", "")
        if not name:
            continue
        models.append({
            "name": name,
            "size_gb": round((m.get("size") or 0) / 1e9, 1),
            "params_b": _parse_params(m.get("details", {}).get("parameter_size", "")),
        })
    models.sort(key=lambda m: m["params_b"])
    return models


def model_capabilities(host: str | None, name: str) -> set[str]:
    """Capabilities Ollama reports for a model, e.g. {'completion', 'vision'}.

    Returns an empty set if Ollama is not reachable.
    """
    host = host or OLLAMA_HOST_DEFAULT
    try:
        req = urllib.request.Request(
            f"{host}/api/show",
            data=json.dumps({"model": name}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        return set(data.get("capabilities") or [])
    except Exception:
        return set()


def sr_vision_error(model: str, caps_fn=None, host=None) -> str | None:
    """SR on Ollama needs a model whose /api/show lists 'vision' (as OCR).
    Returns a message if it cannot read images or is not pulled, else None.
    Shared by main.run_sr_launcher and a direct run of pipelines/sr/main.py
    (Session 40, commit 3b)."""
    caps_fn = caps_fn or model_capabilities
    try:
        caps = caps_fn(host, model)
    except Exception:
        caps = set()
    if "vision" in caps:
        return None
    return (f"SR: Ollama model {model} cannot read page images (no 'vision' "
            f"capability) or is not pulled. Run: ollama pull {SR_VISION_MODEL}, or set "
            "OLLAMA_MODEL to a vision model, or use --provider qwen or openai "
            "(cloud).")


# --- Vision-model picker shared by SR and OCR (Session 42, decision A) -------
# Colleagues pull their own vision models (launcher 10 Setup -> 2 Local AI);
# SR and OCR list whatever is pulled. No model names here apart from
# OLLAMA_DEFAULT_MODEL and VISION_MODEL (SR and OCR, see top of file).

NO_VISION_HINT = (
    "No pulled Ollama model can read images. Pull one in launcher "
    "10 Setup -> 2 Local AI (vision models: https://ollama.com/search?c=vision)."
)


VISION_WAIT_HINT = ("Checking local Ollama models for image support - this can "
                    "take a minute. Please wait, do not press Enter.")


def flush_keyboard() -> None:
    """Drop keys typed while the program was busy (Session 43): an Enter
    pressed during the wait would otherwise answer the next question.
    Real console only; no console (pytest, piped input) -> nothing."""
    import sys
    try:
        if not sys.stdin or not sys.stdin.isatty():
            return
        try:
            import msvcrt
        except ImportError:
            import termios
            termios.tcflush(sys.stdin, termios.TCIFLUSH)
            return
        while msvcrt.kbhit():
            msvcrt.getwch()
    except Exception:
        return


def vision_models(list_fn=None, caps_fn=None, host=None) -> list[dict]:
    """Pulled Ollama models that report the 'vision' capability."""
    list_fn = list_fn or list_ollama_models
    caps_fn = caps_fn or model_capabilities
    return [m for m in list_fn(host) if "vision" in caps_fn(host, m["name"])]


def _with_tag(name: str) -> str:
    """Ollama lists 'llava' as 'llava:latest'."""
    return name if ":" in name else name + ":latest"


def default_vision_model(names: list[str], preferred: str = "") -> str:
    """preferred (SR and OCR pass VISION_MODEL) if pulled, else OLLAMA_MODEL if
    it is in names (with or without ':latest'), else OLLAMA_DEFAULT_MODEL if
    pulled, else the first name."""
    if preferred:
        for candidate in (preferred, _with_tag(preferred)):
            if candidate in names:
                return candidate
    env = os.getenv("OLLAMA_MODEL", "").strip()
    if env:
        for candidate in (env, _with_tag(env)):
            if candidate in names:
                return candidate
    if OLLAMA_DEFAULT_MODEL in names:
        return OLLAMA_DEFAULT_MODEL
    return names[0]


def pick_vision_model(models: list[dict], input_fn=input, log=print,
                      preferred: str = "", flush_fn=None) -> str | None:
    """Ask which pulled vision model to use. Enter = default; no keyboard
    (EOFError) = default; Ctrl+C or a bad answer = None (job not run)."""
    if not models:
        log(NO_VISION_HINT)
        return None
    default = default_vision_model([m["name"] for m in models], preferred=preferred)
    for i, m in enumerate(models, start=1):
        mark = "  (default)" if m["name"] == default else ""
        log(f"  {i}  {describe(m, {'vision'})}{mark}")
    try:
        (flush_fn or flush_keyboard)()
    except Exception:
        pass
    try:
        answer = input_fn("Model number (Enter = default): ").strip()
    except EOFError:
        log(f"No keyboard: using the default model {default}.")
        return default
    except KeyboardInterrupt:
        log("Cancelled. Job not run.")
        return None
    if not answer:
        return default
    if answer.isdigit() and 1 <= int(answer) <= len(models):
        return models[int(answer) - 1]["name"]
    log("Not a valid model number. Job not run.")
    return None


def describe(model: dict, caps: set[str]) -> str:
    """One ASCII line for the launcher's model picker."""
    vision = "yes" if "vision" in caps else "no"
    return (f"{model['name']}  {model['params_b']:g}B  {model['size_gb']:.1f} GB  "
            f"Image/OCR: {vision}")
