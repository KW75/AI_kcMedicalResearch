"""
Provider registry for AI kcMedicalResearch.
Handles all LLM provider connections, auto-detection, fallback chains,
and provider capability assessment.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from urllib.request import urlopen
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Environment / provider config
# ---------------------------------------------------------------------------
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
DASHSCOPE_BASE_URL = os.environ.get(
    "DASHSCOPE_BASE_URL",
    "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
)
QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen-plus-latest")
QWEN_VISION_MODEL = os.getenv("QWEN_VISION_MODEL", "qwen-vl-max")
DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER", "deepseek")

# Fallback chain (configurable via .env)
FALLBACK_PROVIDERS = [
    p.strip()
    for p in os.getenv("FALLBACK_PROVIDERS", "deepseek,qwen,groq").split(",")
    if p.strip()
]

# Ollama performance thresholds
OLLAMA_MIN_TOKENS_PER_SECOND = float(os.getenv("OLLAMA_MIN_TOKENS_PER_SECOND", "10"))


# ---------------------------------------------------------------------------
# Provider capabilities
# ---------------------------------------------------------------------------
PROVIDER_CAPABILITIES = {
    "deepseek": {"vision": False, "streaming": True, "max_context": 128000},
    "qwen": {"vision": True, "streaming": True, "max_context": 128000},
    "openai": {"vision": True, "streaming": True, "max_context": 128000},
    "anthropic": {"vision": True, "streaming": True, "max_context": 200000},
    "groq": {"vision": True, "streaming": True, "max_context": 128000},
    "ollama": {"vision": False, "streaming": True, "max_context": 32768},
}


def get_provider_capabilities(provider: str) -> dict:
    """Return the capabilities dict for a provider."""
    return PROVIDER_CAPABILITIES.get(provider, {"vision": False, "streaming": False, "max_context": 8192})


def supports_vision(provider: str) -> bool:
    """Check if a provider supports vision/image input."""
    return get_provider_capabilities(provider).get("vision", False)


# ---------------------------------------------------------------------------
# Ollama auto-detect best model
# ---------------------------------------------------------------------------
def _ollama_detect_best_model(host: str = "http://localhost:11434") -> str:
    """Query Ollama /api/tags and return the largest non-embedding model available."""
    SKIP_PATTERNS = ("embed", "nomic", "all-minilm")
    try:
        req = urllib.request.Request(f"{host}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        models = data.get("models", [])
        if not models:
            return "llama3.2"
        candidates = []
        for m in models:
            name = m.get("name", "")
            if any(skip in name.lower() for skip in SKIP_PATTERNS):
                continue
            param_str = m.get("details", {}).get("parameter_size", "0B")
            try:
                size = float(param_str.replace("B", "").replace("M", "e-3").replace("K", "e-6"))
            except (ValueError, TypeError):
                size = 0
            candidates.append((name, size))
        if not candidates:
            return "llama3.2"
        candidates.sort(key=lambda x: x[1], reverse=True)
        best = candidates[0][0]
        print(f"[ollama] Auto-detected best model: {best} ({candidates[0][1]:.1f}B params)")
        return best
    except Exception:
        return "llama3.2"


# ---------------------------------------------------------------------------
# Ollama startup probe (performance measurement)
# ---------------------------------------------------------------------------
def ollama_probe_performance(host: str = None, model: str = None) -> dict:
    """
    Send a short prompt to Ollama and measure tokens/second.
    Returns dict with: reachable, tokens_per_second, model, model_size_b
    """
    host = host or OLLAMA_HOST
    model = model or OLLAMA_MODEL or _ollama_detect_best_model(host)

    probe_prompt = "Count from 1 to 20, one number per line."
    url = f"{host}/api/generate"
    payload = json.dumps({
        "model": model,
        "prompt": probe_prompt,
        "stream": False,
        "options": {
            "num_predict": 64,
            "num_ctx": 512,
            "temperature": 0.1,
        },
    }).encode()

    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        start = time.time()
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        elapsed = time.time() - start

        eval_count = data.get("eval_count", 0)
        eval_duration_ns = data.get("eval_duration", 0)

        if eval_duration_ns > 0:
            tokens_per_second = eval_count / (eval_duration_ns / 1e9)
        elif elapsed > 0 and eval_count > 0:
            tokens_per_second = eval_count / elapsed
        else:
            tokens_per_second = 0.0

        return {
            "reachable": True,
            "tokens_per_second": round(tokens_per_second, 1),
            "model": model,
            "model_size_b": _get_model_size(host, model),
        }
    except Exception:
        return {
            "reachable": False,
            "tokens_per_second": 0.0,
            "model": model,
            "model_size_b": 0.0,
        }


def _get_model_size(host: str, model_name: str) -> float:
    """Get the parameter count in billions for a specific Ollama model."""
    try:
        req = urllib.request.Request(f"{host}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        for m in data.get("models", []):
            if m.get("name") == model_name:
                param_str = m.get("details", {}).get("parameter_size", "0B")
                return float(param_str.replace("B", "").replace("M", "e-3").replace("K", "e-6"))
    except Exception:
        pass
    return 0.0


# Auto-detect Ollama model at import time if not explicitly set
if not OLLAMA_MODEL:
    try:
        OLLAMA_MODEL = _ollama_detect_best_model(OLLAMA_HOST)
    except Exception:
        OLLAMA_MODEL = "llama3.2"


# ---------------------------------------------------------------------------
# Provider functions
# ---------------------------------------------------------------------------
def call_openai_provider(
    prompt: str,
    model: str | None = None,
    max_tokens: int = 8192,
) -> str:
    """Send a prompt to the OpenAI chat completions endpoint."""
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to your .env file.")
    model = model or OPENAI_MODEL
    url = "https://api.openai.com/v1/chat/completions"
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
    }).encode()
    req = urllib.request.Request(
        url, data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}",
        },
        method="POST",
    )
    try:
        with urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read())
        choices = data.get("choices", [])
        if not choices or not choices[0].get("message", {}).get("content"):
            raise RuntimeError("OpenAI returned an empty response.")
        return choices[0]["message"]["content"]
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"OpenAI HTTP error {exc.code}: {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"OpenAI connection error: {exc.reason}") from exc


def call_anthropic_provider(
    prompt: str,
    model: str | None = None,
    max_tokens: int = 8192,
) -> str:
    """Send a prompt to the Anthropic messages endpoint."""
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY is not set. Add it to your .env file.")
    model = model or ANTHROPIC_MODEL
    url = "https://api.anthropic.com/v1/messages"
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
    }).encode()
    req = urllib.request.Request(
        url, data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    try:
        with urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read())
        content = data.get("content", [])
        if not content or not content[0].get("text"):
            raise RuntimeError("Anthropic returned an empty response.")
        return content[0]["text"]
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Anthropic HTTP error {exc.code}: {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Anthropic connection error: {exc.reason}") from exc


def call_ollama_provider(
    prompt: str,
    model: str | None = None,
    max_tokens: int = 8192,
) -> str:
    """Send a prompt to the local Ollama generate endpoint."""
    model = model or OLLAMA_MODEL
    url = f"{OLLAMA_HOST}/api/generate"
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": max_tokens,
            "num_ctx": int(os.getenv("OLLAMA_CONTEXT", "32768")),
            "temperature": float(os.getenv("OLLAMA_TEMPERATURE", "0.3")),
            "top_p": 0.9,
            "repeat_penalty": 1.1,
        },
    }).encode()
    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=900) as resp:
            data = json.loads(resp.read())
        response_text = data.get("response", "")
        if not response_text:
            raise RuntimeError("Ollama returned an empty response.")
        return response_text
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Ollama HTTP error {exc.code}: {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Ollama connection error: {exc.reason}") from exc


def call_deepseek_provider(
    prompt: str,
    model: str | None = None,
    max_tokens: int = 8192,
) -> str:
    """Send a prompt to the DeepSeek chat completions endpoint."""
    if not DEEPSEEK_API_KEY:
        raise RuntimeError("DEEPSEEK_API_KEY is not set. Add it to your .env file.")
    model = model or DEEPSEEK_MODEL
    url = "https://api.deepseek.com/chat/completions"
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "stream": False,
        "thinking": {"type": "disabled"},
    }).encode()
    req = urllib.request.Request(
        url, data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        },
        method="POST",
    )
    try:
        with urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read())
        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError("DeepSeek returned an empty response.")
        msg = choices[0].get("message", {})
        content = msg.get("content") or msg.get("reasoning_content", "")
        if not content:
            raise RuntimeError("DeepSeek returned an empty response.")
        return content
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"DeepSeek HTTP error {exc.code}: {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"DeepSeek connection error: {exc.reason}") from exc


def call_groq_provider(
    prompt: str,
    model: str | None = None,
    max_tokens: int = 8192,
) -> str:
    """Send a prompt to the Groq inference endpoint."""
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not set. Add it to your .env file.")
    model = model or GROQ_MODEL
    url = "https://api.groq.com/openai/v1/chat/completions"
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "stream": False,
    }).encode()
    req = urllib.request.Request(
        url, data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROQ_API_KEY}",
        },
        method="POST",
    )
    try:
        with urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read())
        choices = data.get("choices", [])
        if not choices or not choices[0].get("message", {}).get("content"):
            raise RuntimeError("Groq returned an empty response.")
        return choices[0]["message"]["content"]
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Groq HTTP error {exc.code}: {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Groq connection error: {exc.reason}") from exc


def call_qwen_provider(
    prompt: str,
    model: str | None = None,
    max_tokens: int = 8192,
) -> str:
    """Send a prompt to Alibaba Cloud Model Studio (Qwen) via OpenAI-compatible API."""
    if not DASHSCOPE_API_KEY:
        raise RuntimeError("DASHSCOPE_API_KEY is not set. Add it to your .env file.")
    model = model or QWEN_MODEL
    url = f"{DASHSCOPE_BASE_URL.rstrip('/')}/chat/completions"
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "stream": False,
        "enable_thinking": False,
    }).encode()
    req = urllib.request.Request(
        url, data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        },
        method="POST",
    )
    try:
        with urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read())
        choices = data.get("choices", [])
        if not choices or not choices[0].get("message", {}).get("content"):
            raise RuntimeError("Qwen returned an empty response.")
        return choices[0]["message"]["content"]
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Qwen HTTP error {exc.code}: {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Qwen connection error: {exc.reason}") from exc


# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------
PROVIDERS: dict[str, callable] = {
    "ollama": call_ollama_provider,
    "openai": call_openai_provider,
    "anthropic": call_anthropic_provider,
    "deepseek": call_deepseek_provider,
    "groq": call_groq_provider,
    "qwen": call_qwen_provider,
}


def call_ai(
    prompt: str,
    provider: str = None,
    model: str | None = None,
) -> str:
    """Dispatch an AI call to the correct provider function."""
    provider = provider or DEFAULT_PROVIDER
    fn = PROVIDERS.get(provider, call_deepseek_provider)
    return fn(prompt, model=model)


# ---------------------------------------------------------------------------
# Fallback-aware call
# ---------------------------------------------------------------------------
_TRANSIENT_INDICATORS = ("timeout", "timed out", "503", "502", "429", "rate limit", "connection")


def _is_transient_error(error: Exception) -> bool:
    """Determine if an error is transient (worth retrying with another provider)."""
    msg = str(error).lower()
    return any(indicator in msg for indicator in _TRANSIENT_INDICATORS)


def call_ai_with_fallback(
    prompt: str,
    provider: str = None,
    model: str | None = None,
    fallback_chain: list[str] | None = None,
) -> str:
    """
    Call AI with automatic fallback to next provider on transient errors.
    Auth errors raise immediately. Prints warnings on fallback.
    """
    provider = provider or DEFAULT_PROVIDER
    chain = fallback_chain or FALLBACK_PROVIDERS
    ordered = [provider] + [p for p in chain if p != provider]

    last_error = None
    for attempt_provider in ordered:
        try:
            result = call_ai(prompt, provider=attempt_provider, model=model if attempt_provider == provider else None)
            if attempt_provider != provider:
                print(f"[fallback] Succeeded with {attempt_provider} (primary {provider} failed)")
            return result
        except RuntimeError as exc:
            last_error = exc
            if not _is_transient_error(exc):
                raise
            print(f"[fallback] {attempt_provider} failed ({exc}), trying next...")
            continue

    raise RuntimeError(
        f"All providers failed. Last error: {last_error}. "
        f"Tried: {', '.join(ordered)}"
    )


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------
def validate_provider(provider: str) -> tuple[bool, str]:
    """Pre-flight check: is the provider configured and likely to work?"""
    if provider not in PROVIDERS:
        return False, f"Unknown provider '{provider}'. Available: {', '.join(PROVIDERS.keys())}"

    key_checks = {
        "deepseek": ("DEEPSEEK_API_KEY", DEEPSEEK_API_KEY),
        "openai": ("OPENAI_API_KEY", OPENAI_API_KEY),
        "anthropic": ("ANTHROPIC_API_KEY", ANTHROPIC_API_KEY),
        "groq": ("GROQ_API_KEY", GROQ_API_KEY),
        "qwen": ("DASHSCOPE_API_KEY", DASHSCOPE_API_KEY),
    }

    if provider in key_checks:
        env_var, value = key_checks[provider]
        if not value or not value.strip():
            return False, f"{env_var} is not set. Add it to your .env file."

    if provider == "ollama":
        try:
            req = urllib.request.Request(f"{OLLAMA_HOST}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                pass
        except Exception:
            return False, f"Ollama not reachable at {OLLAMA_HOST}. Is it running?"

    return True, ""


def get_default_model(provider: str) -> str:
    """Return the default model for a given provider."""
    defaults = {
        "deepseek": DEEPSEEK_MODEL,
        "openai": OPENAI_MODEL,
        "anthropic": ANTHROPIC_MODEL,
        "groq": GROQ_MODEL,
        "qwen": QWEN_MODEL,
        "ollama": OLLAMA_MODEL,
    }
    return defaults.get(provider, "")


def list_available_providers() -> list[dict]:
    """Return a list of all providers with their configuration status."""
    results = []
    for name in PROVIDERS:
        valid, msg = validate_provider(name)
        results.append({
            "name": name,
            "configured": valid,
            "error": msg if not valid else "",
            "model": get_default_model(name),
            "capabilities": get_provider_capabilities(name),
        })
    return results
