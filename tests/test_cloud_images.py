"""Cloud OCR: Qwen and OpenAI calls accept images (OpenAI-style image_url parts).

No network: urlopen is faked and the request body is captured.
"""
import base64
import json

import pytest

import providers

PNG = b"\x89PNG fake page"


class FakeResp:
    def __init__(self, body):
        self._b = json.dumps(body).encode()

    def read(self):
        return self._b

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


@pytest.fixture
def sent(monkeypatch):
    box = {}

    def fake_urlopen(req, timeout=None):
        box["payload"] = json.loads(req.data)
        return FakeResp({"choices": [{"message": {"content": "OK"}}]})

    monkeypatch.setattr(providers, "urlopen", fake_urlopen)
    monkeypatch.setattr(providers, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(providers, "DASHSCOPE_API_KEY", "test-key")
    return box


CALLS = {"openai": "call_openai_provider", "qwen": "call_qwen_provider"}


def _call(name, *args, **kwargs):
    return getattr(providers, CALLS[name])(*args, **kwargs)


@pytest.mark.parametrize("name", ["openai", "qwen"])
def test_images_sent_as_image_url_parts(sent, name):
    _call(name, "Transcribe", images=[PNG, PNG])
    content = sent["payload"]["messages"][0]["content"]
    images = [p for p in content if p["type"] == "image_url"]
    texts = [p for p in content if p["type"] == "text"]
    b64 = base64.b64encode(PNG).decode("ascii")
    assert [p["image_url"]["url"] for p in images] == [f"data:image/png;base64,{b64}"] * 2
    assert [p["text"] for p in texts] == ["Transcribe"]


@pytest.mark.parametrize("name", ["openai", "qwen"])
def test_text_call_unchanged(sent, name):
    _call(name, "hello")
    assert sent["payload"]["messages"][0]["content"] == "hello"


def test_qwen_images_default_to_vision_model(sent):
    providers.call_qwen_provider("x", images=[PNG])
    assert sent["payload"]["model"] == providers.QWEN_VISION_MODEL


def test_qwen_text_keeps_text_model(sent):
    providers.call_qwen_provider("x")
    assert sent["payload"]["model"] == providers.QWEN_MODEL


def test_chosen_model_is_kept_with_images(sent):
    providers.call_qwen_provider("x", model="my-model", images=[PNG])
    assert sent["payload"]["model"] == "my-model"
