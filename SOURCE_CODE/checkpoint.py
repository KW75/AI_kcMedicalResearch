"""
checkpoint.py - Pipeline checkpointing for AI kcMedicalResearch.
Saves intermediate state after each pipeline step so that long-running
multi-iteration pipelines can be resumed after failure.

Usage:
    from checkpoint import PipelineCheckpoint

    cp = PipelineCheckpoint(mode="coding", session_id="20260813_143022")

    # Save after each step
    cp.save_step("builder", iteration=1, output="...", metadata={...})
    cp.save_step("reviewer", iteration=1, output="...", metadata={...})

    # On restart, check for resume
    if cp.has_checkpoint():
        state = cp.load()
        # Resume from state["last_completed_step"]

    # On success, clean up
    cp.clear()
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Checkpoint directory
# ---------------------------------------------------------------------------
def _checkpoint_dir() -> Path:
    """Return the checkpoints directory (project_root/reports/.checkpoints/)."""
    root = Path(__file__).resolve().parent.parent
    d = root / "reports" / ".checkpoints"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---------------------------------------------------------------------------
# PipelineCheckpoint class
# ---------------------------------------------------------------------------
class PipelineCheckpoint:
    """
    Manages checkpoint state for a single pipeline run.

    Each checkpoint is a JSON file containing:
    - mode, session_id, provider, model
    - steps: list of completed steps with their outputs
    - last_completed_step: name of the last successfully completed step
    - last_completed_iteration: iteration number
    - timestamp of last update
    """

    def __init__(
        self,
        mode: str,
        session_id: str = None,
        provider: str = None,
        model: str = None,
    ):
        self.mode = mode
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.provider = provider or ""
        self.model = model or ""
        self._path = _checkpoint_dir() / f"{mode}_{self.session_id}.json"
        self._state: dict[str, Any] = {
            "mode": mode,
            "session_id": self.session_id,
            "provider": self.provider,
            "model": self.model,
            "steps": [],
            "last_completed_step": "",
            "last_completed_iteration": 0,
            "created": datetime.now().isoformat(),
            "updated": datetime.now().isoformat(),
        }

    @property
    def path(self) -> Path:
        return self._path

    def has_checkpoint(self) -> bool:
        """Check if a checkpoint file exists for this session."""
        return self._path.exists()

    def save_step(
        self,
        step_name: str,
        iteration: int = 1,
        output: str = "",
        metadata: dict = None,
    ) -> None:
        """
        Save a completed step to the checkpoint file.
        Appends to the steps list and updates the last_completed fields.
        """
        step_data = {
            "step_name": step_name,
            "iteration": iteration,
            "output": output,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
        }

        # Load existing state if file exists
        if self._path.exists():
            try:
                self._state = json.loads(self._path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass

        self._state["steps"].append(step_data)
        self._state["last_completed_step"] = step_name
        self._state["last_completed_iteration"] = iteration
        self._state["updated"] = datetime.now().isoformat()

        self._path.write_text(
            json.dumps(self._state, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def load(self) -> dict[str, Any]:
        """
        Load checkpoint state from file.
        Returns the full state dict, or empty dict if no checkpoint exists.
        """
        if not self._path.exists():
            return {}
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def get_last_step(self) -> Optional[dict]:
        """Return the last completed step data, or None."""
        state = self.load()
        steps = state.get("steps", [])
        return steps[-1] if steps else None

    def get_step_output(self, step_name: str, iteration: int = None) -> Optional[str]:
        """
        Get the output of a specific step (optionally at a specific iteration).
        Returns None if not found.
        """
        state = self.load()
        for step in reversed(state.get("steps", [])):
            if step["step_name"] == step_name:
                if iteration is None or step["iteration"] == iteration:
                    return step.get("output", "")
        return None

    def get_completed_iterations(self) -> int:
        """Return the number of completed full iterations."""
        state = self.load()
        return state.get("last_completed_iteration", 0)

    def clear(self) -> None:
        """Delete the checkpoint file (call on successful pipeline completion)."""
        if self._path.exists():
            self._path.unlink()
            print(f"[checkpoint] Cleared: {self._path.name}")

    def summary(self) -> str:
        """Return a human-readable summary of the checkpoint state."""
        state = self.load()
        if not state:
            return "[No checkpoint found]"
        steps = state.get("steps", [])
        last_step = state.get("last_completed_step", "none")
        last_iter = state.get("last_completed_iteration", 0)
        updated = state.get("updated", "unknown")
        return (
            f"Checkpoint: {self.mode} | Session: {self.session_id}\n"
            f"  Steps completed: {len(steps)}\n"
            f"  Last step: {last_step} (iteration {last_iter})\n"
            f"  Last updated: {updated}\n"
            f"  Provider: {state.get('provider', 'unknown')}"
        )


# ---------------------------------------------------------------------------
# Resume helper
# ---------------------------------------------------------------------------
def find_resumable_checkpoint(mode: str) -> Optional[PipelineCheckpoint]:
    """
    Look for an existing checkpoint for the given mode.
    Returns a PipelineCheckpoint instance if found, None otherwise.
    """
    checkpoint_dir = _checkpoint_dir()
    if not checkpoint_dir.exists():
        return None

    # Find the most recent checkpoint for this mode
    candidates = sorted(
        checkpoint_dir.glob(f"{mode}_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    if not candidates:
        return None

    # Load the most recent one
    try:
        state = json.loads(candidates[0].read_text(encoding="utf-8"))
        cp = PipelineCheckpoint(
            mode=mode,
            session_id=state.get("session_id", ""),
            provider=state.get("provider", ""),
            model=state.get("model", ""),
        )
        return cp
    except (json.JSONDecodeError, OSError):
        return None


def prompt_resume(mode: str) -> tuple[bool, Optional[PipelineCheckpoint]]:
    """
    Check for a resumable checkpoint and ask the user if they want to resume.
    Returns (should_resume, checkpoint_or_None).
    """
    cp = find_resumable_checkpoint(mode)
    if cp is None or not cp.has_checkpoint():
        return False, None

    print(f"\n[checkpoint] Found incomplete session:")
    print(f"  {cp.summary()}")

    try:
        choice = input("  Resume from last checkpoint? [Y/n]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        choice = "n"

    if choice in ("", "y", "yes"):
        return True, cp
    else:
        # User chose not to resume - clear old checkpoint
        cp.clear()
        return False, None
