# Architecture

## Overview
AI kcMedicalResearch is a Python CLI/web application built around specialised
AI pipelines for medical research tasks. Each pipeline implements a multi-agent
pattern where roles collaborate sequentially. The application supports local
inference (Ollama) and multiple cloud providers.

## Project Structure

    AI_kcMedicalResearch/
    ├── SOURCE_CODE/
    │   ├── main.py                          <- Core engine: providers, CLI, mode routing
    │   ├── __init__.py
    │   ├── pipelines/
    │   │   ├── coding/coding.py            <- Builder->Reviewer->Tester loop
    │   │   ├── writing/writing.py          <- Writer->Editor->QA loop
    │   │   ├── appraisal/appraisal.py      <- Appraiser->Methodologist->Summariser
    │   │   ├── search/search.py            <- Researcher (single agent)
    │   │   ├── rct_search/rct_search.py    <- Formulator->Searcher->Validator
    │   │   ├── sr/                          <- Systematic Review (self-contained)
    │   │   └── shared/                      <- Cross-pipeline utilities
    │   ├── utils/
    │   │   ├── path_utils.py              <- PATH_MANAGER, directory resolution
    │   │   ├── document_reader.py         <- PDF/DOCX/TXT file reading
    │   │   └── rag.py                      <- RAG embedding and retrieval
    │   └── ui/
    │       └── app.py                       <- Streamlit web interface
    ├── scripts/
    │   ├── launcher.py                      <- Interactive CLI menu
    │   ├── windows/                         <- Windows setup scripts
    │   └── macos/                           <- macOS setup scripts
    ├── prompts/                             <- Role prompt definitions (15 files)
    ├── docs/                                <- Mode-specific guidelines (injected into LLM)
    │   ├── project/                         <- Project-level documentation
    │   ├── coding/                          <- Coding mode standards
    │   ├── writing/                         <- Writing mode standards
    │   ├── appraisal/                       <- Appraisal mode guide + scoring
    │   ├── search/                          <- Search output format
    │   └── rct_search/                      <- PICO, database guide, validation
    ├── input/                               <- Per-mode input files
    ├── output/                              <- Per-mode generated output
    ├── reports/                             <- Session transcripts and logs
    ├── tests/                               <- pytest test suite (275+ tests)
    ├── .env                                 <- API keys and model config (gitignored)
    ├── pytest.ini                           <- Test configuration
    ├── requirements.txt                     <- Python dependencies
    └── README.md

## Core Components

### SOURCE_CODE/main.py (2438 lines)
The central engine containing:
- Provider functions: call_ollama_provider, call_qwen_provider,
  call_deepseek_provider, call_openai_provider, call_anthropic_provider,
  call_groq_provider
- Ollama auto-detection: _ollama_detect_best_model() queries /api/tags at startup
- Mode routing: dispatches to the appropriate pipeline based on --mode flag
- CLI argument parsing and interactive session management
- Environment variable loading (.env via python-dotenv)

### Pipeline Pattern
Each pipeline follows the same pattern:
1. Load guidelines from docs/<mode>/ via _load_md_guidelines()
2. Load input files from input/<mode>/
3. Construct system prompt (guidelines as context)
4. Construct user prompt (task + input content)
5. Call LLM provider
6. Parse response, iterate if needed
7. Write output to output/<mode>/ and report to reports/<mode>/

### Provider System
All providers share the same interface:
    def call_<provider>_provider(prompt: str, model: str = None, max_tokens: int = 8192) -> str

The active provider is selected via --provider flag or launcher menu.
Ollama options (context, temperature, num_predict) are read from .env at call time.

### Guidelines Injection
Each pipeline calls _load_md_guidelines(docs/<mode>/) which:
- Reads all .md files from the mode's docs folder
- Concatenates them with section headers
- Injects them into the system prompt as background context

This means updating a .md file in docs/ immediately changes LLM behaviour
without any code changes.

### scripts/launcher.py
Interactive TUI menu that:
- Presents mode selection (Coding, Writing, Appraisal, Search, RCT Search, SR)
- Presents provider selection
- Launches the appropriate pipeline via subprocess
- Inherits stdin/stdout/stderr for interactive LLM communication

## Data Flow

    User input -> launcher.py -> main.py --mode X --provider Y
      -> pipeline loads docs/X/*.md as guidelines
      -> pipeline loads input/X/* as source material
      -> pipeline constructs prompt (system + user)
      -> pipeline calls provider (Ollama/Qwen/DeepSeek/etc.)
      -> LLM response parsed
      -> iterate (Builder->Reviewer->Tester) if applicable
      -> output written to output/X/
      -> report written to reports/X/

## Configuration
All runtime configuration via .env file:
- OLLAMA_HOST, OLLAMA_MODEL (empty = auto-detect), OLLAMA_CONTEXT,
  OLLAMA_NUM_PREDICT, OLLAMA_TEMPERATURE
- QWEN_MODEL, DASHSCOPE_API_KEY, DASHSCOPE_BASE_URL
- DEEPSEEK_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY, GROQ_API_KEY
