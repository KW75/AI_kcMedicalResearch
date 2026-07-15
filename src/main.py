from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]

AI_DIR = PROJECT_ROOT / "ai"
DOCS_DIR = PROJECT_ROOT / "docs"
REPORTS_DIR = PROJECT_ROOT / "reports"

DEFAULT_OLLAMA_HOST = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "qwen2.5-coder:3b"

ROLE_FILES = {
    "1": ("Builder", AI_DIR / "builder-prompt.md", REPORTS_DIR / "builder-output.md"),
    "2": ("Reviewer", AI_DIR / "reviewer-prompt.md", REPORTS_DIR / "review-log.md"),
    "3": ("Tester", AI_DIR / "tester-prompt.md", REPORTS_DIR / "test-report.md"),
}

DOC_FILES = [
    DOCS_DIR / "PRD.md",
    DOCS_DIR / "architecture.md",
    DOCS_DIR / "coding-standards.md",
    DOCS_DIR / "test-strategy.md",
    DOCS_DIR / "decision-log.md",
]


def read_text_file(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def build_project_context() -> str:
    sections = []

    for path in DOC_FILES:
        content = read_text_file(path)
        if content:
            sections.append(f"## {path.name}\n{content}")

    return "\n\n".join(sections)

def choose_role() -> tuple[str, Path, Path]:
    while True:
        print("\nChoose AI role:")
        print("1. Builder AI")
        print("2. Reviewer AI")
        print("3. Tester AI")

        choice = input("\nEnter 1, 2, or 3: ").strip()

        if choice in ROLE_FILES:
            return ROLE_FILES[choice]

        print("Invalid choice. Please enter 1, 2, or 3.")


def call_ollama(model: str, prompt: str, host: str) -> str:
    url = host.rstrip("/") + "/api/generate"

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }

    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=180) as response:
            raw_response = response.read().decode("utf-8")
    except HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Ollama HTTP error {error.code}: {body}") from error
    except URLError as error:
        raise RuntimeError(
            "Could not connect to Ollama. Make sure Ollama is running, then try: ollama list"
        ) from error
    except TimeoutError as error:
        raise RuntimeError("Ollama took too long to respond. Try again or use a smaller model.") from error

    result = json.loads(raw_response)

    if "error" in result:
        raise RuntimeError(f"Ollama error: {result['error']}")

    response_text = result.get("response", "").strip()

    if not response_text:
        raise RuntimeError(f"Ollama returned no response. Raw result: {result}")

    return response_text


def save_report(report_path: Path, role_name: str, model: str, task: str, response_text: str) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    entry = f"""
# {role_name} AI Response

Time: {timestamp}
Model: {model}

## User Task

{task}

## AI Response

{response_text}

---
"""

    with report_path.open("a", encoding="utf-8") as file:
        file.write(entry)


def start_session_transcript(reports_dir: Path) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    transcript_path = reports_dir / f"session_{timestamp}.md"
    header = f"# Session Transcript\n\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n"
    transcript_path.write_text(header, encoding="utf-8")
    return transcript_path


def append_to_transcript(transcript_path: Path, step: int, role_name: str, task: str, response_text: str) -> None:
    entry = f"## Step {step} - {role_name} AI\n\n**Task:** {task}\n\n**Response:**\n\n{response_text}\n\n---\n"
    with transcript_path.open("a", encoding="utf-8") as file:
        file.write(entry)

def truncate_context(text: str, max_chars: int = 2000) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"\n\n[Response truncated at {max_chars} characters to keep prompt size manageable.]"


def print_session_summary(step: int, roles_used: list[str], transcript_path: Path) -> None:
    from collections import Counter
    role_counts = Counter(roles_used)
    roles_str = ", ".join(f"{role} ({count})" for role, count in role_counts.items())
    print("\n" + "=" * 42)
    print("Session Summary")
    print("=" * 42)
    print(f"Steps completed : {step}")
    print(f"Roles used      : {roles_str if roles_str else 'none'}")
    print(f"Transcript saved: {transcript_path}")
    print("=" * 42 + "\n")


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")

    model = os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
    host = os.getenv("OLLAMA_HOST", DEFAULT_OLLAMA_HOST)

    print("\nAI Automation Tool")
    print("==================")
    print("Type 'quit' or 'exit' at any prompt to stop.\n")

    transcript_path = start_session_transcript(REPORTS_DIR)
    print(f"Session transcript: {transcript_path}\n")

    step = 0
    roles_used = []
    last_response = ""


    while True:
        role_name, prompt_path, report_path = choose_role()

        role_prompt = read_text_file(prompt_path)
        project_context = build_project_context()

        task = input("\nEnter your task for the AI: ").strip()

        if task.lower() in ("quit", "exit"):
            print("\nGoodbye.")
            break

        if not task:
            print("Task cannot be empty. Please try again.")
            continue

        safety_rules = """
Safety rules:
- Do not include secrets, passwords, or API keys.
- Do not create malware, spyware, keyloggers, credential theft tools, exploit payloads, reverse shells, or unauthorized scanning tools.
- If a task is unsafe, refuse and suggest a safe defensive alternative.
"""

        previous_context = (
            f"\nPrevious AI output:\n\n{truncate_context(last_response)}\n"
            if last_response
            else ""
        )

        full_prompt = f"""
{role_prompt}

{safety_rules}

Project context:

{project_context}

{previous_context}User task:

{task}

Respond as the {role_name} AI.
"""

        print(f"\nSending task to local {role_name} AI using Ollama model {model}...\n")

        try:
            response_text = call_ollama(model=model, prompt=full_prompt, host=host)
        except RuntimeError as error:
            print(f"\nError: {error}")
            print("Please check Ollama is running and try again.\n")
            continue

        step += 1
        roles_used.append(role_name)
        last_response = response_text


        print("\nAI RESPONSE")
        print("=" * 60)
        print(response_text)
        print("=" * 60)

        save_report(report_path, role_name, model, task, response_text)
        append_to_transcript(transcript_path, step, role_name, task, response_text)

        print(f"\nSaved response to: {report_path}")
        print(f"Session transcript updated: {transcript_path}")

        again = input("\nSend another task? (yes to continue, anything else to quit): ").strip().lower()
        if again != "yes":
            print_session_summary(step, roles_used, transcript_path)
            print("Goodbye.")
            break




if __name__ == "__main__":
    main()
