"""Shared Ollama vision-model picker for SR and OCR (Session 42, decision A).

ollama_models.py holds the vision list, the default rule and the question,
so SR and OCR cannot drift apart. No Ollama needed: the model list and
capabilities are faked. No model names in code apart from
OLLAMA_DEFAULT_MODEL; colleagues pull and pick their own.
"""
import pytest

import ollama_models as om

PULLED = [  # list_ollama_models: every pulled model
    {"name": "nomic-embed-text:latest", "size_gb": 0.3, "params_b": 0.1},
    {"name": "qwen3:8b", "size_gb": 5.2, "params_b": 8.0},
    {"name": "gemma4:e4b", "size_gb": 6.6, "params_b": 7.5},
    {"name": "qwen2.5vl:7b", "size_gb": 6.0, "params_b": 7.0},
]
VISION = {"gemma4:e4b", "qwen2.5vl:7b"}


def fake_list(host=None):
    return PULLED


def fake_caps(host, name):
    return {"completion", "vision"} if name in VISION else {"completion"}


def _answers(*items, asked=None):
    it = iter(items)

    def _input(prompt=""):
        if asked is not None:
            asked.append(prompt)
        return next(it)
    return _input


def _vision():
    return om.vision_models(fake_list, fake_caps)


def _quiet(*a):
    return None


@pytest.fixture(autouse=True)
def no_env_model(monkeypatch):
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)


# --- which models are listed ------------------------------------------------

def test_vision_models_keeps_only_vision_capable():
    assert [m["name"] for m in _vision()] == ["gemma4:e4b", "qwen2.5vl:7b"]


# --- default rule -------------------------------------------------------------

def test_default_is_built_in_default_when_env_unset():
    names = ["qwen2.5vl:7b", om.OLLAMA_DEFAULT_MODEL]
    assert om.default_vision_model(names) == om.OLLAMA_DEFAULT_MODEL


def test_default_follows_OLLAMA_MODEL_when_it_can_read_images(monkeypatch):
    monkeypatch.setenv("OLLAMA_MODEL", "qwen2.5vl:7b")
    assert om.default_vision_model(["gemma4:e4b", "qwen2.5vl:7b"]) == "qwen2.5vl:7b"


def test_text_only_OLLAMA_MODEL_is_ignored(monkeypatch):
    monkeypatch.setenv("OLLAMA_MODEL", "qwen3:8b")
    assert om.default_vision_model(["gemma4:e4b", "qwen2.5vl:7b"]) == "gemma4:e4b"


def test_OLLAMA_MODEL_without_tag_matches_latest(monkeypatch):
    monkeypatch.setenv("OLLAMA_MODEL", "llava")
    assert om.default_vision_model(["gemma4:e4b", "llava:latest"]) == "llava:latest"


def test_default_is_first_when_built_in_default_not_pulled():
    assert om.default_vision_model(["llava:13b", "qwen2.5vl:7b"]) == "llava:13b"


# --- the question -------------------------------------------------------------

def test_picker_lists_size_and_params_and_marks_default():
    log = []
    om.pick_vision_model(_vision(), input_fn=_answers(""), log=log.append)
    gemma = [line for line in log if "gemma4:e4b" in line]
    qwen = [line for line in log if "qwen2.5vl:7b" in line]
    assert gemma and "1  gemma4:e4b  7.5B  6.6 GB" in gemma[0]
    assert gemma[0].rstrip().endswith("(default)")
    assert qwen and "2  qwen2.5vl:7b  7B  6.0 GB" in qwen[0]
    assert "(default)" not in qwen[0]


def test_picker_prompt_says_enter_is_default():
    asked = []
    om.pick_vision_model(_vision(), input_fn=_answers("", asked=asked), log=_quiet)
    assert "Enter = default" in asked[0]


def test_picker_enter_returns_default():
    assert om.pick_vision_model(_vision(), input_fn=_answers(""), log=_quiet) == "gemma4:e4b"


def test_picker_number_picks_that_model():
    assert om.pick_vision_model(_vision(), input_fn=_answers("2"), log=_quiet) == "qwen2.5vl:7b"


@pytest.mark.parametrize("answer", ["0", "3", "x"])
def test_picker_bad_answer_returns_none_and_says_so(answer):
    log = []
    assert om.pick_vision_model(_vision(), input_fn=_answers(answer), log=log.append) is None
    assert "not a valid" in " ".join(log).lower()


def test_picker_without_keyboard_takes_default():
    def no_keyboard(prompt=""):
        raise EOFError
    assert om.pick_vision_model(_vision(), input_fn=no_keyboard, log=_quiet) == "gemma4:e4b"


def test_picker_ctrl_c_cancels():
    def ctrl_c(prompt=""):
        raise KeyboardInterrupt
    assert om.pick_vision_model(_vision(), input_fn=ctrl_c, log=_quiet) is None


# --- nothing pulled -----------------------------------------------------------

def test_no_vision_hint_points_to_setup_and_vision_search():
    assert "10 Setup -> 2 Local AI" in om.NO_VISION_HINT
    assert "https://ollama.com/search?c=vision" in om.NO_VISION_HINT


# --- SR uses the same picker (main.sr_choose_ollama_model) -------------------

import inspect  # noqa: E402

import main  # noqa: E402


def _never_asked(prompt=""):
    raise AssertionError("should not ask")


def test_sr_typed_model_is_kept_without_asking():
    assert main.sr_choose_ollama_model(
        "llava:13b", list_fn=fake_list, caps_fn=fake_caps,
        input_fn=_never_asked, log=_quiet) == "llava:13b"


def test_sr_enter_takes_default_vision_model():
    assert main.sr_choose_ollama_model(
        "", list_fn=fake_list, caps_fn=fake_caps,
        input_fn=_answers(""), log=_quiet) == "gemma4:e4b"


def test_sr_number_picks_that_model():
    assert main.sr_choose_ollama_model(
        "", list_fn=fake_list, caps_fn=fake_caps,
        input_fn=_answers("2"), log=_quiet) == "qwen2.5vl:7b"


def test_sr_bad_answer_means_sr_not_run():
    assert main.sr_choose_ollama_model(
        "", list_fn=fake_list, caps_fn=fake_caps,
        input_fn=_answers("9"), log=_quiet) is None


def test_sr_no_vision_model_gives_setup_hint_and_empty_string():
    log = []
    result = main.sr_choose_ollama_model(
        "", list_fn=fake_list, caps_fn=lambda host, name: {"completion"},
        input_fn=_never_asked, log=log.append)
    assert result == ""
    assert any("10 Setup -> 2 Local AI" in line for line in log)


def test_sr_ollama_not_reachable_gives_empty_string():
    def down(host=None):
        raise OSError("connection refused")
    assert main.sr_choose_ollama_model(
        "", list_fn=down, caps_fn=fake_caps,
        input_fn=_never_asked, log=_quiet) == ""


def test_sr_launcher_asks_before_the_vision_check():
    src = inspect.getsource(main.run_sr_launcher)
    assert "sr_choose_ollama_model(" in src
    assert src.index("sr_choose_ollama_model(") < src.index("sr_ollama_vision_error(")
