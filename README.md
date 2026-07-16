# AI Automation Tool

A local Python AI automation tool powered by [Ollama](https://ollama.com).
Run Builder, Reviewer, and Tester AI roles from your terminal —
no cloud APIs, no data leaving your machine.

---

## Features

- Three AI roles — Builder, Reviewer, and Tester
- Multi-task sessions — stay in a session and send multiple tasks without restarting
- Forward context passing — each step automatically receives the previous AI response
- Session transcripts — timestamped markdown file saved per session in `reports/`
- Session summary — printed at exit showing steps completed, roles used, and transcript path
- Coloured terminal output — each role has its own colour, errors in red, summary in magenta
- `--model` flag — override the Ollama model from the command line
- `--list-sessions` flag — list all past session transcripts sorted newest first
- `--read-session` flag — print a past session transcript to the terminal
- `--dry-run` flag — run a full session without calling Ollama, for testing
- `--version` flag — show tool version and exit
- `--help` flag — show usage and examples
- `--delete-session` flag — delete a past session transcript from the command line
- `--export-session` flag — export a session transcript as a plain text file
- `--stats` flag — show statistics across all past sessions


---

## Requirements

- Python 3.11+
- [Ollama](https://ollama.com) installed and running locally
- A pulled Ollama model (default: `qwen2.5-coder:3b`)

---

## Setup

**1. Clone the repository:**

```bash
git clone https://github.com/KW75/ai-automation-tool.git
cd ai-automation-tool


2. Create and activate a virtual environment:

python -m venv .venv
# Windows
.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate

3. Install dependencies:

pip install -r requirements.txt

4. Create your .env file:

cp .env.example .env

Edit .env if you want to change the default model or host:

OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:3b

5. Pull a model in Ollama:

ollama pull qwen2.5-coder:3b


Usage

Start a session:
python src/main.py

Use a different model:
python src/main.py --model llama3.2:3b

List past session transcripts:
 python src/main.py --list-sessions

Read a past session transcript:
python src/main.py --read-session session_20260716_154643.md

Run without Ollama (dry run):
 python src/main.py --dry-run

Show version:
python src/main.py --version

Delete a past session transcript:
python src/main.py --delete-session session_20260716_154643.md

Export a session transcript as plain text:
python src/main.py --export-session session_20260716_154643.md



Workflow

Builder AI  →  writes or suggests code
Reviewer AI →  reviews and gives feedback
Builder AI  →  fixes issues
Tester AI   →  creates or checks tests
Human       →  approves before deploy

Each step automatically passes the previous AI response as context to the next step.

Running Tests

python -m pytest -v
python -m pytest -v --cov=src --cov-report=term-missing

Project Structure

ai-automation-tool/
├── src/
│   ├── __init__.py
│   └── main.py
├── tests/
│   ├── __init__.py
│   └── test_main.py
├── ai/
│   ├── builder-prompt.md
│   ├── reviewer-prompt.md
│   └── tester-prompt.md
├── docs/
│   ├── PRD.md
│   ├── architecture.md
│   ├── coding-standards.md
│   ├── test-strategy.md
│   └── decision-log.md
├── reports/              # ignored by git
├── .venv/                # ignored by git
├── .env                  # ignored by git
├── .env.example
├── .gitignore
├── conftest.py
├── pytest.ini
├── requirements.txt
└── README.md


AI Roles

Builder AI — creates and modifies code based on your task description.
Reviewer AI — reviews code and gives structured feedback on quality, correctness, and improvement areas.
Tester AI — suggests tests, checks test coverage, and assesses readiness before deployment.

License

MIT





