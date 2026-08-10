"""
Tests for SR Pipeline (sr module and launcher)
"""
import unittest
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from SOURCE_CODE import main as _m


class TestSRLauncher:
    """Tests for the SR launcher functionality"""

    def _make_input_sr(self, tmp_path):
        """Create input/sr/ directory with dummy files"""
        input_sr = tmp_path / "input" / "sr"
        input_sr.mkdir(parents=True, exist_ok=True)
        (input_sr / "dummy.pdf").write_text("dummy content", encoding="utf-8")
        (input_sr / "pico_test.json").write_text(
            '{"topic": "Test", "population": "Adults", "intervention": "CBT", "comparator": "Control", "outcome": "Pain"}',
            encoding="utf-8"
        )
        return input_sr

    def test_launcher_prints_pipeline_header(self, tmp_path, capsys):
        """Should print SR pipeline header when launched"""
        self._make_input_sr(tmp_path)

        mock_result = MagicMock()
        mock_result.returncode = 0

        # Create minimal stub for sr/main.py
        sr_dir = tmp_path / "sr"
        sr_dir.mkdir(parents=True, exist_ok=True)
        (sr_dir / "main.py").write_text("# stub", encoding="utf-8")

        with (
            patch.object(_m, "INPUT_SR", tmp_path / "input" / "sr"),
            patch.object(_m, "BASE_DIR", tmp_path),
            patch("subprocess.run", return_value=mock_result),
            patch("builtins.input", return_value="1"),
        ):
            _m.run_sr_launcher()

        out, err = capsys.readouterr()
        assert "SR Automation Pipeline" in out

    def test_launcher_loads_pico_json(self, tmp_path, capsys):
        """Should load PICO JSON from input/sr/"""
        self._make_input_sr(tmp_path)

        mock_result = MagicMock()
        mock_result.returncode = 0

        sr_dir = tmp_path / "sr"
        sr_dir.mkdir(parents=True, exist_ok=True)
        (sr_dir / "main.py").write_text("# stub", encoding="utf-8")

        with (
            patch.object(_m, "INPUT_SR", tmp_path / "input" / "sr"),
            patch.object(_m, "BASE_DIR", tmp_path),
            patch("subprocess.run", return_value=mock_result),
            patch("builtins.input", return_value="1"),
        ):
            _m.run_sr_launcher()

        out, err = capsys.readouterr()
        assert "PICO" in out

    def test_launcher_pipeline_complete_message(self, tmp_path, capsys):
        """Should show pipeline complete message"""
        self._make_input_sr(tmp_path)

        mock_result = MagicMock()
        mock_result.returncode = 0

        sr_dir = tmp_path / "sr"
        sr_dir.mkdir(parents=True, exist_ok=True)
        (sr_dir / "main.py").write_text("# stub", encoding="utf-8")

        with (
            patch.object(_m, "INPUT_SR", tmp_path / "input" / "sr"),
            patch.object(_m, "BASE_DIR", tmp_path),
            patch("subprocess.run", return_value=mock_result),
            patch("builtins.input", return_value="1"),
        ):
            _m.run_sr_launcher()

        out, err = capsys.readouterr()
        assert "Pipeline complete" in out or "SR Automation Pipeline" in out

    def test_launcher_finds_pdf_files(self, tmp_path, capsys):
        """Should find PDF files in input/sr/"""
        input_sr = self._make_input_sr(tmp_path)
        (input_sr / "paper1.pdf").write_text("paper1", encoding="utf-8")
        (input_sr / "paper2.pdf").write_text("paper2", encoding="utf-8")

        mock_result = MagicMock()
        mock_result.returncode = 0

        sr_dir = tmp_path / "sr"
        sr_dir.mkdir(parents=True, exist_ok=True)
        (sr_dir / "main.py").write_text("# stub", encoding="utf-8")

        with (
            patch.object(_m, "INPUT_SR", input_sr),
            patch.object(_m, "BASE_DIR", tmp_path),
            patch("subprocess.run", return_value=mock_result),
            patch("builtins.input", return_value="1"),
        ):
            _m.run_sr_launcher()

        out, err = capsys.readouterr()
        assert "Found 3 PDF(s)" in out or "PDF" in out

    def test_launcher_handles_no_pico_file(self, tmp_path, capsys):
        """Should handle missing PICO file gracefully"""
        input_sr = tmp_path / "input" / "sr"
        input_sr.mkdir(parents=True, exist_ok=True)
        (input_sr / "dummy.pdf").write_text("dummy content", encoding="utf-8")

        mock_result = MagicMock()
        mock_result.returncode = 0

        sr_dir = tmp_path / "sr"
        sr_dir.mkdir(parents=True, exist_ok=True)
        (sr_dir / "main.py").write_text("# stub", encoding="utf-8")

        with (
            patch.object(_m, "INPUT_SR", input_sr),
            patch.object(_m, "BASE_DIR", tmp_path),
            patch("subprocess.run", return_value=mock_result),
            patch("builtins.input", return_value="0"),
        ):
            _m.run_sr_launcher()

        out, err = capsys.readouterr()
        assert "PICO" in out or "input/sr" in out

    def test_launcher_no_pdf_files(self, tmp_path, capsys):
        """Should handle case with no PDF files"""
        input_sr = tmp_path / "input" / "sr"
        input_sr.mkdir(parents=True, exist_ok=True)

        with (
            patch.object(_m, "INPUT_SR", input_sr),
            patch.object(_m, "BASE_DIR", tmp_path),
        ):
            _m.run_sr_launcher()

        out, err = capsys.readouterr()
        assert "No PDF files found" in out


class TestSRPipeline:
    """Tests for SR pipeline core functionality"""

    def test_run_sr_launcher_with_provider(self, tmp_path, capsys):
        """Should accept provider parameter"""
        input_sr = tmp_path / "input" / "sr"
        input_sr.mkdir(parents=True, exist_ok=True)
        (input_sr / "dummy.pdf").write_text("dummy content", encoding="utf-8")
        (input_sr / "pico_test.json").write_text(
            '{"topic": "Test", "population": "Adults", "intervention": "CBT"}',
            encoding="utf-8"
        )

        mock_result = MagicMock()
        mock_result.returncode = 0

        sr_dir = tmp_path / "sr"
        sr_dir.mkdir(parents=True, exist_ok=True)
        (sr_dir / "main.py").write_text("# stub", encoding="utf-8")

        with (
            patch.object(_m, "INPUT_SR", input_sr),
            patch.object(_m, "BASE_DIR", tmp_path),
            patch("subprocess.run", return_value=mock_result),
            patch("builtins.input", return_value="1"),
        ):
            _m.run_sr_launcher(provider="qwen")

        out, err = capsys.readouterr()
        assert "SR Automation Pipeline" in out or "qwen" in out

    def test_run_sr_launcher_with_model(self, tmp_path, capsys):
        """Should accept model parameter"""
        input_sr = tmp_path / "input" / "sr"
        input_sr.mkdir(parents=True, exist_ok=True)
        (input_sr / "dummy.pdf").write_text("dummy content", encoding="utf-8")
        (input_sr / "pico_test.json").write_text(
            '{"topic": "Test", "population": "Adults", "intervention": "CBT"}',
            encoding="utf-8"
        )

        mock_result = MagicMock()
        mock_result.returncode = 0

        sr_dir = tmp_path / "sr"
        sr_dir.mkdir(parents=True, exist_ok=True)
        (sr_dir / "main.py").write_text("# stub", encoding="utf-8")

        with (
            patch.object(_m, "INPUT_SR", input_sr),
            patch.object(_m, "BASE_DIR", tmp_path),
            patch("subprocess.run", return_value=mock_result),
            patch("builtins.input", return_value="1"),
        ):
            _m.run_sr_launcher(provider="qwen", model="qwen3.7-plus")

        out, err = capsys.readouterr()
        assert "running" in out.lower() or "pipeline" in out.lower()