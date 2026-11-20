"""Session 49 PR C: --mode samd (launcher menu 9), stub only.

Pinned:
- --mode samd is accepted; --dry-run is still a main.py flag.
- SaMD calls one provider directly: data_destinations lists only it.
- SaMD reads images, so only Ollama, Qwen and OpenAI are allowed; the
  OCR refusal text is unchanged.
- The SaMD cloud banner names clinical images and asks for de-identified data.
- The stub prints the intended-use statement, lists input/samd/ and
  makes no AI call.
"""
import io
from contextlib import redirect_stdout
from unittest.mock import patch

import pytest

from SOURCE_CODE import main


def _parse(argv):
    with patch("sys.argv", ["main.py"] + argv):
        return main.parse_args()


def test_mode_samd_is_accepted():
    assert _parse(["--mode", "samd"]).mode == "samd"


def test_dry_run_flag_still_exists():
    assert _parse(["--dry-run"]).dry_run is True


@pytest.mark.parametrize("prov", ["ollama", "qwen", "openai"])
def test_samd_lists_only_chosen_provider(prov):
    assert main.data_destinations("samd", prov) == [prov]


@pytest.mark.parametrize("prov", ["groq", "deepseek", "anthropic"])
def test_samd_refuses_non_vision_providers(prov):
    msg = main.ocr_provider_error("samd", prov)
    assert msg and msg.startswith(f"SaMD: {prov}")


@pytest.mark.parametrize("prov", ["ollama", "qwen", "openai"])
def test_samd_allows_vision_providers(prov):
    assert main.ocr_provider_error("samd", prov) is None


def test_ocr_refusal_text_unchanged():
    assert main.ocr_provider_error("ocr", "groq").startswith("OCR: groq")


def test_samd_cloud_banner_names_clinical_images():
    buf = io.StringIO()
    with redirect_stdout(buf):
        ok = main.confirm_data_destinations(
            "samd", "qwen", confirm_cloud=True, stdin_is_tty=False)
    out = buf.getvalue().lower()
    assert ok is True
    assert "clinical photos" in out
    assert "identifiers" in out


def test_stub_lists_input_and_prints_intended_use(tmp_path):
    from SOURCE_CODE.pipelines.samd import cli as samd_cli
    d = tmp_path / "input" / "samd"
    d.mkdir(parents=True)
    for name in ("rash.jpg", "labs.png", "notes.txt", "ignore.exe"):
        (d / name).write_bytes(b"x")
    lines = []
    res = samd_cli.run(tmp_path, log=lines.append,
                       input_fn=lambda _p, a=iter(["", ""]): next(a))
    out = "\n".join(lines)
    assert "not a cleared or certified medical device" in out
    assert res["files"] == ["labs.png", "notes.txt", "rash.jpg"]
    assert "ignore.exe" not in out
    assert res["ai_called"] is False


def test_stub_creates_missing_input_folder(tmp_path):
    from SOURCE_CODE.pipelines.samd import cli as samd_cli
    lines = []
    res = samd_cli.run(tmp_path, log=lines.append,
                       input_fn=lambda _p, a=iter([""]): next(a))
    assert (tmp_path / "input" / "samd").is_dir()
    assert res is None  # PR D: no files and no text = not run
    assert "input/samd" in "\n".join(lines).replace("\\", "/")
