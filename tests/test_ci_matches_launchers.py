"""CI must install exactly what the launchers install.

Session 34: requirements-local.txt (the file both launchers install) pinned
openai/anthropic but not httpx; pip pulled httpx 0.28 and every cloud call
crashed. CI installed requirements-ci.txt, so it never saw that file.
These tests fail if CI and the launchers drift apart again.
"""
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
LAUNCHERS = [
    ROOT / "scripts" / "windows" / "AI_kcMedicalResearch_CLI.bat",
    ROOT / "scripts" / "macos" / "Mac_kcMedicalResearch_CLI.sh",
]
CI_FILE = ROOT / ".github" / "workflows" / "ci.yml"
# [\w.-]+\.txt, not \S+: the macOS line ends "requirements-local.txt; then".
INSTALL_RE = re.compile(r"-m pip install -r ([\w.-]+\.txt)")


def _launcher_files():
    found = set()
    for path in LAUNCHERS:
        text = path.read_text(encoding="utf-8", errors="replace")
        names = INSTALL_RE.findall(text)
        assert names, f"{path.name}: no '-m pip install -r' line found"
        found.update(names)
    return found


def _jobs():
    return yaml.safe_load(CI_FILE.read_text(encoding="utf-8"))["jobs"]


def _runs(job):
    return "\n".join(step.get("run", "") for step in job.get("steps", []))


def _job_installing(wanted):
    for name, job in _jobs().items():
        if wanted <= set(INSTALL_RE.findall(_runs(job))):
            return name, job
    return None, None


def test_launchers_install_one_requirements_file():
    assert _launcher_files() == {"requirements-local.txt"}


def test_a_ci_job_installs_what_the_launchers_install():
    wanted = _launcher_files()
    name, _ = _job_installing(wanted)
    assert name, f"no CI job runs '-m pip install -r' for {sorted(wanted)}"


def test_that_job_runs_the_suite_without_extra_build_tools():
    name, job = _job_installing(_launcher_files())
    assert name, "no CI job installs the launchers' requirements file"
    runs = _runs(job)
    assert 'pytest -m "not live"' in runs, name
    assert "build-essential" not in runs, name
