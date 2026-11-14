"""Session 41: 4d (the SR pipeline writes no log) and 4c ([SAMPLING] shows
the wrong temperature on Ollama).

4d: run 20261114_184026 left no log; a Start-Transcript workaround was never
created. main() now attaches a FileHandler writing <run folder>/run.log as
soon as the run folder is known, and detaches it at the end. A second attach
replaces the first, so a run that returns early never makes a later run
write into an old folder.

4c: the [SAMPLING] line logged self.temperature (SR_EXTRACT_TEMPERATURE,
0.0) while Ollama calls use OLLAMA_TEMPERATURE (0.3) via
providers.call_ollama_provider. On Ollama it must show the value sent.
"""
import importlib
import logging
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MAIN_SRC = ROOT / "SOURCE_CODE" / "pipelines" / "sr" / "main.py"


@pytest.fixture
def sr_main():
    # Other test files stub rob2_tool (no RoB2Assessor); main needs the real one.
    name = "pipelines.sr.src.screening.rob2_tool"
    if name in sys.modules and not hasattr(sys.modules[name], "RoB2Assessor"):
        del sys.modules[name]
    return importlib.import_module("pipelines.sr.main")


def _read(folder):
    return (folder / "run.log").read_text(encoding="utf-8")


def test_attach_creates_run_log_and_records_lines(sr_main, tmp_path):
    folder = tmp_path / "20990101_000000"          # does not exist yet
    h = sr_main.attach_run_log(folder)
    try:
        logging.getLogger("sr.main").warning("[AGREEMENT] test line")
        logging.getLogger("pipelines.sr.src.extraction.data_extractor").warning(
            "[METADATA] test line")
    finally:
        sr_main.detach_run_log(h)
    text = _read(folder)
    assert "[WARNING] sr.main -- [AGREEMENT] test line" in text
    assert "[METADATA] test line" in text


def test_detach_stops_writing_and_removes_handler(sr_main, tmp_path):
    h = sr_main.attach_run_log(tmp_path)
    sr_main.detach_run_log(h)
    logging.getLogger("sr.main").warning("after detach")
    assert "after detach" not in _read(tmp_path)
    assert h not in logging.getLogger().handlers


def test_second_attach_replaces_the_first(sr_main, tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    h1 = sr_main.attach_run_log(a)
    h2 = sr_main.attach_run_log(b)
    try:
        logging.getLogger("sr.main").warning("only in b")
    finally:
        sr_main.detach_run_log(h2)
    assert h1 not in logging.getLogger().handlers
    assert "only in b" in _read(b)
    assert "only in b" not in _read(a)


def test_main_attaches_after_layout_and_detaches_at_end():
    src = MAIN_SRC.read_text(encoding="utf-8")
    i = src.index("layout = SRProjectLayout(run_id=args.run_id)")
    j = src.index("_run_log = attach_run_log(layout.project)")
    assert i < j < src.index("layout.initialise(pdf_sources)")
    assert src.index("detach_run_log(_run_log)") > src.index('logger.info("Pipeline complete.")')


def _sampling_line(caplog, **kw):
    de = importlib.import_module("pipelines.sr.src.extraction.data_extractor")
    with caplog.at_level(logging.INFO):
        de.DataExtractor(pico_criteria={"outcome": "pain"}, **kw)
    return next(m for m in caplog.messages if "[SAMPLING]" in m)


def test_sampling_line_shows_ollama_temperature(monkeypatch, caplog):
    monkeypatch.setenv("OLLAMA_TEMPERATURE", "0.3")
    monkeypatch.delenv("SR_EXTRACT_TEMPERATURE", raising=False)
    line = _sampling_line(caplog, provider="ollama", model="gemma4:e4b")
    assert "temperature=0.3" in line, line


def test_sampling_line_on_qwen_unchanged(monkeypatch, caplog):
    monkeypatch.setenv("OLLAMA_TEMPERATURE", "0.3")
    monkeypatch.setenv("SR_EXTRACT_TEMPERATURE", "0.0")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "k")
    line = _sampling_line(caplog, provider="qwen", model="qwen3-vl-plus", api_key="k")
    assert "temperature=0.0" in line, line