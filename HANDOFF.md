# Handoff: AI Automation Tool — Local Ollama Version

## Project location

```text
D:\ai-automation-tool
```

## Current stop point

This handoff is current through:

- Project folder created
- Python virtual environment created
- Basic folder/file structure created
- Project docs created
- Three AI role prompts created
- Basic coding standards created
- Python dependencies configured
- Ollama installed and working
- Local model pulled and tested
- Python CLI tool updated to use Ollama locally
- `.env` cleaned to use Ollama settings only

## User environment

- OS/terminal: Windows PowerShell
- Editor: VS Code
- Python: installed
- Python virtual environment: `.venv`
- GitHub account: created
- Git repository: not initialized/pushed yet
- Docker: not used yet
- AI provider: local Ollama
- Current Ollama model: `qwen2.5-coder:3b`

## Project goal

Build a local Python AI automation tool with three AI roles:

1. **Builder AI** — creates or modifies code.
2. **Reviewer AI** — checks code and gives feedback.
3. **Tester AI** — suggests tests and checks readiness before deployment.

Target workflow:

```text
Builder AI writes or suggests code
Reviewer AI reviews and gives feedback
Builder AI fixes issues
Tester AI creates/checks tests
Human approves before deploy
```

## Important rule from user

Proceed **one step at a time**.

Do not move to the next step until the user says:

```text
OK
```

## Completed setup steps

### 1. Created project folder

```powershell
mkdir d:\ai-automation-tool
cd d:\ai-automation-tool
```

### 2. Created and activated Python virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Expected prompt:

```text
(.venv) PS D:\ai-automation-tool>
```

### 3. Created project folders

```powershell
mkdir src, docs, ai, reports, tests
```

Folders:

```text
src/
docs/
ai/
reports/
tests/
```

### 4. Created project files

Created:

```text
README.md
.gitignore
requirements.txt

docs/PRD.md
docs/architecture.md
docs/coding-standards.md
docs/test-strategy.md
docs/decision-log.md

ai/builder-prompt.md
ai/reviewer-prompt.md
ai/tester-prompt.md

reports/review-log.md
reports/test-report.md

src/main.py
```

## Current `.gitignore`

```text
.venv/
__pycache__/
*.py[cod]

.env
.env.*
!.env.example

.pytest_cache/
.coverage
htmlcov/

dist/
build/
*.egg-info/

.vscode/
```

Important:

- `.env` is ignored.
- `.venv` is ignored.
- Secrets should not be committed.

## Current `requirements.txt`

```text
python-dotenv
pytest
```

Installed with:

```powershell
python -m pip install -r requirements.txt
```

Verified with:

```powershell
python -c "from dotenv import load_dotenv; print('dotenv OK')"
```

Expected output:

```text
dotenv OK
```

## Current `.env.example`

```text
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:3b
```

`.env` was overwritten from `.env.example` so it should contain only Ollama settings.

Verified with:

```powershell
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('OLLAMA_HOST')); print(os.getenv('OLLAMA_MODEL'))"
```

Expected output:

```text
http://localhost:11434
qwen2.5-coder:3b
```

## Project documents

### `docs/PRD.md`

Purpose:

- Defines the project as a local Python AI automation tool.
- Version 1 scope:
  - Read prompts from `ai/`
  - Read project documents from `docs/`
  - Let user choose Builder, Reviewer, or Tester
  - Send task to local AI model
  - Save AI responses into `reports/`

Version 1 does not include:

- Docker
- Web interface
- Automatic deployment
- Autonomous GitHub pull requests
- Custom vector database/RAG

### `docs/coding-standards.md`

Main rules:

- Use clear Python names.
- Keep functions small and readable.
- Avoid unnecessary complexity.
- Handle errors clearly.
- Do not hardcode secrets.
- Use environment variables for settings.
- Make small AI-driven changes.
- Do not edit unrelated files.
- Add tests for important logic.

## AI role prompts

Created these files:

```text
ai/builder-prompt.md
ai/reviewer-prompt.md
ai/tester-prompt.md
```

### Builder AI

Responsibilities:

- Create or modify code based on user task.
- Follow `docs/PRD.md`.
- Follow `docs/coding-standards.md`.
- Make the smallest safe change.
- Explain changed files.
- Suggest commands to verify work.

### Reviewer AI

Responsibilities:

- Review code, plans, or Builder output.
- Check against PRD and coding standards.
- Find bugs, security issues, missing tests, and unclear design.
- Return:
  1. Blockers
  2. Major issues
  3. Minor issues
  4. Suggested fixes
  5. Final decision

### Tester AI

Responsibilities:

- Create test plans.
- Suggest unit, integration, and manual tests.
- Review test results.
- Decide whether code is ready for deployment.

Return:
1. Test plan
2. Missing tests
3. Commands to run
4. Risks
5. Final decision

## Ollama installation completed

Ollama was installed for Windows.

Ollama was checked with:

```powershell
ollama --version
```

Model pulled:

```powershell
ollama pull qwen2.5-coder:3b
```

Model tested:

```powershell
ollama run qwen2.5-coder:3b "Say hello and explain what you are."
```

User confirmed:

```text
Ollama works
```

## Current `src/main.py` status

`src/main.py` has been updated to use local Ollama instead of an external API.

It currently:

- Loads `.env`
- Reads Ollama host from `OLLAMA_HOST`
- Reads Ollama model from `OLLAMA_MODEL`
- Reads role prompts from `ai/`
- Reads project documents from `docs/`
- Lets user choose:
  - `1` Builder AI
  - `2` Reviewer AI
  - `3` Tester AI
- Sends the prompt to Ollama at:

```text
http://localhost:11434/api/generate
```

- Saves output to:
  - Builder: `reports/builder-output.md`
  - Reviewer: `reports/review-log.md`
  - Tester: `reports/test-report.md`

## Current run command

From PowerShell:

```powershell
cd D:\ai-automation-tool
.\.venv\Scripts\Activate.ps1
python src\main.py
```

Then choose:

```text
1
```

Test task used:

```text
Say hello and explain your Builder AI role for this project.
```

User confirmed this worked.

## Safety rules currently included in the tool

The tool prompt includes safety rules:

- Do not include secrets, passwords, or API keys.
- Do not create malware, spyware, keyloggers, credential theft tools, exploit payloads, reverse shells, or unauthorized scanning tools.
- If a task is unsafe, refuse and suggest a safe defensive alternative.

## Current project state summary

Working local CLI prototype:

```text
User selects role
      ↓
Tool loads role prompt
      ↓
Tool loads docs context
      ↓
Tool sends task to local Ollama
      ↓
Tool prints AI response
      ↓
Tool saves response into reports/
```

## Not done yet

The following have not been done yet:

- Git repository initialization
- First Git commit
- Push to GitHub
- Automated tests
- Docker
- RAG/vector database
- Multi-agent orchestration framework
- GitHub Actions
- Deployment

## Recommended next step

Next recommended step is:

```text
Initialize Git locally and make the first safe commit.
```

Before committing, verify:

```powershell
git status
```

Make sure these are not included:

```text
.env
.venv/
```

## Handoff instruction to next assistant

Continue one step at a time.

Suggested next message to user:

```text
Step 15 — Initialize Git locally
```

Do not introduce Docker, RAG, deployment, or GitHub Actions yet.
