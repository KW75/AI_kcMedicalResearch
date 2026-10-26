"""
ollama_models.py - Local Ollama model list and picker information.

Shared by scripts/launcher.py, ui/app.py and providers.py, so all three show
the same models, the same default and the same descriptions.

Standard library only: the launcher imports this file directly.

Where each piece of information comes from:
- Coding / reasoning ranks: local model comparison doc, 2026-10 (1 = best).
  Ollama cannot report these, so they are kept here.
- Disk size and parameter count: Ollama /api/tags, read live.
- Vision (Image/OCR) and thinking: Ollama /api/show, read live.
"""
from __future__ import annotations

import json
import os
import urllib.request

OLLAMA_HOST_DEFAULT = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

# Default local model. gemma4:e4b ranks best for coding, second for
# reasoning, and is the only model in the comparison that reads images
# (needed for OCR, v2.5 update #5). README Step 2 and .env.example must
# name the same model (tested in test_providers.py).
OLLAMA_DEFAULT_MODEL = "gemma4:e4b"

RANKS_SOURCE = "Local model comparison, 2026-10 (1 = best)"
MODEL_RANKS = {
    "qwen3:4b":             {"coding": 4, "reasoning": 3},
    "gemma4:e4b":           {"coding": 1, "reasoning": 2},
    "granite3.3:latest":    {"coding": 5, "reasoning": 5},
    "qwen3:8b":             {"coding": 2, "reasoning": 1},
    "qwen2.5:14b-instruct": {"coding": 3, "reasoning": 4},
}

# Embedding models cannot chat, so they are never offered.
_SKIP_PATTERNS = ("embed", "nomic", "all-minilm")


def _norm(name: str) -> str:
    """Ollama treats 'granite3.3' and 'granite3.3:latest' as the same model."""
    name = (name or "").strip()
    return name if ":" in name else f"{name}:latest"


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
    """Pulled chat models, smallest first: [{name, size_gb, params_b}].

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
        if not name or any(p in name.lower() for p in _SKIP_PATTERNS):
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


def choose_default(models: list[dict]) -> str:
    """OLLAMA_DEFAULT_MODEL if pulled, else the largest pulled model.

    Nothing pulled -> OLLAMA_DEFAULT_MODEL (the 404 message then tells the
    user to run `ollama pull`).
    """
    if not models:
        return OLLAMA_DEFAULT_MODEL
    if _norm(OLLAMA_DEFAULT_MODEL) in {_norm(m["name"]) for m in models}:
        return OLLAMA_DEFAULT_MODEL
    return max(models, key=lambda m: m["params_b"])["name"]


def rank_label(name: str) -> str:
    """'Coding 1 of 5, Reasoning 2 of 5 (1 = best)' or 'not ranked'."""
    r = MODEL_RANKS.get(_norm(name))
    if not r:
        return "not ranked"
    n = len(MODEL_RANKS)
    return f"Coding {r['coding']} of {n}, Reasoning {r['reasoning']} of {n} (1 = best)"


def missing_ranked(models: list[dict]) -> list[str]:
    """Ranked models that are not pulled yet (shown as 'ollama pull ...')."""
    pulled = {_norm(m["name"]) for m in models}
    return [name for name in MODEL_RANKS if name not in pulled]


def describe(model: dict, caps: set[str]) -> str:
    """One ASCII line for the launcher and UI pickers."""
    vision = "yes" if "vision" in caps else "no"
    return (f"{model['name']}  {model['params_b']:g}B  {model['size_gb']:.1f} GB  "
            f"Image/OCR: {vision}  {rank_label(model['name'])}")
