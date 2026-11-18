"""Session 48: generate_writing_report saves to OUTPUT_WRITING (output/writing/),
as the docs say; the unused reports_dir argument is removed so no caller can
think it chooses the folder."""

import inspect
import sys
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "SOURCE_CODE"))
sys.path.insert(0, str(PROJECT_ROOT))

from SOURCE_CODE.main import generate_writing_report  # noqa: E402


def test_no_reports_dir_parameter():
    params = inspect.signature(generate_writing_report).parameters
    assert "reports_dir" not in params


def test_report_saved_in_output_writing(tmp_path):
    in_dir = tmp_path / "input"
    in_dir.mkdir()
    (in_dir / "note.txt").write_text("Short test document.", encoding="utf-8")
    out_dir = tmp_path / "output"
    with patch("SOURCE_CODE.main.call_ai", return_value="[MOCK] report"), \
         patch("SOURCE_CODE.main.OUTPUT_WRITING", out_dir):
        md_path = generate_writing_report(docs_dir=tmp_path / "docs",
                                          provider="ollama", input_dir=in_dir)
    assert md_path.parent == out_dir and md_path.exists()
    assert md_path.with_suffix(".docx").exists()
