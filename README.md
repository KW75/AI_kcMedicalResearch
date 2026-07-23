# AI kcMedical Research

A multi-mode AI assistant for medical research, critical appraisal, systematic review, coding, and writing.
Runs locally via Ollama or via cloud providers (OpenAI, Anthropic, DeepSeek, Groq).

## Quick Start

Run from: D:\\AI_kcMedicalResearch

    python src/main.py                          # coding mode (Ollama default)
    python src/main.py --mode writing --report  # writing report from docs/writing/
    python src/main.py --mode writing            # interactive writing session
    python src/main.py --mode rct_search         # RCT search strategy pipeline
    python src/main.py --mode search             # PubMed medical search
    python src/main.py --mode appraisal          # critical appraisal of articles
    python src/main.py --mode sr                 # systematic review pipeline
    python src/main.py --mode coding --revise    # code revision Builder->Review->Test
    python src/main.py --mode coding --revise --role Reviewer
    python src/main.py --provider deepseek       # use DeepSeek instead of Ollama
    python src/main.py --dry-run                 # simulate without AI calls
    python src/main.py --list-roles              # show all roles and prompt files
    python src/main.py --help-guide              # open HTML flashcard guide

## Modes

| Mode | Flag | Roles | Output |
|---|---|---|---|
| Coding | --mode coding | Builder, Reviewer, Tester | reports/session_*.md |
| Coding Revise | --mode coding --revise | Builder, Reviewer, Tester | reports/code_revision_*.md + .docx |
| Writing | --mode writing | Writer, Editor, QA | reports/writing_report_*.md + .docx |
| RCT Search | --mode rct_search | Formulator, Searcher, Validator | reports/rct_search_*.md + .docx |
| Search | --mode search | Researcher | reports/search_*.md + .docx |
| Appraisal | --mode appraisal | Appraiser, Methodologist, Summariser | reports/session_*.md |
| SR | --mode sr | Full pipeline | sr/outputs/reports/ |

## Flags

| Flag | Description |
|---|---|
| --report | Writing mode: single-pass report from docs/writing/ files |
| --revise | Coding mode: single-pass revision pipeline Builder->Review->Test |
| --role | With --revise: start role (Builder, Reviewer, Tester) |
| --provider | AI provider: ollama, openai, anthropic, deepseek, groq |
| --model | Override default model for the selected provider |
| --dry-run | Run without making AI calls (for testing) |
| --list-roles | Print all roles and their prompt files |
| --help-guide | Open interactive HTML flashcard guide |

## Word Limits

| Mode / Section | Limit |
|---|---|
| Appraisal full report | 1500 words |
| Summariser plain-language section | 200 words |
| Summariser full report | 1500 words |
| Search paper plain-language section | 200 words |
| Search paper full report | 1500 words |
| Search clinical topic | Thorough but concise |
| Writing report | 1500 words |

## Search Mode Runtime Prompt

When running --mode search, the tool asks at runtime:

    Are you searching for a research paper or a clinical topic?
    1. Research paper
    2. Clinical topic
    Enter 1 or 2:

- Research paper: structured critical appraisal report (7 sections, 1500 words)
- Clinical topic: reviewer-format summary (thorough, no strict word limit)

## RCT Search Pipeline

Single-pass automated pipeline:
1. Formulator: builds structured PICO from your topic
2. Searcher: creates Boolean search strategy for 7 databases
3. Validator: reviews strategy -> APPROVED FOR DOWNLOAD or REQUIRES REFINEMENT

Output: reports/rct_search_{timestamp}.md and .docx
Next step: run --mode appraisal to appraise retrieved articles.

## Code Revision Pipeline (--revise)

Place code files (.py .js .ts .cs .java .sql .html .css) in docs/coding/
Guidance docs (PRD.md, architecture.md etc.) are used as context only.

    python src/main.py --mode coding --revise              # Builder->Review->Test
    python src/main.py --mode coding --revise --role Reviewer  # Review->Test
    python src/main.py --mode coding --revise --role Tester    # Test only

Output: reports/code_revision_{timestamp}.md + .docx with suggested changes.
Developer reviews and applies changes manually.

## Providers

| Provider | Flag | Notes |
|---|---|---|
| Ollama | --provider ollama | Default, runs locally, no API key needed |
| OpenAI | --provider openai | Requires OPENAI_API_KEY in .env |
| Anthropic | --provider anthropic | Requires ANTHROPIC_API_KEY in .env |
| DeepSeek | --provider deepseek | Requires DEEPSEEK_API_KEY in .env |
| Groq | --provider groq | Requires GROQ_API_KEY in .env, fast inference |

## SR Pipeline (Systematic Review)

    notepad sr\\config\\prisma_criteria.yaml   # 1. Edit PICO criteria
    copy *.pdf sr\\data\\uploads\\            # 2. Place RCT PDFs
    python sr\\main.py --pdf-dir sr\\data\\uploads --effect-measure SMD

Outputs:
  sr/data/screened/screening_log.csv
  sr/data/extracted/extracted_data.csv
  sr/data/results/meta_analysis_results.csv
  sr/outputs/figures/forest_plot.png
  sr/outputs/reports/systematic_review.html
  sr/outputs/reports/systematic_review.docx

WARNING: Research accelerator only. All outputs require human verification before publication.

## RAG (Retrieval-Augmented Generation)

Place files in the relevant uploads folder before starting a session.
Supported: .txt .md .pdf .py .js .ts .json .yaml
URLs on their own line in .txt/.md files are fetched and indexed automatically.

| Mode | Upload folder |
|---|---|
| coding | uploads/coding/ |
| writing | uploads/writing/ |
| rct_search | uploads/rct_search/ |
| appraisal | uploads/appraisal/ |
| search | uploads/search/ |

## Environment Variables (.env)

  OLLAMA_URL=http://localhost:11434
  OLLAMA_MODEL=llama3.2
  OPENAI_API_KEY=sk-...
  OPENAI_MODEL=gpt-4o
  ANTHROPIC_API_KEY=sk-ant-...
  ANTHROPIC_MODEL=claude-sonnet-4-5
  DEEPSEEK_API_KEY=sk-...
  DEEPSEEK_MODEL=deepseek-chat
  GROQ_API_KEY=gsk_...
  GROQ_MODEL=llama-3.3-70b-versatile
  EMBEDDING_PROVIDER=ollama
  EMBEDDING_MODEL=nomic-embed-text

## Project Structure

  AI_kcMedicalResearch/
  src/main.py              # main CLI all interactive modes
  src/rag.py               # RAG chunking embedding ChromaDB
  sr/                      # SR pipeline standalone
  ai/                      # prompt files one per role
  docs/flashcard-help.html # interactive help guide
  docs/coding/             # PRD architecture coding standards
  docs/writing/            # project brief style guide
  docs/rct_search/         # PICO framework database guide
  uploads/                 # RAG input files git-ignored
  reports/                 # session outputs git-ignored
  tests/test_main.py       # 227 tests for src/main.py
  tests/test_sr.py         # 21 tests for sr/ pipeline
  .env                     # API keys git-ignored
  requirements.txt

## Tests

  python -m pytest -v
  python -m pytest tests/test_main.py -v
  python -m pytest tests/test_sr.py -v
  python -m pytest -v --cov=src --cov-report=term-missing

Current status: 248 tests, 0 failures, 87% coverage

## AI Roles

| Mode | Roles |
|---|---|
| coding | Builder, Reviewer, Tester |
| writing | Writer, Editor, QA |
| rct_search | Formulator, Searcher, Validator |
| search | Researcher |
| appraisal | Appraiser, Methodologist, Summariser |
| sr | SR Methodologist via appraisal mode |

## Known Gaps

- SR Streamlit UI not yet integrated
- SR placeholder modules: heterogeneity.py funnel_plot.py prisma_flow.py
- PDF OCR not supported (text-based PDFs only)
- WeasyPrint PDF output requires native libs on Windows
- nomic-embed-text must be pulled manually: ollama pull nomic-embed-text
- Writing docs templates need project-specific content