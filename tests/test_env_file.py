"""Tests for SOURCE_CODE/env_file.py - safe, minimal edits to .env (Session 33 commit 2)."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "SOURCE_CODE"))

import env_file  # noqa: E402


def _write(p: Path, text: str, newline: str = "\n") -> None:
    p.write_bytes(text.replace("\n", newline).encode("utf-8"))


# --- set_value: change one key, leave everything else alone -----------------

def test_replaces_only_that_key_and_keeps_everything_else(tmp_path):
    env = tmp_path / ".env"
    _write(env, "# comment\nDEEPSEEK_API_KEY=old\nOLLAMA_MODEL=gemma4:e4b\n\nCLI_THEME=dark\n")
    env_file.set_value(env, "DEEPSEEK_API_KEY", "sk-new1234")
    assert env.read_bytes() == (
        b"# comment\nDEEPSEEK_API_KEY=sk-new1234\nOLLAMA_MODEL=gemma4:e4b\n\nCLI_THEME=dark\n"
    )


def test_duplicate_key_lines_are_all_updated(tmp_path):
    env = tmp_path / ".env"
    _write(env, "DEEPSEEK_API_KEY=a\nX=1\nDEEPSEEK_API_KEY=b\n")
    env_file.set_value(env, "DEEPSEEK_API_KEY", "new")
    assert env.read_bytes() == b"DEEPSEEK_API_KEY=new\nX=1\nDEEPSEEK_API_KEY=new\n"


def test_keeps_crlf_line_endings(tmp_path):
    env = tmp_path / ".env"
    _write(env, "A=1\nDEEPSEEK_API_KEY=old\n", newline="\r\n")
    env_file.set_value(env, "DEEPSEEK_API_KEY", "new")
    assert env.read_bytes() == b"A=1\r\nDEEPSEEK_API_KEY=new\r\n"


def test_appends_missing_key(tmp_path):
    env = tmp_path / ".env"
    _write(env, "A=1\n")
    env_file.set_value(env, "GROQ_API_KEY", "gsk_x")
    assert env.read_bytes() == b"A=1\nGROQ_API_KEY=gsk_x\n"


def test_appends_after_file_without_trailing_newline(tmp_path):
    env = tmp_path / ".env"
    env.write_bytes(b"A=1")
    env_file.set_value(env, "GROQ_API_KEY", "g")
    assert env.read_bytes() == b"A=1\nGROQ_API_KEY=g\n"


def test_commented_line_is_not_touched(tmp_path):
    env = tmp_path / ".env"
    _write(env, "# OPENAI_API_KEY=example\n")
    env_file.set_value(env, "OPENAI_API_KEY", "k")
    assert env.read_bytes() == b"# OPENAI_API_KEY=example\nOPENAI_API_KEY=k\n"


def test_spaces_around_equals_are_matched(tmp_path):
    env = tmp_path / ".env"
    _write(env, "DEEPSEEK_API_KEY = old\n")
    env_file.set_value(env, "DEEPSEEK_API_KEY", "new")
    assert env.read_bytes() == b"DEEPSEEK_API_KEY=new\n"


def test_new_file_without_template_has_no_bom(tmp_path):
    env = tmp_path / ".env"
    env_file.set_value(env, "K", "v")
    assert env.read_bytes() == b"K=v\n"


def test_missing_env_copies_template_first(tmp_path):
    template = tmp_path / ".env.example"
    _write(template, "# header\nDEEPSEEK_API_KEY=\nCLI_THEME=dark\n")
    env = tmp_path / ".env"
    env_file.set_value(env, "DEEPSEEK_API_KEY", "sk-1", template=template)
    assert env.read_bytes() == b"# header\nDEEPSEEK_API_KEY=sk-1\nCLI_THEME=dark\n"
    assert template.read_bytes() == b"# header\nDEEPSEEK_API_KEY=\nCLI_THEME=dark\n"


def test_value_is_stripped(tmp_path):
    env = tmp_path / ".env"
    _write(env, "A=1\n")
    env_file.set_value(env, "A", "  sk-1  ")
    assert env.read_bytes() == b"A=sk-1\n"


# --- set_value: bad input changes nothing ------------------------------------

@pytest.mark.parametrize("value", ["a\nb", "a\rb", "a b", 'a"b'])
def test_rejects_unsafe_values(tmp_path, value):
    env = tmp_path / ".env"
    _write(env, "A=1\n")
    with pytest.raises(ValueError):
        env_file.set_value(env, "A", value)
    assert env.read_bytes() == b"A=1\n"


@pytest.mark.parametrize("key", ["", "1ABC", "A B", "A=B"])
def test_rejects_bad_key_names(tmp_path, key):
    env = tmp_path / ".env"
    _write(env, "A=1\n")
    with pytest.raises(ValueError):
        env_file.set_value(env, key, "v")
    assert env.read_bytes() == b"A=1\n"


# --- set_value: safe save -----------------------------------------------------

def test_leaves_no_temp_file(tmp_path):
    env = tmp_path / ".env"
    _write(env, "A=1\n")
    env_file.set_value(env, "A", "2")
    assert sorted(p.name for p in tmp_path.iterdir()) == [".env"]


def test_failed_save_keeps_the_old_file(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    _write(env, "DEEPSEEK_API_KEY=old\n")

    def boom(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(env_file.os, "replace", boom)
    with pytest.raises(OSError):
        env_file.set_value(env, "DEEPSEEK_API_KEY", "new")
    assert env.read_bytes() == b"DEEPSEEK_API_KEY=old\n"
    assert sorted(p.name for p in tmp_path.iterdir()) == [".env"]


# --- read_values ----------------------------------------------------------------

def test_read_values(tmp_path):
    env = tmp_path / ".env"
    _write(env, '# c\nA=1\nB = two\n# C=3\nD="quoted"\nE=\n', newline="\r\n")
    assert env_file.read_values(env) == {"A": "1", "B": "two", "D": "quoted", "E": ""}


def test_read_values_missing_file_is_empty(tmp_path):
    assert env_file.read_values(tmp_path / ".env") == {}


# --- mask -------------------------------------------------------------------------

@pytest.mark.parametrize("value, shown", [
    ("", "(not set)"),
    ("sk-abcdef1234", "****1234"),
    ("short", "****"),
])
def test_mask(value, shown):
    assert env_file.mask(value) == shown


# --- guard: real keys and temp files can never be committed ------------------------

def test_env_and_temp_files_are_gitignored():
    lines = [ln.strip() for ln in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()]
    assert ".env" in lines
    assert ".env.*" in lines
