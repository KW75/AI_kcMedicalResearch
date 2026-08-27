"""
test_live_providers.py  -  Live provider smoke test

Run standalone:  python tests/test_live_providers.py
Run via pytest:  pytest tests/test_live_providers.py -v
                 (requires .env with at least one real API key)

Marks all tests with @pytest.mark.live so they can be excluded:
    pytest --ignore=tests/test_live_providers.py
    pytest -m "not live"
"""
import os
import sys
import time
from pathlib import Path

import pytest
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

PROMPT = "Reply with exactly: OK"

# Mark all tests in this module as 'live' (requires network + API keys)
pytestmark = pytest.mark.live


# ── Ollama ────────────────────────────────────────────────────────────────
@pytest.mark.live
def test_ollama():
    import requests
    url = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    # Auto-detect model like main.py does
    try:
        tags = requests.get(f"{url}/api/tags", timeout=5).json()
        models = [m["name"] for m in tags.get("models", [])
                  if "embed" not in m["name"].lower() and "nomic" not in m["name"].lower()]
        model = models[0] if models else "llama3.2"
    except Exception:
        pytest.skip("Ollama not running")
        return

    r = requests.post(
        f"{url}/api/generate",
        json={"model": model, "prompt": PROMPT, "stream": False},
        timeout=60,
    )
    r.raise_for_status()
    text = r.json().get("response", "")
    assert "OK" in text.upper(), f"Expected 'OK' in response, got: {text[:100]}"


# ── OpenAI ────────────────────────────────────────────────────────────────
@pytest.mark.live
def test_openai():
    key = os.getenv("OPENAI_API_KEY", "")
    if not key or key.startswith("sk-placeholder"):
        pytest.skip("No OPENAI_API_KEY")
    import openai
    client = openai.OpenAI(api_key=key)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": PROMPT}],
        max_tokens=10,
    )
    text = resp.choices[0].message.content or ""
    assert "OK" in text.upper(), f"Expected 'OK' in response, got: {text[:100]}"


# ── Anthropic ─────────────────────────────────────────────────────────────
@pytest.mark.live
def test_anthropic():
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if not key or key.startswith("sk-placeholder"):
        pytest.skip("No ANTHROPIC_API_KEY")
    import anthropic
    client = anthropic.Anthropic(api_key=key)
    try:
        msg = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=10,
            messages=[{"role": "user", "content": PROMPT}],
        )
    except anthropic.PermissionDeniedError:
        pytest.skip("Anthropic geo-restricted (VPN required)")
        return
    text = msg.content[0].text if msg.content else ""
    assert "OK" in text.upper(), f"Expected 'OK' in response, got: {text[:100]}"


# ── DeepSeek ──────────────────────────────────────────────────────────────
@pytest.mark.live
def test_deepseek():
    key = os.getenv("DEEPSEEK_API_KEY", "")
    if not key or key.startswith("sk-placeholder"):
        pytest.skip("No DEEPSEEK_API_KEY")
    import openai
    client = openai.OpenAI(api_key=key, base_url="https://api.deepseek.com")
    resp = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[{"role": "user", "content": PROMPT}],
        max_tokens=20,
        extra_body={"thinking": {"type": "disabled"}},
    )
    text = resp.choices[0].message.content or ""
    assert "OK" in text.upper(), f"Expected 'OK' in response, got: {text[:100]}"


# ── Groq ──────────────────────────────────────────────────────────────────
@pytest.mark.live
def test_groq():
    key = os.getenv("GROQ_API_KEY", "")
    if not key or key.startswith("sk-placeholder"):
        pytest.skip("No GROQ_API_KEY")
    import groq
    client = groq.Groq(api_key=key)
    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": PROMPT}],
        max_tokens=10,
    )
    text = resp.choices[0].message.content or ""
    assert "OK" in text.upper(), f"Expected 'OK' in response, got: {text[:100]}"


# ── Qwen/DashScope ────────────────────────────────────────────────────────
@pytest.mark.live
def test_qwen():
    key = os.getenv("DASHSCOPE_API_KEY", "")
    base_url = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1")
    if not key or key.startswith("sk-placeholder"):
        pytest.skip("No DASHSCOPE_API_KEY")
    import openai
    model = os.getenv("QWEN_MODEL", "qwen-plus-latest")
    client = openai.OpenAI(api_key=key, base_url=base_url)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": PROMPT}],
        max_tokens=20,
        extra_body={"enable_thinking": False},
    )
    text = resp.choices[0].message.content or ""
    assert "OK" in text.upper(), f"Expected 'OK' in response, got: {text[:100]}"


# ── Standalone runner ─────────────────────────────────────────────────────
if __name__ == "__main__":
    TESTS = [
        ("ollama",    test_ollama),
        ("openai",    test_openai),
        ("anthropic", test_anthropic),
        ("deepseek",  test_deepseek),
        ("groq",      test_groq),
        ("qwen",      test_qwen),
    ]

    print("\n=== AI_kcMedicalResearch - Live Provider Smoke Test ===\n")
    passed = skipped = failed = 0
    for name, fn in TESTS:
        print(f"  Testing {name}...", end=" ", flush=True)
        t0 = time.time()
        try:
            fn()
            print(f"PASS  ({time.time() - t0:.1f}s)")
            passed += 1
        except pytest.skip.Exception as e:
            print(f"SKIPPED ({e})")
            skipped += 1
        except Exception as e:
            print(f"FAIL  ({time.time() - t0:.1f}s) - {e}")
            failed += 1

    print(f"\nResults: {passed} passed, {skipped} skipped, {failed} failed")
    sys.exit(1 if failed else 0)
