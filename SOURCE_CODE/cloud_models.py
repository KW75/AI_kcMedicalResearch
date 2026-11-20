"""Session 48: check cloud model names with each provider (launcher Setup).

Stdlib only, like ollama_models, so scripts/launcher.py can import it
without the app's packages. Listing models costs no tokens. Nothing here
changes .env; the launcher asks before it saves a name.

Value order matches the app: a system environment variable wins (load_dotenv
never overrides it), then .env, then the default in providers.py.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
from pathlib import Path
from urllib.request import Request, urlopen

_PROVIDERS_PY = Path(__file__).resolve().parent / "providers.py"
DASHSCOPE_DEFAULT_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
SYSTEM = "system variable"

# provider, label, key variable, model variables, list URL ("" = DashScope base)
PROVIDERS = [
    ("deepseek", "DeepSeek", "DEEPSEEK_API_KEY", ["DEEPSEEK_MODEL"],
     "https://api.deepseek.com/models"),
    ("qwen", "Qwen (DashScope)", "DASHSCOPE_API_KEY",
     ["QWEN_MODEL", "QWEN_VISION_MODEL"], ""),
    ("openai", "OpenAI", "OPENAI_API_KEY", ["OPENAI_MODEL"],
     "https://api.openai.com/v1/models"),
    ("groq", "Groq", "GROQ_API_KEY", ["GROQ_MODEL"],
     "https://api.groq.com/openai/v1/models"),
    ("anthropic", "Anthropic", "ANTHROPIC_API_KEY", ["ANTHROPIC_MODEL"],
     "https://api.anthropic.com/v1/models?limit=100"),
]


def code_defaults() -> dict[str, str]:
    """*_MODEL defaults as written in providers.py (one source of truth)."""
    try:
        src = _PROVIDERS_PY.read_text(encoding="utf-8")
    except OSError:
        return {}
    return dict(re.findall(
        r'^(\w+_MODEL)\s*=\s*os\.(?:getenv|environ\.get)\(\s*"\w+"\s*,\s*"([^"]*)"',
        src, re.M))


def resolve(var: str, env_values: dict, defaults: dict | None = None) -> tuple[str, str]:
    """(value, source): system variable, then .env, then providers.py default."""
    system = os.environ.get(var, "").strip()
    if system:
        return system, SYSTEM
    value = (env_values.get(var) or "").strip()
    if value:
        return value, ".env"
    default = (code_defaults() if defaults is None else defaults).get(var, "")
    return default, ("code default" if default else "")


def list_models(url: str, headers: dict, timeout: int = 20) -> list[str]:
    """Model ids the provider lists. Raises RuntimeError with the reply."""
    try:
        with urlopen(Request(url, headers=headers), timeout=timeout) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        try:
            body = " ".join(exc.read().decode("utf-8", "replace").split())[:200]
        except Exception:
            body = ""
        raise RuntimeError(
            f"HTTP error {exc.code}: {exc.reason} | {body or '(no reply)'}") from exc
    except (urllib.error.URLError, OSError, ValueError) as exc:
        raise RuntimeError(f"could not reach the provider ({exc})") from exc
    items = data.get("data", []) if isinstance(data, dict) else []
    return sorted(str(m["id"]) for m in items if isinstance(m, dict) and m.get("id"))


def _headers(provider: str, key: str) -> dict:
    if provider == "anthropic":
        return {"x-api-key": key, "anthropic-version": "2023-06-01"}
    return {"Authorization": "Bearer " + key}


def check_all(env_values: dict, template_values: dict, timeout: int = 20) -> list[dict]:
    """One row per provider. A model is 'listed' True/False only when the
    list call worked; 'suggest' is the .env.example name, offered only when
    the provider lists it and the current name is not listed."""
    defaults = code_defaults()
    results = []
    for provider, label, key_var, model_vars, url in PROVIDERS:
        key, _ = resolve(key_var, env_values, {})
        row = {"provider": provider, "label": label, "key_set": bool(key),
               "error": "", "names": [], "models": []}
        for var in model_vars:
            value, source = resolve(var, env_values, defaults)
            row["models"].append({"var": var, "value": value, "source": source,
                                  "listed": None, "suggest": ""})
        if key:
            if not url:
                base, _ = resolve("DASHSCOPE_BASE_URL", env_values, {})
                url = (base or DASHSCOPE_DEFAULT_URL).rstrip("/") + "/models"
            try:
                row["names"] = list_models(url, _headers(provider, key), timeout)
            except RuntimeError as exc:
                row["error"] = str(exc)
            else:
                names = set(row["names"])
                for m in row["models"]:
                    m["listed"] = m["value"] in names
                    tpl = (template_values.get(m["var"]) or "").strip()
                    if not m["listed"] and tpl and tpl != m["value"] and tpl in names:
                        m["suggest"] = tpl
        results.append(row)
    return results
