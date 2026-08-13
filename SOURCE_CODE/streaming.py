"""
streaming.py - Streaming output for AI kcMedicalResearch.
Provides streaming variants of provider calls that yield tokens as they arrive.
Works with DeepSeek, Qwen, OpenAI, Anthropic, Groq (all support SSE).
Ollama supports streaming natively via stream=True.

Usage:
    from streaming import stream_ai, stream_to_console

    # Stream to console with live output
    full_response = stream_to_console("Write a poem", provider="deepseek")

    # Stream with custom handler
    for chunk in stream_ai("Write a poem", provider="deepseek"):
        my_widget.append(chunk)
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Generator

from dotenv import load_dotenv

load_dotenv()

# Import config from providers module
from providers import (
    OLLAMA_HOST, OLLAMA_MODEL,
    OPENAI_API_KEY, OPENAI_MODEL,
    ANTHROPIC_API_KEY, ANTHROPIC_MODEL,
    DEEPSEEK_API_KEY, DEEPSEEK_MODEL,
    GROQ_API_KEY, GROQ_MODEL,
    DASHSCOPE_API_KEY, DASHSCOPE_BASE_URL, QWEN_MODEL,
    DEFAULT_PROVIDER,
)


# ---------------------------------------------------------------------------
# SSE line parser
# ---------------------------------------------------------------------------
def _parse_sse_lines(response) -> Generator[str, None, None]:
    """
    Parse Server-Sent Events from an HTTP response.
    Yields content strings as they arrive.
    """
    for raw_line in response:
        line = raw_line.decode("utf-8", errors="replace").strip()
        if not line:
            continue
        if line == "data: [DONE]":
            break
        if line.startswith("data: "):
            json_str = line[6:]
            try:
                data = json.loads(json_str)
                # OpenAI / DeepSeek / Groq / Qwen format
                choices = data.get("choices", [])
                if choices:
                    delta = choices[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yield content
            except json.JSONDecodeError:
                continue


# ---------------------------------------------------------------------------
# Streaming provider functions
# ---------------------------------------------------------------------------
def _stream_openai_compatible(
    prompt: str,
    url: str,
    api_key: str,
    model: str,
    extra_body: dict = None,
) -> Generator[str, None, None]:
    """Stream from any OpenAI-compatible API (DeepSeek, OpenAI, Groq, Qwen)."""
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 8192,
        "stream": True,
    }
    if extra_body:
        body.update(extra_body)

    payload = json.dumps(body).encode()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=900)
        yield from _parse_sse_lines(resp)
        resp.close()
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Streaming HTTP error {exc.code}: {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Streaming connection error: {exc.reason}") from exc


def _stream_anthropic(prompt: str, model: str = None) -> Generator[str, None, None]:
    """Stream from Anthropic's messages API (different SSE format)."""
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY is not set.")
    model = model or ANTHROPIC_MODEL
    url = "https://api.anthropic.com/v1/messages"
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 8192,
        "stream": True,
    }
    payload = json.dumps(body).encode()
    headers = {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
    }

    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=900)
        for raw_line in resp:
            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line or not line.startswith("data: "):
                continue
            json_str = line[6:]
            try:
                data = json.loads(json_str)
                event_type = data.get("type", "")
                if event_type == "content_block_delta":
                    delta = data.get("delta", {})
                    text = delta.get("text", "")
                    if text:
                        yield text
                elif event_type == "message_stop":
                    break
            except json.JSONDecodeError:
                continue
        resp.close()
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Anthropic streaming error {exc.code}: {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Anthropic connection error: {exc.reason}") from exc


def _stream_ollama(prompt: str, model: str = None) -> Generator[str, None, None]:
    """Stream from local Ollama (native streaming, not SSE)."""
    model = model or OLLAMA_MODEL
    url = f"{OLLAMA_HOST}/api/generate"
    body = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "options": {
            "num_predict": 8192,
            "num_ctx": int(os.getenv("OLLAMA_CONTEXT", "32768")),
            "temperature": float(os.getenv("OLLAMA_TEMPERATURE", "0.3")),
        },
    }
    payload = json.dumps(body).encode()
    headers = {"Content-Type": "application/json"}

    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=900)
        for raw_line in resp:
            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                token = data.get("response", "")
                if token:
                    yield token
                if data.get("done", False):
                    break
            except json.JSONDecodeError:
                continue
        resp.close()
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Ollama streaming error {exc.code}: {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Ollama connection error: {exc.reason}") from exc


# ---------------------------------------------------------------------------
# Main streaming dispatcher
# ---------------------------------------------------------------------------
def stream_ai(
    prompt: str,
    provider: str = None,
    model: str = None,
) -> Generator[str, None, None]:
    """
    Stream AI response token by token.
    Yields string chunks as they arrive from the provider.
    """
    provider = provider or DEFAULT_PROVIDER

    if provider == "deepseek":
        if not DEEPSEEK_API_KEY:
            raise RuntimeError("DEEPSEEK_API_KEY is not set.")
        yield from _stream_openai_compatible(
            prompt,
            url="https://api.deepseek.com/chat/completions",
            api_key=DEEPSEEK_API_KEY,
            model=model or DEEPSEEK_MODEL,
            extra_body={"thinking": {"type": "disabled"}},
        )

    elif provider == "openai":
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not set.")
        yield from _stream_openai_compatible(
            prompt,
            url="https://api.openai.com/v1/chat/completions",
            api_key=OPENAI_API_KEY,
            model=model or OPENAI_MODEL,
        )

    elif provider == "groq":
        if not GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is not set.")
        yield from _stream_openai_compatible(
            prompt,
            url="https://api.groq.com/openai/v1/chat/completions",
            api_key=GROQ_API_KEY,
            model=model or GROQ_MODEL,
        )

    elif provider == "qwen":
        if not DASHSCOPE_API_KEY:
            raise RuntimeError("DASHSCOPE_API_KEY is not set.")
        yield from _stream_openai_compatible(
            prompt,
            url=f"{DASHSCOPE_BASE_URL.rstrip('/')}/chat/completions",
            api_key=DASHSCOPE_API_KEY,
            model=model or QWEN_MODEL,
            extra_body={"enable_thinking": False},
        )

    elif provider == "anthropic":
        yield from _stream_anthropic(prompt, model=model)

    elif provider == "ollama":
        yield from _stream_ollama(prompt, model=model)

    else:
        raise RuntimeError(f"Unknown streaming provider: {provider}")


# ---------------------------------------------------------------------------
# Convenience: stream to console and return full text
# ---------------------------------------------------------------------------
def stream_to_console(
    prompt: str,
    provider: str = None,
    model: str = None,
    prefix: str = "",
) -> str:
    """
    Stream response to stdout in real-time, return the complete text.
    Use this as a drop-in replacement for call_ai() when you want visible output.
    """
    if prefix:
        sys.stdout.write(prefix)
        sys.stdout.flush()

    chunks = []
    try:
        for chunk in stream_ai(prompt, provider=provider, model=model):
            sys.stdout.write(chunk)
            sys.stdout.flush()
            chunks.append(chunk)
    except RuntimeError as exc:
        # On streaming failure, fall back to non-streaming
        from providers import call_ai
        print(f"\n[streaming failed: {exc}, falling back to non-streaming]")
        result = call_ai(prompt, provider=provider, model=model)
        sys.stdout.write(result)
        sys.stdout.flush()
        return result

    sys.stdout.write("\n")
    sys.stdout.flush()
    return "".join(chunks)


# ---------------------------------------------------------------------------
# Tee stream: stream to display while buffering for transcript
# ---------------------------------------------------------------------------
def tee_stream(
    prompt: str,
    provider: str = None,
    model: str = None,
    display_fn=None,
) -> str:
    """
    Stream response, calling display_fn(chunk) for each piece,
    and return the complete buffered response.

    If display_fn is None, prints to stdout.
    Useful for Streamlit: pass st.write_stream or a container.write method.
    """
    if display_fn is None:
        display_fn = lambda chunk: (sys.stdout.write(chunk), sys.stdout.flush())

    chunks = []
    try:
        for chunk in stream_ai(prompt, provider=provider, model=model):
            display_fn(chunk)
            chunks.append(chunk)
    except RuntimeError as exc:
        from providers import call_ai
        result = call_ai(prompt, provider=provider, model=model)
        display_fn(result)
        return result

    return "".join(chunks)
