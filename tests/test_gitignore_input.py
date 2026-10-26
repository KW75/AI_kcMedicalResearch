"""input/ holds user data (uploaded PDFs, saved prompts): never commit it.

Session 31: .gitignore covered output/ and .env but not input/, so beta-test
uploads and input/<mode>/instructions.txt showed as untracked and could be
committed by mistake. Only the two tracked SR samples stay committable.
"""
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _ignored(rel_path: str) -> bool:
    # --no-index: judge by .gitignore rules alone, even for tracked files.
    result = subprocess.run(
        ["git", "check-ignore", "-q", "--no-index", rel_path],
        cwd=REPO_ROOT, capture_output=True,
    )
    return result.returncode == 0


@pytest.mark.parametrize("rel_path", [
    "input/coding/instructions.txt",
    "input/sr/papers/trial1.pdf",
    "input/sr/new_overrides.yaml",
    "input/writing/draft.docx",
])
def test_user_data_in_input_is_ignored(rel_path):
    assert _ignored(rel_path)


@pytest.mark.parametrize("rel_path", [
    "input/sr/pico_sample.json",
    "input/sr/study_overrides.yaml",
])
def test_tracked_samples_stay_committable(rel_path):
    assert not _ignored(rel_path)
