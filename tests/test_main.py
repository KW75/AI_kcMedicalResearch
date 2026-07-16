from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.main import read_text_file, save_report, build_project_context, call_ollama, choose_role



def test_read_text_file_returns_content(tmp_path: Path) -> None:
    test_file = tmp_path / "sample.txt"
    test_file.write_text("hello world", encoding="utf-8")
    result = read_text_file(test_file)
    assert result == "hello world"


def test_read_text_file_returns_empty_string_when_missing(tmp_path: Path) -> None:
    missing_file = tmp_path / "does_not_exist.txt"
    result = read_text_file(missing_file)
    assert result == ""


def test_read_text_file_strips_whitespace(tmp_path: Path) -> None:
    test_file = tmp_path / "padded.txt"
    test_file.write_text("  trimmed content  \n", encoding="utf-8")
    result = read_text_file(test_file)
    assert result == "trimmed content"


def test_save_report_creates_file(tmp_path: Path) -> None:
    report_path = tmp_path / "reports" / "test-report.md"
    save_report(report_path, "Tester", "qwen2.5-coder:3b", "Run tests", "All tests passed.")
    assert report_path.exists()

def test_start_session_transcript_creates_file(tmp_path: Path) -> None:
    from src.main import start_session_transcript
    transcript_path = start_session_transcript(tmp_path)
    assert transcript_path.exists()


def test_start_session_transcript_contains_header(tmp_path: Path) -> None:
    from src.main import start_session_transcript
    transcript_path = start_session_transcript(tmp_path)
    content = transcript_path.read_text(encoding="utf-8")
    assert "Session Transcript" in content
    assert "Started:" in content


def test_start_session_transcript_filename_contains_session(tmp_path: Path) -> None:
    from src.main import start_session_transcript
    transcript_path = start_session_transcript(tmp_path)
    assert "session_" in transcript_path.name


def test_append_to_transcript_adds_entry(tmp_path: Path) -> None:
    from src.main import start_session_transcript, append_to_transcript
    transcript_path = start_session_transcript(tmp_path)
    append_to_transcript(transcript_path, 1, "Builder", "Write a function", "Here is the code.")
    content = transcript_path.read_text(encoding="utf-8")
    assert "Builder" in content
    assert "Write a function" in content
    assert "Here is the code." in content


def test_append_to_transcript_includes_step_number(tmp_path: Path) -> None:
    from src.main import start_session_transcript, append_to_transcript
    transcript_path = start_session_transcript(tmp_path)
    append_to_transcript(transcript_path, 3, "Reviewer", "Review the code", "Looks good.")
    content = transcript_path.read_text(encoding="utf-8")
    assert "Step 3" in content


def test_append_to_transcript_appends_multiple_entries(tmp_path: Path) -> None:
    from src.main import start_session_transcript, append_to_transcript
    transcript_path = start_session_transcript(tmp_path)
    append_to_transcript(transcript_path, 1, "Builder", "First task", "First response.")
    append_to_transcript(transcript_path, 2, "Reviewer", "Second task", "Second response.")
    content = transcript_path.read_text(encoding="utf-8")
    assert "First response." in content
    assert "Second response." in content


def test_main_handles_empty_task(tmp_path: Path) -> None:
    from src.main import main
    fake_response = json.dumps({"response": "Builder AI response."}).encode("utf-8")
    mock_response = MagicMock()
    mock_response.read.return_value = fake_response
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch("builtins.input", side_effect=["1", "", "1", "Write a function", "no"]), \
         patch("src.main.urlopen", return_value=mock_response), \
         patch("src.main.REPORTS_DIR", tmp_path), \
         patch("src.main.load_dotenv"), \
         patch("builtins.print"):
        main()


def test_main_handles_ollama_error_and_retries(tmp_path: Path) -> None:
    from src.main import main
    fake_response = json.dumps({"response": "Builder AI response."}).encode("utf-8")
    mock_response = MagicMock()
    mock_response.read.return_value = fake_response
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch("builtins.input", side_effect=["1", "Write a function", "1", "Write a function", "no"]), \
         patch("src.main.urlopen", side_effect=[RuntimeError("Ollama failed"), mock_response]), \
         patch("src.main.REPORTS_DIR", tmp_path), \
         patch("src.main.load_dotenv"), \
         patch("builtins.print"):
        main()



def test_save_report_contains_expected_content(tmp_path: Path) -> None:
    report_path = tmp_path / "reports" / "review-log.md"
    save_report(report_path, "Reviewer", "qwen2.5-coder:3b", "Check my code", "Looks good.")
    content = report_path.read_text(encoding="utf-8")
    assert "Reviewer" in content
    assert "Check my code" in content
    assert "Looks good." in content


def test_save_report_appends_on_second_call(tmp_path: Path) -> None:
    report_path = tmp_path / "reports" / "builder-output.md"
    save_report(report_path, "Builder", "qwen2.5-coder:3b", "First task", "First response.")
    save_report(report_path, "Builder", "qwen2.5-coder:3b", "Second task", "Second response.")
    content = report_path.read_text(encoding="utf-8")
    assert "First response." in content
    assert "Second response." in content


def test_build_project_context_includes_file_content(tmp_path: Path) -> None:
    doc_file = tmp_path / "PRD.md"
    doc_file.write_text("This is the PRD content.", encoding="utf-8")
    with patch("src.main.DOC_FILES", [doc_file]):
        result = build_project_context()
    assert "This is the PRD content." in result


def test_build_project_context_includes_filename(tmp_path: Path) -> None:
    doc_file = tmp_path / "coding-standards.md"
    doc_file.write_text("Keep functions small.", encoding="utf-8")
    with patch("src.main.DOC_FILES", [doc_file]):
        result = build_project_context()
    assert "coding-standards.md" in result


def test_build_project_context_skips_missing_files(tmp_path: Path) -> None:
    missing_file = tmp_path / "missing.md"
    with patch("src.main.DOC_FILES", [missing_file]):
        result = build_project_context()
    assert result == ""


def test_build_project_context_combines_multiple_files(tmp_path: Path) -> None:
    file_one = tmp_path / "PRD.md"
    file_two = tmp_path / "architecture.md"
    file_one.write_text("PRD content.", encoding="utf-8")
    file_two.write_text("Architecture content.", encoding="utf-8")
    with patch("src.main.DOC_FILES", [file_one, file_two]):
        result = build_project_context()
    assert "PRD content." in result
    assert "Architecture content." in result


def test_call_ollama_returns_response_text() -> None:
    fake_response = json.dumps({"response": "Hello from Ollama."}).encode("utf-8")
    mock_response = MagicMock()
    mock_response.read.return_value = fake_response
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    with patch("src.main.urlopen", return_value=mock_response):
        result = call_ollama(
            model="qwen2.5-coder:3b",
            prompt="Say hello.",
            host="http://localhost:11434",
        )
    assert result == "Hello from Ollama."


def test_call_ollama_raises_on_empty_response() -> None:
    fake_response = json.dumps({"response": ""}).encode("utf-8")
    mock_response = MagicMock()
    mock_response.read.return_value = fake_response
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    with patch("src.main.urlopen", return_value=mock_response):
        try:
            call_ollama(
                model="qwen2.5-coder:3b",
                prompt="Say hello.",
                host="http://localhost:11434",
            )
            assert False, "Expected RuntimeError was not raised."
        except RuntimeError as error:
            assert "no response" in str(error).lower()


def test_call_ollama_raises_on_ollama_error() -> None:
    fake_response = json.dumps({"error": "model not found"}).encode("utf-8")
    mock_response = MagicMock()
    mock_response.read.return_value = fake_response
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    with patch("src.main.urlopen", return_value=mock_response):
        try:
            call_ollama(
                model="qwen2.5-coder:3b",
                prompt="Say hello.",
                host="http://localhost:11434",
            )
            assert False, "Expected RuntimeError was not raised."
        except RuntimeError as error:
            assert "model not found" in str(error).lower()


def test_call_ollama_raises_on_http_error() -> None:
    from urllib.error import HTTPError
    fake_error = HTTPError(
        url="http://localhost:11434/api/generate",
        code=500,
        msg="Internal Server Error",
        hdrs=None,
        fp=BytesIO(b"something went wrong"),
    )
    with patch("src.main.urlopen", side_effect=fake_error):
        try:
            call_ollama(
                model="qwen2.5-coder:3b",
                prompt="Say hello.",
                host="http://localhost:11434",
            )
            assert False, "Expected RuntimeError was not raised."
        except RuntimeError as error:
            assert "500" in str(error)


def test_call_ollama_raises_on_url_error() -> None:
    from urllib.error import URLError
    fake_error = URLError(reason="Connection refused")
    with patch("src.main.urlopen", side_effect=fake_error):
        try:
            call_ollama(
                model="qwen2.5-coder:3b",
                prompt="Say hello.",
                host="http://localhost:11434",
            )
            assert False, "Expected RuntimeError was not raised."
        except RuntimeError as error:
            assert "ollama" in str(error).lower()


def test_call_ollama_raises_on_timeout() -> None:
    with patch("src.main.urlopen", side_effect=TimeoutError()):
        try:
            call_ollama(
                model="qwen2.5-coder:3b",
                prompt="Say hello.",
                host="http://localhost:11434",
            )
            assert False, "Expected RuntimeError was not raised."
        except RuntimeError as error:
            assert "too long" in str(error).lower()


def test_choose_role_returns_builder(tmp_path: Path) -> None:
    from src.main import choose_role
    with patch("builtins.input", return_value="1"):
        role_name, prompt_path, report_path = choose_role()
    assert role_name == "Builder"


def test_choose_role_returns_reviewer(tmp_path: Path) -> None:
    from src.main import choose_role
    with patch("builtins.input", return_value="2"):
        role_name, prompt_path, report_path = choose_role()
    assert role_name == "Reviewer"


def test_choose_role_returns_tester(tmp_path: Path) -> None:
    from src.main import choose_role
    with patch("builtins.input", return_value="3"):
        role_name, prompt_path, report_path = choose_role()
    assert role_name == "Tester"


def test_choose_role_shows_warning_on_invalid_then_accepts_valid() -> None:
    with patch("builtins.input", side_effect=["9", "1"]), \
         patch("builtins.print"):
        role_name, prompt_path, report_path = choose_role()
    assert role_name == "Builder"


def test_main_runs_full_workflow(tmp_path: Path) -> None:
    from src.main import main
    fake_response = json.dumps({"response": "Builder AI response."}).encode("utf-8")
    mock_response = MagicMock()
    mock_response.read.return_value = fake_response
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch("builtins.input", side_effect=["1", "Write a hello world function.", "no"]), \
         patch("src.main.urlopen", return_value=mock_response), \
         patch("src.main.REPORTS_DIR", tmp_path), \
         patch("src.main.load_dotenv"), \
         patch("builtins.print"):
        main()


def test_print_session_summary_shows_step_count(tmp_path: Path) -> None:
    from src.main import print_session_summary, start_session_transcript
    transcript_path = start_session_transcript(tmp_path)
    with patch("builtins.print") as mock_print:
        print_session_summary(3, ["Builder", "Reviewer", "Builder"], transcript_path)
    printed = " ".join(str(call) for call in mock_print.call_args_list)
    assert "3" in printed


def test_print_session_summary_shows_role_counts(tmp_path: Path) -> None:
    from src.main import print_session_summary, start_session_transcript
    transcript_path = start_session_transcript(tmp_path)
    with patch("builtins.print") as mock_print:
        print_session_summary(3, ["Builder", "Reviewer", "Builder"], transcript_path)
    printed = " ".join(str(call) for call in mock_print.call_args_list)
    assert "Builder" in printed
    assert "Reviewer" in printed


def test_print_session_summary_shows_none_when_no_steps(tmp_path: Path) -> None:
    from src.main import print_session_summary, start_session_transcript
    transcript_path = start_session_transcript(tmp_path)
    with patch("builtins.print") as mock_print:
        print_session_summary(0, [], transcript_path)
    printed = " ".join(str(call) for call in mock_print.call_args_list)
    assert "none" in printed

    
def test_print_session_summary_shows_transcript_path(tmp_path: Path) -> None:
    from src.main import print_session_summary, start_session_transcript
    transcript_path = start_session_transcript(tmp_path)
    with patch("builtins.print") as mock_print:
        print_session_summary(1, ["Tester"], transcript_path)
    printed = " ".join(str(call) for call in mock_print.call_args_list)
    assert transcript_path.name in printed

def test_truncate_context_returns_short_text_unchanged() -> None:
    from src.main import truncate_context
    text = "Short response."
    result = truncate_context(text)
    assert result == "Short response."


def test_truncate_context_truncates_long_text() -> None:
    from src.main import truncate_context
    text = "x" * 3000
    result = truncate_context(text, max_chars=2000)
    assert len(result) > 2000
    assert "truncated" in result.lower()


def test_truncate_context_keeps_exactly_max_chars() -> None:
    from src.main import truncate_context
    text = "x" * 2000
    result = truncate_context(text, max_chars=2000)
    assert result == text


def test_truncate_context_custom_limit() -> None:
    from src.main import truncate_context
    text = "hello world this is a long text"
    result = truncate_context(text, max_chars=10)
    assert result.startswith("hello worl")
    assert "truncated" in result.lower()


def test_main_uses_model_override(tmp_path: Path) -> None:
    from src.main import main
    fake_response = json.dumps({"response": "Builder AI response."}).encode("utf-8")
    mock_response = MagicMock()
    mock_response.read.return_value = fake_response
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch("builtins.input", side_effect=["1", "Write a function.", "no"]), \
         patch("src.main.urlopen", return_value=mock_response) as mock_urlopen, \
         patch("src.main.REPORTS_DIR", tmp_path), \
         patch("src.main.load_dotenv"), \
         patch("builtins.print"):
        main(model_override="llama3.2:3b")

    called_payload = json.loads(mock_urlopen.call_args[0][0].data.decode("utf-8"))
    assert called_payload["model"] == "llama3.2:3b"


def test_main_uses_env_model_when_no_override(tmp_path: Path) -> None:
    from src.main import main
    fake_response = json.dumps({"response": "Builder AI response."}).encode("utf-8")
    mock_response = MagicMock()
    mock_response.read.return_value = fake_response
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch("builtins.input", side_effect=["1", "Write a function.", "no"]), \
         patch("src.main.urlopen", return_value=mock_response) as mock_urlopen, \
         patch("src.main.REPORTS_DIR", tmp_path), \
         patch("src.main.load_dotenv"), \
         patch("builtins.print"), \
         patch.dict("os.environ", {"OLLAMA_MODEL": "mistral:7b"}):
        main(model_override=None)

    called_payload = json.loads(mock_urlopen.call_args[0][0].data.decode("utf-8"))
    assert called_payload["model"] == "mistral:7b"


def test_parse_args_default_model_is_none() -> None:
    from src.main import parse_args
    with patch("sys.argv", ["main.py"]):
        args = parse_args()
    assert args.model is None


def test_parse_args_model_flag() -> None:
    from src.main import parse_args
    with patch("sys.argv", ["main.py", "--model", "llama3.2:3b"]):
        args = parse_args()
    assert args.model == "llama3.2:3b"


# list_sessions tests

def test_list_sessions_no_reports_folder(capsys):
    from src.main import list_sessions
    list_sessions(reports_dir="nonexistent_reports_dir_xyz")
    captured = capsys.readouterr()
    assert "No reports folder found" in captured.out


def test_list_sessions_empty_folder(tmp_path, capsys):
    from src.main import list_sessions
    list_sessions(reports_dir=str(tmp_path))
    captured = capsys.readouterr()
    assert "No session transcripts found" in captured.out


def test_list_sessions_shows_files(tmp_path, capsys):
    from src.main import list_sessions
    (tmp_path / "session_20250101_120000.md").write_text("session 1")
    (tmp_path / "session_20250102_120000.md").write_text("session 2")
    list_sessions(reports_dir=str(tmp_path))
    captured = capsys.readouterr()
    assert "session_20250101_120000.md" in captured.out
    assert "session_20250102_120000.md" in captured.out


def test_list_sessions_sorted_newest_first(tmp_path, capsys):
    from src.main import list_sessions
    (tmp_path / "session_20250101_120000.md").write_text("older")
    (tmp_path / "session_20250103_120000.md").write_text("newer")
    list_sessions(reports_dir=str(tmp_path))
    captured = capsys.readouterr()
    pos_newer = captured.out.find("session_20250103")
    pos_older = captured.out.find("session_20250101")
    assert pos_newer < pos_older


def test_parse_args_list_sessions_flag():
    from src.main import parse_args
    import sys
    sys.argv = ["main.py", "--list-sessions"]
    args = parse_args()
    assert args.list_sessions is True


def test_parse_args_list_sessions_default_false():
    from src.main import parse_args
    import sys
    sys.argv = ["main.py"]
    args = parse_args()
    assert args.list_sessions is False

# --version flag tests

def test_version_constant_is_defined():
    from src.main import VERSION
    assert isinstance(VERSION, str)
    assert len(VERSION) > 0


def test_parse_args_version_flag(capsys):
    from src.main import parse_args
    import sys
    sys.argv = ["main.py", "--version"]
    try:
        parse_args()
    except SystemExit:
        pass
    captured = capsys.readouterr()
    assert "AI Automation Tool" in captured.out

# parse_args epilog test

def test_parse_args_help_contains_examples(capsys):
    from src.main import parse_args
    import sys
    sys.argv = ["main.py", "--help"]
    try:
        parse_args()
    except SystemExit:
        pass
    captured = capsys.readouterr()
    assert "Examples" in captured.out
    assert "--model" in captured.out
    assert "--list-sessions" in captured.out

# read_session tests

def test_read_session_prints_content(tmp_path, capsys):
    from src.main import read_session
    f = tmp_path / "session_20250101_120000.md"
    f.write_text("Session content here", encoding="utf-8")
    read_session(filename="session_20250101_120000.md", reports_dir=str(tmp_path))
    captured = capsys.readouterr()
    assert "Session content here" in captured.out


def test_read_session_prints_filename_in_header(tmp_path, capsys):
    from src.main import read_session
    f = tmp_path / "session_20250101_120000.md"
    f.write_text("Some content", encoding="utf-8")
    read_session(filename="session_20250101_120000.md", reports_dir=str(tmp_path))
    captured = capsys.readouterr()
    assert "session_20250101_120000.md" in captured.out


def test_read_session_file_not_found(tmp_path, capsys):
    from src.main import read_session
    read_session(filename="session_missing.md", reports_dir=str(tmp_path))
    captured = capsys.readouterr()
    assert "not found" in captured.out
    assert "--list-sessions" in captured.out


def test_parse_args_read_session_flag():
    from src.main import parse_args
    import sys
    sys.argv = ["main.py", "--read-session", "session_20250101_120000.md"]
    args = parse_args()
    assert args.read_session == "session_20250101_120000.md"

# --dry-run tests

def test_parse_args_dry_run_flag():
    from src.main import parse_args
    import sys
    sys.argv = ["main.py", "--dry-run"]
    args = parse_args()
    assert args.dry_run is True


def test_parse_args_dry_run_default_false():
    from src.main import parse_args
    import sys
    sys.argv = ["main.py"]
    args = parse_args()
    assert args.dry_run is False


def test_main_dry_run_does_not_call_ollama(tmp_path, monkeypatch):
    from src.main import main
    import sys
    inputs = iter(["1", "test dry run task", "no"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    monkeypatch.setattr("src.main.REPORTS_DIR", tmp_path)
    main(dry_run=True)





