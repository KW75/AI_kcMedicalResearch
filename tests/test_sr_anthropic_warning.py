"""SR --provider anthropic is refused since Session 40: SR uses the OCR
provider list (ollama, qwen, openai). The old warning about the two checks
the Anthropic route skipped (sr_provider_warning) is removed with it.
The guard against citing closed #61 is kept."""
from pathlib import Path

import main


def test_sr_refuses_anthropic():
    msg = main.sr_provider_error("sr", "anthropic")
    assert msg and "anthropic" in msg


def test_anthropic_warning_removed():
    assert not hasattr(main, "sr_provider_warning")


def test_main_no_longer_cites_known_issue_61():
    src = (Path(main.__file__)).read_text(encoding="utf-8")
    assert "Known Issue #61" not in src
    assert "(#61)" not in src
