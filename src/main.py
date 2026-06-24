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
    print("\nChoose AI role:")
    print("1. Builder AI")
    print("2. Reviewer AI")
    print("3. Tester AI")

    choice = input("\nEnter 1, 2, or 3: ").strip()

    if choice not in ROLE_FILES:
        raise ValueError("Invalid choice. Please run again and choose 1, 2, or 3.")

    return ROLE_FILES[choice]


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


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")

    model = os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
    host = os.getenv("OLLAMA_HOST", DEFAULT_OLLAMA_HOST)

    print("\nAI Automation Tool")
    print("==================")
    print("Type 'quit' or 'exit' at any prompt to stop.\n")

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

        full_prompt = f"""
{role_prompt}

{safety_rules}

Project context:

{project_context}

User task:

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

        print("\nAI RESPONSE")
        print("=" * 60)
        print(response_text)
        print("=" * 60)

        save_report(report_path, role_name, model, task, response_text)

        print(f"\nSaved response to: {report_path}")

        again = input("\nSend another task? (yes to continue, anything else to quit): ").strip().lower()
        if again != "yes":
            print("\nGoodbye.")
            break


if __name__ == "__main__":
    main()
