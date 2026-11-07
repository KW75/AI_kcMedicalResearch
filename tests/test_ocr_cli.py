"""OCR step 5a: --mode ocr in main.py and the terminal prompts (pipelines/ocr/cli.py).

No Ollama needed: model listing, capabilities and the engine are faked.
Prompt order: function (1/2) -> file (function 1 only) -> name -> model.
"""
import pytest

import main
from pipelines.ocr import cli

PULLED = [
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


class FakeEngine:
    def __init__(self):
        self.calls = []

    def single(self, path, out_dir, name, model, log=print):
        self.calls.append(("single", path, out_dir, name, model))
        return {"header": "H", "records": [path.name], "failed": [], "summary": None}

    def set(self, folder, out_dir, name, model, log=print):
        self.calls.append(("set", folder, out_dir, name, model))
        return {"header": "H", "records": [], "failed": [], "summary": None}


def _answers(*items):
    it = iter(items)
    return lambda prompt="": next(it)


def _base(tmp_path, files=("a.pdf", "b.png")):
    inp = tmp_path / "input" / "ocr"
    inp.mkdir(parents=True)
    for f in files:
        (inp / f).write_bytes(b"x")
    return tmp_path


def _run(tmp_path, answers, model=None, files=("a.pdf", "b.png")):
    eng = FakeEngine()
    result = cli.run(_base(tmp_path, files), model=model, input_fn=_answers(*answers),
                     list_fn=fake_list, caps_fn=fake_caps,
                     run_single=eng.single, run_set=eng.set, log=lambda *a: None)
    return eng, result


def test_vision_models_keeps_only_vision_capable():
    names = [m["name"] for m in cli.vision_models(fake_list, fake_caps)]
    assert names == ["gemma4:e4b", "qwen2.5vl:7b"]


def test_function_1_runs_the_chosen_file(tmp_path, monkeypatch):
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    eng, _ = _run(tmp_path, ["1", "2", "PT0123", ""])
    kind, path, out_dir, name, model = eng.calls[0]
    assert kind == "single" and path.name == "b.png"
    assert out_dir == tmp_path / "output" / "ocr"
    assert (name, model) == ("PT0123", "gemma4:e4b")


def test_function_2_runs_the_whole_folder(tmp_path, monkeypatch):
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    eng, _ = _run(tmp_path, ["2", "Cardio lectures", "2"])
    kind, folder, _, name, model = eng.calls[0]
    assert kind == "set" and folder == tmp_path / "input" / "ocr"
    assert (name, model) == ("Cardio lectures", "qwen2.5vl:7b")


def test_default_model_follows_OLLAMA_MODEL_when_it_has_vision(tmp_path, monkeypatch):
    monkeypatch.setenv("OLLAMA_MODEL", "qwen2.5vl:7b")
    eng, _ = _run(tmp_path, ["2", "", ""])
    assert eng.calls[0][4] == "qwen2.5vl:7b"


def test_text_only_OLLAMA_MODEL_falls_back_to_gemma4(tmp_path, monkeypatch):
    monkeypatch.setenv("OLLAMA_MODEL", "qwen3:8b")
    eng, _ = _run(tmp_path, ["2", "", ""])
    assert eng.calls[0][4] == "gemma4:e4b"


def test_model_flag_skips_the_model_question(tmp_path):
    eng, _ = _run(tmp_path, ["2", ""], model="gemma4:e4b")
    assert eng.calls[0][4] == "gemma4:e4b"


def test_model_flag_without_vision_is_refused_before_any_question(tmp_path):
    eng, result = _run(tmp_path, [], model="qwen3:8b")
    assert result is None and eng.calls == []


def test_no_vision_model_pulled_says_what_to_pull(tmp_path):
    logs, eng = [], FakeEngine()
    result = cli.run(_base(tmp_path), input_fn=_answers(),
                     list_fn=lambda host=None: PULLED[:2], caps_fn=fake_caps,
                     run_single=eng.single, run_set=eng.set, log=logs.append)
    assert result is None and eng.calls == []
    assert any("ollama pull gemma4:e4b" in line for line in logs)


def test_empty_input_folder_asks_nothing(tmp_path):
    eng, result = _run(tmp_path, [], files=())
    assert result is None and eng.calls == []


@pytest.mark.parametrize("answers", [["x"], ["1", "9"], ["2", "", "7"]])
def test_invalid_choice_does_not_run(tmp_path, monkeypatch, answers):
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    eng, result = _run(tmp_path, answers)
    assert result is None and eng.calls == []


def test_parse_args_accepts_mode_ocr():
    assert main.parse_args(["--mode", "ocr"]).mode == "ocr"


def test_ocr_lists_only_the_chosen_provider():
    assert main.data_destinations("ocr", "openai") == ["openai"]


def test_ocr_provider_error_only_for_ocr_with_cloud():
    msg = main.ocr_provider_error("ocr", "openai")
    assert msg and "ollama" in msg.lower()
    assert main.ocr_provider_error("ocr", "ollama") is None
    assert main.ocr_provider_error("coding", "openai") is None


def test_run_cli_stops_cloud_ocr_with_the_message(capsys):
    with pytest.raises(SystemExit):
        main.run_cli(main.parse_args(["--mode", "ocr", "--provider", "openai"]))
    assert main.ocr_provider_error("ocr", "openai") in capsys.readouterr().out
