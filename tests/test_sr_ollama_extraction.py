"""Session 40, item 12 commit 2: SR extraction on local Ollama.
call_ollama_provider is faked: no network."""
import base64
import inspect

import pytest

import main
import providers
from pipelines.sr.src.extraction.data_extractor import DataExtractor

PNG = b"\x89PNG\r\n\x1a\nfake"
B64 = base64.b64encode(PNG).decode("ascii")


@pytest.fixture
def fake_ollama(monkeypatch):
    calls = []

    def _fake(prompt, model=None, max_tokens=8192, images=None):
        calls.append({"prompt": prompt, "model": model,
                      "max_tokens": max_tokens, "images": images})
        return "  OUT  "
    monkeypatch.setattr(providers, "call_ollama_provider", _fake)
    return calls


def _ollama_extractor():
    return DataExtractor(provider="ollama", model="gemma4:e4b")


def test_extractor_accepts_ollama_without_cloud_client():
    assert _ollama_extractor().client is None


@pytest.mark.parametrize("p", ["anthropic", "groq"])
def test_extractor_refuses_anthropic_and_groq(monkeypatch, p):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "dummy")
    monkeypatch.setenv("GROQ_API_KEY", "dummy")
    with pytest.raises(ValueError) as e:
        DataExtractor(provider=p, model="x")
    assert "ollama" in str(e.value)


def test_vision_call_sends_png_bytes_max_five(fake_ollama):
    out = _ollama_extractor()._call_vision_api([B64] * 7, "PROMPT")
    assert out == "OUT"
    c = fake_ollama[0]
    assert c["images"] == [PNG] * 5
    assert c["model"] == "gemma4:e4b" and c["prompt"] == "PROMPT"


def test_text_call_goes_to_ollama_without_images(fake_ollama):
    out = _ollama_extractor()._call_text_api("Table 2 text", "p.pdf")
    assert out == "OUT"
    assert fake_ollama[0]["images"] is None
    assert "Table 2 text" in fake_ollama[0]["prompt"]


def test_chat_call_goes_to_ollama(fake_ollama):
    out = _ollama_extractor()._call_chat_api_with_prompt("Q", max_tokens=256)
    assert out == "OUT"
    assert fake_ollama[0]["max_tokens"] == 256
    assert fake_ollama[0]["images"] is None


def test_sr_default_is_local():
    assert main.SR_DEFAULT_PROVIDER == "ollama"
    src = inspect.getsource(main.run_sr_launcher)
    assert "provider or SR_DEFAULT_PROVIDER" in src
    assert "sr_ollama_vision_error(" in src


def test_vision_error_when_model_cannot_read_images():
    msg = main.sr_ollama_vision_error("qwen3:8b",
                                      caps_fn=lambda h, m: {"completion"})
    assert msg and "qwen3:8b" in msg and "vision" in msg
    assert "qwen" in msg and "openai" in msg


def test_no_vision_error_for_vision_model():
    assert main.sr_ollama_vision_error(
        "gemma4:e4b", caps_fn=lambda h, m: {"completion", "vision"}) is None



# --- SR sub-pipeline (pipelines/sr/main.py) run directly: same rule.
# resolve_model is faked to stop main() right after argument parsing.
import sys

import pipelines.sr.main as sr_main


class _Stop(Exception):
    pass


def _sr_main_provider(monkeypatch, argv):
    seen = {}

    def _fake(provider, model):
        seen["provider"] = provider
        raise _Stop
    monkeypatch.setattr(sr_main, "resolve_model", _fake)
    monkeypatch.setattr(sys, "argv", ["sr_main"] + argv)
    with pytest.raises(_Stop):
        sr_main.main()
    return seen["provider"]


def test_sr_subpipeline_defaults_to_ollama(monkeypatch):
    assert _sr_main_provider(monkeypatch, []) == "ollama"


@pytest.mark.parametrize("p", ["ollama", "qwen", "openai"])
def test_sr_subpipeline_accepts_ocr_providers(monkeypatch, p):
    assert _sr_main_provider(monkeypatch, ["--provider", p]) == p


@pytest.mark.parametrize("p", ["anthropic", "deepseek", "groq"])
def test_sr_subpipeline_refuses_other_providers(monkeypatch, p):
    monkeypatch.setattr(sys, "argv", ["sr_main", "--provider", p])
    with pytest.raises(SystemExit) as e:
        sr_main.main()
    assert e.value.code == 2
