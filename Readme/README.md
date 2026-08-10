# AI kcMedical Research

A multi-mode AI assistant for medical research, critical appraisal, systematic review, coding, and writing.
Runs locally via Ollama or via cloud providers (OpenAI, Anthropic, DeepSeek, Groq, Qwen).

- **Version:** 2.3.0
- **Tests:** ~243 passed, 3 skipped
- **Coverage:** ~50%
- **Last commit:** 4a77472
- **GitHub:** https://github.com/KW75/AI_kcMedicalResearch
- **Live App:** https://ai-kcmedicalresearch.onrender.com

---

## Quick Start

### 🚀 One-Click Setup (Recommended for Colleagues)

#### Windows 🪟
```cmd
git clone https://github.com/KW75/AI_kcMedicalResearch.git
cd AI_kcMedicalResearch
docker\docker_setup.bat
# Follow prompts → START WORKING!

macOS 🍎
bash

git clone https://github.com/KW75/AI_kcMedicalResearch.git
cd AI_kcMedicalResearch
chmod +x docker/mac_*.sh
./docker/mac_docker_setup.sh
# Follow prompts → START WORKING!

Total time: ~5 minutes. No Python setup required!
🐳 Docker (Manual - All Platforms)
bash

# Build image
docker build -f docker/Dockerfile -t ai-kcmedicalresearch .

# CLI mode
docker run -it --rm \
    -v $(pwd)/input:/app/input \
    -v $(pwd)/output:/app/output \
    -v $(pwd)/data:/app/data \
    -v $(pwd)/reports:/app/reports \
    --env-file .env \
    --add-host host.docker.internal:host-gateway \
    ai-kcmedicalresearch \
    python SOURCE_CODE/main.py

# UI mode
docker run -it --rm -p 8501:8501 \
    -v $(pwd)/input:/app/input \
    -v $(pwd)/output:/app/output \
    -v $(pwd)/data:/app/data \
    -v $(pwd)/reports:/app/reports \
    --env-file .env \
    --add-host host.docker.internal:host-gateway \
    ai-kcmedicalresearch \
    streamlit run SOURCE_CODE/ui/app.py --server.port=8501 --server.address=0.0.0.0

💻 Local Development (Without Docker)

Run all commands from the project root.
bash

# CLI mode
python SOURCE_CODE/main.py                            # coding mode (Ollama default)
python SOURCE_CODE/main.py --mode writing             # writing mode
python SOURCE_CODE/main.py --mode rct_search          # RCT search pipeline
python SOURCE_CODE/main.py --mode search              # PubMed search
python SOURCE_CODE/main.py --mode appraisal           # critical appraisal
python SOURCE_CODE/main.py --mode sr                  # systematic review pipeline

# With options
python SOURCE_CODE/main.py --provider qwen            # use Qwen instead of Ollama
python SOURCE_CODE/main.py --model llama3.2           # specify model
python SOURCE_CODE/main.py --dry-run                  # test without API calls
python SOURCE_CODE/main.py --help-guide               # open interactive HTML help in browser

Modes
Mode	Flag	Roles	Output
Coding	--mode coding	Builder, Reviewer, Tester	output/coding/ + reports/coding/
Coding Revise	--mode coding --revise	Builder, Reviewer, Tester	output/coding/ + reports/coding/
Writing	--mode writing	Writer, Editor, QA	output/writing/ + reports/writing/
Writing Report	--mode writing --report	Writer, Editor, QA	output/writing/ + reports/writing/
RCT Search	--mode rct_search	Formulator, Searcher, Validator	output/rct_search/ + reports/rct_search/
Search	--mode search	Researcher	output/search/ + reports/search/
Appraisal	--mode appraisal	Appraiser, Methodologist, Summariser	output/appraisal/ + reports/appraisal/
SR	--mode sr	SR Methodologist	output/sr/ + reports/sr/
Flags
Flag	Description
--mode	Select mode: coding, writing, rct_search, search, appraisal, sr
--provider	AI provider: ollama, openai, anthropic, deepseek, groq, qwen
--model	Specify model name (provider-specific)
--report	Writing mode: single-pass report from input/writing/ files
--revise	Coding mode: Builder → Reviewer → Tester pipeline
--role	Override the starting role for coding mode
--sub	Sub-mode for search: 1=Topic Search, 2=Article Search
--dry-run	Run without making real API calls
--help-guide	Open interactive HTML help guide in browser
--ui	Launch Streamlit UI
--list-sessions	List all session transcripts
--list-roles	Show available roles and their docs
--stats	Show session statistics
File-Based Input

Avoid interactive prompts by placing input files in the relevant folder before running.
Input Directories
Mode	Input Folder	Supported Formats
Coding	input/coding/	.py, .js, .ts, .html, .css, .java, .c, .cpp, .cs, .rb, .go, .rs, .txt, .md, .php, .swift, .kt, .r, .sh, .sql, .svg
Writing	input/writing/	.txt, .md, .docx, .pdf
Appraisal	input/appraisal/	.pdf, .txt, .md, .docx
RCT Search	input/rct_search/	.txt, .md
Search	input/search/	.txt, .md
SR	input/sr/	.pdf
RCT Search

Create docs/rct_search/topic.md with one line — the research topic.
Example: Effect of metformin on HbA1c in type 2 diabetes
If absent, the mode prompts at runtime.
Search

Create docs/search/topic.md with two lines.

    Line 1: paper (find a specific paper) or topic (clinical topic summary)

    Line 2: your query.
    If absent, the mode prompts at runtime.

Appraisal

Place article files in input/appraisal/

    Supported formats: .txt, .md, .pdf, .docx

    Files up to 8000 characters are injected directly into the prompt.

    Files over 8000 characters are handled via RAG chunking.

Docs Folder Structure

Guidance files are loaded as context for each mode. Edit to customise AI behaviour.
text

docs/
├── appraisal/
│   ├── appraisal-guide.md       ← 7-section structure, per-section word limits
│   ├── custom-checklist.md      ← Custom appraisal checklist
│   ├── grade-guidance.md        ← GRADE evidence rating
│   ├── project-brief.md         ← Appraisal project brief
│   └── scoring-criteria.md      ← RoB 2, CASP, AMSTAR 2, GRADE tables
├── coding/
│   ├── architecture.md
│   ├── coding-standards.md
│   ├── decision-log.md
│   ├── PRD.md
│   └── test-strategy.md
├── rct_search/
│   ├── database-guide.md
│   ├── pico-framework.md
│   ├── topic.md.example         ← copy to topic.md and edit
│   └── validation-criteria.md
├── search/
│   ├── article-types.md
│   ├── search-guide.md
│   ├── search-prompt.md
│   └── topic.md.example         ← copy to topic.md and edit
└── writing/
    ├── article/                 ← Medical journal article track
    │   ├── editorial-standards.md
    │   ├── project-brief.md
    │   ├── qa-checklist.md
    │   └── style-guide.md
    └── topic/                   ← Editorial/opinion track
        ├── editorial-standards.md
        ├── project-brief.md
        ├── qa-checklist.md
        └── style-guide.md

Providers
Provider	Flag	Environment Variable	Notes
Ollama (local)	--provider ollama	OLLAMA_HOST (default: http://localhost:11434)	Free, no key
Qwen	--provider qwen	DASHSCOPE_API_KEY	Recommended for SR
OpenAI	--provider openai	OPENAI_API_KEY	GPT-4 vision
Anthropic	--provider anthropic	ANTHROPIC_API_KEY	Claude vision
DeepSeek	--provider deepseek	DEEPSEEK_API_KEY	Cost-efficient
Groq	--provider groq	GROQ_API_KEY	Fast inference

Set keys in .env at the project root.
Vision Providers (for SR Pipeline)
Provider	Vision Support	Notes
✅ Qwen	Yes	Recommended
✅ OpenAI	Yes	GPT-4 vision
✅ Anthropic	Yes	Claude vision
✅ Groq	Yes	Vision models
❌ DeepSeek	No	Blocked for SR
❌ Ollama	No	Blocked for SR
Environment Variables (.env)
bash

# Local Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Cloud Providers
GROQ_API_KEY=gsk_...
DASHSCOPE_API_KEY=sk-...
DASHSCOPE_BASE_URL=https://ws-uv5pi4kkqbrg1vpe.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1
DASHSCOPE_ANTHROPIC_URL=https://ws-uv5pi4kkqbrg1vpe.ap-southeast-1.maas.aliyuncs.com/apps/anthropic

# Optional
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
DEEPSEEK_API_KEY=sk-...

# RAG
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text

# Theme (auto-detected, override if needed)
CLI_THEME=dark   # or light

SR Pipeline
bash

# 1. Edit configuration
notepad SOURCE_CODE/pipelines/sr/config/prisma_criteria.yaml

# 2. Place PDFs in input/sr/
copy *.pdf input/sr/

# 3. Run SR pipeline
python SOURCE_CODE/main.py --mode sr --provider qwen

# Or use the SR UI
python SOURCE_CODE/pipelines/sr/src/ui/app.py

SR Outputs:

    output/sr/forest_plot.png - Forest plot

    reports/sr/systematic_review.docx - Word report

    reports/sr/systematic_review.html - HTML report

    reports/sr/systematic_review.pdf - PDF report (if WeasyPrint installed)

    reports/sr/<run_id>/ - Full audit trail

Multi-Format Document Support

The Writing and Appraisal modes now support multiple document formats:
Format	Writing	Appraisal	OCR Support
PDF	✅	✅	✅
DOCX	✅	✅	❌
DOC	✅	✅	❌
TXT/MD	✅	✅	❌
Images (JPG, PNG, TIFF, BMP)	✅	✅	✅
Excel (XLS, XLSX)	✅ (text)	✅ (text)	❌

Just place files in the appropriate input/ folder and the app handles everything!
Project Structure
text

AI_kcMedicalResearch/
├── 🪟 WINDOWS SCRIPTS
│   ├── docker_setup.bat               ⭐ One-click Windows Docker setup
│   ├── docker_menu.bat                🎨 Interactive menu (CLI/UI)
│   └── docker_cli.bat                 ⚡ Quick CLI launch
├── 🍎 MACOS SCRIPTS
│   ├── mac_docker_setup.sh            ⭐ One-click macOS Docker setup
│   ├── mac_docker_menu.sh             🎨 Interactive menu (CLI/UI)
│   ├── mac_docker_cli.sh              ⚡ Quick CLI launch
│   └── mac_make_Scripts_executable.sh 🔧 Helper to make scripts executable
├── 🐳 DOCKER SUPPORT
│   ├── Dockerfile                     Container definition
│   ├── docker-compose.yml             Orchestration
│   └── .dockerignore                  Build exclusions
├── 📄 SOURCE_CODE/                    ★ MAIN SOURCE CODE
│   ├── main.py
│   ├── pipelines/
│   │   ├── coding/
│   │   ├── writing/
│   │   ├── appraisal/
│   │   ├── search/
│   │   ├── rct_search/
│   │   └── sr/                        ★ SR Pipeline
│   ├── ui/
│   │   └── app.py                     ★ Streamlit UI
│   └── utils/
│       ├── path_utils.py
│       ├── document_reader.py         ★ Multi-format reader
│       └── rag.py
├── 📝 prompts/                        ★ Prompt templates (15 files)
├── 📖 Readme/                         ★ Documentation
│   ├── HANDOFF.md                     ★ Comprehensive handoff
│   ├── README.md                      ★ This file
│   ├── Setup_Instructions_for_Users.txt
│   └── flashcard-help.html            ★ Interactive help guide
├── 🎨 assets/                         ★ UI assets
├── 📁 input/                          ★ Input files
│   ├── coding/
│   ├── writing/
│   ├── appraisal/
│   ├── search/
│   ├── rct_search/
│   └── sr/
├── 📁 output/                         ★ Generated output
├── 📁 reports/                        ★ Generated reports
├── 📁 tests/                          ★ All tests (~243 tests)
│   ├── test_appraisal.py              ★ 22 tests
│   ├── test_coding.py                 ★ 41 tests
│   ├── test_main.py                   ★ 40 tests
│   ├── test_rct_search.py             ★ 27 tests
│   ├── test_search.py                 ★ 25 tests
│   ├── test_sr.py                     ★ 19 tests
│   ├── test_ui.py                     ★ 33 tests
│   └── test_writing.py                ★ 36 tests
├── 📁 chroma_db/                      ★ RAG vector database
├── requirements.txt
├── render.yaml
├── .env.template
└── .env                               ★ API keys (local only)

Running Tests
bash

# Run all tests
python -m pytest -v

# Run specific test file
python -m pytest tests/test_main.py -v

# Run tests with coverage
python -m pytest --cov=SOURCE_CODE --cov-report=term-missing

# Run live provider tests (requires API keys)
python tests/test_live_providers.py

Current status: ~243 passed, 3 skipped, ~50% coverage
Laptop / New Machine Setup
Windows 🪟

    Install Docker Desktop: https://www.docker.com/products/docker-desktop

    Clone the repository:
    cmd

    git clone https://github.com/KW75/AI_kcMedicalResearch.git
    cd AI_kcMedicalResearch

    Double-click docker\docker_setup.bat

    Follow prompts and start working!

macOS 🍎

    Install Docker Desktop: https://www.docker.com/products/docker-desktop

    Clone the repository:
    bash

    git clone https://github.com/KW75/AI_kcMedicalResearch.git
    cd AI_kcMedicalResearch

    Make scripts executable: chmod +x docker/mac_*.sh

    Run: ./docker/mac_docker_setup.sh

    Follow prompts and start working!

No hard-coded drive letters — the project works from any path!
OCR Support (optional — for scanned PDFs)

Text-based PDFs work automatically via PyMuPDF. For scanned/image PDFs:

    Install Tesseract binary: https://github.com/UB-Mannheim/tesseract/wiki

    Install Poppler for Windows: https://github.com/oschwartz10612/poppler-windows

    Add both bin/ folders to your system PATH

    Install Python packages: pip install pytesseract pillow pdf2image

    OCR fallback activates automatically when PyMuPDF returns empty text

Known Issues
#	Issue	Priority	Root Cause
1	Lami extraction fails	High	Table 4 not found
2	WeasyPrint not installed	Medium	PDF output falls back to HTML
3	~~Low test coverage~~	✅ RESOLVED	Now ~50% coverage
Contributing

    Fork the repository

    Create a feature branch: git checkout -b feature/your-feature

    Make your changes

    Run tests: python -m pytest

    Commit and push

    Create a pull request
    '@

$readmeContent | Out-File -FilePath "Readme/README.md" -Encoding UTF8 -NoNewline

Write-Host "✅ Updated README.md with latest test status"

