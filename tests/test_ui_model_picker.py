"""v2.5 update #1: Ollama model dropdown in the Streamlit UI.

Pinned properties:
- With provider=ollama and models pulled, the UI offers the same models,
  descriptions and default as the launcher (ollama_models is the one source).
- Ollama unreachable, a cloud provider, or Render -> no choices, so the UI
  keeps the free-text model box. Cloud and Render never query Ollama.
- Detection uses only the RENDER* variables, not _is_cloud_environment():
  that one treats STREAMLIT_SERVER_PORT as cloud and would hide the
  dropdown on a local run that happens to set it.
- app.py must not import ollama_models at module level: Streamlit only puts
  ui/ on sys.path, so the real app would crash on startup. conftest.py puts
  SOURCE_CODE on sys.path, so only this source check can catch that.
"""
import ast
from pathlib import Path
from unittest.mock import patch

import pytest

import ui.app as app

ROOT = Path(__file__).resolve().parent.parent
RENDER_VARS = ("RENDER", "RENDER_SERVICE_ID", "RENDER_GIT_COMMIT")

MODELS = [  # what list_ollama_models returns: smallest first
    {"name": "llama3.2:latest", "size_gb": 2.0, "params_b": 3.2},
    {"name": "gemma4:e4b", "size_gb": 6.6, "params_b": 7.5},
    {"name": "qwen3:8b", "size_gb": 5.2, "params_b": 8.2},
    {"name": "qwen2.5:14b-instruct", "size_gb": 9.0, "params_b": 14.8},
]


@pytest.fixture(autouse=True)
def _not_on_render(monkeypatch):
    for var in RENDER_VARS:
        monkeypatch.delenv(var, raising=False)


def _caps(host, name):
    return {"completion", "vision"} if name == "gemma4:e4b" else {"completion"}


def _choices(provider, models=MODELS):
    with patch("ollama_models.list_ollama_models", return_value=models) as fake_list, \
         patch("ollama_models.model_capabilities", side_effect=_caps):
        return app._ollama_model_choices(provider), fake_list


class TestOllamaModelChoices:
    def test_lists_pulled_models_with_launcher_descriptions_and_default(self):
        from ollama_models import describe
        (choices, default), _ = _choices("ollama")
        assert [name for name, _ in choices] == [m["name"] for m in MODELS]
        assert dict(choices) == {m["name"]: describe(m, _caps(None, m["name"])) for m in MODELS}
        assert default == "gemma4:e4b"

    def test_ollama_unreachable_gives_no_choices(self):
        (choices, default), _ = _choices("ollama", models=[])
        assert (choices, default) == ([], "")

    def test_cloud_provider_never_queries_ollama(self):
        (choices, default), fake_list = _choices("deepseek")
        assert (choices, default) == ([], "")
        fake_list.assert_not_called()

    def test_render_never_queries_ollama(self, monkeypatch):
        monkeypatch.setenv("RENDER", "true")
        (choices, default), fake_list = _choices("ollama")
        assert (choices, default) == ([], "")
        fake_list.assert_not_called()

    def test_streamlit_server_port_alone_does_not_hide_the_dropdown(self, monkeypatch):
        monkeypatch.setenv("STREAMLIT_SERVER_PORT", "8501")
        (choices, _), _ = _choices("ollama")
        assert len(choices) == len(MODELS)


def test_app_does_not_import_ollama_models_at_module_level():
    tree = ast.parse((ROOT / "SOURCE_CODE" / "ui" / "app.py").read_text(encoding="utf-8"))
    for node in tree.body:  # module level only; imports inside functions are fine
        if isinstance(node, ast.Import):
            assert all(a.name != "ollama_models" for a in node.names)
        if isinstance(node, ast.ImportFrom):
            assert node.module != "ollama_models"


class TestLocalRunBlocked:
    """With provider=ollama and no models found, Run is disabled with a reason."""

    def test_blocked_when_no_local_models(self):
        msg = app._local_run_blocked("ollama", [])
        assert "Ollama" in msg

    def test_not_blocked_when_models_found(self):
        assert app._local_run_blocked("ollama", [("gemma4:e4b", "label")]) == ""

    def test_cloud_provider_never_blocked_by_this_rule(self):
        assert app._local_run_blocked("deepseek", []) == ""

    def test_render_message_points_to_a_cloud_provider(self, monkeypatch):
        monkeypatch.setenv("RENDER", "true")
        assert "cloud provider" in app._local_run_blocked("ollama", []).lower()

def test_every_mode_page_renders_with_ollama_down(monkeypatch):
    """Render each mode page with the default provider (ollama) and no local
    models. Catches page-level bugs such as a variable assigned only inside
    an if-block (Session 30: local_block UnboundLocalError), which the
    helper tests above cannot see."""
    from pathlib import Path
    from streamlit.testing.v1 import AppTest
    import ollama_models
    import ui.app as app_mod

    for var in ("RENDER", "RENDER_SERVICE_ID", "RENDER_GIT_COMMIT"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr(ollama_models, "list_ollama_models", lambda *a, **k: [])

    app_path = str(Path(app_mod.__file__))
    for mode in app_mod.MODES:
        at = AppTest.from_file(app_path, default_timeout=30)
        at.session_state["page"] = mode
        at.run()
        assert not at.exception, f"{mode}: {at.exception[0].message}"


class TestDefaultProviderIndex:
    """The Provider dropdown starts on Ollama locally (local-first), but never
    on the hosted app: Render has no Ollama, so Run would start blocked."""

    def test_local_starts_on_ollama_even_with_port_and_env_default(self, monkeypatch):
        monkeypatch.setenv("STREAMLIT_SERVER_PORT", "8501")
        monkeypatch.setenv("DEFAULT_PROVIDER", "deepseek")
        assert app.PROVIDERS[app._default_provider_index()] == "ollama"

    def test_render_never_starts_on_a_local_provider(self, monkeypatch):
        monkeypatch.setenv("RENDER", "true")
        monkeypatch.delenv("DEFAULT_PROVIDER", raising=False)
        assert app.PROVIDERS[app._default_provider_index()] not in app._LOCAL_PROVIDERS

    def test_render_uses_cloud_default_provider(self, monkeypatch):
        monkeypatch.setenv("RENDER", "true")
        monkeypatch.setenv("DEFAULT_PROVIDER", "qwen")
        assert app.PROVIDERS[app._default_provider_index()] == "qwen"

    @pytest.mark.parametrize("value", ["ollama", "no-such-provider", ""])
    def test_render_ignores_local_or_unknown_default(self, monkeypatch, value):
        monkeypatch.setenv("RENDER", "true")
        monkeypatch.setenv("DEFAULT_PROVIDER", value)
        assert app.PROVIDERS[app._default_provider_index()] not in app._LOCAL_PROVIDERS


def test_render_page_does_not_start_on_ollama(monkeypatch):
    """Page-level check: on Render the Provider dropdown's starting value is a
    cloud provider, so a first visit does not land on a blocked Run button."""
    from streamlit.testing.v1 import AppTest
    import ollama_models

    monkeypatch.setenv("RENDER", "true")
    monkeypatch.delenv("DEFAULT_PROVIDER", raising=False)
    monkeypatch.setattr(ollama_models, "list_ollama_models", lambda *a, **k: [])

    mode = next(iter(app.MODES))
    at = AppTest.from_file(str(Path(app.__file__)), default_timeout=30)
    at.session_state["page"] = mode
    at.run()
    assert not at.exception, f"{mode}: {at.exception[0].message}"
    assert at.selectbox(key=f"provider_{mode}").value not in app._LOCAL_PROVIDERS
