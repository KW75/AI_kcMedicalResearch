from __future__ import annotations

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from urllib.error import HTTPError, URLError
from src.main import (
    read_text_file, save_report, build_project_context,
    call_ollama_provider, call_ai, choose_role, DOC_FILES_BY_ROLE,
)


# ===========================================================================
# read_text_file
# ===========================================================================
def test_read_text_file_returns_content(tmp_path: Path) -> None:
    f = tmp_path / "sample.txt"
    f.write_text("hello world", encoding="utf-8")
    assert read_text_file(f) == "hello world"


def test_read_text_file_returns_empty_string_when_missing(tmp_path: Path) -> None:
    assert read_text_file(tmp_path / "does_not_exist.txt") == ""


def test_read_text_file_strips_whitespace(tmp_path: Path) -> None:
    f = tmp_path / "padded.txt"
    f.write_text("  trimmed content  \n", encoding="utf-8")
    assert read_text_file(f) == "trimmed content"


# ===========================================================================
# save_report
# ===========================================================================
def test_save_report_creates_file(tmp_path: Path) -> None:
    p = tmp_path / "reports" / "test-report.md"
    save_report(p, "Tester", "qwen2.5-coder:3b", "Run tests", "All tests passed.")
    assert p.exists()


def test_save_report_contains_expected_content(tmp_path: Path) -> None:
    p = tmp_path / "reports" / "review-log.md"
    save_report(p, "Reviewer", "qwen2.5-coder:3b", "Check my code", "Looks good.")
    content = p.read_text(encoding="utf-8")
    assert "Reviewer" in content
    assert "Check my code" in content
    assert "Looks good." in content


def test_save_report_appends_on_second_call(tmp_path: Path) -> None:
    p = tmp_path / "reports" / "builder-output.md"
    save_report(p, "Builder", "qwen2.5-coder:3b", "First task",  "First response.")
    save_report(p, "Builder", "qwen2.5-coder:3b", "Second task", "Second response.")
    content = p.read_text(encoding="utf-8")
    assert "First response."  in content
    assert "Second response." in content


# ===========================================================================
# start_session_transcript
# ===========================================================================
def test_start_session_transcript_creates_file(tmp_path: Path) -> None:
    from src.main import start_session_transcript
    assert start_session_transcript(tmp_path).exists()


def test_start_session_transcript_contains_header(tmp_path: Path) -> None:
    from src.main import start_session_transcript
    content = start_session_transcript(tmp_path).read_text(encoding="utf-8")
    assert "Session Transcript" in content
    assert "Started:" in content


def test_start_session_transcript_filename_contains_session(tmp_path: Path) -> None:
    from src.main import start_session_transcript
    assert "session_" in start_session_transcript(tmp_path).name


# ===========================================================================
# append_to_transcript
# ===========================================================================
def test_append_to_transcript_adds_entry(tmp_path: Path) -> None:
    from src.main import start_session_transcript, append_to_transcript
    p = start_session_transcript(tmp_path)
    append_to_transcript(p, "Builder", 1, "Write a function", "Here is the code.")
    assert "Here is the code." in p.read_text(encoding="utf-8")


def test_append_to_transcript_includes_step_number(tmp_path: Path) -> None:
    from src.main import start_session_transcript, append_to_transcript
    p = start_session_transcript(tmp_path)
    append_to_transcript(p, "Builder", 3, "Task", "Response")
    assert "Step 3" in p.read_text(encoding="utf-8")


def test_append_to_transcript_appends_multiple_entries(tmp_path: Path) -> None:
    from src.main import start_session_transcript, append_to_transcript
    p = start_session_transcript(tmp_path)
    append_to_transcript(p, "Builder",  1, "First task",  "First response.")
    append_to_transcript(p, "Reviewer", 2, "Second task", "Second response.")
    content = p.read_text(encoding="utf-8")
    assert "First response."  in content
    assert "Second response." in content


# ===========================================================================
# build_project_context
# ===========================================================================
def test_build_project_context_includes_file_content(tmp_path: Path) -> None:
    doc = tmp_path / "PRD.md"
    doc.write_text("Project goals here.", encoding="utf-8")
    with patch.dict("src.main.DOC_FILES_BY_ROLE", {"Builder": [doc]}):
        assert "Project goals here." in build_project_context("Builder")


def test_build_project_context_includes_filename(tmp_path: Path) -> None:
    doc = tmp_path / "PRD.md"
    doc.write_text("content", encoding="utf-8")
    with patch.dict("src.main.DOC_FILES_BY_ROLE", {"Builder": [doc]}):
        assert "PRD.md" in build_project_context("Builder")


def test_build_project_context_skips_missing_files(tmp_path: Path) -> None:
    missing = tmp_path / "missing.md"
    with patch.dict("src.main.DOC_FILES_BY_ROLE", {"Builder": [missing]}):
        assert build_project_context("Builder") == ""


def test_build_project_context_combines_multiple_files(tmp_path: Path) -> None:
    a = tmp_path / "a.md"
    b = tmp_path / "b.md"
    a.write_text("Content A", encoding="utf-8")
    b.write_text("Content B", encoding="utf-8")
    with patch.dict("src.main.DOC_FILES_BY_ROLE", {"Builder": [a, b]}):
        ctx = build_project_context("Builder")
    assert "Content A" in ctx
    assert "Content B" in ctx


def test_build_project_context_builder_receives_coding_standards(tmp_path: Path) -> None:
    cs = tmp_path / "coding-standards.md"
    cs.write_text("Use type hints.", encoding="utf-8")
    original = list(DOC_FILES_BY_ROLE["Builder"])
    patched  = [f for f in original if f.name != "coding-standards.md"] + [cs]
    with patch.dict("src.main.DOC_FILES_BY_ROLE", {"Builder": patched}):
        assert "Use type hints." in build_project_context("Builder")


def test_build_project_context_reviewer_receives_decision_log(tmp_path: Path) -> None:
    dl = tmp_path / "decision-log.md"
    dl.write_text("Chose REST over GraphQL.", encoding="utf-8")
    original = list(DOC_FILES_BY_ROLE["Reviewer"])
    patched  = [f for f in original if f.name != "decision-log.md"] + [dl]
    with patch.dict("src.main.DOC_FILES_BY_ROLE", {"Reviewer": patched}):
        assert "Chose REST over GraphQL." in build_project_context("Reviewer")


def test_build_project_context_tester_receives_test_strategy(tmp_path: Path) -> None:
    ts = tmp_path / "test-strategy.md"
    ts.write_text("Use pytest.", encoding="utf-8")
    original = list(DOC_FILES_BY_ROLE["Tester"])
    patched  = [f for f in original if f.name != "test-strategy.md"] + [ts]
    with patch.dict("src.main.DOC_FILES_BY_ROLE", {"Tester": patched}):
        assert "Use pytest." in build_project_context("Tester")


def test_build_project_context_builder_does_not_receive_decision_log() -> None:
    doc_names = [p.name for p in DOC_FILES_BY_ROLE.get("Builder", [])]
    assert "decision-log.md" not in doc_names


def test_build_project_context_unknown_role_returns_empty() -> None:
    assert build_project_context("UnknownRole") == ""


# ===========================================================================
# truncate_context
# ===========================================================================
def test_truncate_context_returns_short_text_unchanged() -> None:
    from src.main import truncate_context
    assert truncate_context("short", max_chars=100) == "short"


def test_truncate_context_truncates_long_text() -> None:
    from src.main import truncate_context
    result = truncate_context("a" * 3000, max_chars=2000)
    assert len(result) <= 2001  # 2000 chars + ellipsis


def test_truncate_context_keeps_exactly_max_chars() -> None:
    from src.main import truncate_context
    text = "x" * 2000
    assert truncate_context(text, max_chars=2000) == text


def test_truncate_context_custom_limit() -> None:
    from src.main import truncate_context
    result = truncate_context("hello world", max_chars=5)
    assert result.startswith("hello")
    assert len(result) <= 6


# ===========================================================================
# call_ollama_provider
# ===========================================================================
def _mock_urlopen(body: bytes):
    mock_resp = MagicMock()
    mock_resp.read.return_value = body
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__  = MagicMock(return_value=False)
    return mock_resp


def test_call_ollama_provider_returns_response_text() -> None:
    body = json.dumps({"response": "Hello from Ollama"}).encode()
    with patch("src.main.urlopen", return_value=_mock_urlopen(body)):
        assert call_ollama_provider("prompt") == "Hello from Ollama"


def test_call_ollama_provider_raises_on_empty_response() -> None:
    body = json.dumps({"response": ""}).encode()
    with patch("src.main.urlopen", return_value=_mock_urlopen(body)):
        with pytest.raises(RuntimeError):
            call_ollama_provider("prompt")


def test_call_ollama_provider_raises_on_ollama_error() -> None:
    body = json.dumps({"error": "model not found"}).encode()
    with patch("src.main.urlopen", return_value=_mock_urlopen(body)):
        with pytest.raises(RuntimeError):
            call_ollama_provider("prompt")


def test_call_ollama_provider_raises_on_http_error() -> None:
    with patch("src.main.urlopen", side_effect=HTTPError(None, 500, "Server Error", {}, None)):
        with pytest.raises(RuntimeError, match="HTTP error"):
            call_ollama_provider("prompt")


def test_call_ollama_provider_raises_on_url_error() -> None:
    with patch("src.main.urlopen", side_effect=URLError("connection refused")):
        with pytest.raises(RuntimeError, match="connection error"):
            call_ollama_provider("prompt")


def test_call_ollama_provider_raises_on_timeout() -> None:
    import socket
    with patch("src.main.urlopen", side_effect=TimeoutError("timed out")):
        with pytest.raises((RuntimeError, TimeoutError)):
            call_ollama_provider("prompt")


# ===========================================================================
# choose_role
# ===========================================================================
def test_choose_role_returns_builder() -> None:
    with patch("builtins.input", return_value="1"):
        role_name, role_cfg = choose_role(mode="coding")
    assert role_name == "Builder"
    assert "prompt" in role_cfg


def test_choose_role_returns_reviewer() -> None:
    with patch("builtins.input", return_value="2"):
        role_name, _ = choose_role(mode="coding")
    assert role_name == "Reviewer"


def test_choose_role_returns_tester() -> None:
    with patch("builtins.input", return_value="3"):
        role_name, _ = choose_role(mode="coding")
    assert role_name == "Tester"


def test_choose_role_shows_warning_on_invalid_then_accepts_valid() -> None:
    with patch("builtins.input", side_effect=["9", "1"]), \
         patch("builtins.print"):
        role_name, _ = choose_role(mode="coding")
    assert role_name == "Builder"


# ===========================================================================
# print_session_summary
# ===========================================================================
def test_print_session_summary_shows_step_count(tmp_path: Path, capsys) -> None:
    from src.main import print_session_summary, start_session_transcript
    p = start_session_transcript(tmp_path)
    print_session_summary(p, 5, {"Builder": 5})
    assert "5" in capsys.readouterr().out


def test_print_session_summary_shows_role_counts(tmp_path: Path, capsys) -> None:
    from src.main import print_session_summary, start_session_transcript
    p = start_session_transcript(tmp_path)
    print_session_summary(p, 3, {"Builder": 3, "Reviewer": 0})
    out = capsys.readouterr().out
    assert "Builder" in out


def test_print_session_summary_shows_none_when_no_steps(tmp_path: Path, capsys) -> None:
    from src.main import print_session_summary, start_session_transcript
    p = start_session_transcript(tmp_path)
    print_session_summary(p, 0, {})
    assert "No steps" in capsys.readouterr().out


def test_print_session_summary_shows_transcript_path(tmp_path: Path, capsys) -> None:
    from src.main import print_session_summary, start_session_transcript
    p = start_session_transcript(tmp_path)
    print_session_summary(p, 1, {"Builder": 1})
    assert p.name in capsys.readouterr().out


# ===========================================================================
# main() dry-run
# ===========================================================================
def test_main_dry_run_does_not_call_ai(tmp_path, monkeypatch) -> None:
    from src.main import main
    inputs = iter(["1", "test dry run task"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    monkeypatch.setattr("src.main.REPORTS_DIR", tmp_path)
    with patch("src.main.call_ai") as mock_ai:
        try:
            main(dry_run=True)
        except StopIteration:
            pass
    mock_ai.assert_not_called()


def test_main_runs_full_workflow(tmp_path: Path) -> None:
    from src.main import main
    body = json.dumps({"response": "Builder AI response."}).encode()
    with patch("builtins.input", side_effect=["1", "Write a hello world function.", KeyboardInterrupt()]), \
         patch("src.main.urlopen", return_value=_mock_urlopen(body)), \
         patch("src.main.REPORTS_DIR", tmp_path), \
         patch("builtins.print"):
        main(mode="coding", provider="ollama")
    reports = list(tmp_path.glob("session_*.md"))
    assert len(reports) == 1


def test_main_handles_empty_task(tmp_path: Path) -> None:
    from src.main import main
    body = json.dumps({"response": "AI response."}).encode()
    with patch("builtins.input", side_effect=["1", "", "Write a function", KeyboardInterrupt()]), \
         patch("src.main.urlopen", return_value=_mock_urlopen(body)), \
         patch("src.main.REPORTS_DIR", tmp_path), \
         patch("builtins.print"):
        main(mode="coding", provider="ollama")


def test_main_uses_model_override(tmp_path: Path) -> None:
    from src.main import main
    body = json.dumps({"response": "AI response."}).encode()
    with patch("builtins.input", side_effect=["1", "Write a function.", KeyboardInterrupt()]), \
         patch("src.main.urlopen", return_value=_mock_urlopen(body)) as mock_u, \
         patch("src.main.REPORTS_DIR", tmp_path), \
         patch("builtins.print"):
        main(model_override="llama3.2:3b", mode="coding", provider="ollama")
    call_data = json.loads(mock_u.call_args[0][0].data)
    assert call_data["model"] == "llama3.2:3b"


def test_main_uses_env_model_when_no_override(tmp_path: Path) -> None:
    from src.main import main
    body = json.dumps({"response": "AI response."}).encode()
    with patch("builtins.input", side_effect=["1", "Write a function.", KeyboardInterrupt()]), \
         patch("src.main.urlopen", return_value=_mock_urlopen(body)) as mock_u, \
         patch("src.main.REPORTS_DIR", tmp_path), \
         patch("builtins.print"), \
         patch("src.main.OLLAMA_MODEL", "mistral:7b"):
        main(mode="coding", provider="ollama")
    call_data = json.loads(mock_u.call_args[0][0].data)
    assert call_data["model"] == "mistral:7b"


def test_main_handles_ollama_error_and_retries(tmp_path: Path) -> None:
    from src.main import main
    body = json.dumps({"response": "AI response."}).encode()
    with patch("builtins.input", side_effect=["1", "Write a function", KeyboardInterrupt()]), \
         patch("src.main.urlopen", side_effect=URLError("refused")), \
         patch("src.main.REPORTS_DIR", tmp_path), \
         patch("builtins.print"):
        main(mode="coding", provider="ollama")


# ===========================================================================
# parse_args
# ===========================================================================
def test_parse_args_default_model_is_none() -> None:
    from src.main import parse_args
    with patch("sys.argv", ["main.py"]):
        assert parse_args().model is None


def test_parse_args_model_flag() -> None:
    from src.main import parse_args
    with patch("sys.argv", ["main.py", "--model", "llama3.2:3b"]):
        assert parse_args().model == "llama3.2:3b"


def test_parse_args_mode_default() -> None:
    from src.main import parse_args
    with patch("sys.argv", ["main.py"]):
        assert parse_args().mode == "coding"


def test_parse_args_mode_writing() -> None:
    from src.main import parse_args
    with patch("sys.argv", ["main.py", "--mode", "writing"]):
        assert parse_args().mode == "writing"


def test_parse_args_provider_default() -> None:
    from src.main import parse_args
    with patch("sys.argv", ["main.py"]):
        assert parse_args().provider == "ollama"


def test_parse_args_list_sessions_flag() -> None:
    from src.main import parse_args
    with patch("sys.argv", ["main.py", "--list-sessions"]):
        assert parse_args().list_sessions is True


def test_parse_args_list_sessions_default_false() -> None:
    from src.main import parse_args
    with patch("sys.argv", ["main.py"]):
        assert parse_args().list_sessions is False


def test_parse_args_dry_run_flag() -> None:
    from src.main import parse_args
    with patch("sys.argv", ["main.py", "--dry-run"]):
        assert parse_args().dry_run is True


def test_parse_args_dry_run_default_false() -> None:
    from src.main import parse_args
    with patch("sys.argv", ["main.py"]):
        assert parse_args().dry_run is False


def test_parse_args_read_session_flag() -> None:
    from src.main import parse_args
    with patch("sys.argv", ["main.py", "--read-session", "session_abc.md"]):
        assert parse_args().read_session == "session_abc.md"


def test_parse_args_delete_session_flag() -> None:
    from src.main import parse_args
    with patch("sys.argv", ["main.py", "--delete-session", "session_abc.md"]):
        assert parse_args().delete_session == "session_abc.md"


def test_parse_args_export_session_flag() -> None:
    from src.main import parse_args
    with patch("sys.argv", ["main.py", "--export-session", "session_abc.md"]):
        assert parse_args().export_session == "session_abc.md"


def test_parse_args_rename_session_flag() -> None:
    from src.main import parse_args
    with patch("sys.argv", ["main.py", "--rename-session", "session_abc.md"]):
        assert parse_args().rename_session == "session_abc.md"


def test_parse_args_stats_flag() -> None:
    from src.main import parse_args
    with patch("sys.argv", ["main.py", "--stats"]):
        assert parse_args().stats is True


def test_version_constant_is_defined() -> None:
    from src.main import VERSION
    assert VERSION


def test_parse_args_version_flag() -> None:
    from src.main import parse_args
    with patch("sys.argv", ["main.py", "--version"]):
        with pytest.raises(SystemExit):
            parse_args()


def test_parse_args_help_contains_examples(capsys) -> None:
    from src.main import parse_args
    with patch("sys.argv", ["main.py", "--help"]):
        with pytest.raises(SystemExit):
            parse_args()
    assert "Examples" in capsys.readouterr().out


# ===========================================================================
# list_sessions
# ===========================================================================
def test_list_sessions_no_reports_folder(capsys) -> None:
    from src.main import list_sessions
    list_sessions(reports_dir="nonexistent_reports_dir_xyz")
    assert "No reports folder found" in capsys.readouterr().out


def test_list_sessions_empty_folder(tmp_path, capsys) -> None:
    from src.main import list_sessions
    list_sessions(reports_dir=str(tmp_path))
    assert "No session transcripts found" in capsys.readouterr().out


def test_list_sessions_shows_files(tmp_path, capsys) -> None:
    from src.main import list_sessions
    (tmp_path / "session_20250101_120000.md").write_text("x")
    list_sessions(reports_dir=str(tmp_path))
    assert "session_20250101_120000.md" in capsys.readouterr().out


def test_list_sessions_sorted_newest_first(tmp_path, capsys) -> None:
    from src.main import list_sessions
    (tmp_path / "session_20250101_120000.md").write_text("older")
    (tmp_path / "session_20250103_120000.md").write_text("newer")
    list_sessions(reports_dir=str(tmp_path))
    out = capsys.readouterr().out
    assert out.find("session_20250103") < out.find("session_20250101")


# ===========================================================================
# read_session
# ===========================================================================
def test_read_session_prints_content(tmp_path, capsys) -> None:
    from src.main import read_session
    f = tmp_path / "session_20250101_120000.md"
    f.write_text("Some content", encoding="utf-8")
    read_session(filename="session_20250101_120000.md", reports_dir=str(tmp_path))
    assert "Some content" in capsys.readouterr().out


def test_read_session_prints_filename_in_header(tmp_path, capsys) -> None:
    from src.main import read_session
    f = tmp_path / "session_20250101_120000.md"
    f.write_text("Some content", encoding="utf-8")
    read_session(filename="session_20250101_120000.md", reports_dir=str(tmp_path))
    assert "session_20250101_120000.md" in capsys.readouterr().out


def test_read_session_file_not_found(tmp_path, capsys) -> None:
    from src.main import read_session
    read_session(filename="session_missing.md", reports_dir=str(tmp_path))
    out = capsys.readouterr().out
    assert "not found" in out
    assert "--list-sessions" in out


# ===========================================================================
# delete_session
# ===========================================================================
def test_delete_session_removes_file(tmp_path, monkeypatch) -> None:
    from src.main import delete_session
    f = tmp_path / "session_20250101_120000.md"
    f.write_text("content", encoding="utf-8")
    monkeypatch.setattr("builtins.input", lambda _: "y")
    delete_session(filename="session_20250101_120000.md", reports_dir=str(tmp_path))
    assert not f.exists()


def test_delete_session_cancelled(tmp_path, monkeypatch, capsys) -> None:
    from src.main import delete_session
    f = tmp_path / "session_20250101_120000.md"
    f.write_text("content", encoding="utf-8")
    monkeypatch.setattr("builtins.input", lambda _: "n")
    delete_session(filename="session_20250101_120000.md", reports_dir=str(tmp_path))
    assert f.exists()
    assert "cancelled" in capsys.readouterr().out.lower()


def test_delete_session_file_not_found(tmp_path, capsys) -> None:
    from src.main import delete_session
    delete_session(filename="session_missing.md", reports_dir=str(tmp_path))
    out = capsys.readouterr().out
    assert "not found" in out
    assert "--list-sessions" in out


def test_delete_session_prints_confirmation(tmp_path, monkeypatch, capsys) -> None:
    from src.main import delete_session
    f = tmp_path / "session_20250101_120000.md"
    f.write_text("content", encoding="utf-8")
    monkeypatch.setattr("builtins.input", lambda _: "y")
    delete_session(filename="session_20250101_120000.md", reports_dir=str(tmp_path))
    assert "Deleted" in capsys.readouterr().out


# ===========================================================================
# export_session
# ===========================================================================
def test_export_session_creates_txt_file(tmp_path) -> None:
    from src.main import export_session
    f = tmp_path / "session_20250101_120000.md"
    f.write_text("# Session\n\nSome content here", encoding="utf-8")
    export_session(filename="session_20250101_120000.md", reports_dir=str(tmp_path))
    assert (tmp_path / "session_20250101_120000.txt").exists()


def test_export_session_strips_markdown(tmp_path) -> None:
    from src.main import export_session
    f = tmp_path / "session_20250101_120000.md"
    f.write_text("# Title\n\n## Section\n\n**bold** content", encoding="utf-8")
    export_session(filename="session_20250101_120000.md", reports_dir=str(tmp_path))
    content = (tmp_path / "session_20250101_120000.txt").read_text(encoding="utf-8")
    assert "bold" in content
    assert "**" not in content


def test_export_session_file_not_found(tmp_path, capsys) -> None:
    from src.main import export_session
    export_session(filename="session_missing.md", reports_dir=str(tmp_path))
    out = capsys.readouterr().out
    assert "not found" in out
    assert "--list-sessions" in out


def test_export_session_prints_export_path(tmp_path, capsys) -> None:
    from src.main import export_session
    f = tmp_path / "session_20250101_120000.md"
    f.write_text("content", encoding="utf-8")
    export_session(filename="session_20250101_120000.md", reports_dir=str(tmp_path))
    assert "Exported" in capsys.readouterr().out


# ===========================================================================
# show_stats
# ===========================================================================
def test_show_stats_no_reports_folder(capsys) -> None:
    from src.main import show_stats
    show_stats(reports_dir="nonexistent_reports_dir_xyz")
    assert "No reports folder found" in capsys.readouterr().out


def test_show_stats_empty_folder(tmp_path, capsys) -> None:
    from src.main import show_stats
    show_stats(reports_dir=str(tmp_path))
    assert "No session transcripts found" in capsys.readouterr().out


def test_show_stats_counts_sessions(tmp_path, capsys) -> None:
    from src.main import show_stats
    (tmp_path / "session_20250101_120000.md").write_text("## Step 1 - Builder AI\n")
    (tmp_path / "session_20250102_120000.md").write_text("## Step 1 - Reviewer AI\n")
    show_stats(reports_dir=str(tmp_path))
    assert "Total sessions    : 2" in capsys.readouterr().out


def test_show_stats_counts_roles(tmp_path, capsys) -> None:
    from src.main import show_stats
    (tmp_path / "session_20250101_120000.md").write_text(
        "## Builder\nsome content\n## Builder\nmore content\n"
    )
    show_stats(reports_dir=str(tmp_path))
    out = capsys.readouterr().out
    assert "Builder" in out


# ===========================================================================
# rename_session
# ===========================================================================
def test_rename_session_renames_file(tmp_path, monkeypatch) -> None:
    from src.main import rename_session
    f = tmp_path / "session_20250101_120000.md"
    f.write_text("content", encoding="utf-8")
    monkeypatch.setattr("builtins.input", lambda _: "my-first-session")
    rename_session(filename="session_20250101_120000.md", reports_dir=str(tmp_path))
    assert (tmp_path / "my-first-session.md").exists()


def test_rename_session_file_not_found(tmp_path, capsys) -> None:
    from src.main import rename_session
    rename_session(filename="session_missing.md", reports_dir=str(tmp_path))
    out = capsys.readouterr().out
    assert "not found" in out
    assert "--list-sessions" in out


def test_rename_session_empty_name_cancelled(tmp_path, monkeypatch, capsys) -> None:
    from src.main import rename_session
    f = tmp_path / "session_20250101_120000.md"
    f.write_text("content", encoding="utf-8")
    monkeypatch.setattr("builtins.input", lambda _: "")
    rename_session(filename="session_20250101_120000.md", reports_dir=str(tmp_path))
    assert "cannot be empty" in capsys.readouterr().out


def test_rename_session_duplicate_name_cancelled(tmp_path, monkeypatch, capsys) -> None:
    from src.main import rename_session
    f = tmp_path / "session_20250101_120000.md"
    f.write_text("content", encoding="utf-8")
    (tmp_path / "my-first-session.md").write_text("other content", encoding="utf-8")
    monkeypatch.setattr("builtins.input", lambda _: "my-first-session")
    rename_session(filename="session_20250101_120000.md", reports_dir=str(tmp_path))
    assert "already exists" in capsys.readouterr().out


def test_rename_session_prints_confirmation(tmp_path, monkeypatch, capsys) -> None:
    from src.main import rename_session
    f = tmp_path / "session_20250101_120000.md"
    f.write_text("content", encoding="utf-8")
    monkeypatch.setattr("builtins.input", lambda _: "new-name")
    rename_session(filename="session_20250101_120000.md", reports_dir=str(tmp_path))
    assert "Renamed" in capsys.readouterr().out


# ===========================================================================
# ALL_MODES
# ===========================================================================
def test_all_modes_contains_coding_and_writing() -> None:
    from src.main import ALL_MODES
    assert "coding"     in ALL_MODES
    assert "writing"    in ALL_MODES
    assert "rct_search" in ALL_MODES


# ===========================================================================
# call_openai_provider
# ===========================================================================
def test_call_openai_provider_returns_response_text() -> None:
    from src.main import call_openai_provider
    body = json.dumps({"choices": [{"message": {"content": "Hello from OpenAI"}}]}).encode()
    with patch("src.main.urlopen", return_value=_mock_urlopen(body)), \
         patch("src.main.OPENAI_API_KEY", "sk-test-key"):
        assert call_openai_provider("prompt") == "Hello from OpenAI"


def test_call_openai_provider_raises_when_api_key_missing() -> None:
    from src.main import call_openai_provider
    with patch("src.main.OPENAI_API_KEY", ""):
        with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
            call_openai_provider("prompt")


def test_call_openai_provider_raises_on_empty_response() -> None:
    from src.main import call_openai_provider
    body = json.dumps({"choices": [{"message": {"content": ""}}]}).encode()
    with patch("src.main.urlopen", return_value=_mock_urlopen(body)), \
         patch("src.main.OPENAI_API_KEY", "sk-test-key"):
        with pytest.raises(RuntimeError):
            call_openai_provider("prompt")


def test_call_openai_provider_raises_on_api_error() -> None:
    from src.main import call_openai_provider
    body = json.dumps({"error": {"message": "invalid model"}}).encode()
    with patch("src.main.urlopen", return_value=_mock_urlopen(body)), \
         patch("src.main.OPENAI_API_KEY", "sk-test-key"):
        with pytest.raises(RuntimeError):
            call_openai_provider("prompt")


def test_call_openai_provider_raises_on_http_error() -> None:
    from src.main import call_openai_provider
    with patch("src.main.urlopen", side_effect=HTTPError(None, 401, "Unauthorized", {}, None)), \
         patch("src.main.OPENAI_API_KEY", "sk-test-key"):
        with pytest.raises(RuntimeError, match="HTTP error"):
            call_openai_provider("prompt")


def test_call_openai_provider_raises_on_url_error() -> None:
    from src.main import call_openai_provider
    with patch("src.main.urlopen", side_effect=URLError("refused")), \
         patch("src.main.OPENAI_API_KEY", "sk-test-key"):
        with pytest.raises(RuntimeError, match="connection error"):
            call_openai_provider("prompt")


def test_call_openai_provider_raises_on_timeout() -> None:
    from src.main import call_openai_provider
    with patch("src.main.urlopen", side_effect=TimeoutError()), \
         patch("src.main.OPENAI_API_KEY", "sk-test-key"):
        with pytest.raises((RuntimeError, TimeoutError)):
            call_openai_provider("prompt")


def test_call_openai_provider_sends_correct_payload() -> None:
    from src.main import call_openai_provider
    body = json.dumps({"choices": [{"message": {"content": "ok"}}]}).encode()
    with patch("src.main.urlopen", return_value=_mock_urlopen(body)) as mock_u, \
         patch("src.main.OPENAI_API_KEY", "sk-test-key"):
        call_openai_provider("hello", model="gpt-4o-mini")
    payload = json.loads(mock_u.call_args[0][0].data)
    assert payload["model"] == "gpt-4o-mini"
    assert payload["messages"][0]["content"] == "hello"


def test_call_openai_provider_sends_auth_header() -> None:
    from src.main import call_openai_provider
    body = json.dumps({"choices": [{"message": {"content": "ok"}}]}).encode()
    with patch("src.main.urlopen", return_value=_mock_urlopen(body)) as mock_u, \
         patch("src.main.OPENAI_API_KEY", "sk-test-key"):
        call_openai_provider("hello")
    headers = mock_u.call_args[0][0].headers
    assert "Authorization" in headers or "authorization" in {k.lower() for k in headers}


# ===========================================================================
# call_anthropic_provider
# ===========================================================================
def test_call_anthropic_provider_returns_response_text() -> None:
    from src.main import call_anthropic_provider
    body = json.dumps({"content": [{"text": "Hello from Anthropic"}]}).encode()
    with patch("src.main.urlopen", return_value=_mock_urlopen(body)), \
         patch("src.main.ANTHROPIC_API_KEY", "sk-ant-test"):
        assert call_anthropic_provider("prompt") == "Hello from Anthropic"


def test_call_anthropic_provider_raises_when_api_key_missing() -> None:
    from src.main import call_anthropic_provider
    with patch("src.main.ANTHROPIC_API_KEY", ""):
        with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
            call_anthropic_provider("prompt")


def test_call_anthropic_provider_raises_on_empty_response() -> None:
    from src.main import call_anthropic_provider
    body = json.dumps({"content": [{"text": ""}]}).encode()
    with patch("src.main.urlopen", return_value=_mock_urlopen(body)), \
         patch("src.main.ANTHROPIC_API_KEY", "sk-ant-test"):
        with pytest.raises(RuntimeError):
            call_anthropic_provider("prompt")


def test_call_anthropic_provider_raises_on_api_error() -> None:
    from src.main import call_anthropic_provider
    body = json.dumps({"error": {"type": "invalid_request_error"}}).encode()
    with patch("src.main.urlopen", return_value=_mock_urlopen(body)), \
         patch("src.main.ANTHROPIC_API_KEY", "sk-ant-test"):
        with pytest.raises(RuntimeError):
            call_anthropic_provider("prompt")


def test_call_anthropic_provider_raises_on_http_error() -> None:
    from src.main import call_anthropic_provider
    with patch("src.main.urlopen", side_effect=HTTPError(None, 403, "Forbidden", {}, None)), \
         patch("src.main.ANTHROPIC_API_KEY", "sk-ant-test"):
        with pytest.raises(RuntimeError, match="HTTP error"):
            call_anthropic_provider("prompt")


def test_call_anthropic_provider_raises_on_url_error() -> None:
    from src.main import call_anthropic_provider
    with patch("src.main.urlopen", side_effect=URLError("refused")), \
         patch("src.main.ANTHROPIC_API_KEY", "sk-ant-test"):
        with pytest.raises(RuntimeError, match="connection error"):
            call_anthropic_provider("prompt")


def test_call_anthropic_provider_raises_on_timeout() -> None:
    from src.main import call_anthropic_provider
    with patch("src.main.urlopen", side_effect=TimeoutError()), \
         patch("src.main.ANTHROPIC_API_KEY", "sk-ant-test"):
        with pytest.raises((RuntimeError, TimeoutError)):
            call_anthropic_provider("prompt")


def test_call_anthropic_provider_sends_correct_payload() -> None:
    from src.main import call_anthropic_provider
    body = json.dumps({"content": [{"text": "ok"}]}).encode()
    with patch("src.main.urlopen", return_value=_mock_urlopen(body)) as mock_u, \
         patch("src.main.ANTHROPIC_API_KEY", "sk-ant-test"):
        call_anthropic_provider("hello", model="claude-sonnet-4-6")
    payload = json.loads(mock_u.call_args[0][0].data)
    assert payload["model"] == "claude-sonnet-4-6"
    assert payload["messages"][0]["content"] == "hello"


def test_call_anthropic_provider_sends_api_key_header() -> None:
    from src.main import call_anthropic_provider
    body = json.dumps({"content": [{"text": "ok"}]}).encode()
    with patch("src.main.urlopen", return_value=_mock_urlopen(body)) as mock_u, \
         patch("src.main.ANTHROPIC_API_KEY", "sk-ant-test"):
        call_anthropic_provider("hello")
    headers = {k.lower(): v for k, v in mock_u.call_args[0][0].headers.items()}
    assert "x-api-key" in headers


def test_call_anthropic_provider_sends_anthropic_version_header() -> None:
    from src.main import call_anthropic_provider
    body = json.dumps({"content": [{"text": "ok"}]}).encode()
    with patch("src.main.urlopen", return_value=_mock_urlopen(body)) as mock_u, \
         patch("src.main.ANTHROPIC_API_KEY", "sk-ant-test"):
        call_anthropic_provider("hello")
    headers = {k.lower(): v for k, v in mock_u.call_args[0][0].headers.items()}
    assert "anthropic-version" in headers


# ===========================================================================
# call_ai dispatcher
# ===========================================================================
def test_call_ai_dispatches_to_openai() -> None:
    with patch.dict("src.main.PROVIDERS", {"openai": MagicMock(return_value="openai result")}):
        result = call_ai(prompt="Hello", provider="openai")
    assert result == "openai result"


def test_call_ai_dispatches_to_anthropic() -> None:
    with patch.dict("src.main.PROVIDERS", {"anthropic": MagicMock(return_value="anthropic result")}):
        result = call_ai(prompt="Hello", provider="anthropic")
    assert result == "anthropic result"


def test_call_ai_falls_back_to_ollama_for_unknown_provider() -> None:
    with patch("src.main.call_ollama_provider", return_value="ollama fallback") as mock_ollama:
        result = call_ai(prompt="Hello", provider="unknown-provider")
    assert result == "ollama fallback"


# ===========================================================================
# list_roles
# ===========================================================================
def test_list_roles_coding_shows_builder_reviewer_tester(capsys) -> None:
    from src.main import list_roles
    list_roles(mode="coding")
    out = capsys.readouterr().out
    assert "Builder"  in out
    assert "Reviewer" in out
    assert "Tester"   in out


def test_list_roles_writing_shows_writer_editor_qa(capsys) -> None:
    from src.main import list_roles
    list_roles(mode="writing")
    out = capsys.readouterr().out
    assert "Writer" in out
    assert "Editor" in out
    assert "QA"     in out


def test_list_roles_coding_shows_correct_docs(capsys) -> None:
    from src.main import list_roles
    list_roles(mode="coding")
    out = capsys.readouterr().out
    assert "coding-standards.md" in out
    assert "decision-log.md"     in out
    assert "test-strategy.md"    in out


def test_list_roles_writing_shows_correct_docs(capsys) -> None:
    from src.main import list_roles
    list_roles(mode="writing")
    out = capsys.readouterr().out
    assert "style-guide.md"         in out
    assert "editorial-standards.md" in out
    assert "qa-checklist.md"        in out


def test_list_roles_shows_prompt_path(capsys) -> None:
    from src.main import list_roles
    list_roles(mode="coding")
    assert "builder-prompt.md" in capsys.readouterr().out


def test_list_roles_coding_does_not_show_writing_docs(capsys) -> None:
    from src.main import list_roles
    list_roles(mode="coding")
    assert "style-guide.md" not in capsys.readouterr().out


def test_list_roles_writing_does_not_show_coding_docs(capsys) -> None:
    from src.main import list_roles
    list_roles(mode="writing")
    assert "coding-standards.md" not in capsys.readouterr().out


def test_list_roles_shows_mode_in_header(capsys) -> None:
    from src.main import list_roles
    list_roles(mode="coding")
    assert "coding" in capsys.readouterr().out


def test_list_roles_defaults_to_coding(capsys) -> None:
    from src.main import list_roles
    list_roles()
    assert "Builder" in capsys.readouterr().out


def test_parse_args_list_roles_flag() -> None:
    from src.main import parse_args
    with patch("sys.argv", ["main.py", "--list-roles"]):
        assert parse_args().list_roles is True


def test_parse_args_list_roles_default_false() -> None:
    from src.main import parse_args
    with patch("sys.argv", ["main.py"]):
        assert parse_args().list_roles is False


def test_parse_args_list_roles_with_mode_writing() -> None:
    from src.main import parse_args
    with patch("sys.argv", ["main.py", "--list-roles", "--mode", "writing"]):
        args = parse_args()
    assert args.list_roles is True
    assert args.mode == "writing"


# ===========================================================================
# rct_search mode
# ===========================================================================
def test_rct_search_mode_has_three_roles() -> None:
    from src.main import ALL_MODES
    assert len(ALL_MODES["rct_search"]) == 3


def test_rct_search_mode_roles_are_formulator_searcher_validator() -> None:
    from src.main import ALL_MODES
    assert list(ALL_MODES["rct_search"].keys()) == ["Formulator", "Searcher", "Validator"]


def test_choose_role_rct_search_returns_formulator() -> None:
    with patch("builtins.input", return_value="1"):
        role_name, _ = choose_role(mode="rct_search")
    assert role_name == "Formulator"


def test_choose_role_rct_search_returns_searcher() -> None:
    with patch("builtins.input", return_value="2"):
        role_name, _ = choose_role(mode="rct_search")
    assert role_name == "Searcher"


def test_choose_role_rct_search_returns_validator() -> None:
    with patch("builtins.input", return_value="3"):
        role_name, _ = choose_role(mode="rct_search")
    assert role_name == "Validator"


def test_formulator_receives_pico_framework(tmp_path: Path) -> None:
    doc = tmp_path / "pico-framework.md"
    doc.write_text("PICO template content.", encoding="utf-8")
    with patch.dict("src.main.DOC_FILES_BY_ROLE", {"Formulator": [doc]}):
        assert "PICO template content." in build_project_context("Formulator")


def test_searcher_receives_pico_framework_and_database_guide(tmp_path: Path) -> None:
    pico = tmp_path / "pico-framework.md"
    db   = tmp_path / "database-guide.md"
    pico.write_text("PICO", encoding="utf-8")
    db.write_text("PubMed, Cochrane", encoding="utf-8")
    with patch.dict("src.main.DOC_FILES_BY_ROLE", {"Searcher": [pico, db]}):
        ctx = build_project_context("Searcher")
    assert "PICO"             in ctx
    assert "PubMed, Cochrane" in ctx


def test_validator_receives_pico_framework_and_validation_criteria(tmp_path: Path) -> None:
    pico = tmp_path / "pico-framework.md"
    vc   = tmp_path / "validation-criteria.md"
    pico.write_text("PICO", encoding="utf-8")
    vc.write_text("Appraisal checklist", encoding="utf-8")
    with patch.dict("src.main.DOC_FILES_BY_ROLE", {"Validator": [pico, vc]}):
        ctx = build_project_context("Validator")
    assert "PICO"               in ctx
    assert "Appraisal checklist" in ctx


def test_formulator_does_not_receive_database_guide() -> None:
    doc_names = [p.name for p in DOC_FILES_BY_ROLE.get("Formulator", [])]
    assert "database-guide.md" not in doc_names


def test_validator_does_not_receive_database_guide() -> None:
    doc_names = [p.name for p in DOC_FILES_BY_ROLE.get("Validator", [])]
    assert "database-guide.md" not in doc_names


def test_parse_args_mode_rct_search() -> None:
    from src.main import parse_args
    with patch("sys.argv", ["main.py", "--mode", "rct_search"]):
        assert parse_args().mode == "rct_search"


def test_list_roles_rct_search_shows_correct_roles(capsys) -> None:
    from src.main import list_roles
    list_roles(mode="rct_search")
    out = capsys.readouterr().out
    assert "Formulator" in out
    assert "Searcher"   in out
    assert "Validator"  in out


def test_list_roles_rct_search_shows_correct_docs(capsys) -> None:
    from src.main import list_roles
    list_roles(mode="rct_search")
    out = capsys.readouterr().out
    assert "pico-framework.md"    in out
    assert "database-guide.md"    in out
    assert "validation-criteria.md" in out


def test_list_roles_rct_search_does_not_show_coding_docs(capsys) -> None:
    from src.main import list_roles
    list_roles(mode="rct_search")
    assert "coding-standards.md" not in capsys.readouterr().out


def test_main_dry_run_rct_search_mode(tmp_path, monkeypatch) -> None:
    from src.main import main
    inputs = iter(["1", "test RCT search task"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    monkeypatch.setattr("src.main.REPORTS_DIR", tmp_path)
    with patch("src.main.call_ai") as mock_ai:
        try:
            main(dry_run=True, mode="rct_search")
        except StopIteration:
            pass
    mock_ai.assert_not_called()
