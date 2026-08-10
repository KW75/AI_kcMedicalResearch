"""
test_live_providers.py  -  Live provider smoke test
Run manually:  python test_live_providers.py
Requires:  .env with at least one real API key
"""
import os, sys, time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

PROMPT = "Reply with exactly: OK"

# ── Ollama ────────────────────────────────────────────────────────────────
def test_ollama():
    import requests
    url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "llama3")
    try:
        r = requests.post(
            f"{url}/api/chat",
            json={"model": model, "messages": [{"role": "user", "content": PROMPT}], "stream": False},
            timeout=30,
        )
        r.raise_for_status()
        text = r.json().get("message", {}).get("content", "")
        return "OK" in text.upper()
    except Exception as e:
        print(f"  [ollama] {e}")
        return False

# ── OpenAI ────────────────────────────────────────────────────────────────
def test_openai():
    key = os.getenv("OPENAI_API_KEY", "")
    if not key or key.startswith("sk-placeholder"):
        return None
    try:
        import openai
        client = openai.OpenAI(api_key=key)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": PROMPT}],
            max_tokens=10,
        )
        text = resp.choices[0].message.content or ""
        return "OK" in text.upper()
    except Exception as e:
        print(f"  [openai] {e}")
        return False

# ── Anthropic ─────────────────────────────────────────────────────────────
def test_anthropic():
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if not key or key.startswith("sk-placeholder"):
        return None
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key)
        msg = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=10,
            messages=[{"role": "user", "content": PROMPT}],
        )
        text = msg.content[0].text if msg.content else ""
        return "OK" in text.upper()
    except anthropic.PermissionDeniedError:
        print(f"  [anthropic] geo-restricted (VPN required)")
        return None
    except Exception as e:
        print(f"  [anthropic] {e}")
        return False


# ── DeepSeek ──────────────────────────────────────────────────────────────
def test_deepseek():
    key = os.getenv("DEEPSEEK_API_KEY", "")
    if not key or key.startswith("sk-placeholder"):
        return None
    try:
        import openai
        client = openai.OpenAI(api_key=key, base_url="https://api.deepseek.com")
        resp = client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=[{"role": "user", "content": PROMPT}],
            max_tokens=20,
            extra_body={"thinking": {"type": "disabled"}},
        )
        text = resp.choices[0].message.content or ""
        return "OK" in text.upper()
    except Exception as e:
        print(f"  [deepseek] {e}")
        return False

# ── Groq ──────────────────────────────────────────────────────────────────
def test_groq():
    key = os.getenv("GROQ_API_KEY", "")
    if not key or key.startswith("sk-placeholder"):
        return None
    try:
        import groq
        client = groq.Groq(api_key=key)
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": PROMPT}],
            max_tokens=10,
        )
        text = resp.choices[0].message.content or ""
        return "OK" in text.upper()
    except Exception as e:
        print(f"  [groq] {e}")
        return False

# ── Qwen/DashScope ────────────────────────────────────────────────────────
def test_qwen():
    key = os.getenv("DASHSCOPE_API_KEY", "")
    base_url = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1")
    if not key or key.startswith("sk-placeholder"):
        return None
    try:
        import openai
        client = openai.OpenAI(api_key=key, base_url=base_url)
        resp = client.chat.completions.create(
            model="qwen3.7-plus",
            messages=[{"role": "user", "content": PROMPT}],
            max_tokens=20,
            extra_body={"enable_thinking": False},
        )
        text = resp.choices[0].message.content or ""
        return "OK" in text.upper()
    except Exception as e:
        print(f"  [qwen] {e}")
        return False

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
    result = fn()
    elapsed = time.time() - t0
    if result is None:
        print(f"SKIPPED (no API key)")
        skipped += 1
    elif result:
        print(f"PASS  ({elapsed:.1f}s)")
        passed += 1
    else:
        print(f"FAIL  ({elapsed:.1f}s)")
        failed += 1

print(f"\nResults: {passed} passed, {skipped} skipped (no key), {failed} failed")
if failed:
    sys.exit(1)
