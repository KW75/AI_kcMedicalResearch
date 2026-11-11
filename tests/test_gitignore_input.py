"""input/ holds user data (uploaded PDFs, saved prompts): never commit it.

Session 31: .gitignore covered output/ and .env but not input/, so beta-test
uploads and input/<mode>/instructions.txt showed as untracked and could be
committed by mistake. Session 38 (7h): pico_sample.json is search output, now ignored.
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
    "input/sr/pico_sample.json",
    "input/writing/draft.docx",
    "reference/sr_cbt_fibromyalgia/trial1.pdf",
    "reference/sr_cbt_fibromyalgia/paper_text/trial1.txt",
])
def test_user_data_in_input_is_ignored(rel_path):
    assert _ignored(rel_path)


@pytest.mark.parametrize("rel_path", [
    "input/sr/study_overrides.yaml",
    "reference/sr_cbt_fibromyalgia/README.md",
    "reference/sr_cbt_fibromyalgia/prisma_criteria.yaml",
    "reference/sr_cbt_fibromyalgia/pico_sample.json",
    "reference/sr_cbt_fibromyalgia/study_overrides.yaml",
])
def test_tracked_samples_stay_committable(rel_path):
    assert not _ignored(rel_path)
