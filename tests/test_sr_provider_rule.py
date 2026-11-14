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


# --- Session 40: a .env DEFAULT_PROVIDER that SR cannot use must not stop
# SR when --provider was not typed (CI sets deepseek). A typed --provider is
# still refused. Tests set DEFAULT_PROVIDER themselves: no .env dependence.

def _run_sr(monkeypatch, env_default, argv):
    calls = []
    monkeypatch.setattr(main, "DEFAULT_PROVIDER", env_default)
    monkeypatch.setattr(main, "validate_api_keys", lambda *a, **k: None)
    monkeypatch.setattr(main, "run_sr_launcher",
                        lambda **kw: calls.append(kw))
    main.run_cli(main.parse_args(argv))
    return calls


def test_env_default_sr_cannot_use_falls_back_to_sr_default(monkeypatch, capsys):
    calls = _run_sr(monkeypatch, "deepseek", ["--mode", "sr", "--confirm-cloud"])
    assert calls and calls[0]["provider"] == main.SR_DEFAULT_PROVIDER
    assert main.SR_DEFAULT_PROVIDER in main.SR_PROVIDERS
    out = capsys.readouterr().out
    assert "deepseek" in out and main.SR_DEFAULT_PROVIDER in out


def test_env_default_sr_can_use_is_kept(monkeypatch):
    calls = _run_sr(monkeypatch, "ollama", ["--mode", "sr", "--confirm-cloud"])
    assert calls and calls[0]["provider"] == "ollama"


def test_typed_provider_still_refused_whatever_env_says(monkeypatch):
    with pytest.raises(SystemExit) as e:
        _run_sr(monkeypatch, "ollama",
                ["--mode", "sr", "--provider", "deepseek", "--confirm-cloud"])
    assert e.value.code == 1


def test_parse_args_records_whether_provider_was_typed(monkeypatch):
    monkeypatch.setattr(main, "DEFAULT_PROVIDER", "deepseek")
    a = main.parse_args(["--mode", "coding"])
    assert a.provider == "deepseek" and a.provider_explicit is False
    b = main.parse_args(["--mode", "coding", "--provider", "qwen"])
    assert b.provider == "qwen" and b.provider_explicit is True
