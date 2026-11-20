"""Session 48: launcher Setup can update models.

10 Setup -> 2 Local AI -> 3 Update pulled models pulls every pulled
model again (asks first). 10 Setup -> 4 Cloud AI models asks each
provider with a key for its model list (no tokens), shows where each
*_MODEL value comes from and copies the .env.example name only after y.
Nothing here touches the network, Ollama or the real .env.
"""
import importlib
import importlib.util
import io
import json
import sys
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import env_file

ROOT = Path(__file__).resolve().parent.parent
EXE = r"C:\Ollama\ollama.exe"
MODELS = [
    {"name": "nomic-embed-text:latest", "size_gb": 0.3, "params_b": 0.1},
    {"name": "gemma4:e4b", "size_gb": 6.6, "params_b": 7.5},
    {"name": "qwen3:8b", "size_gb": 5.2, "params_b": 8.2},
]
VARS = ("DEEPSEEK_API_KEY", "DEEPSEEK_MODEL", "DASHSCOPE_API_KEY",
        "DASHSCOPE_BASE_URL", "QWEN_MODEL", "QWEN_VISION_MODEL",
        "OPENAI_API_KEY", "OPENAI_MODEL", "GROQ_API_KEY", "GROQ_MODEL",
        "ANTHROPIC_API_KEY", "ANTHROPIC_MODEL", "OLLAMA_MODEL")


def _cm():
    return importlib.import_module("cloud_models")


def _fake(ids, seen):
    def fake(req, timeout=None):
        seen.append(req)
        return io.BytesIO(json.dumps({"data": [{"id": i} for i in ids]}).encode())
    return fake


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """providers.py loads .env into os.environ; these tests need none of it."""
    for var in VARS:
        monkeypatch.delenv(var, raising=False)


@pytest.fixture(scope="module")
def launcher():
    spec = importlib.util.spec_from_file_location(
        "launcher_s48_setup_under_test", ROOT / "scripts" / "launcher.py")
    mod = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {"colorama": MagicMock()}):
        spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def env_path(launcher, tmp_path, monkeypatch):
    template = tmp_path / ".env.example"
    template.write_text("DEEPSEEK_MODEL=deepseek-flash\nOLLAMA_MODEL=gemma4:e4b\n",
                        encoding="utf-8")
    path = tmp_path / ".env"
    monkeypatch.setattr(launcher, "ENV_FILE", path)
    monkeypatch.setattr(launcher, "ENV_TEMPLATE", template)
    return path


# --- cloud_models -------------------------------------------------------------

def test_defaults_read_from_providers_source():
    d = _cm().code_defaults()
    assert d["DEEPSEEK_MODEL"] == "deepseek-flash"
    assert d["QWEN_VISION_MODEL"] == "qwen3-vl-plus"


def test_system_variable_wins_over_env(monkeypatch):
    cm = _cm()
    monkeypatch.setenv("ANTHROPIC_MODEL", "deepseek-v4-pro[1m]")
    assert cm.resolve("ANTHROPIC_MODEL", {"ANTHROPIC_MODEL": "claude-sonnet-5"}) == (
        "deepseek-v4-pro[1m]", cm.SYSTEM)


def test_env_then_code_default():
    cm = _cm()
    assert cm.resolve("DEEPSEEK_MODEL", {"DEEPSEEK_MODEL": "x"}) == ("x", ".env")
    assert cm.resolve("DEEPSEEK_MODEL", {}) == ("deepseek-flash", "code default")


def test_unlisted_name_gets_template_suggestion(monkeypatch):
    cm = _cm()
    seen = []
    monkeypatch.setattr(cm, "urlopen", _fake(["deepseek-flash", "deepseek-v4-pro"], seen))
    rows = cm.check_all({"DEEPSEEK_API_KEY": "k", "DEEPSEEK_MODEL": "old-name"},
                        {"DEEPSEEK_MODEL": "deepseek-flash"})
    m = next(r for r in rows if r["provider"] == "deepseek")["models"][0]
    assert (m["value"], m["source"], m["listed"], m["suggest"]) == (
        "old-name", ".env", False, "deepseek-flash")
    assert len(seen) == 1
    assert seen[0].get_header("Authorization") == "Bearer k"


def test_no_key_sends_nothing(monkeypatch):
    cm = _cm()
    def boom(*a, **k):
        raise AssertionError("no request expected")
    monkeypatch.setattr(cm, "urlopen", boom)
    rows = cm.check_all({}, {})
    assert rows and not any(r["key_set"] for r in rows)


def test_http_error_is_reported_not_raised(monkeypatch):
    cm = _cm()
    def fail(req, timeout=None):
        raise urllib.error.HTTPError("https://x.test", 401, "Unauthorized", {},
                                     io.BytesIO(b'{"error": "invalid key"}'))
    monkeypatch.setattr(cm, "urlopen", fail)
    row = next(r for r in cm.check_all({"DEEPSEEK_API_KEY": "k"}, {})
               if r["provider"] == "deepseek")
    assert "HTTP error 401" in row["error"] and "invalid key" in row["error"]
    assert row["models"][0]["listed"] is None


def test_anthropic_uses_its_own_headers(monkeypatch):
    cm = _cm()
    seen = []
    monkeypatch.setattr(cm, "urlopen", _fake(["claude-sonnet-5"], seen))
    cm.check_all({"ANTHROPIC_API_KEY": "k"}, {})
    assert len(seen) == 1
    assert seen[0].full_url.startswith("https://api.anthropic.com/v1/models")
    assert seen[0].get_header("X-api-key") == "k"


def test_qwen_checks_both_models_at_the_env_base_url(monkeypatch):
    cm = _cm()
    seen = []
    monkeypatch.setattr(cm, "urlopen", _fake(["qwen-plus-latest", "qwen3-vl-plus"], seen))
    rows = cm.check_all({"DASHSCOPE_API_KEY": "k",
                         "DASHSCOPE_BASE_URL": "https://example.test/v1/"}, {})
    qwen = next(r for r in rows if r["provider"] == "qwen")
    assert seen[0].full_url == "https://example.test/v1/models"
    assert [m["var"] for m in qwen["models"]] == ["QWEN_MODEL", "QWEN_VISION_MODEL"]
    assert all(m["listed"] for m in qwen["models"])


# --- launcher: Setup -> 4 Cloud AI models -------------------------------------

def _rows(source=".env", listed=False, suggest="deepseek-flash", key_set=True):
    return [{"provider": "deepseek", "label": "DeepSeek", "key_set": key_set,
             "error": "", "names": ["deepseek-flash", "deepseek-v4-pro"],
             "models": [{"var": "DEEPSEEK_MODEL", "value": "old-name",
                         "source": source, "listed": listed, "suggest": suggest}]}]


def _cloud(launcher, rows, inputs):
    with patch.object(launcher.cloud_models, "check_all", return_value=rows), \
         patch.object(launcher, "safe_input", side_effect=inputs) as fake_input:
        launcher.cloud_models_menu()
    return fake_input


def _saved(path):
    return env_file.read_values(path).get("DEEPSEEK_MODEL") if path.exists() else None


def test_setup_item_4_opens_cloud_models(launcher):
    with patch.object(launcher, "cloud_models_menu") as fake_menu, \
         patch.object(launcher, "safe_input", side_effect=["4", "0"]):
        launcher.setup_menu()
    fake_menu.assert_called_once()


def test_setup_help_stays_item_3(launcher):
    with patch.object(launcher, "open_help") as fake_help, \
         patch.object(launcher, "safe_input", side_effect=["3", "0"]):
        launcher.setup_menu()
    fake_help.assert_called_once()


def test_cloud_menu_without_keys_says_so(launcher, env_path, capsys):
    fake_input = _cloud(launcher, _rows(key_set=False), [""])
    assert "No cloud API keys" in capsys.readouterr().out
    assert fake_input.call_count == 1


def test_cloud_menu_saves_suggestion_after_yes(launcher, env_path):
    _cloud(launcher, _rows(), ["y", ""])
    assert _saved(env_path) == "deepseek-flash"


def test_cloud_menu_changes_nothing_on_enter(launcher, env_path):
    _cloud(launcher, _rows(), ["", ""])
    assert _saved(env_path) is None


def test_cloud_menu_system_variable_warns_and_offers_nothing(launcher, env_path, capsys):
    fake_input = _cloud(launcher, _rows(source="system variable"), [""])
    assert "system environment variable" in capsys.readouterr().out
    assert fake_input.call_count == 1
    assert _saved(env_path) is None


# --- launcher: Local AI -> 3 Update pulled models -----------------------------

def _local(launcher, inputs, rc=0):
    with patch.object(launcher, "_ollama_exe", return_value=EXE), \
         patch.object(launcher, "ollama_version", return_value="0.40.11"), \
         patch.object(launcher, "list_ollama_models", return_value=MODELS), \
         patch.object(launcher, "model_capabilities", side_effect=lambda h, n: {"completion"}), \
         patch.object(launcher, "safe_input", side_effect=inputs) as fake_input, \
         patch.object(launcher.subprocess, "run",
                      return_value=MagicMock(returncode=rc)) as fake_run:
        launcher.local_ai_menu()
    return fake_input, fake_run


def test_update_pulls_every_model_after_yes(launcher, env_path):
    _, fake_run = _local(launcher, ["3", "y", "0"])
    assert [c.args[0] for c in fake_run.call_args_list] == [
        [EXE, "pull", m["name"]] for m in MODELS]


def test_update_asks_first_and_enter_cancels(launcher, env_path):
    fake_input, fake_run = _local(launcher, ["3", "", "0"])
    assert "Update all" in " ".join(str(c.args[0]) for c in fake_input.call_args_list)
    fake_run.assert_not_called()


def test_update_goes_on_after_a_failure(launcher, env_path, capsys):
    _, fake_run = _local(launcher, ["3", "y", "0"], rc=1)
    assert fake_run.call_count == len(MODELS)
    assert f"{len(MODELS)} failed" in capsys.readouterr().out


def test_docs_name_both_options():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    setup = (ROOT / "Readme" / "Setup_Instructions_for_Users.txt").read_text(encoding="utf-8")
    assert "10 Setup -> 4 Cloud AI models" in readme
    assert "3 Update pulled models" in readme
    assert "4 Cloud AI models" in setup
    assert "3 Update pulled models" in setup
