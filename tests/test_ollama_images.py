"""Ollama image input for OCR (Session 35 design).

call_ollama_provider(prompt, images=[png_bytes, ...]) must send the images
base64-encoded in the "images" field of /api/generate. Calls without images
must send exactly what they sent before (no "images" key), so text modes
are unchanged. No live Ollama needed: urlopen is patched.
"""
import base64
import json

import providers


class _FakeResponse:
    def __init__(self, body):
        self._body = json.dumps(body).encode()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self._body


def _capture(monkeypatch):
    sent = {}

    def fake_urlopen(req, timeout=0):
        sent["payload"] = json.loads(req.data)
        return _FakeResponse({"response": "ok"})

    monkeypatch.setattr(providers, "urlopen", fake_urlopen)
    return sent


def test_images_are_sent_base64(monkeypatch):
    sent = _capture(monkeypatch)
    png1, png2 = b"\x89PNG-page-1", b"\x89PNG-page-2"
    providers.call_ollama_provider("read this", model="gemma4:e4b",
                                   images=[png1, png2])
    assert sent["payload"]["images"] == [
        base64.b64encode(png1).decode("ascii"),
        base64.b64encode(png2).decode("ascii"),
    ]


def test_image_request_keeps_think_off(monkeypatch):
    sent = _capture(monkeypatch)
    providers.call_ollama_provider("read this", model="gemma4:e4b",
                                   images=[b"\x89PNG"])
    assert sent["payload"]["think"] is False


def test_text_call_sends_no_images_key(monkeypatch):
    sent = _capture(monkeypatch)
    providers.call_ollama_provider("hello", model="gemma4:e4b")
    assert "images" not in sent["payload"]
