# AI Automation Tool

A local Python CLI tool that uses Ollama to run AI-assisted development workflows.
Three AI roles work together in a connected session — Builder writes code,
Reviewer checks it, and Tester validates it — with each role automatically
receiving the previous role's output as context.

## What it does

- Runs a multi-role AI session entirely on your local machine using Ollama
- Lets you switch between Builder, Reviewer, and Tester roles in one session
- Passes the previous AI response forward as context to the next step automatically
- Saves each response to a role-specific report file in `reports/`
- Saves a full timestamped session transcript capturing the entire workflow
- Prints a session summary at the end showing steps completed and roles used

## AI roles

- **Builder AI** — creates or modifies code based on your task and project context
- **Reviewer AI** — reviews code and gives structured feedback with a final decision
- **Tester AI** — suggests tests and checks readiness before deployment

## Target workflow

```
Builder AI writes code
      ↓
Reviewer AI reviews and gives feedback
      ↓
Builder AI fixes issues
      ↓
Tester AI suggests tests and checks readiness
      ↓
Human approves before deploy
```

## Requirements

- Python 3.11+
- Ollama installed and running locally
- Ollama model pulled (default: `qwen2.5-coder:3b`)

## Setup

1. Clone the repository:

```powershell
git clone https://github.com/KW75/ai-automation-tool.git
cd ai-automation-tool
```

2. Create and activate the virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

3. Install dependencies:

```powershell
pip install -r requirements.txt
```

4. Copy `.env.example` to `.env`:

```powershell
Copy-Item .env.example .env
```

5. Make sure Ollama is running and the model is available:

```powershell
ollama list
```

If `qwen2.5-coder:3b` is not listed, pull it:

```powershell
ollama pull qwen2.5-coder:3b
```

## Run

```powershell
python src\main.py
```

You will see:

```
AI Automation Tool
==================
Type 'quit' or 'exit' at any prompt to stop.

Session transcript: D:\ai-automation-tool\reports\session_20260624_111934.md

Choose AI role:
1. Builder AI
2. Reviewer AI
3. Tester AI

Enter 1, 2, or 3:
```

- Choose a role, enter your task, and wait for the AI response
- After each response, type `yes` to send another task or anything else to quit
- Type `exit` or `quit` at any task prompt to stop immediately
- A session summary is printed at the end of every session

## Session transcript example

Each session creates a timestamped file in `reports/` capturing the full workflow:

```
# Session Transcript

Started: 2026-06-24 11:19:34

---
## Step 1 - Builder AI

**Task:** write a Python function that adds two numbers

**Response:** ...

---
## Step 2 - Reviewer AI

**Task:** review the code from the previous step

**Response:** ...

---
## Step 3 - Tester AI

**Task:** suggest tests for the add function

**Response:** ...
```

## Run tests

```powershell
python -m pytest -v
```

With coverage:

```powershell
python -m pytest -v --cov=src --cov-report=term-missing
```

Current status: **37 tests passing, 98% coverage**

## Project structure

```
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
├── reports/              (ignored, not committed)
├── .env                  (ignored, not committed)
├── .env.example
├── .gitignore
├── conftest.py
├── pytest.ini
├── requirements.txt
└── README.md
```

## Configuration

All settings are controlled via `.env`:

```
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:3b
```

Change `OLLAMA_MODEL` to use a different locally available model.
