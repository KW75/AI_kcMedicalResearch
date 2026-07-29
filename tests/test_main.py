from __future__ import annotations

import json
import urllib.error
import pytest
from urllib.error import HTTPError, URLError
import chromadb
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.main import (
    read_text_file, save_report, build_project_context,
    call_ollama_provider, call_openai_provider, call_anthropic_provider,
    call_deepseek_provider, call_groq_provider, call_qwen_provider,
    call_ai, choose_role, DOC_FILES_BY_ROLE,
    PROVIDERS, parse_args, BASE_DIR,
    start_session_transcript, append_to_transcript, print_session_summary,
    truncate_context, list_sessions, read_session, delete_session,
    export_session, rename_session, show_stats, list_roles,
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

# ---------------------------------------------------------------------------
# DeepSeek provider tests
# ---------------------------------------------------------------------------

def test_call_deepseek_provider_raises_without_key(monkeypatch):
    monkeypatch.setattr("src.main.DEEPSEEK_API_KEY", "")
    with pytest.raises(RuntimeError, match="DEEPSEEK_API_KEY"):
        call_deepseek_provider("hello")


def test_call_deepseek_provider_returns_content(monkeypatch):
    monkeypatch.setattr("src.main.DEEPSEEK_API_KEY", "test-key")
    fake = {"choices": [{"message": {"content": "DeepSeek reply"}}]}
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(fake).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("src.main.urlopen", return_value=mock_resp):
        result = call_deepseek_provider("hello", model="deepseek-v4-flash")
    assert result == "DeepSeek reply"


def test_call_deepseek_provider_http_error(monkeypatch):
    monkeypatch.setattr("src.main.DEEPSEEK_API_KEY", "test-key")
    with patch("src.main.urlopen", side_effect=urllib.error.HTTPError(
            None, 401, "Unauthorized", {}, None)):
        with pytest.raises(RuntimeError, match="DeepSeek HTTP error 401"):
            call_deepseek_provider("hello")


def test_call_deepseek_provider_empty_response(monkeypatch):
    monkeypatch.setattr("src.main.DEEPSEEK_API_KEY", "test-key")
    fake = {"choices": []}
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(fake).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("src.main.urlopen", return_value=mock_resp):
        with pytest.raises(RuntimeError, match="empty response"):
            call_deepseek_provider("hello", model="deepseek-v4-flash")


# ---------------------------------------------------------------------------
# Groq provider tests
# ---------------------------------------------------------------------------

def test_call_groq_provider_raises_without_key(monkeypatch):
    monkeypatch.setattr("src.main.GROQ_API_KEY", "")
    with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
        call_groq_provider("hello")


def test_call_groq_provider_returns_content(monkeypatch):
    monkeypatch.setattr("src.main.GROQ_API_KEY", "test-key")
    fake = {"choices": [{"message": {"content": "Groq reply"}}]}
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(fake).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("src.main.urlopen", return_value=mock_resp):
        result = call_groq_provider("hello", model="llama-3.3-70b-versatile")
    assert result == "Groq reply"


def test_call_groq_provider_http_error(monkeypatch):
    monkeypatch.setattr("src.main.GROQ_API_KEY", "test-key")
    with patch("src.main.urlopen", side_effect=urllib.error.HTTPError(
            None, 429, "Too Many Requests", {}, None)):
        with pytest.raises(RuntimeError, match="Groq HTTP error 429"):
            call_groq_provider("hello")


def test_call_groq_provider_empty_response(monkeypatch):
    monkeypatch.setattr("src.main.GROQ_API_KEY", "test-key")
    fake = {"choices": []}
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(fake).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("src.main.urlopen", return_value=mock_resp):
        with pytest.raises(RuntimeError, match="empty response"):
            call_groq_provider("hello", model="llama-3.3-70b-versatile")


# ---------------------------------------------------------------------------
# Provider registry includes new providers
# ---------------------------------------------------------------------------

def test_providers_dict_contains_deepseek():
    assert "deepseek" in PROVIDERS


def test_providers_dict_contains_groq():
    assert "groq" in PROVIDERS


def test_parse_args_provider_deepseek():
    args = parse_args(["--provider", "deepseek"])
    assert args.provider == "deepseek"


def test_parse_args_provider_groq():
    args = parse_args(["--provider", "groq"])
    assert args.provider == "groq"

# ---------------------------------------------------------------------------
# generate_writing_report tests
# ---------------------------------------------------------------------------

def test_generate_writing_report_no_files(tmp_path):
    from src.main import generate_writing_report
    empty_input = tmp_path / "empty_input"
    empty_input.mkdir()
    result = generate_writing_report(
        docs_dir=tmp_path / "empty",
        reports_dir=tmp_path / "reports",
        input_dir=empty_input,
    )
    assert result.name == "writing_report_empty.md"


def test_generate_writing_report_creates_report(tmp_path, monkeypatch):
    from src.main import generate_writing_report
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "brief.md").write_text("This is the project brief.", encoding="utf-8")

    prompt_dir = tmp_path / "ai"
    prompt_dir.mkdir()
    (prompt_dir / "writing-report-prompt.md").write_text(
        "Summarise the documents.", encoding="utf-8"
    )

    reports = tmp_path / "reports"
    monkeypatch.setattr("src.main.AI_DIR", prompt_dir)

    with patch.dict("src.main.PROVIDERS", {"ollama": lambda p, model=None: "Summary output"}):
        result = generate_writing_report(
            docs_dir=docs,
            reports_dir=reports,
            provider="ollama",
        )

    assert result.exists()
    content = result.read_text(encoding="utf-8")
    assert "Summary output" in content
    assert "Writing Report" in content


def test_generate_writing_report_missing_prompt(tmp_path, monkeypatch):
    from src.main import generate_writing_report
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "brief.md").write_text("content", encoding="utf-8")
    monkeypatch.setattr("src.main.AI_DIR", tmp_path / "no_ai_dir")
    with pytest.raises(FileNotFoundError, match="writing-report-prompt"):
        generate_writing_report(docs_dir=docs, reports_dir=tmp_path / "reports")


# ---------------------------------------------------------------------------
# rct_search_reminder tests
# ---------------------------------------------------------------------------

def test_rct_search_reminder_proceeds_on_y(monkeypatch, capsys):
    from src.main import rct_search_reminder
    monkeypatch.setattr("builtins.input", lambda _: "y")
    rct_search_reminder()   # should not raise or exit
    out = capsys.readouterr().out
    assert "PICO" in out


def test_rct_search_reminder_exits_on_n(monkeypatch):
    from src.main import rct_search_reminder
    monkeypatch.setattr("builtins.input", lambda _: "n")
    with pytest.raises(SystemExit):
        rct_search_reminder()


# ---------------------------------------------------------------------------
# appraisal mode tests
# ---------------------------------------------------------------------------

def test_appraisal_mode_in_all_modes():
    from src.main import ALL_MODES
    assert "appraisal" in ALL_MODES


def test_appraisal_mode_has_appraiser_role():
    from src.main import ALL_MODES
    assert "Appraiser" in ALL_MODES["appraisal"]


def test_parse_args_mode_appraisal():
    args = parse_args(["--mode", "appraisal"])
    assert args.mode == "appraisal"


def test_parse_args_report_flag():
    args = parse_args(["--mode", "writing", "--report"])
    assert args.report is True


def test_parse_args_report_default_false():
    args = parse_args([])
    assert args.report is False




def test_generate_writing_report_missing_prompt(tmp_path, monkeypatch):
    from src.main import generate_writing_report
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "brief.md").write_text("content", encoding="utf-8")
    monkeypatch.setattr("src.main.AI_DIR", tmp_path / "no_ai_dir")
    with pytest.raises(FileNotFoundError, match="writing-report-prompt"):
        generate_writing_report(docs_dir=docs, reports_dir=tmp_path / "reports")


# ---------------------------------------------------------------------------
# rct_search_reminder tests
# ---------------------------------------------------------------------------

def test_rct_search_reminder_proceeds_on_y(monkeypatch, capsys):
    from src.main import rct_search_reminder
    monkeypatch.setattr("builtins.input", lambda _: "y")
    rct_search_reminder()
    out = capsys.readouterr().out
    assert "PICO" in out


def test_rct_search_reminder_exits_on_n(monkeypatch):
    from src.main import rct_search_reminder
    monkeypatch.setattr("builtins.input", lambda _: "n")
    with pytest.raises(SystemExit):
        rct_search_reminder()




def test_generate_writing_report_missing_prompt(tmp_path, monkeypatch):
    from src.main import generate_writing_report
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "brief.md").write_text("content", encoding="utf-8")
    monkeypatch.setattr("src.main.AI_DIR", tmp_path / "no_ai_dir")
    with pytest.raises(FileNotFoundError, match="writing-report-prompt"):
        generate_writing_report(docs_dir=docs, reports_dir=tmp_path / "reports")

# ---------------------------------------------------------------------------
# appraisal mode full role set tests
# ---------------------------------------------------------------------------

def test_appraisal_mode_has_methodologist_role():
    from src.main import ALL_MODES
    assert "Methodologist" in ALL_MODES["appraisal"]


def test_appraisal_mode_has_summariser_role():
    from src.main import ALL_MODES
    assert "Summariser" in ALL_MODES["appraisal"]


def test_appraisal_mode_has_three_roles():
    from src.main import ALL_MODES
    assert len(ALL_MODES["appraisal"]) == 3


def test_appraiser_in_doc_files_by_role():
    assert "Appraiser" in DOC_FILES_BY_ROLE


def test_methodologist_in_doc_files_by_role():
    assert "Methodologist" in DOC_FILES_BY_ROLE


def test_summariser_in_doc_files_by_role():
    assert "Summariser" in DOC_FILES_BY_ROLE


def test_appraiser_colour_defined():
    from src.main import COLOURS
    assert "Appraiser" in COLOURS


def test_methodologist_colour_defined():
    from src.main import COLOURS
    assert "Methodologist" in COLOURS


def test_summariser_colour_defined():
    from src.main import COLOURS
    assert "Summariser" in COLOURS


def test_list_roles_appraisal_shows_all_three(capsys):
    list_roles(mode="appraisal")
    out = capsys.readouterr().out
    assert "Appraiser" in out
    assert "Methodologist" in out
    assert "Summariser" in out


# ---------------------------------------------------------------------------
# rag.py code file extension tests
# ---------------------------------------------------------------------------



def test_rag_indexes_python_file(tmp_path):
    from src import rag
    import chromadb as _chromadb
    client = _chromadb.Client()
    rag.set_client(client)

    upload_dir = tmp_path / "uploads" / "coding"
    upload_dir.mkdir(parents=True)
    (upload_dir / "example.py").write_text(
        "def hello():\n    return 'world'\n" * 20,
        encoding="utf-8",
    )

    def fake_embeddings(texts):
        return [[0.1] * 5 for _ in texts]

    with patch.object(rag, "get_embeddings", side_effect=fake_embeddings):
        count = rag.index_uploads(
            mode="coding",
            session_id="testpyfile",
            upload_base=str(tmp_path / "uploads"),
        )
    assert count > 0


def test_rag_indexes_json_file(tmp_path):
    from src import rag
    import chromadb as _chromadb
    client = _chromadb.Client()
    rag.set_client(client)

    upload_dir = tmp_path / "uploads" / "coding"
    upload_dir.mkdir(parents=True)
    (upload_dir / "config.json").write_text(
        '{"key": "value", "items": [1, 2, 3]}' * 30,
        encoding="utf-8",
    )

    def fake_embeddings(texts):
        return [[0.1] * 5 for _ in texts]

    with patch.object(rag, "get_embeddings", side_effect=fake_embeddings):
        count = rag.index_uploads(
            mode="coding",
            session_id="testjsonfile",
            upload_base=str(tmp_path / "uploads"),
        )
    assert count > 0

# ---------------------------------------------------------------------------
# URL fetching tests (rag.py)
# ---------------------------------------------------------------------------

def test_extract_urls_finds_bare_urls():
    from src.rag import _extract_urls
    text = "Some text\nhttps://pubmed.ncbi.nlm.nih.gov/12345\nmore text"
    urls = _extract_urls(text)
    assert urls == ["https://pubmed.ncbi.nlm.nih.gov/12345"]


def test_extract_urls_ignores_inline_urls():
    from src.rag import _extract_urls
    text = "See https://example.com for details"
    urls = _extract_urls(text)
    assert urls == []


def test_extract_urls_empty_text():
    from src.rag import _extract_urls
    assert _extract_urls("") == []


def test_fetch_url_returns_empty_on_error():
    from src.rag import _fetch_url
    with patch("urllib.request.urlopen", side_effect=Exception("network error")):
        result = _fetch_url("https://example.com")
    assert result == ""


def test_fetch_url_strips_html_tags():
    from src.rag import _fetch_url
    html_bytes = b"<html><body><p>Hello world</p></body></html>"
    mock_resp = MagicMock()
    mock_resp.read.return_value = html_bytes
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = _fetch_url("https://example.com")
    assert "Hello world" in result
    assert "<p>" not in result


def test_index_uploads_fetches_urls_in_txt_file(tmp_path):
    from src import rag
    import chromadb as _chromadb
    client = _chromadb.Client()
    rag.set_client(client)

    upload_dir = tmp_path / "uploads" / "appraisal"
    upload_dir.mkdir(parents=True)
    (upload_dir / "links.txt").write_text(
        "https://pubmed.ncbi.nlm.nih.gov/12345\n",
        encoding="utf-8",
    )

    def fake_embeddings(texts):
        return [[0.1] * 5 for _ in texts]

    with patch.object(rag, "_fetch_url", return_value="Fetched article content " * 20), \
         patch.object(rag, "get_embeddings", side_effect=fake_embeddings):
        count = rag.index_uploads(
            mode="appraisal",
            session_id="testurlfile",
            upload_base=str(tmp_path / "uploads"),
        )
    assert count > 0


# ---------------------------------------------------------------------------
# save_rct_search_links tests
# ---------------------------------------------------------------------------

def test_save_rct_search_links_creates_file(tmp_path):
    from src.main import save_rct_search_links
    response = "Search here: https://pubmed.ncbi.nlm.nih.gov/search?term=rct"
    result = save_rct_search_links(response=response, reports_dir=tmp_path)
    assert result.exists()
    content = result.read_text(encoding="utf-8")
    assert "pubmed" in content
    assert "RCT Search Links" in content


def test_save_rct_search_links_no_urls(tmp_path):
    from src.main import save_rct_search_links
    response = "No links in this response."
    result = save_rct_search_links(response=response, reports_dir=tmp_path)
    assert result.exists()
    content = result.read_text(encoding="utf-8")
    assert "No URLs found" in content


def test_save_rct_search_links_cleans_trailing_punctuation(tmp_path):
    from src.main import save_rct_search_links
    response = "See https://example.com/search?q=rct, for details."
    result = save_rct_search_links(response=response, reports_dir=tmp_path)
    content = result.read_text(encoding="utf-8")
    assert "example.com/search?q=rct" in content
    assert content.count("example.com/search?q=rct,") == 0

# ---------------------------------------------------------------------------
# fetch_pubmed_articles tests
# ---------------------------------------------------------------------------

def test_fetch_pubmed_returns_empty_on_network_error():
    from src.main import fetch_pubmed_articles
    with patch("src.main.urlopen", side_effect=Exception("network error")):
        result = fetch_pubmed_articles("hypertension")
    assert result == []


def test_fetch_pubmed_returns_empty_when_no_ids():
    from src.main import fetch_pubmed_articles
    search_response = json.dumps(
        {"esearchresult": {"idlist": []}}
    ).encode()
    mock_resp = MagicMock()
    mock_resp.read.return_value = search_response
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("src.main.urlopen", return_value=mock_resp):
        result = fetch_pubmed_articles("xyznotamedicalterm")
    assert result == []


def test_fetch_pubmed_parses_xml_correctly():
    from src.main import fetch_pubmed_articles
    search_json = json.dumps(
        {"esearchresult": {"idlist": ["12345678"]}}
    ).encode()
    xml_response = b"""<?xml version="1.0"?>
    <PubmedArticleSet>
      <PubmedArticle>
        <MedlineCitation>
          <PMID>12345678</PMID>
          <Article>
            <ArticleTitle>Test Article Title</ArticleTitle>
            <Abstract>
              <AbstractText>This is the abstract text.</AbstractText>
            </Abstract>
          </Article>
        </MedlineCitation>
      </PubmedArticle>
    </PubmedArticleSet>"""

    call_count = 0
    def mock_urlopen(url, timeout=None):
        nonlocal call_count
        mock_resp = MagicMock()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        if call_count == 0:
            mock_resp.read.return_value = search_json
        else:
            mock_resp.read.return_value = xml_response
        call_count += 1
        return mock_resp

    with patch("src.main.urlopen", side_effect=mock_urlopen):
        result = fetch_pubmed_articles("test query")

    assert len(result) == 1
    assert result[0]["pmid"] == "12345678"
    assert result[0]["title"] == "Test Article Title"
    assert result[0]["abstract"] == "This is the abstract text."
    assert result[0]["url"] == "https://pubmed.ncbi.nlm.nih.gov/12345678/"


# ---------------------------------------------------------------------------
# run_search_mode tests
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="run_search_mode removed — superseded by handle_search_mode")
def test_run_search_mode_dry_run_creates_report(tmp_path, monkeypatch):
    from src import main as m
    from pathlib import Path
    ai_dir = tmp_path / "ai"
    ai_dir.mkdir()
    (ai_dir / "researcher-prompt.md").write_text("You are a researcher.", encoding="utf-8")
    monkeypatch.setattr(m, "BASE_DIR", tmp_path)
    monkeypatch.setattr(m, "fetch_pubmed_articles", lambda q, max_results=10: [{
        "pmid": "99999",
        "title": "Heart failure study",
        "abstract": "Abstract text.",
        "url": "https://pubmed.ncbi.nlm.nih.gov/99999/",
    }])
    responses = iter(["2", "heart failure treatment"])
    monkeypatch.setattr("builtins.input", lambda _: next(responses))
    md_path = m.run_search_mode(dry_run=True, ai_dir=ai_dir, reports_dir=tmp_path)
    assert md_path.exists()
    assert md_path.stat().st_size > 0


@pytest.mark.skip(reason="run_search_mode removed — superseded by handle_search_mode")
def test_run_search_mode_empty_topic_exits(tmp_path, monkeypatch):
    from src import main as m
    monkeypatch.setattr(m, "BASE_DIR", tmp_path)
    responses = iter(["1", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(responses))
    with pytest.raises(SystemExit):
        m.run_search_mode(dry_run=True)


@pytest.mark.skip(reason="run_search_mode removed — superseded by handle_search_mode")
def test_run_search_mode_no_articles_exits(monkeypatch, tmp_path):
    from src import main as m
    monkeypatch.setattr(m, "BASE_DIR", tmp_path)
    monkeypatch.setattr(m, "REPORTS_DIR", tmp_path)
    monkeypatch.setattr(m, "AI_DIR", Path("ai"))
    responses = iter(["2", "xyznotreal"])
    monkeypatch.setattr("builtins.input", lambda _: next(responses))
    monkeypatch.setattr(m, "fetch_pubmed_articles", lambda q, max_results=10: [])
    with pytest.raises(SystemExit):
        m.run_search_mode(dry_run=False)


# ---------------------------------------------------------------------------
# search mode registration tests
# ---------------------------------------------------------------------------

def test_search_mode_in_all_modes():
    from src.main import ALL_MODES
    assert "search" in ALL_MODES


def test_search_mode_has_researcher_role():
    from src.main import ALL_MODES
    assert "Researcher" in ALL_MODES["search"]


def test_researcher_in_doc_files_by_role():
    assert "Researcher" in DOC_FILES_BY_ROLE


def test_parse_args_mode_search():
    args = parse_args(["--mode", "search"])
    assert args.mode == "search"


def test_researcher_colour_defined():
    from src.main import COLOURS
    assert "Researcher" in COLOURS

# ---------------------------------------------------------------------------
# generate_code_revision tests
# ---------------------------------------------------------------------------

def test_read_code_files_returns_empty_for_missing_dir(tmp_path):
    from src.main import _read_code_files
    result = _read_code_files(tmp_path / "nonexistent")
    assert result == []


def test_read_code_files_ignores_guidance_docs(tmp_path):
    from src.main import _read_code_files
    (tmp_path / "PRD.md").write_text("Product requirements", encoding="utf-8")
    (tmp_path / "architecture.md").write_text("Architecture", encoding="utf-8")
    result = _read_code_files(tmp_path)
    assert result == []


def test_read_code_files_reads_py_files(tmp_path):
    from src.main import _read_code_files
    (tmp_path / "example.py").write_text("def hello(): pass", encoding="utf-8")
    result = _read_code_files(tmp_path)
    assert len(result) == 1
    assert result[0]["name"] == "example.py"
    assert "hello" in result[0]["content"]


def test_read_code_files_reads_multiple_extensions(tmp_path):
    from src.main import _read_code_files
    (tmp_path / "app.py").write_text("x = 1", encoding="utf-8")
    (tmp_path / "style.css").write_text("body {}", encoding="utf-8")
    (tmp_path / "query.sql").write_text("SELECT 1", encoding="utf-8")
    result = _read_code_files(tmp_path)
    names = [r["name"] for r in result]
    assert "app.py" in names
    assert "style.css" in names
    assert "query.sql" in names


def test_read_code_files_skips_empty_files(tmp_path):
    from src.main import _read_code_files
    (tmp_path / "empty.py").write_text("   ", encoding="utf-8")
    result = _read_code_files(tmp_path)
    assert result == []


def test_generate_code_revision_no_files_returns_empty(tmp_path):
    from src.main import generate_code_revision
    result = generate_code_revision(
        docs_dir=tmp_path / "empty",
        reports_dir=tmp_path,
        dry_run=True,
    )
    assert result.name == "code_revision_empty.md"


def test_generate_code_revision_builder_pipeline_dry_run(tmp_path, monkeypatch):
    from src.main import generate_code_revision
    docs = tmp_path / "coding"
    docs.mkdir()
    (docs / "app.py").write_text("def add(a, b): return a + b", encoding="utf-8")
    monkeypatch.setattr("builtins.input", lambda _: "improve readability")
    result = generate_code_revision(
        start_role="Builder",
        docs_dir=docs,
        reports_dir=tmp_path,
        dry_run=True,
    )
    assert result.exists()
    content = result.read_text(encoding="utf-8")
    assert "Builder Output" in content
    assert "Reviewer Output" in content
    assert "Tester Output" in content


def test_generate_code_revision_reviewer_pipeline_dry_run(tmp_path, monkeypatch):
    from src.main import generate_code_revision
    docs = tmp_path / "coding"
    docs.mkdir()
    (docs / "app.py").write_text("def add(a, b): return a + b", encoding="utf-8")
    monkeypatch.setattr("builtins.input", lambda _: "")
    result = generate_code_revision(
        start_role="Reviewer",
        docs_dir=docs,
        reports_dir=tmp_path,
        dry_run=True,
    )
    assert result.exists()
    content = result.read_text(encoding="utf-8")
    assert "Builder Output" not in content
    assert "Reviewer Output" in content
    assert "Tester Output" in content


def test_generate_code_revision_tester_only_dry_run(tmp_path, monkeypatch):
    from src.main import generate_code_revision
    docs = tmp_path / "coding"
    docs.mkdir()
    (docs / "app.py").write_text("def add(a, b): return a + b", encoding="utf-8")
    monkeypatch.setattr("builtins.input", lambda _: "")
    result = generate_code_revision(
        start_role="Tester",
        docs_dir=docs,
        reports_dir=tmp_path,
        dry_run=True,
    )
    assert result.exists()
    content = result.read_text(encoding="utf-8")
    assert "Builder Output" not in content
    assert "Reviewer Output" not in content
    assert "Tester Output" in content


def test_generate_code_revision_creates_docx(tmp_path, monkeypatch):
    from src.main import generate_code_revision
    docs = tmp_path / "coding"
    docs.mkdir()
    (docs / "app.py").write_text("def add(a, b): return a + b", encoding="utf-8")
    monkeypatch.setattr("builtins.input", lambda _: "refactor")
    generate_code_revision(
        start_role="Tester",
        docs_dir=docs,
        reports_dir=tmp_path,
        dry_run=True,
    )
    docx_files = list(tmp_path.glob("code_revision_*.docx"))
    assert len(docx_files) == 1
    assert docx_files[0].stat().st_size > 0


def test_parse_args_revise_flag():
    args = parse_args(["--mode", "coding", "--revise"])
    assert args.revise is True
    assert args.role == "Builder"


def test_parse_args_role_reviewer():
    args = parse_args(["--mode", "coding", "--revise", "--role", "Reviewer"])
    assert args.role == "Reviewer"


def test_parse_args_role_tester():
    args = parse_args(["--mode", "coding", "--revise", "--role", "Tester"])
    assert args.role == "Tester"

# ---------------------------------------------------------------------------
# run_rct_search_pipeline tests
# ---------------------------------------------------------------------------

def test_rct_pipeline_empty_topic_exits(monkeypatch):
    from src.main import run_rct_search_pipeline
    monkeypatch.setattr("builtins.input", lambda _: "")
    with pytest.raises(SystemExit):
        run_rct_search_pipeline(dry_run=True)


def test_rct_pipeline_creates_md_report(tmp_path, monkeypatch):
    from src.main import run_rct_search_pipeline
    monkeypatch.setattr("builtins.input", lambda _: "metformin in type 2 diabetes")
    result = run_rct_search_pipeline(
        reports_dir=tmp_path,
        dry_run=True,
    )
    assert result.exists()
    assert result.suffix == ".md"


def test_rct_pipeline_report_contains_topic(tmp_path, monkeypatch):
    from src.main import run_rct_search_pipeline
    monkeypatch.setattr("builtins.input", lambda _: "metformin in type 2 diabetes")
    result = run_rct_search_pipeline(
        reports_dir=tmp_path,
        dry_run=True,
    )
    content = result.read_text(encoding="utf-8")
    assert "metformin in type 2 diabetes" in content


def test_rct_pipeline_report_contains_all_stages(tmp_path, monkeypatch):
    from src.main import run_rct_search_pipeline
    monkeypatch.setattr("builtins.input", lambda _: "aspirin for stroke prevention")
    result = run_rct_search_pipeline(
        reports_dir=tmp_path,
        dry_run=True,
    )
    content = result.read_text(encoding="utf-8")
    assert "Formulator Output" in content
    assert "Searcher Output" in content
    assert "Validator Output" in content


def test_rct_pipeline_report_contains_final_status(tmp_path, monkeypatch):
    from src.main import run_rct_search_pipeline
    monkeypatch.setattr("builtins.input", lambda _: "beta blockers in heart failure")
    result = run_rct_search_pipeline(
        reports_dir=tmp_path,
        dry_run=True,
    )
    content = result.read_text(encoding="utf-8")
    assert "Final Status" in content


def test_rct_pipeline_report_contains_next_steps(tmp_path, monkeypatch):
    from src.main import run_rct_search_pipeline
    monkeypatch.setattr("builtins.input", lambda _: "beta blockers in heart failure")
    result = run_rct_search_pipeline(
        reports_dir=tmp_path,
        dry_run=True,
    )
    content = result.read_text(encoding="utf-8")
    assert "Next Steps" in content
    assert "appraisal" in content


def test_rct_pipeline_creates_docx(tmp_path, monkeypatch):
    from src.main import run_rct_search_pipeline
    monkeypatch.setattr("builtins.input", lambda _: "statins in cardiovascular disease")
    run_rct_search_pipeline(
        reports_dir=tmp_path,
        dry_run=True,
    )
    docx_files = list(tmp_path.glob("rct_search_*.docx"))
    assert len(docx_files) == 1
    assert docx_files[0].stat().st_size > 0


def test_rct_pipeline_report_has_no_appraisal_content(tmp_path, monkeypatch):
    from src.main import run_rct_search_pipeline
    monkeypatch.setattr("builtins.input", lambda _: "insulin therapy in type 1 diabetes")
    result = run_rct_search_pipeline(
        reports_dir=tmp_path,
        dry_run=True,
    )
    content = result.read_text(encoding="utf-8")
    assert "Appraiser Output" not in content
    assert "Methodologist Output" not in content
    assert "Summariser Output" not in content


def test_rct_pipeline_in_parse_args(monkeypatch):
    args = parse_args(["--mode", "rct_search"])
    assert args.mode == "rct_search"

# ── Step 71 tests ──────────────────────────────────────────────────────────

def test_read_topic_file_missing(tmp_path):
    from src.main import _read_topic_file
    assert _read_topic_file(tmp_path / "missing.md") == ""

def test_read_topic_file_reads_content(tmp_path):
    from src.main import _read_topic_file
    f = tmp_path / "topic.md"
    f.write_text("metformin diabetes RCT", encoding="utf-8")
    assert _read_topic_file(f) == "metformin diabetes RCT"

def test_read_topic_file_strips_whitespace(tmp_path):
    from src.main import _read_topic_file
    f = tmp_path / "topic.md"
    f.write_text("  my topic  \n", encoding="utf-8")
    assert _read_topic_file(f) == "my topic"

def test_read_article_files_missing_dir(tmp_path):
    from src.main import _read_article_files
    result = _read_article_files(tmp_path / "nonexistent")
    assert result == []

def test_read_article_files_reads_txt(tmp_path):
    from src.main import _read_article_files
    f = tmp_path / "article.txt"
    f.write_text("A" * 100, encoding="utf-8")
    result = _read_article_files(tmp_path)
    assert len(result) == 1
    assert result[0]["name"] == "article.txt"

def test_read_article_files_skips_large_file(tmp_path):
    from src.main import _read_article_files
    f = tmp_path / "big.txt"
    f.write_text("A" * 9000, encoding="utf-8")
    result = _read_article_files(tmp_path)
    assert result == []

def test_read_article_files_skips_unsupported_extension(tmp_path):
    from src.main import _read_article_files
    f = tmp_path / "data.csv"
    f.write_text("col1,col2", encoding="utf-8")
    result = _read_article_files(tmp_path)
    assert result == []

def test_read_article_files_skips_empty_file(tmp_path):
    from src.main import _read_article_files
    f = tmp_path / "empty.txt"
    f.write_text("", encoding="utf-8")
    result = _read_article_files(tmp_path)
    assert result == []

def test_rct_search_uses_topic_file(tmp_path, monkeypatch):
    from src import main as m
    topic_file = tmp_path / "topic.md"
    topic_file.write_text("metformin diabetes", encoding="utf-8")
    monkeypatch.setattr(m, "DOCS_RCT_SEARCH", tmp_path)
    monkeypatch.setattr(m, "REPORTS_DIR", tmp_path)
    monkeypatch.setattr(m, "fetch_pubmed_articles", lambda q, max_results=10: [])
    monkeypatch.setattr(m, "call_ai", lambda **kw: "[DRY RUN]")
    monkeypatch.setattr("builtins.input", lambda _: "y")
    result = m.run_rct_search_pipeline(provider="ollama", dry_run=True, reports_dir=tmp_path)
    content = Path(result).read_text(encoding="utf-8")
    assert "metformin diabetes" in content

@pytest.mark.skip(reason="run_search_mode removed")
def test_search_uses_topic_file(tmp_path, monkeypatch):
    from src import main as m
    ai_dir = tmp_path / "ai"
    ai_dir.mkdir()
    (ai_dir / "researcher-prompt.md").write_text("You are a researcher.", encoding="utf-8")
    search_dir = tmp_path / "docs" / "search"
    search_dir.mkdir(parents=True)
    (search_dir / "topic.md").write_text("topic\nheart failure", encoding="utf-8")
    monkeypatch.setattr(m, "BASE_DIR", tmp_path)
    result = m.run_search_mode(provider="ollama", dry_run=True, ai_dir=ai_dir, reports_dir=tmp_path)
    content_text = Path(result).read_text(encoding="utf-8")
    assert "heart failure" in content_text
    assert "Clinical Topic" in content_text


# ---------------------------------------------------------------------------
# Tests for validate_api_keys
# ---------------------------------------------------------------------------
class TestValidateApiKeys:

    def test_ollama_requires_no_key(self):
        from src.main import validate_api_keys
        validate_api_keys("ollama")  # should not raise

    def test_anthropic_passes_when_key_present(self):
        import os
        from src.main import validate_api_keys
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test"}):
            validate_api_keys("anthropic")

    def test_openai_passes_when_key_present(self):
        import os
        from src.main import validate_api_keys
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
            validate_api_keys("openai")

    def test_deepseek_passes_when_key_present(self):
        import os
        from src.main import validate_api_keys
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "sk-test"}):
            validate_api_keys("deepseek")

    def test_groq_passes_when_key_present(self):
        import os
        from src.main import validate_api_keys
        with patch.dict(os.environ, {"GROQ_API_KEY": "gsk-test"}):
            validate_api_keys("groq")

    def test_missing_key_raises_environment_error(self):
        import os
        from src.main import validate_api_keys
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            with pytest.raises(EnvironmentError, match="ANTHROPIC_API_KEY"):
                validate_api_keys("anthropic")

    def test_empty_string_key_raises_environment_error(self):
        import os
        from src.main import validate_api_keys
        with patch.dict(os.environ, {"OPENAI_API_KEY": "   "}):
            with pytest.raises(EnvironmentError, match="OPENAI_API_KEY"):
                validate_api_keys("openai")

    def test_unknown_provider_raises_value_error(self):
        from src.main import validate_api_keys
        with pytest.raises(ValueError, match="Unknown provider"):
            validate_api_keys("unknown_provider")

# ---------------------------------------------------------------------------
# Tests for interactive input() paths (Gap 83)
# ---------------------------------------------------------------------------
class TestInteractiveInputPaths:

    # run_search_mode — interactive search type selection
    @pytest.mark.skip(reason="run_search_mode removed — superseded by handle_search_mode")
    def test_search_mode_interactive_paper_search(self, tmp_path):
        """run_search_mode: interactive path, type=1 (paper search)."""
        from src.main import run_search_mode
        with patch("src.main._read_topic_file", return_value=""), \
             patch("builtins.input", side_effect=["1", "metformin diabetes"]), \
             patch("src.main.fetch_pubmed_articles", return_value=[{
                 "pmid": "11111",
                 "title": "Metformin paper",
                 "abstract": "Abstract text.",
                 "url": "https://pubmed.ncbi.nlm.nih.gov/11111/",
             }]):
            md_path = run_search_mode(
                provider="ollama",
                dry_run=True,
                reports_dir=tmp_path,
            )
        assert md_path.exists()
        content = md_path.read_text(encoding="utf-8")
        assert "metformin" in content.lower()

    @pytest.mark.skip(reason="run_search_mode removed — superseded by handle_search_mode")
    def test_search_mode_interactive_clinical_topic(self, tmp_path):
        """run_search_mode: interactive path, type=2 (clinical topic)."""
        from src.main import run_search_mode
        with patch("src.main._read_topic_file", return_value=""), \
             patch("builtins.input", side_effect=["2", "hypertension treatment"]), \
             patch("src.main.fetch_pubmed_articles", return_value=[{
                 "pmid": "22222",
                 "title": "Hypertension study",
                 "abstract": "Abstract text.",
                 "url": "https://pubmed.ncbi.nlm.nih.gov/22222/",
             }]):
            md_path = run_search_mode(
                provider="ollama",
                dry_run=True,
                reports_dir=tmp_path,
            )
        assert md_path.exists()
        content = md_path.read_text(encoding="utf-8")
        assert "hypertension" in content.lower()

    @pytest.mark.skip(reason="run_search_mode removed — superseded by handle_search_mode")
    def test_search_mode_invalid_then_valid_type(self, tmp_path):
        """run_search_mode: invalid input retries until valid."""
        from src.main import run_search_mode
        with patch("src.main._read_topic_file", return_value=""), \
             patch("builtins.input", side_effect=["9", "x", "2", "diabetes"]), \
             patch("src.main.fetch_pubmed_articles", return_value=[{
                 "pmid": "33333",
                 "title": "Diabetes study",
                 "abstract": "Abstract text.",
                 "url": "https://pubmed.ncbi.nlm.nih.gov/33333/",
             }]):
            md_path = run_search_mode(
                provider="ollama",
                dry_run=True,
                reports_dir=tmp_path,
            )
        assert md_path.exists()

    # generate_code_revision — task input
    def test_code_revision_interactive_task_input(self, tmp_path):
        """generate_code_revision: task entered interactively."""
        from src.main import generate_code_revision
        coding_dir = tmp_path / "coding"
        coding_dir.mkdir()
        (coding_dir / "example.py").write_text(
            "def add(a, b):\n    return a + b\n",
            encoding="utf-8",
        )
        with patch("builtins.input", return_value="Check for bugs"):
            md_path = generate_code_revision(
                start_role="Tester",
                docs_dir=coding_dir,
                reports_dir=tmp_path,
                provider="ollama",
                dry_run=True,
            )
        assert md_path.exists()
        content = md_path.read_text(encoding="utf-8")
        assert "Check for bugs" in content

    def test_code_revision_empty_task_uses_default(self, tmp_path):
        """generate_code_revision: empty task input falls back to default."""
        from src.main import generate_code_revision
        coding_dir = tmp_path / "coding"
        coding_dir.mkdir()
        (coding_dir / "example.py").write_text(
            "def subtract(a, b):\n    return a - b\n",
            encoding="utf-8",
        )
        with patch("builtins.input", return_value=""):
            md_path = generate_code_revision(
                start_role="Tester",
                docs_dir=coding_dir,
                reports_dir=tmp_path,
                provider="ollama",
                dry_run=True,
            )
        assert md_path.exists()
        content = md_path.read_text(encoding="utf-8")
        assert "Review and improve" in content

    # rct_search — interactive topic input
    def test_rct_search_interactive_topic_input(self, tmp_path):
        """run_rct_search_pipeline: topic entered interactively when no file."""
        from src.main import run_rct_search_pipeline
        with patch("src.main._read_topic_file", return_value=""), \
             patch("builtins.input", return_value="aspirin and cardiovascular disease"):
            md_path = run_rct_search_pipeline(
                provider="ollama",
                reports_dir=tmp_path,
                dry_run=True,
            )
        assert md_path.exists()
        content = md_path.read_text(encoding="utf-8")
        assert "aspirin" in content.lower()

    # delete_session — input() confirmation paths already covered,
    # but test the y/n boundary explicitly
    def test_delete_session_confirms_y(self, tmp_path):
        """delete_session: 'y' confirmation deletes the file."""
        from src.main import delete_session
        f = tmp_path / "session_del.md"
        f.write_text("content", encoding="utf-8")
        with patch("builtins.input", return_value="y"):
            delete_session(filename="session_del.md", reports_dir=str(tmp_path))
        assert not f.exists()

    def test_delete_session_confirms_uppercase_n(self, tmp_path):
        """delete_session: 'N' cancels deletion."""
        from src.main import delete_session
        f = tmp_path / "session_keep.md"
        f.write_text("content", encoding="utf-8")
        with patch("builtins.input", return_value="N"):
            delete_session(filename="session_keep.md", reports_dir=str(tmp_path))
        assert f.exists()

    # rename_session — new name input
    def test_rename_session_interactive_new_name(self, tmp_path):
        """rename_session: new name entered interactively."""
        from src.main import rename_session
        f = tmp_path / "session_old.md"
        f.write_text("content", encoding="utf-8")
        with patch("builtins.input", return_value="session_new"):
            rename_session(filename="session_old.md", reports_dir=str(tmp_path))
        assert (tmp_path / "session_new.md").exists()
        assert not f.exists()

        # ---------------------------------------------------------------------------
# Qwen provider tests
# ---------------------------------------------------------------------------

def test_call_qwen_provider_raises_without_key(monkeypatch):
    monkeypatch.setattr("src.main.DASHSCOPE_API_KEY", "")
    with pytest.raises(RuntimeError, match="DASHSCOPE_API_KEY"):
        call_qwen_provider("hello")


def test_call_qwen_provider_returns_content(monkeypatch):
    monkeypatch.setattr("src.main.DASHSCOPE_API_KEY", "test-key")
    fake = {"choices": [{"message": {"content": "Qwen reply"}}]}
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(fake).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("src.main.urlopen", return_value=mock_resp):
        result = call_qwen_provider("hello", model="qwen3.7-plus")
    assert result == "Qwen reply"


def test_call_qwen_provider_http_error(monkeypatch):
    monkeypatch.setattr("src.main.DASHSCOPE_API_KEY", "test-key")
    with patch("src.main.urlopen", side_effect=urllib.error.HTTPError(
            None, 403, "Forbidden", {}, None)):
        with pytest.raises(RuntimeError, match="Qwen HTTP error 403"):
            call_qwen_provider("hello")


def test_call_qwen_provider_empty_response(monkeypatch):
    monkeypatch.setattr("src.main.DASHSCOPE_API_KEY", "test-key")
    fake = {"choices": []}
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(fake).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("src.main.urlopen", return_value=mock_resp):
        with pytest.raises(RuntimeError, match="empty response"):
            call_qwen_provider("hello", model="qwen3.7-plus")


def test_call_qwen_provider_url_error(monkeypatch):
    monkeypatch.setattr("src.main.DASHSCOPE_API_KEY", "test-key")
    with patch("src.main.urlopen", side_effect=urllib.error.URLError("timeout")):
        with pytest.raises(RuntimeError, match="Qwen connection error"):
            call_qwen_provider("hello")


# ---------------------------------------------------------------------------
# Provider registry and arg parsing — Qwen
# ---------------------------------------------------------------------------

def test_providers_dict_contains_qwen():
    assert "qwen" in PROVIDERS


def test_parse_args_provider_qwen():
    args = parse_args(["--provider", "qwen"])
    assert args.provider == "qwen"


def test_validate_api_keys_qwen_passes(monkeypatch):
    from src.main import validate_api_keys
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-test-qwen-key")
    validate_api_keys("qwen")   # should not raise


def test_validate_api_keys_qwen_missing_raises():
    from src.main import validate_api_keys
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(EnvironmentError, match="DASHSCOPE_API_KEY"):
            validate_api_keys("qwen")
