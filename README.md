# AI kcMedical Research

A multi-mode AI assistant for medical research, critical appraisal, systematic review, coding, and writing.
Uses cloud providers by default (DeepSeek, Qwen, OpenAI, Anthropic, Groq) with optional local Ollama support.

- **Version:** 2.4.0
- **Tests:** 362 passed, 3 skipped
- **Coverage:** ~50%
- **CI:** GitHub Actions - Green
- **GitHub:** https://github.com/KW75/AI_kcMedicalResearch
- **Live App:** https://ai-kcmedicalresearch.onrender.com

---

## Quick Start

### One-Click Setup (Recommended for Colleagues)

#### Windows
```cmd
git clone https://github.com/KW75/AI_kcMedicalResearch.git
cd AI_kcMedicalResearch
docker\docker_setup.bat

macOS

git clone https://github.com/KW75/AI_kcMedicalResearch.git
cd AI_kcMedicalResearch
chmod +x docker/mac_*.sh
./docker/mac_docker_setup.sh

Total time: ~5 minutes. No Python setup required!
Docker (Manual - All Platforms)

# Build image
docker build -f docker/Dockerfile -t ai-kcmedicalresearch .

# CLI mode
docker run -it --rm \
    -v $(pwd)/input:/app/input \
    -v $(pwd)/output:/app/output \
    -v $(pwd)/reports:/app/reports \
    --env-file .env \
    --add-host host.docker.internal:host-gateway \
    ai-kcmedicalresearch \
    python SOURCE_CODE/main.py

# UI mode
docker run -it --rm -p 8501:8501 \
    -v $(pwd)/input:/app/input \
    -v $(pwd)/output:/app/output \
    -v $(pwd)/reports:/app/reports \
    --env-file .env \
    --add-host host.docker.internal:host-gateway \
    ai-kcmedicalresearch \
    streamlit run SOURCE_CODE/ui/app.py --server.port=8501 --server.address=0.0.0.0

Local Development (Without Docker)

Run all commands from the project root.

# CLI mode (DeepSeek default, streaming enabled)
python SOURCE_CODE/main.py                            # coding mode
python SOURCE_CODE/main.py --mode writing             # writing mode
python SOURCE_CODE/main.py --mode rct_search          # RCT search pipeline
python SOURCE_CODE/main.py --mode search              # PubMed search
python SOURCE_CODE/main.py --mode appraisal           # critical appraisal
python SOURCE_CODE/main.py --mode sr --provider qwen  # systematic review (needs vision)

# With options
python SOURCE_CODE/main.py --provider qwen            # use Qwen instead
python SOURCE_CODE/main.py --provider ollama          # use local Ollama (slow with large models)
python SOURCE_CODE/main.py --no-stream                # disable live streaming output
python SOURCE_CODE/main.py --resume                   # resume from last checkpoint
python SOURCE_CODE/main.py --dry-run                  # test without API calls
python SOURCE_CODE/main.py --help-guide               # open interactive HTML help

# Interactive launcher
python scripts/launcher.py                            # menu-driven mode/provider selection

Modes
Mode 	Flag 	Roles 	Output
Coding 	--mode coding 	Builder, Reviewer, Tester 	output/coding/ + reports/coding/
Coding Revise 	--mode coding --revise 	Builder, Reviewer, Tester 	output/coding/ + reports/coding/
Writing 	--mode writing 	Writer, Editor, QA 	output/writing/ + reports/writing/
Writing Report 	--mode writing --report 	Writer, Editor, QA 	output/writing/ + reports/writing/
RCT Search 	--mode rct_search 	Formulator, Searcher, Validator 	output/rct_search/
Search 	--mode search 	Researcher 	output/search/ + reports/search/
Appraisal 	--mode appraisal 	Appraiser, Methodologist, Summariser 	output/appraisal/ + reports/appraisal/
SR 	--mode sr 	SR Methodologist 	output/sr/ + reports/sr/
Flags
Flag 	Description
--mode 	Select mode: coding, writing, rct_search, search, appraisal, sr
--provider 	AI provider: deepseek (default), ollama, openai, anthropic, groq, qwen
--model 	Specify model name (provider-specific)
--no-stream 	Disable live streaming output (batch mode)
--resume 	Resume from last checkpoint if available
--report 	Writing mode: single-pass report from input/writing/ files
--revise 	Coding mode: Builder, Reviewer, Tester pipeline
--role 	Override the starting role for coding mode
--sub 	Sub-mode for search: 1=Topic Search, 2=Article Search
--dry-run 	Run without making real API calls
--help-guide 	Open interactive HTML help guide in browser
--ui 	Launch Streamlit UI
--list-sessions 	List all session transcripts
--list-roles 	Show available roles and their docs
--stats 	Show session statistics
--version 	Show version number
Providers
Provider 	Flag 	Environment Variable 	Notes
DeepSeek (DEFAULT) 	--provider deepseek 	DEEPSEEK_API_KEY 	Fast, cost-efficient
Qwen 	--provider qwen 	DASHSCOPE_API_KEY 	Recommended for SR (vision)
OpenAI 	--provider openai 	OPENAI_API_KEY 	GPT-4 vision
Anthropic 	--provider anthropic 	ANTHROPIC_API_KEY 	Claude vision
Groq 	--provider groq 	GROQ_API_KEY 	Fast inference
Ollama (local) 	--provider ollama 	OLLAMA_HOST 	Free but slow; offline/testing only
Provider Fallback Chain

On transient errors (timeout, 429, 502, 503), the system automatically tries the next provider. Default chain: DeepSeek → Qwen → Groq. Configure via FALLBACK_PROVIDERS env var.
Streaming

All providers support live token streaming. Enabled by default in CLI terminals. Use --no-stream to disable. Non-TTY environments (pipes, CI) automatically use batch mode.

Set keys in .env at the project root.
Environment Variables (.env)

# Default provider
DEFAULT_PROVIDER=deepseek

# Fallback chain (comma-separated, empty to disable)
FALLBACK_PROVIDERS=deepseek,qwen,groq

# Local Ollama (for offline/testing)
OLLAMA_HOST=http://localhost:11434
# OLLAMA_MODEL=        # Leave empty for auto-detection
OLLAMA_CONTEXT=32768
OLLAMA_NUM_PREDICT=8192
OLLAMA_TEMPERATURE=0.3

# Cloud Providers
DEEPSEEK_API_KEY=sk-...
GROQ_API_KEY=gsk_...
DASHSCOPE_API_KEY=sk-...
DASHSCOPE_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus-latest

# Optional
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# RAG
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text

# Theme (auto-detected, override if needed)
CLI_THEME=dark   # or light

File-Based Input

Avoid interactive prompts by placing input files in the relevant folder before running.
Mode 	Input Folder 	Supported Formats
Coding 	input/coding/ 	.py, .js, .ts, .html, .css, .java, .c, .cpp, .cs, .rb, .go, .rs, .txt, .md
Writing 	input/writing/ 	.txt, .md, .docx, .pdf
Appraisal 	input/appraisal/ 	.pdf, .txt, .md, .docx
RCT Search 	input/rct_search/ 	.txt, .md
Search 	input/search/ 	.txt, .md
SR 	input/sr/ 	.pdf
Project Structure

AI_kcMedicalResearch/
|-- SOURCE_CODE/                     <- Main source code
|   |-- main.py                      <- Core engine
|   |-- providers.py                 <- Provider registry, fallback chain
|   |-- streaming.py                 <- SSE streaming for all providers
|   |-- checkpoint.py                <- Pipeline checkpoint/resume
|   |-- traice_integration.py        <- PRISMA-trAIce disclosure
|   |-- pipelines/
|   |   |-- coding/coding.py        <- Builder->Reviewer->Tester (max 3 iterations)
|   |   |-- writing/writing.py      <- Writer->Editor->QA
|   |   |-- appraisal/appraisal.py  <- Appraiser->Methodologist->Summariser
|   |   |-- search/search.py        <- Researcher (single agent)
|   |   |-- rct_search/rct_search.py <- Formulator->Searcher->Validator
|   |   |-- sr/                      <- Systematic Review (self-contained)
|   |   +-- shared/                  <- Cross-pipeline utilities
|   |-- ui/
|   |   +-- app.py                   <- Streamlit web interface
|   +-- utils/
|       |-- path_utils.py            <- PATH_MANAGER, directory resolution
|       |-- document_reader.py       <- Multi-format reader (PDF, DOCX, images)
|       +-- rag.py                   <- RAG embedding and retrieval (ChromaDB)
|-- scripts/                         <- Launcher and setup scripts
|-- docker/                          <- Docker configuration
|-- docs/                            <- Mode guidelines (injected into LLM prompts)
|-- prompts/                         <- Role prompt definitions (reference only)
|-- input/                           <- Per-mode input files
|-- output/                          <- Per-mode generated output
|-- reports/                         <- Session transcripts and logs
|-- tests/                           <- pytest test suite (362 tests)
|-- .github/workflows/ci.yml         <- GitHub Actions CI pipeline
|-- .env                             <- API keys and model config (gitignored)
|-- pytest.ini                       <- Test configuration with custom marks
|-- requirements.txt                 <- Python dependencies (local/Windows)
|-- requirements-ci.txt              <- CI dependencies (Ubuntu/chromadb)
|-- requirements-render.txt          <- Lean requirements (Render cloud)
|-- render.yaml                      <- Render deployment config
+-- README.md

Running Tests

# Run all tests (excludes live provider tests by default)
python -m pytest -m "not live" --tb=short -q

# Run all tests including live providers
python -m pytest --tb=short -q

# Run specific test file
python -m pytest tests/test_main.py -v

# Run tests with coverage
python -m pytest --cov=SOURCE_CODE --cov-report=html

# Run only live provider smoke tests
python -m pytest -m live -v

Current status: 362 passed, 3 skipped, 11 deselected
SR Pipeline

# 1. Edit configuration
notepad SOURCE_CODE/pipelines/sr/config/prisma_criteria.yaml

# 2. Place PDFs in input/sr/
copy *.pdf input/sr/

# 3. Run SR pipeline (requires vision provider)
python SOURCE_CODE/main.py --mode sr --provider qwen

# Or use the SR UI
python SOURCE_CODE/pipelines/sr/src/ui/app.py

SR Outputs: forest_plot.png, systematic_review.docx/.html/.pdf, full audit trail.
Vision Providers (for SR Pipeline)
Provider 	Vision Support 	Notes
Qwen 	Yes 	Recommended
OpenAI 	Yes 	GPT-4 vision
Anthropic 	Yes 	Claude vision
Groq 	Yes 	Vision models
DeepSeek 	No 	Blocked for SR
Ollama 	No 	Blocked for SR
Known Issues
# 	Issue 	Priority 	Status
1 	Lami extraction fails (Table 4) 	High 	Open
2 	WeasyPrint not installed 	Medium 	PDF falls back to HTML
3 	Anthropic geo-restricted 	Low 	Use VPN or skip
Contributing

    Fork the repository
    Create a feature branch: git checkout -b feature/your-feature
    Make your changes
    Run tests: python -m pytest -m "not live" --tb=short -q
    Commit and push
    Create a pull request '@

[System.IO.File]::WriteAllText("PWD\README.md", $readme, [System.Text.UTF8Encoding]::new(false))
Verify

Write-Host "README.md written: $((Get-Item 'README.md').Length) bytes"


