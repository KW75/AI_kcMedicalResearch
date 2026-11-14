"""Session 40 (item 12): SR uses the same providers as OCR - local Ollama
(vision model) first; qwen / openai only behind the cloud gate.
DeepSeek (no image input), Anthropic and Groq are refused."""
import argparse

import pytest

import main


@pytest.mark.parametrize("p", ["ollama", "qwen", "openai"])
def test_sr_allows_ollama_qwen_openai(p):
    assert main.sr_provider_error("sr", p) is None


@pytest.mark.parametrize("p", ["deepseek", "anthropic", "groq"])
def test_sr_refuses_other_providers_and_names_the_allowed_ones(p):
    msg = main.sr_provider_error("sr", p)
    assert msg and p in msg
    for ok in ("ollama", "qwen", "openai"):
        assert ok in msg


def test_other_modes_not_affected():
    assert main.sr_provider_error("coding", "anthropic") is None
    assert main.sr_provider_error("ocr", "groq") is None


def test_sr_and_ocr_share_one_provider_list():
    assert tuple(main.SR_PROVIDERS) == tuple(main.OCR_PROVIDERS)


def test_run_cli_stops_before_any_work_on_a_refused_sr_provider(capsys):
    args = argparse.Namespace(mode="sr", provider="anthropic")
    with pytest.raises(SystemExit) as e:
        main.run_cli(args)
    assert e.value.code == 1
    assert "anthropic" in capsys.readouterr().out
