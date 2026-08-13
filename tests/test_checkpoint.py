"""
Tests for checkpoint.py module.
Tests save, load, resume, clear, and find operations.
"""

import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "SOURCE_CODE"))


@pytest.fixture
def tmp_checkpoint_dir(tmp_path):
    """Override checkpoint directory to use temp folder."""
    with patch("checkpoint._checkpoint_dir", return_value=tmp_path):
        yield tmp_path


class TestPipelineCheckpoint:
    """Test PipelineCheckpoint class."""

    def test_create_checkpoint(self, tmp_checkpoint_dir):
        from checkpoint import PipelineCheckpoint
        cp = PipelineCheckpoint(mode="coding", session_id="test_001")
        assert cp.mode == "coding"
        assert cp.session_id == "test_001"
        assert not cp.has_checkpoint()

    def test_save_and_load_step(self, tmp_checkpoint_dir):
        from checkpoint import PipelineCheckpoint
        cp = PipelineCheckpoint(mode="coding", session_id="test_002", provider="deepseek")

        cp.save_step("builder", iteration=1, output="def hello(): pass")
        assert cp.has_checkpoint()

        state = cp.load()
        assert state["mode"] == "coding"
        assert state["provider"] == "deepseek"
        assert len(state["steps"]) == 1
        assert state["steps"][0]["step_name"] == "builder"
        assert state["steps"][0]["output"] == "def hello(): pass"
        assert state["last_completed_step"] == "builder"
        assert state["last_completed_iteration"] == 1

    def test_multiple_steps(self, tmp_checkpoint_dir):
        from checkpoint import PipelineCheckpoint
        cp = PipelineCheckpoint(mode="coding", session_id="test_003")

        cp.save_step("builder", iteration=1, output="code v1")
        cp.save_step("reviewer", iteration=1, output="feedback v1")
        cp.save_step("builder", iteration=2, output="code v2")

        state = cp.load()
        assert len(state["steps"]) == 3
        assert state["last_completed_step"] == "builder"
        assert state["last_completed_iteration"] == 2

    def test_get_step_output(self, tmp_checkpoint_dir):
        from checkpoint import PipelineCheckpoint
        cp = PipelineCheckpoint(mode="writing", session_id="test_004")

        cp.save_step("writer", iteration=1, output="draft text")
        cp.save_step("editor", iteration=1, output="edited text")

        assert cp.get_step_output("writer") == "draft text"
        assert cp.get_step_output("editor") == "edited text"
        assert cp.get_step_output("nonexistent") is None

    def test_get_step_output_by_iteration(self, tmp_checkpoint_dir):
        from checkpoint import PipelineCheckpoint
        cp = PipelineCheckpoint(mode="coding", session_id="test_005")

        cp.save_step("builder", iteration=1, output="v1")
        cp.save_step("builder", iteration=2, output="v2")

        assert cp.get_step_output("builder", iteration=1) == "v1"
        assert cp.get_step_output("builder", iteration=2) == "v2"

    def test_get_completed_iterations(self, tmp_checkpoint_dir):
        from checkpoint import PipelineCheckpoint
        cp = PipelineCheckpoint(mode="coding", session_id="test_006")

        assert cp.get_completed_iterations() == 0
        cp.save_step("builder", iteration=1, output="x")
        assert cp.get_completed_iterations() == 1
        cp.save_step("reviewer", iteration=2, output="y")
        assert cp.get_completed_iterations() == 2

    def test_clear_removes_file(self, tmp_checkpoint_dir):
        from checkpoint import PipelineCheckpoint
        cp = PipelineCheckpoint(mode="coding", session_id="test_007")
        cp.save_step("builder", iteration=1, output="x")
        assert cp.has_checkpoint()

        cp.clear()
        assert not cp.has_checkpoint()

    def test_summary(self, tmp_checkpoint_dir):
        from checkpoint import PipelineCheckpoint
        cp = PipelineCheckpoint(mode="coding", session_id="test_008", provider="deepseek")
        cp.save_step("builder", iteration=1, output="code")
        cp.save_step("reviewer", iteration=1, output="feedback")

        summary = cp.summary()
        assert "coding" in summary
        assert "test_008" in summary
        assert "reviewer" in summary
        assert "deepseek" in summary

    def test_get_last_step(self, tmp_checkpoint_dir):
        from checkpoint import PipelineCheckpoint
        cp = PipelineCheckpoint(mode="coding", session_id="test_009")

        assert cp.get_last_step() is None
        cp.save_step("builder", iteration=1, output="code")
        last = cp.get_last_step()
        assert last["step_name"] == "builder"

    def test_metadata_saved(self, tmp_checkpoint_dir):
        from checkpoint import PipelineCheckpoint
        cp = PipelineCheckpoint(mode="sr", session_id="test_010")
        cp.save_step("extraction", iteration=1, output="data",
                     metadata={"pages": [12, 13], "table": "Table 4"})

        state = cp.load()
        assert state["steps"][0]["metadata"]["pages"] == [12, 13]


class TestFindResumable:
    """Test find_resumable_checkpoint."""

    def test_no_checkpoints_returns_none(self, tmp_checkpoint_dir):
        from checkpoint import find_resumable_checkpoint
        assert find_resumable_checkpoint("coding") is None

    def test_finds_existing_checkpoint(self, tmp_checkpoint_dir):
        from checkpoint import PipelineCheckpoint, find_resumable_checkpoint
        cp = PipelineCheckpoint(mode="coding", session_id="resume_001")
        cp.save_step("builder", iteration=1, output="code")

        found = find_resumable_checkpoint("coding")
        assert found is not None
        assert found.session_id == "resume_001"

    def test_finds_most_recent(self, tmp_checkpoint_dir):
        from checkpoint import PipelineCheckpoint, find_resumable_checkpoint
        import time

        cp1 = PipelineCheckpoint(mode="writing", session_id="old_001")
        cp1.save_step("writer", iteration=1, output="old")
        time.sleep(0.1)

        cp2 = PipelineCheckpoint(mode="writing", session_id="new_002")
        cp2.save_step("writer", iteration=1, output="new")

        found = find_resumable_checkpoint("writing")
        assert found.session_id == "new_002"

    def test_ignores_other_modes(self, tmp_checkpoint_dir):
        from checkpoint import PipelineCheckpoint, find_resumable_checkpoint
        cp = PipelineCheckpoint(mode="writing", session_id="w_001")
        cp.save_step("writer", iteration=1, output="text")

        assert find_resumable_checkpoint("coding") is None
