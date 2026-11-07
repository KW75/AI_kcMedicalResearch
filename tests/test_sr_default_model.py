"""SR route default model (main.run_sr_launcher, Step 4).

Session 33: the SR route used the raw OLLAMA_MODEL, so with OLLAMA_MODEL
unset, `--mode sr --provider ollama` sent an empty model name. It now
follows the same rule as everywhere else: OLLAMA_MODEL, else gemma4:e4b.
"""
import main
import providers


def test_ollama_unset_uses_the_default_model(monkeypatch):
    monkeypatch.setattr(providers, "OLLAMA_MODEL", "")
    assert main._sr_default_model("ollama") == providers.OLLAMA_DEFAULT_MODEL


def test_ollama_env_model_wins(monkeypatch):
    monkeypatch.setattr(providers, "OLLAMA_MODEL", "qwen3:8b")
    assert main._sr_default_model("ollama") == "qwen3:8b"


def test_qwen_uses_the_vision_model():
    assert main._sr_default_model("qwen") == main.QWEN_VISION_MODEL


def test_unknown_provider_falls_back_to_qwen_vision():
    assert main._sr_default_model("nonsense") == main.QWEN_VISION_MODEL
