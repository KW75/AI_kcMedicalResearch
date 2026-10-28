"""
ollama_models.py - Local Ollama model list and picker information.

Shared by scripts/launcher.py (model picker) and providers.py (default model).

Standard library only: the launcher imports this file directly.

Everything about a model is read live from Ollama, never hard-coded:
- Disk size and parameter count: /api/tags.
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


def describe(model: dict, caps: set[str]) -> str:
    """One ASCII line for the launcher's model picker."""
    vision = "yes" if "vision" in caps else "no"
    return (f"{model['name']}  {model['params_b']:g}B  {model['size_gb']:.1f} GB  "
            f"Image/OCR: {vision}")
