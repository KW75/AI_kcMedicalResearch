"""v2.5: UI passes the chosen time limit to main.py, same rule as the
launcher: 15 (default) adds nothing, other choices add --time-limit."""
import pytest


def _cmd(**kw):
    import ui.app as app_mod
    return app_mod._build_cli_cmd("writing", "ollama", "gemma4:e4b", **kw)


def test_default_adds_no_flag():
    assert "--time-limit" not in _cmd()


def test_15_adds_no_flag():
    assert "--time-limit" not in _cmd(time_limit="15")


@pytest.mark.parametrize("key", ["30", "60", "none"])
def test_other_choices_add_the_flag(key):
    cmd = _cmd(time_limit=key)
    i = cmd.index("--time-limit")
    assert cmd[i + 1] == key

class _Stop(BaseException):
    """Stops the launch right after the command is built (BaseException, so
    an 'except Exception' in app.py cannot swallow it). Nothing is launched."""


@pytest.mark.parametrize("cloud", [False, True])
def test_launch_terminal_passes_time_limit_on_both_paths(cloud, monkeypatch):
    import ui.app as app_mod
    seen = {}

    def fake_build(*a, **k):
        seen.update(k)
        raise _Stop

    monkeypatch.setattr(app_mod, "_build_cli_cmd", fake_build)
    monkeypatch.setattr(app_mod, "_is_cloud_environment", lambda: cloud)
    with pytest.raises(_Stop):
        app_mod._launch_terminal("writing", "ollama", "gemma4:e4b", time_limit="60")
    assert seen.get("time_limit") == "60"


def test_page_has_time_limit_dropdown_defaulting_to_15():
    from pathlib import Path
    from streamlit.testing.v1 import AppTest
    import ui.app as app_mod

    at = AppTest.from_file(str(Path(app_mod.__file__)), default_timeout=30)
    at.session_state["page"] = "writing"
    at.run()
    assert not at.exception
    box = at.selectbox(key="time_limit_writing")
    assert box.value == "15"
    assert len(box.options) == 4
