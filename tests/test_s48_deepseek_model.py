"""Session 48: DeepSeek default model name.

The DeepSeek API rejected the old default name with HTTP 400
("The supported API model names are deepseek-flash, ...").
providers.py, .env.example and the live test now use deepseek-flash.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OLD = "deepseek-v4" + "-flash"


def test_default_and_env_example_use_deepseek_flash():
    src = (ROOT / "SOURCE_CODE" / "providers.py").read_text(encoding="utf-8")
    assert 'os.getenv("DEEPSEEK_MODEL", "deepseek-flash")' in src
    env = (ROOT / ".env.example").read_text(encoding="utf-8").splitlines()
    assert "DEEPSEEK_MODEL=deepseek-flash" in env


def test_old_deepseek_name_gone():
    for rel in ("SOURCE_CODE/providers.py", ".env.example",
                "tests/test_live_providers.py", "docs/project/PRD.md"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert OLD not in text, f"{OLD} still in {rel}"
