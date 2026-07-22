# AI Automation Tool

A local-first, multi-mode AI assistant for medical research, writing,
coding, and evidence appraisal. Runs entirely on your machine using Ollama,
or connects to DeepSeek, Groq, OpenAI, or Anthropic via API key.

## Quick Start

```powershell
# Install dependencies
pip install -r requirements.txt

# Pull local embedding model (once)
ollama pull nomic-embed-text

# Run in coding mode (default)
python src/main.py

# Open interactive help guide in browser
python src/main.py --help-guide
```

## Modes

| Mode | Flag | Roles | Purpose |
|---|---|---|---|
| Coding | `--mode coding` | Builder, Reviewer, Tester | AI-assisted software development |
| Writing | `--mode writing` | Writer, Editor, QA | Long-form document creation |
| RCT Search | `--mode rct_search` | Formulator, Searcher, Validator | Build validated PubMed search strategies |
| Appraisal | `--mode appraisal` | Appraiser, Methodologist, Summariser | Critical appraisal of research articles |
| Search | `--mode search` | Researcher | Single-pass medical literature search |

## Providers

| Provider | Flag | Notes |
|---|---|---|
| Ollama | `--provider ollama` | Default. Local, free, no internet needed |
| DeepSeek | `--provider deepseek` | Globally available, no geo-restrictions |
| Groq | `--provider groq` | Fast inference, free developer tier |
| OpenAI | `--provider openai` | Requires `OPENAI_API_KEY` in `.env` |
| Anthropic | `--provider anthropic` | Requires `ANTHROPIC_API_KEY` in `.env` |

## Mode Details

### Coding Mode
Place project documents in `docs/coding/` before starting:
- `PRD.md` — product requirements
- `architecture.md` — system design
- `coding-standards.md` — style rules
- `decision-log.md` — design decisions
- `test-strategy.md` — test approach

Optionally place code files (`.py`, `.js`, `.ts`, `.json`, `.yaml`) in
`uploads/coding/` — the Builder role will use them for revision suggestions
via RAG.

```powershell
python src/main.py
python src/main.py --mode coding --provider deepseek
python src/main.py --list-roles --mode coding
```

### Writing Mode
Place project documents in `docs/writing/`:
- `project-brief.md` — scope and objectives
- `style-guide.md` — tone and formatting rules
- `editorial-standards.md` — editorial criteria
- `qa-checklist.md` — quality checklist

Place source documents (`.txt`, `.md`, `.pdf`) or a URL list file in
`uploads/writing/` for RAG-assisted drafting.

```powershell
python src/main.py --mode writing
python src/main.py --mode writing --report    # generate summary report
```

Output: `reports/session_TIMESTAMP.md` and `reports/writing_report_TIMESTAMP.md`

### RCT Search Mode
**Edit `docs/rct_search/pico-framework.md` before every session.**

| PICO | What to fill in |
|---|---|
| P — Population | Who are the patients? |
| I — Intervention | What is being tested? |
| C — Comparison | What is the control/comparator? |
| O — Outcome | What are you measuring? |

```powershell
python src/main.py --mode rct_search
```

Output: `reports/rct_search_TIMESTAMP.md` — clickable search links only.

### Appraisal Mode
Place article files in `uploads/appraisal/` before starting:
- Formats: `.pdf`, `.txt`, `.md`
- URL list: one URL per line in a `.txt` file — pages fetched automatically
- PubMed abstracts are freely fetchable; full text requires a PDF

```powershell
python src/main.py --mode appraisal
python src/main.py --mode appraisal --provider deepseek
```

Tip: use article URLs from `--mode search` reports as input here.

### Search Mode
No files needed. Queries PubMed live.

```powershell
python src/main.py --mode search
# Prompts: Search topic: beta blockers heart failure
```

Output: `reports/search_TIMESTAMP.md` — article links + AI research summary.

## Session Management

```powershell
python src/main.py --list-sessions
python src/main.py --read-session session_20260101_120000.md
python src/main.py --export-session session_20260101_120000.md  # saves .txt
python src/main.py --delete-session session_20260101_120000.md
python src/main.py --rename-session session_20260101_120000.md
python src/main.py --stats
```

## RAG (Retrieval-Augmented Generation)

Files placed in `uploads/{mode}/` are indexed at session start using
ChromaDB and Ollama embeddings (`nomic-embed-text`). The index is
per-session and deleted at session end — nothing persists between runs.

To switch to OpenAI embeddings, set in `.env`:
```
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
```

## Environment Variables

Copy `.env.example` to `.env` and fill in the keys you need:

```
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:3b
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-sonnet-4-6
DEEPSEEK_API_KEY=
DEEPSEEK_MODEL=deepseek-v4-flash
GROQ_API_KEY=
GROQ_MODEL=llama-3.3-70b-versatile
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
UPLOAD_DIR=uploads
```

## Project Structure

```
ai-automation-tool/
├── src/
│   ├── main.py          ← CLI entry point, all modes and providers
│   └── rag.py           ← RAG module (chunking, embedding, URL fetch)
├── tests/
│   ├── test_main.py     ← main.py tests
│   └── test_rag.py      ← rag.py tests
├── ai/                  ← AI role prompt files
├── docs/
│   ├── coding/          ← coding mode reference docs
│   ├── writing/         ← writing mode reference docs
│   ├── rct_search/      ← PICO framework and search guides
│   ├── appraisal/       ← appraisal reference docs
│   └── flashcard-help.html ← interactive help guide
├── uploads/
│   ├── coding/          ← code files for Builder RAG context
│   ├── writing/         ← documents for writing RAG context
│   ├── rct_search/      ← search-related uploads
│   └── appraisal/       ← articles for critical appraisal
└── reports/             ← all session outputs saved here
```

## Tests

```powershell
python -m pytest -v
python -m pytest -v --cov=src --cov-report=term-missing
```

Current: **205 tests, 0 failing, 87% coverage**

