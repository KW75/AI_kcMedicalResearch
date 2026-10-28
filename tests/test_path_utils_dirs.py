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
