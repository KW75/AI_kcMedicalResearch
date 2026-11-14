"""Item 2a: the launcher never writes the tracked sample prisma_criteria.yaml;
the run's YAML is internal (input/sr, git-ignored, passed with --config), the
PICO JSON is saved in the run folder, and empty P/I/O are refused."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "SOURCE_CODE"))

import main  # noqa: E402
from pipelines.sr.src.utils import criteria_file as cf  # noqa: E402

LAUNCHER_SRC = (ROOT / "SOURCE_CODE" / "main.py").read_text(encoding="utf-8")


def _answers(monkeypatch, *values):
    it = iter(values)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(it))


# empty P/I/O are asked again

def test_create_reasks_empty_population(monkeypatch):
    _answers(monkeypatch, "", "P", "I", "", "O", "", "")
    assert main._create_pico()["population"] == "P"


def test_create_reasks_empty_outcome(monkeypatch):
    _answers(monkeypatch, "P", "I", "", "", "O", "", "")
    assert main._create_pico()["outcome"] == "O"


def test_modify_reasks_when_saved_field_empty(monkeypatch):
    old = {"population": "", "intervention": "I", "comparator": "C", "outcome": "O"}
    _answers(monkeypatch, "", "P2", "", "", "", "", "")
    assert main._modify_pico(dict(old))["population"] == "P2"


# direct run with empty fields is stopped

def test_placeholder_fields_flags_empty_pio():
    cfg = {"pico": {"population": "", "intervention": "I",
                    "comparator": "", "outcome": "  "}}
    assert cf.placeholder_fields(cfg) == ["pico.population", "pico.outcome"]


def test_placeholder_fields_full_pico_ok():
    cfg = {"review_title": "T", "effect_measure": "SMD",
           "pico": {"population": "P", "intervention": "I",
                    "comparator": "C", "outcome": "O"}}
    assert cf.placeholder_fields(cfg) == []


# YAML is internal; the tracked sample is never written

def test_launcher_never_writes_tracked_sample():
    assert main.SR_RUN_CONFIG == main.INPUT_SR / "prisma_criteria.yaml"
    assert '"pipelines" / "sr" / "config" / "prisma_criteria.yaml"' not in LAUNCHER_SRC


def test_build_cmd_passes_config_and_run_id():
    cmd = main._build_sr_cmd("qwen", "qwen3-vl-plus", "SMD",
                             Path("x.yaml"), "20261112_120000")
    assert cmd[cmd.index("--config") + 1] == "x.yaml"
    assert cmd[cmd.index("--run-id") + 1] == "20261112_120000"
    assert cmd[cmd.index("--effect-measure") + 1] == "SMD"


def test_build_cmd_without_config_uses_sample():
    cmd = main._build_sr_cmd("qwen", "qwen3-vl-plus", "SMD", None, "20261112_120000")
    assert "--config" not in cmd   # sample's <...> placeholders then stop the run


# the PICO JSON goes into the run folder

def test_save_pico_to_run_copies_json(tmp_path):
    pico = tmp_path / "pico_20261112_120000.json"
    pico.write_text('{"population": "P"}', encoding="utf-8")
    runs = tmp_path / "runs"
    (runs / "R1").mkdir(parents=True)
    dest = main._save_pico_to_run(pico, runs, "R1")
    assert dest == runs / "R1" / pico.name
    assert dest.read_text(encoding="utf-8") == '{"population": "P"}'


def test_save_pico_to_run_missing_folder(tmp_path):
    pico = tmp_path / "pico_x.json"
    pico.write_text("{}", encoding="utf-8")
    assert main._save_pico_to_run(pico, tmp_path / "runs", "R1") is None
    assert not (tmp_path / "runs").exists()


# prefilled step replaces the y/N question

def test_launcher_no_modify_question():
    assert "Modify this PICO? [y/N]" not in LAUNCHER_SRC
