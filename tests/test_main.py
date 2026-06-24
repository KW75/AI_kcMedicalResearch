from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.main import read_text_file, save_report, build_project_context, call_ollama


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


def test_choose_role_raises_on_invalid_choice() -> None:
    from src.main import choose_role
    with patch("builtins.input", return_value="9"):
        try:
            choose_role()
            assert False, "Expected ValueError was not raised."
        except ValueError as error:
            assert "invalid choice" in str(error).lower()


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


