from __future__ import annotations

from pathlib import Path

from src.main import read_text_file, save_report


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
