# Architecture

## Overview

The AI Automation Tool is a local Python CLI application built around a
three-role AI pipeline. It supports multiple workflow modes and multiple
AI providers. The core engine is domain-agnostic — the active mode and
provider are selected at runtime via CLI flags.

## Core Components

### src/main.py

The single application module. Contains all functions for role selection,
prompt construction, AI communication, session management, and CLI handling.

### Mode System

The tool supports multiple workflow modes. Each mode defines a set of three
AI roles. The active mode is selected via the `--mode` flag and resolved at
startup:

```python
ALL_MODES = {
    "coding": ROLE_FILES_CODING,
    "writing": ROLE_FILES_WRITING,
}
```

New modes are added by creating prompt files in `ai/` and adding a new
dictionary entry in `ALL_MODES`. No other code changes are required.

### Provider System

The tool supports multiple AI providers. Each provider is a callable that
accepts `model`, `prompt`, and `host` and returns a response string.
The active provider is selected via the `--provider` flag and defaults to
`ollama`:

```python
PROVIDERS = {
    "ollama":    call_ollama_provider,
    "openai":    call_openai_provider,
    "anthropic": call_anthropic_provider,
}
```

New providers are added by writing one caller function and adding one entry
to `PROVIDERS`. No other code changes are required.

### Prompt Construction

`build_project_context()` is mode-aware. It injects only the documentation
files relevant to the active mode, keeping prompts lean and preventing
conflicting instructions from reaching the model.

### Session Management

Each session creates a timestamped transcript in `reports/`. Steps are
appended to the transcript after each AI response. The session summary
is printed at exit.

### Forward Context Passing

The previous AI response is automatically included in the next prompt,
truncated to `max_chars` (default 2000) to keep prompt size manageable.

## File Structure

```
ai-automation-tool/
├── src/
│   ├── __init__.py
│   └── main.py
├── tests/
│   ├── __init__.py
│   └── test_main.py
├── ai/
│   ├── builder-prompt.md       # coding mode — role 1
│   ├── reviewer-prompt.md      # coding mode — role 2
│   ├── tester-prompt.md        # coding mode — role 3
│   ├── writer-prompt.md        # writing mode — role 1
│   ├── editor-prompt.md        # writing mode — role 2
│   └── qa-prompt.md            # writing mode — role 3
├── docs/
│   ├── PRD.md
│   ├── architecture.md
│   ├── coding-standards.md     # coding mode only
│   ├── test-strategy.md        # coding mode only
│   └── decision-log.md
├── reports/                    # ignored by git
├── .venv/                      # ignored by git
├── .env                        # ignored by git
├── .env.example
├── .gitignore
├── conftest.py
├── pytest.ini
├── requirements.txt
└── README.md
```
