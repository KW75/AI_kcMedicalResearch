# AI Automation Tool

A local Python AI automation tool supporting multiple AI providers and workflow
modes. Run Builder, Reviewer, and Tester roles in coding mode, or Writer,
Editor, and QA roles in writing mode — powered by Ollama locally or OpenAI /
Anthropic via API.

---

## Features

- **Two workflow modes** — `coding` mode (Builder, Reviewer, Tester) and
  `writing` mode (Writer, Editor, QA)
- **Three provider choices** — `ollama` (local, default), `openai`, `anthropic`
- Three AI roles per mode — each with its own prompt file in `ai/`
- Multi-task sessions — stay in a session and send multiple tasks without restarting
- Forward context passing — each step automatically receives the previous AI response
- Session transcripts — timestamped markdown file saved per session in `reports/`
- Session summary — printed at exit showing steps completed, roles used, and transcript path
- Coloured terminal output — each role has its own colour, errors in red, summary in magenta
- `--mode` flag — switch between `coding` and `writing` workflows
- `--provider` flag — choose `ollama`, `openai`, or `anthropic`
- `--model` flag — override the model for any provider from the command line
- `--list-roles` flag — show roles, prompt files, and injected docs for a mode
- `--list-sessions` flag — list all past session transcripts sorted newest first
- `--read-session` flag — print a past session transcript to the terminal
- `--delete-session` flag — delete a past session transcript from the command line
- `--export-session` flag — export a session transcript as a plain text file
- `--rename-session` flag — rename a past session transcript file
- `--stats` flag — show statistics across all past sessions
- `--dry-run` flag — run a full session without calling any AI provider, for testing
- `--version` flag — show tool version and exit
- `--help` flag — show usage and examples

---

## Requirements

- Python 3.11+
- [Ollama](https://ollama.com) installed and running locally (for `ollama` provider)
- A pulled Ollama model (default: `qwen2.5-coder:3b`)
- An `OPENAI_API_KEY` in `.env` (for `openai` provider)
- An `ANTHROPIC_API_KEY` in `.env` (for `anthropic` provider)

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

Edit .env with the settings relevant to your chosen provider:

# Ollama (local)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:3b

# OpenAI (optional — required only if using --provider openai)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o

# Anthropic (optional — required only if using --provider anthropic)
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-6

5. Pull a model in Ollama:

ollama pull qwen2.5-coder:3b

Providers
Provider 	Flag 	Runs locally 	Requires API key 	Default model
Ollama 	--provider ollama 	✅ Yes 	❌ No 	qwen2.5-coder:3b
OpenAI 	--provider openai 	❌ No 	✅ OPENAI_API_KEY 	gpt-4o
Anthropic 	--provider anthropic 	❌ No 	✅ ANTHROPIC_API_KEY 	claude-sonnet-4-6

ollama is the default. No API key or internet connection is needed to get started.
Modes
Mode 	Flag 	Roles 	Docs injected per role
Coding 	--mode coding 	Builder, Reviewer, Tester 	PRD + architecture (all); coding-standards (Builder); decision-log (Reviewer); test-strategy (Tester)
Writing 	--mode writing 	Writer, Editor, QA 	project-brief (all); style-guide (Writer); editorial-standards (Editor); qa-checklist (QA)

coding is the default. Each role receives only the documentation relevant to its specific job — no role receives another role's instructions. Use --list-roles to inspect the exact docs injected for any mode.
Usage

Start a coding session (default):

python src/main.py

Start a writing session:

python src/main.py --mode writing

Use OpenAI instead of Ollama:

python src/main.py --provider openai

Use Anthropic in writing mode:

python src/main.py --mode writing --provider anthropic

Use a different model:

python src/main.py --model llama3.2:3b
python src/main.py --provider openai --model gpt-4o-mini

Show roles, prompt files, and injected docs for a mode:

python src/main.py --list-roles
python src/main.py --list-roles --mode writing

Example output for --list-roles (coding mode):

==========================================
  Roles — coding mode
==========================================

1. Builder AI
   Prompt : ai\builder-prompt.md
   Docs   : PRD.md, architecture.md, coding-standards.md

2. Reviewer AI
   Prompt : ai\reviewer-prompt.md
   Docs   : PRD.md, architecture.md, decision-log.md

3. Tester AI
   Prompt : ai\tester-prompt.md
   Docs   : PRD.md, architecture.md, test-strategy.md

==========================================

Run without calling any AI provider (dry run):

python src/main.py --dry-run
python src/main.py --mode writing --provider anthropic --dry-run

List past session transcripts:

python src/main.py --list-sessions

Read a past session transcript:

python src/main.py --read-session session_20260716_154643.md

Delete a past session transcript:

python src/main.py --delete-session session_20260716_154643.md

Export a session transcript as plain text:

python src/main.py --export-session session_20260716_154643.md

Rename a session transcript:

python src/main.py --rename-session session_20260716_154643.md

Show statistics across all sessions:

python src/main.py --stats

Show version:

python src/main.py --version

Workflow

Coding mode:

Builder AI  →  writes or suggests code
Reviewer AI →  reviews and gives feedback
Builder AI  →  fixes issues
Tester AI   →  creates or checks tests
Human       →  approves before deploy

Writing mode:

Writer AI   →  drafts the content
Editor AI   →  reviews structure, clarity, and tone
QA AI       →  checks accuracy, consistency, and completeness
Human       →  approves before publishing

Each step automatically passes the previous AI response as context to the next step.
Running Tests

python -m pytest -v
python -m pytest -v --cov=src --cov-report=term-missing

Current status: 121 tests, 121 passing, 94% coverage.
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
│   ├── tester-prompt.md
│   ├── writer-prompt.md
│   ├── editor-prompt.md
│   └── qa-prompt.md
├── docs/
│   ├── coding/
│   │   ├── PRD.md
│   │   ├── architecture.md
│   │   ├── coding-standards.md
│   │   ├── decision-log.md
│   │   └── test-strategy.md
│   └── writing/
│       ├── project-brief.md
│       ├── style-guide.md
│       ├── editorial-standards.md
│       └── qa-checklist.md
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

Coding mode:

    Builder AI — creates and modifies code based on your task description. Receives coding-standards.md to ensure output follows project conventions.
    Reviewer AI — reviews code and gives structured feedback on quality, correctness, and improvement areas. Receives decision-log.md so it understands past decisions and does not flag intentional choices as problems.
    Tester AI — suggests tests, checks test coverage, and assesses readiness before deployment. Receives test-strategy.md to align with project testing conventions.

Writing mode:

    Writer AI — drafts content based on your brief. Receives style-guide.md to ensure tone, vocabulary, and formatting are correct from the first draft.
    Editor AI — reviews structure, clarity, tone, and flow. Receives editorial-standards.md defining what to check and what to leave to the Writer.
    QA AI — checks for accuracy, consistency, and completeness before publication. Receives qa-checklist.md with explicit sign-off criteria.

License

MIT


---

**Commit:**

```powershell
git add README.md
git commit -m "Step 55: update README — add --list-roles, correct modes table to show per-role doc injection, update project structure and test count"

