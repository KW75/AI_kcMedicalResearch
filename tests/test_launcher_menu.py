"""Launcher main menu (Session 33).

7 Data Analysis runs --mode data_analysis with no AI questions (Session 53),
8 OCR, 9 SaMD (was Dry Run), 10 Setup.
Custom flags moved from 9 to C; H still opens Help. Setup -> Open Help
opens Readme/flashcard-help.html, found relative to the launcher.
The Streamlit UI (--ui) is no longer offered.

The launcher is loaded by path with a dummy colorama, as in
test_launcher_model_picker.py.
"""
import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def launcher():
    spec = importlib.util.spec_from_file_location(
        "launcher_menu_under_test", ROOT / "scripts" / "launcher.py"
    )
    mod = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {"colorama": MagicMock()}):
        spec.loader.exec_module(mod)
    return mod


def _quiet(launcher):
    """No screen clearing or banner during tests."""
    return patch.multiple(launcher, clear=MagicMock(), banner=MagicMock())


def _run_main(launcher, inputs):
    """Run the main loop with typed inputs. Nothing real is launched."""
    with _quiet(launcher), \
         patch.object(launcher, "safe_input", side_effect=inputs), \
         patch.object(launcher, "_run_cmd") as run_cmd, \
         patch.object(launcher, "pick_provider", return_value="") as pick_provider, \
         patch.object(launcher, "run_ui", create=True), \
         patch("subprocess.Popen"), \
         patch("webbrowser.open") as wb_open:
        launcher.main()
    return run_cmd, pick_provider, wb_open


# --- menu table -------------------------------------------------------------

def test_menu_numbers_labels_and_flags(launcher):
    table = {k: (label, flag) for k, label, flag in launcher.MODES}
    assert [k for k, _, _ in launcher.MODES] == [str(n) for n in range(1, 11)]
    assert table["7"] == ("Data Analysis", "--mode data_analysis")
    assert table["8"] == ("OCR", "--mode ocr")
    assert table["9"] == ("SaMD", "--mode samd")
    assert table["10"] == ("Setup", "setup")


def test_streamlit_ui_is_not_offered(launcher):
    assert all(flag != "--ui" for _, _, flag in launcher.MODES)
    assert not hasattr(launcher, "run_ui")


# --- pick_mode --------------------------------------------------------------

@pytest.mark.parametrize("typed, expected", [
    ("1", ("Coding", "--mode coding", False, False)),
    ("9", ("SaMD", "--mode samd", False, False)),
    ("10", ("Setup", "setup", False, False)),
    ("c", (None, None, True, False)),
    ("h", (None, None, False, True)),
    ("x", (None, None, False, False)),
])
def test_pick_mode_keys(launcher, typed, expected):
    # If the key is invalid, "" answers "Press Enter to try again" and X exits,
    # so a wrong key gives an AssertionError instead of hanging.
    with _quiet(launcher), \
         patch.object(launcher, "safe_input", side_effect=[typed, "", "X"]):
        assert launcher.pick_mode() == expected


def test_prompt_lists_the_new_keys(launcher):
    with _quiet(launcher), \
         patch.object(launcher, "safe_input", side_effect=["x"]) as fake:
        launcher.pick_mode()
    prompt = fake.call_args_list[0].args[0]
    assert "1-10" in prompt
    assert "/ C /" in prompt


# --- main loop --------------------------------------------------------------

def test_data_analysis_runs_main_without_ai_questions(launcher):
    # Session 53: menu 7 runs main.py --mode data_analysis. No AI model is
    # used, so no provider, model or time-limit question is asked.
    with patch.object(launcher, "time_limit_flag") as tlf:
        run_cmd, pick_provider, _ = _run_main(launcher, ["7", "", "X"])
    run_cmd.assert_called_once()
    cmd = run_cmd.call_args.args[0]
    assert cmd[-2:] == ["--mode", "data_analysis"]
    assert str(cmd[1]).endswith("main.py")
    pick_provider.assert_not_called()
    tlf.assert_not_called()


def test_setup_open_help_opens_the_help_page(launcher):
    run_cmd, _, wb_open = _run_main(launcher, ["10", "3", "0", "X"])
    wb_open.assert_called_once()
    assert str(wb_open.call_args.args[0]).endswith("flashcard-help.html")
    run_cmd.assert_not_called()


def test_h_still_opens_help(launcher):
    # Guard: passes before and after (H is kept as a shortcut).
    _, _, wb_open = _run_main(launcher, ["H", "X", "X"])
    wb_open.assert_called_once()


# --- help file --------------------------------------------------------------

def test_help_file_is_found_relative_to_the_launcher(launcher):
    assert launcher.BASE.resolve() == ROOT
    assert launcher.HELP_FILE == launcher.BASE / "Readme" / "flashcard-help.html"
    assert launcher.HELP_FILE.is_file()


def test_open_help_missing_file_says_so(launcher, capsys, tmp_path):
    missing = tmp_path / "missing.html"
    with patch.object(launcher, "HELP_FILE", missing), \
         patch.object(launcher, "safe_input", return_value=""), \
         patch("webbrowser.open") as wb_open:
        assert launcher.open_help() is False
    wb_open.assert_not_called()
    out = capsys.readouterr().out
    assert "missing.html" in out
    assert "not found" in out.lower()

# --- banner -----------------------------------------------------------------

def _banner_text(launcher, capsys):
    import re
    with patch.object(launcher, "clear", MagicMock()):
        launcher.banner()
    out = capsys.readouterr().out
    return re.sub(r"\x1b\[[0-9;]*m", "", out)   # drop colour codes


def test_banner_does_not_mention_render(launcher, capsys):
    # Render service deleted in Session 33.
    assert "render" not in _banner_text(launcher, capsys).lower()


def test_banner_modes_line_does_not_list_ui(launcher, capsys):
    # The Streamlit UI is no longer offered from the launcher.
    assert "ui" not in _banner_text(launcher, capsys).split()

def test_banner_box_lines_are_all_the_same_width(launcher, capsys):
    # Every line of the box must end at the same column.
    lines = [l.strip() for l in _banner_text(launcher, capsys).splitlines()
             if l.strip()[:1] in ("║", "╔", "╠", "╚")]
    widths = {len(l) for l in lines}
    assert len(widths) == 1, sorted((len(l), l) for l in lines)

def test_samd_provider_refuses_groq_and_skips_model_list(launcher):
    # Session 49: SaMD reads images, so it uses the OCR lists; Groq is
    # refused, Enter picks Ollama, and no text-model list is shown.
    with _quiet(launcher), \
         patch.object(launcher, "safe_input", side_effect=["3", "", ""]), \
         patch.object(launcher, "pick_ollama_model") as pom:
        assert launcher.pick_provider("--mode samd") == "--provider ollama"
    pom.assert_not_called()
