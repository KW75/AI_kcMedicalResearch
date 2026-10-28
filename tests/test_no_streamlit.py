"""Guards: the Streamlit UI and Render deploy are removed (Session 33 commit 3).

Local-first CLI only. pyarrow==12.0.1 stays pinned because chromadb needs it.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "SOURCE_CODE"))

GONE = [
    "SOURCE_CODE/ui/app.py",
    "SOURCE_CODE/ui/__init__.py",
    "SOURCE_CODE/pipelines/sr/run_sr_ui.bat",
    ".streamlit/config.toml",
    ".streamlit/secrets.toml.example",
    "assets/logo_AI_kcMedicalResearch.png",
    "assets/icon_AI_kcMedicalResearch.ico",
    "render.yaml",
    "requirements-render.txt",
    "scripts/windows/AI_kcMedicalResearch_UI.bat",
    "scripts/macos/Mac_kcMedicalResearch_UI.sh",
    "tests/test_ui.py",
    "tests/test_ui_cloud_gate.py",
    "tests/test_ui_model_picker.py",
    "tests/test_ui_time_limit.py",
    "tests/test_render_without_chromadb.py",
]

REQUIREMENTS = [
    "requirements.txt",
    "requirements-base.txt",
    "requirements-local.txt",
    "requirements-ci.txt",
    "SOURCE_CODE/pipelines/sr/requirements.txt",
]


def _main_text() -> str:
    return (ROOT / "SOURCE_CODE" / "main.py").read_text(encoding="utf-8")


def test_streamlit_and_render_files_are_deleted():
    still_there = [p for p in GONE if (ROOT / p).exists()]
    assert still_there == []


def test_main_has_no_ui_flag_or_streamlit():
    text = _main_text()
    assert "--ui" not in text
    assert "streamlit" not in text.lower()


def test_main_has_no_render_cloud_detection():
    text = _main_text()
    assert "'RENDER'" not in text
    assert "is_cloud" not in text


def test_path_manager_has_no_ui_or_assets():
    import utils.path_utils as pu
    pm = pu.PathManager()
    for attr in ("ui_dir", "assets_dir", "get_assets_path"):
        assert not hasattr(pm, attr), attr
    assert not hasattr(pu, "get_assets")


def test_path_manager_does_not_create_assets(tmp_path):
    import utils.path_utils as pu
    pu.PathManager(tmp_path)
    assert not (tmp_path / "assets").exists()


def test_requirements_have_no_streamlit():
    offenders = []
    for name in REQUIREMENTS:
        path = ROOT / name
        if not path.exists():
            continue
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip().lower().startswith("streamlit"):
                offenders.append(f"{name}:{n}")
    assert offenders == []


def test_pyarrow_pin_is_kept_for_chromadb():
    text = (ROOT / "requirements-local.txt").read_text(encoding="utf-8")
    assert "pyarrow==12.0.1" in text.splitlines()


def test_gitignore_has_no_streamlit_line():
    lines = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert not any(".streamlit" in ln for ln in lines)
    
def test_readme_has_no_hosted_app_or_web_ui():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    for banned in ("onrender.com", "--ui", "web UI", "Streamlit UI",
                   "Deployment (Render)", "UptimeRobot"):
        assert banned not in text, banned
