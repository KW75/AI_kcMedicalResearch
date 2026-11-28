"""Session 53 B1: --mode data_analysis (launcher menu 7), file list only.

Pinned:
- --mode data_analysis is accepted and dispatched to pipelines.data_analysis.cli.
- No AI model is called: data_destinations lists nothing and the cloud gate
  never asks, whatever provider .env or --provider names.
- The step lists .csv and .xlsx files in input/data_analysis/ (case-insensitive
  suffix; Excel ~$ lock files ignored), names the files it skips, and creates
  the folder if it is missing.
- docs/project/architecture.md: SaMD built and frozen; a Data Analysis section.
  docs/project/PRD.md: the ninth mode is no longer 'planned'.
"""
import io
from contextlib import redirect_stdout
from pathlib import Path

import pytest

import main

# From main.py, not __file__, so a copy of this file run elsewhere (the
# fail-first check) still finds the repo.
ROOT = Path(main.__file__).resolve().parents[1]
ARCH = ROOT / "docs" / "project" / "architecture.md"
PRD = ROOT / "docs" / "project" / "PRD.md"


def _cli():
    from pipelines.data_analysis import cli
    return cli


def _run(tmp_path, names=()):
    d = tmp_path / "input" / "data_analysis"
    d.mkdir(parents=True)
    for n in names:
        (d / n).write_text("x", encoding="utf-8")
    lines = []
    # B2: run() asks when there are several files; 0 = stop.
    found = _cli().run(tmp_path, say=lines.append, input_fn=lambda prompt: "0")
    return found, "\n".join(lines)


# --- main.py ----------------------------------------------------------------

def test_mode_data_analysis_is_accepted():
    assert main.parse_args(["--mode", "data_analysis"]).mode == "data_analysis"


@pytest.mark.parametrize("prov", ["ollama", "deepseek", "qwen", "openai", "anthropic", "groq"])
def test_no_data_destinations(prov):
    assert main.data_destinations("data_analysis", prov) == []


def test_cloud_gate_never_asks():
    def no_input(*a, **k):
        raise AssertionError("the cloud gate asked a question")
    buf = io.StringIO()
    with redirect_stdout(buf):
        ok = main.confirm_data_destinations(
            "data_analysis", "deepseek", stdin_is_tty=True, input_fn=no_input)
    assert ok is True
    assert "[CLOUD]" not in buf.getvalue()


def test_run_cli_dispatches_without_cloud_gate(monkeypatch, capsys):
    cli = _cli()
    calls = []
    monkeypatch.setattr(cli, "run", lambda base_dir, **kw: calls.append(base_dir))
    main.run_cli(main.parse_args(["--mode", "data_analysis", "--provider", "deepseek"]))
    assert len(calls) == 1
    assert Path(calls[0]) == Path(main.BASE_DIR)
    assert "[CLOUD]" not in capsys.readouterr().out


# --- pipelines/data_analysis/cli.py -------------------------------------------

def test_lists_csv_and_xlsx_only(tmp_path):
    found, out = _run(tmp_path, ["b.xlsx", "a.csv", "C.CSV", "notes.txt",
                                 "old.xls", "~$b.xlsx"])
    assert found == ["a.csv", "b.xlsx", "C.CSV"]
    assert "notes.txt" in out
    assert "old.xls" in out and "save it as .xlsx" in out


def test_says_no_ai_is_used(tmp_path):
    _, out = _run(tmp_path, ["a.csv"])
    assert "no ai" in out.lower()


def test_empty_folder_says_where_to_put_files(tmp_path):
    found, out = _run(tmp_path)
    assert found == []
    assert str(tmp_path / "input" / "data_analysis") in out


def test_creates_missing_input_folder(tmp_path):
    lines = []
    assert _cli().run(tmp_path, say=lines.append) == []
    assert (tmp_path / "input" / "data_analysis").is_dir()


# --- docs -------------------------------------------------------------------

def test_architecture_samd_built_and_frozen():
    text = ARCH.read_text(encoding="utf-8")
    assert "## SaMD Mode (planned" not in text
    assert "(samd planned)" not in text
    assert "frozen" in text.lower()


def test_architecture_has_data_analysis_section():
    text = ARCH.read_text(encoding="utf-8")
    assert "## Data Analysis Mode" in text
    assert "coming soon" not in text.lower()
    assert "--mode data_analysis" in text


def test_prd_no_longer_says_data_analysis_planned():
    text = " ".join(PRD.read_text(encoding="utf-8").split())
    assert "with a ninth (Data Analysis) planned" not in text
    assert "Data Analysis" in text
