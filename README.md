
# AI Automation Tool

A local Python CLI tool that uses Ollama to run AI-assisted development workflows.

## What it does

Lets you choose an AI role and send it a task. The AI responds based on its role
and the project context. The response is printed and saved to a report file.

## AI roles

- **Builder AI** - creates or modifies code
- **Reviewer AI** - reviews code and gives feedback
- **Tester AI** - suggests tests and checks readiness

## Workflow

User selects role -> Tool loads role prompt -> Tool loads docs context
-> Tool sends task to Ollama -> Tool prints response -> Tool saves to reports/

## Requirements

- Python 3.11+
- Ollama installed and running locally
- Ollama model pulled (default: qwen2.5-coder:3b)

## Setup

1. Clone the repository
2. Create and activate the virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
