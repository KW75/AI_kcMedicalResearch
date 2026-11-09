"""path_utils must not create folders the app no longer uses.

data/ was never read by any code, and docker/ was removed in Session 31
(#28, Won't do). _ensure_directories() still created both every time
utils.path_utils was imported (PATH_MANAGER = PathManager()), so deleting
them by hand never stuck.
"""
import utils.path_utils as path_utils
from utils.path_utils import PathManager

MODES = ("coding", "writing", "appraisal", "search", "rct_search", "sr")


def test_does_not_create_data_or_docker(tmp_path):
    PathManager(tmp_path)
    assert not (tmp_path / "data").exists()
    assert not (tmp_path / "docker").exists()


def test_still_creates_input_and_output_for_each_mode(tmp_path):
    # Guard: the fix must not stop creating the folders users need.
    PathManager(tmp_path)
    for mode in MODES:
        assert (tmp_path / "input" / mode).is_dir()
        assert (tmp_path / "output" / mode).is_dir()


def test_data_and_docker_attributes_and_helpers_are_gone(tmp_path):
    pm = PathManager(tmp_path)
    assert not hasattr(pm, "data_dir")
    assert not hasattr(pm, "docker_dir")
    assert not hasattr(PathManager, "get_docker_path")
    assert not hasattr(path_utils, "get_docker_file")


# OCR and data_analysis are planned but not runnable modes yet. Git ignores
# input/*, output/ and reports/, so the app itself must create these folders
# for colleagues. They get no docs/ folder until the mode code exists.
FUTURE_MODES = ("ocr", "data_analysis")


def test_creates_input_output_reports_for_future_modes(tmp_path):
    PathManager(tmp_path)
    for mode in FUTURE_MODES:
        for top in ("input", "output", "reports"):
            assert (tmp_path / top / mode).is_dir(), f"{top}/{mode} not created"


def test_future_modes_get_no_docs_folder(tmp_path):
    PathManager(tmp_path)
    for mode in FUTURE_MODES:
        assert not (tmp_path / "docs" / mode).exists(), f"docs/{mode} should not exist yet"
