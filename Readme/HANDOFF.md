
markdown

# AI kcMedicalResearch - Handoff Document
## Version 2.3.0 with Docker Support & Cross-Platform Deployment

**Date:** 2026-08-10
**Repository:** https://github.com/KW75/AI_kcMedicalResearch
**Live App:** https://ai-kcmedicalresearch.onrender.com

---

## 1. SESSION SUMMARY

This session successfully completed the full reorganization of AI kcMedicalResearch with **SOURCE_CODE structure**, **cross-platform support** (Windows + macOS), **Docker containerization**, **one-click setup** for colleagues, and **comprehensive test suite** with ~243 passing tests. The problematic `setup_colleague.bat` file has been permanently removed and replaced with professional deployment solutions.

### 1.1 SOURCE_CODE Restructure ✅ COMPLETE
- **SOURCE_CODE/**: All Python source code organized
- **scripts/**: Launcher scripts (Windows + macOS)
- **docker/**: Complete Docker support with Windows and macOS scripts
- **prompts/**: All prompt templates
- **Readme/**: Documentation and help files
- **assets/**: UI assets and icons
- **Clean root directory**: Only configuration files

### 1.2 Test Coverage Improvements ✅ NEW
- **Total Tests:** ~243 passing tests (up from 127)
- **Overall Coverage:** ~50% (up from 26%)
- **New Test Files:** 8 new test files created
- **All Tests Passing:** ✅

### 1.3 Cross-Platform Docker Support ✅ NEW
- **Windows**: `docker_setup.bat`, `docker_menu.bat`, `docker_cli.bat`
- **macOS**: `mac_docker_setup.sh`, `mac_docker_menu.sh`, `mac_docker_cli.sh`
- **One-click setup** for all platforms
- **Zero Python required** - just Docker!

### 1.4 Docker Support ✅ COMPLETE
- **Dockerfile**: Containerized application for easy deployment
- **docker-compose.yml**: Orchestration for colleagues
- **Windows Scripts**:
  - `docker_setup.bat`: Complete one-click Windows setup
  - `docker_menu.bat`: Interactive menu (CLI/UI)
  - `docker_cli.bat`: Quick CLI launch
- **macOS Scripts**:
  - `mac_docker_setup.sh`: Complete one-click macOS setup
  - `mac_docker_menu.sh`: Interactive menu (CLI/UI)
  - `mac_docker_cli.sh`: Quick CLI launch
  - `mac_make_Scripts_executable.sh`: Helper to make scripts executable
- **Zero Setup Required**: Colleagues just need Docker installed
- **Eliminates**: Python setup, virtual environment, dependency conflicts

### 1.5 Enhanced CLI/UI Launchers ✅ COMPLETE
- **Theme Detection**: Automatic dark/light background detection
- **Color-safe ANSI**: Works on both dark and light terminals
- **CLI_THEME Persistence**: User preference saved via `setx`
- **Improved Error Handling**: Better user feedback and guidance
- **First-Run Setup**: Auto-creates virtual environment if missing

### 1.6 Removed Files ✅
- **setup_colleague.bat**: Permanently removed (replaced by Docker)
- **Old Handoff Files**: Combined into this single document
- **Duplicate files**: Cleaned up throughout the project

### 1.7 Render.com Deployment ✅ (Existing)
- **Live URL:** https://ai-kcmedicalresearch.onrender.com
- **Auto-deploy:** Enabled (pushes to main auto-deploy)
- **Environment:** Python 3.11.9 with Streamlit
- **Free Tier:** 750 hours/month

### 1.8 API Key Management ✅ (Existing)
- **Sidebar Interface**: Users enter their own API keys
- **Environment Variables**: Admin pre-configures keys in Render dashboard
- **Session Storage**: Keys persist during user session
- **Provider Support**: OpenAI, Anthropic, Groq, DeepSeek, Qwen (Alibaba)

### 1.9 Dual-Mode Execution ✅ (Existing)
- **Render (Cloud)**: Runs pipelines directly in browser
- **Local**: Opens terminal window (preserves original behavior)
- **Auto-Detection**: Detects environment and uses appropriate method

### 1.10 Bug Fixes ✅
| Issue | Fix |
|-------|-----|
| `TypeError: str expected, not NoneType` for Ollama | Added provider check in `_run_cli_cloud` |
| `x-terminal-emulator` error on Render | Added Render detection in `_launch_terminal` |
| `EOFError` in Search mode | Added `--sub` argument support |
| Duplicate `[theme]` in `config.toml` | Removed duplicate section |
| White text on white background in launcher | Color-safe ANSI codes with theme detection |
| Corrupted character encoding | All files saved with UTF-8 |
| `_load_guidelines` None path issue | Fixed in writing.py |
| `_paths` doc_root key issue | Fixed in appraisal.py |
| `call_ai` import path issue | Fixed in rct_search.py |

---

## 2. QUICK ACCESS

| Resource | Link |
|----------|------|
| **Live App** | https://ai-kcmedicalresearch.onrender.com |
| **GitHub Repo** | https://github.com/KW75/AI_kcMedicalResearch |
| **Render Dashboard** | https://dashboard.render.com |

---

## 3. SYSTEM STATUS

### ✅ What's Working
| Component | Status | Details |
|-----------|--------|---------|
| **Render Deployment** | ✅ Live | Auto-deploy enabled |
| **Docker Support** | ✅ Complete | Windows + macOS scripts |
| **Windows Docker Setup** | ✅ Complete | `docker_setup.bat` one-click |
| **macOS Docker Setup** | ✅ Complete | `mac_docker_setup.sh` one-click |
| **Theme Detection** | ✅ Complete | Dark/light auto-detection |
| **CLI/UI Launchers** | ✅ Complete | Enhanced error handling |
| **API Key Sidebar** | ✅ Working | Session storage |
| **Ollama Provider** | ✅ Fixed | No API key required |
| **Search Mode** | ✅ Fixed | `--sub` support |
| **RCT Search** | ✅ Complete | PubMed + Europe PMC |
| **SR Pipeline** | ✅ Complete | 6-stage, vision-based |
| **Meta-analysis** | ✅ Complete | 4 studies, SMD with Forest plot |
| **PICO Management** | ✅ Complete | Interactive selection, creation |
| **Provider Checks** | ✅ Complete | Blocks non-vision for SR |
| **Color-safe Launcher** | ✅ Complete | Light/dark mode compatible |
| **Tests** | ✅ Complete | ~243 passed, 3 skipped |

### ❌ Known Issues
| Issue | Priority | Root Cause |
|-------|----------|------------|
| Lami extraction fails | High | Table 4 not found |
| WeasyPrint not installed | Medium | PDF output falls back to HTML |

---

## 4. TEST COVERAGE SUMMARY

### 4.1 Test Coverage by Module
| Module | Coverage | Tests | Status |
|--------|----------|-------|--------|
| **appraisal.py** | **86%** | 22 | ✅ Excellent |
| **writing.py** | **89%** | 36 | ✅ Excellent |
| **coding.py** | **78%** | 41 | ✅ Good |
| **search.py** | **72%** | 25 | ✅ Good |
| **rct_search.py** | **63%** | 27 | ✅ Good |
| **ui/app.py** | **59%** | 33 | ✅ Good |
| **main.py** | **~50%** | 40 | ✅ Good |
| **Total** | **~50%** | **~243** | ✅ |

### 4.2 New Test Files Created
| File | Tests | Status |
|------|-------|--------|
| `tests/test_appraisal.py` | 22 | ✅ Passing |
| `tests/test_coding.py` | 41 | ✅ Passing |
| `tests/test_main.py` | 40 | ✅ Passing |
| `tests/test_rct_search.py` | 27 | ✅ Passing |
| `tests/test_search.py` | 25 | ✅ Passing |
| `tests/test_sr.py` | 19 | ✅ Passing |
| `tests/test_ui.py` | 33 | ✅ Passing |
| `tests/test_writing.py` | 36 | ✅ Passing |

### 4.3 Coverage Improvement Summary
| Module | Before | After | Improvement |
|--------|--------|-------|-------------|
| **appraisal.py** | 19% | **86%** | **+67%** |
| **writing.py** | 15% | **89%** | **+74%** |
| **coding.py** | 10% | **78%** | **+68%** |
| **search.py** | 17% | **72%** | **+55%** |
| **rct_search.py** | 38% | **63%** | **+25%** |
| **ui/app.py** | 0% | **59%** | **+59%** |
| **main.py** | 39% | **~50%** | **+11%** |
| **Total** | ~26% | **~50%** | **+24%** |

---

## 5. SETUP FOR USERS

### 5.1 For Windows Colleagues 🪟

**The EASIEST way to get started:**

1. **Install Docker Desktop** (one-time):
   https://www.docker.com/products/docker-desktop

2. **Clone the repository:**
   ```cmd
   git clone https://github.com/KW75/AI_kcMedicalResearch.git
   cd AI_kcMedicalResearch

    Double-click docker\docker_setup.bat

    Follow the prompts:

        Choose C: or D: drive

        Add API keys (optional now, can do later)

        Choose CLI or UI mode

    Start using the app!

That's it! No Python, no virtual environment, no dependencies to install!
5.2 For macOS Colleagues 🍎

The EASIEST way to get started:

    Install Docker Desktop (one-time):
    https://www.docker.com/products/docker-desktop

    Clone the repository:
    bash

    git clone https://github.com/KW75/AI_kcMedicalResearch.git
    cd AI_kcMedicalResearch

    Make scripts executable (first time only):
    bash

    chmod +x docker/mac_*.sh

    Run the setup:
    bash

    ./docker/mac_docker_setup.sh

    Follow the prompts:

        Choose install location (Projects, Documents, Desktop, or Custom)

        Add API keys (optional now, can do later)

        Choose CLI or UI mode

    Start using the app!

That's it! No Python, no virtual environment, no dependencies to install!
5.3 For You (Admin) - Render Pre-configured API Keys

    Go to Render dashboard → Environment Variables

    Add:
    text

    OPENAI_API_KEY=sk-...
    ANTHROPIC_API_KEY=sk-ant-...
    DASHSCOPE_API_KEY=your_key_here
    DASHSCOPE_BASE_URL=https://ws-uv5pi4kkqbrg1vpe.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1
    DASHSCOPE_ANTHROPIC_URL=https://ws-uv5pi4kkqbrg1vpe.ap-southeast-1.maas.aliyuncs.com/apps/anthropic

    Click Save → Render restarts automatically

5.4 For Other Users (Web App)

    Open the app URL: https://ai-kcmedicalresearch.onrender.com

    Enter their own API keys in the sidebar

    Select a pipeline and run

5.5 For Local Development (Without Docker)
bash

git clone https://github.com/KW75/AI_kcMedicalResearch.git
cd AI_kcMedicalResearch

# Run CLI (auto-creates .venv on first run)
AI_kcMedicalResearch_CLI.bat  # Windows
./Mac_kcMedicalResearch_CLI.sh  # macOS

# Or run UI
AI_kcMedicalResearch_UI.bat  # Windows
./Mac_kcMedicalResearch_UI.sh  # macOS

5.6 Theme Configuration NEW

The launcher automatically detects your terminal background:

    Dark background: Uses bright ANSI colors

    Light background: Uses darker ANSI colors

    Override: Set CLI_THEME=dark or CLI_THEME=light via setx (Windows) or export (macOS/Linux)

6. HOW IT WORKS
Execution Methods
Environment	Execution Method	API Key Source
Render	Browser (no terminal)	Env vars or user input
Docker	Containerized	.env file or user input
Local	Terminal window	.env file or user input
Provider Defaults

    Default: Ollama (local, free) - no API key needed

    Cloud Providers: User enters API key in sidebar

Vision Providers (for SR)
Provider	Support	Notes
✅ Qwen	Recommended	Vision support
✅ OpenAI	Yes	GPT-4 vision
✅ Anthropic	Yes	Claude vision
✅ Groq	Yes	Vision models
❌ DeepSeek	No	Blocked for SR
❌ Ollama	No	Blocked for SR
7. FILE STRUCTURE
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
│   ├── main.py                        Core pipeline logic
│   ├── 📁 pipelines/
│   │   ├── 📁 coding/                 Coding pipeline
│   │   ├── 📁 writing/                Writing pipeline
│   │   ├── 📁 appraisal/              Appraisal pipeline
│   │   ├── 📁 search/                 Search pipeline
│   │   ├── 📁 rct_search/             RCT Search pipeline
│   │   ├── 📁 sr/                     Systematic Review pipeline
│   │   └── 📁 shared/                 Shared utilities
│   ├── 📁 ui/
│   │   └── app.py                     Main Streamlit UI
│   ├── 📁 utils/
│   │   ├── path_utils.py              Path management
│   │   ├── document_reader.py         Multi-format document reader
│   │   └── rag.py                     RAG utilities
│   └── 📁 docs/                       AI reference docs
├── 📝 prompts/                        ★ PROMPT FILES (15 files)
├── 📖 Readme/                         ★ DOCUMENTATION
│   ├── HANDOFF.md                     Comprehensive handoff
│   ├── README.md                      Quick start guide
│   ├── Setup_Instructions_for_Users.txt Simple setup guide
│   └── flashcard-help.html            Interactive help guide
├── 🎨 assets/                         ★ UI ASSETS
├── 📁 input/                          ★ INPUT FILES
│   ├── coding/
│   ├── writing/
│   ├── appraisal/
│   ├── search/
│   ├── rct_search/
│   └── sr/                            PDFs + pico_*.json
├── 📁 output/                         ★ GENERATED OUTPUT
├── 📁 reports/                        ★ GENERATED REPORTS
├── 📁 tests/                          ★ ALL TESTS (~243 tests)
│   ├── test_appraisal.py              ★ 22 tests
│   ├── test_coding.py                 ★ 41 tests
│   ├── test_main.py                   ★ 40 tests
│   ├── test_rct_search.py             ★ 27 tests
│   ├── test_search.py                 ★ 25 tests
│   ├── test_sr.py                     ★ 19 tests
│   ├── test_ui.py                     ★ 33 tests
│   └── test_writing.py                ★ 36 tests
├── 📁 chroma_db/                      ★ RAG VECTOR DATABASE
├── requirements.txt                   Python dependencies
├── render.yaml                        Render deployment config
├── .env.template                      Environment variables template
└── .env                               API keys (local only)

8. RECENT COMMITS
Commit	Description
4a77472	test: improve main.py test coverage and finalize test suite
5aa9c82	feat: major testing and code quality improvements
1436a46	docs: update Setup_Instructions_for_Users.txt with macOS Docker scripts
d1b7ab1	feat: add macOS Docker scripts for one-click Docker experience
f0d381a	refactor: reorganize Docker files in docker/ folder
a0c996f	docs: update all documentation for v2.3.0 cross-platform release
b82f4d2	feat: complete SOURCE_CODE restructure with cross-platform support
9. QUICK COMMANDS
Windows One-Click Setup 🪟
cmd

docker\docker_setup.bat

macOS One-Click Setup 🍎
bash

chmod +x docker/mac_*.sh
./docker/mac_docker_setup.sh

Docker (Manual - All Platforms)
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

Local (Without Docker)
bash

# Launch CLI
AI_kcMedicalResearch_CLI.bat  # Windows
./Mac_kcMedicalResearch_CLI.sh  # macOS

# Launch UI
AI_kcMedicalResearch_UI.bat  # Windows
./Mac_kcMedicalResearch_UI.sh  # macOS

# Run RCT Search
python SOURCE_CODE/main.py --mode rct_search --provider qwen

# Run SR Pipeline
python SOURCE_CODE/main.py --mode sr --provider qwen

# Run Tests
.venv\Scripts\python.exe -m pytest --tb=short -q
# ~243 passed, 3 skipped

# Run with coverage
.venv\Scripts\python.exe -m pytest --cov=SOURCE_CODE --cov-report=term-missing

10. TROUBLESHOOTING
Docker Issues
Issue	Solution
Docker not found	Install Docker Desktop: https://www.docker.com/products/docker-desktop
Docker not running	Start Docker Desktop from system tray/menu bar
Build fails	Check internet connection and Docker Desktop logs
Volume mount errors	Ensure folders exist: input/, output/, data/, reports/
docker_setup.bat fails	Run as Administrator, check internet connection
mac_docker_setup.sh fails	Ensure scripts are executable: chmod +x docker/mac_*.sh
App Not Loading on Render

    Check logs: Render dashboard → Logs

    Check build command: pip install --upgrade pip && pip install -r requirements.txt

    Check start command: streamlit run SOURCE_CODE/ui/app.py --server.port $PORT --server.address 0.0.0.0

API Key Not Working

    Check if entered correctly (no extra spaces)

    For Qwen: Use DASHSCOPE_API_KEY env var

    Check Render env variables are saved

Pipeline Fails

    Check logs in the UI output area

    Verify input files are in correct folder

    Check API key is valid for selected provider

Theme Not Detected

    Launcher auto-detects on first run

    Override with:

        Windows: setx CLI_THEME dark or setx CLI_THEME light

        macOS/Linux: export CLI_THEME=dark or export CLI_THEME=light

    Close and reopen terminal for changes to take effect

11. NEXT SESSION PRIORITIES
Priority	Task	Details
1	Fix Lami Extraction	Inspect pages 12-13 for Table 4
2	Install WeasyPrint	pip install weasyprint + GTK3 runtime
3	Push Docker Image	Push to Docker Hub for easier sharing
4	Linux Support	Add Linux scripts if needed
5	Improve Coverage	Target 60%+ coverage
12. ENVIRONMENT
Item	Value
Python	3.11.9
Virtual env	D:\AI_kcMedicalResearch.venv
Primary provider	Qwen (qwen3.7-plus)
Vision providers	qwen, openai, anthropic, groq
Non-vision providers	ollama, deepseek (blocked for SR)
OS	Windows (PowerShell) + macOS supported
WeasyPrint	NOT installed
Render	Free tier, 750 hours/month
Docker	Available (containerized deployment)
Tests	~243 passed, 3 skipped
Coverage	~50%
13. WORKFLOW REMINDER
powershell

# Run RCT Search (PubMed + Europe PMC)
python SOURCE_CODE/main.py --mode rct_search --provider qwen

# Run SR pipeline
python SOURCE_CODE/main.py --mode sr --provider qwen

# Run tests
.venv\Scripts\python.exe -m pytest --tb=short -q
# ~243 passed, 3 skipped

# Run with coverage
.venv\Scripts\python.exe -m pytest --cov=SOURCE_CODE --cov-report=term-missing

# Push changes (auto-deploys to Render)
git add .
git commit -m "feat: <description>"
git push origin main

14. WHAT'S NEW IN v2.3.0
Feature	Description
🐳 Docker Support	Containerized deployment, zero setup for colleagues
🪟 Windows One-Click	docker_setup.bat - clones, configures, builds, runs
🍎 macOS One-Click	mac_docker_setup.sh - full automation for Mac users
📁 SOURCE_CODE Structure	Complete project reorganization
📄 Multi-Format Documents	PDF, DOCX, Images, Text, Excel support
🔍 OCR Integration	Scanned PDFs and images - text extraction
🧠 RAG Integration	Document indexing and retrieval for all formats
🌓 Theme Detection	Auto-detects dark/light terminal backgrounds
🎨 Color-safe ANSI	Works on both dark and light terminals
🚀 Enhanced Launchers	Better error handling and user guidance
🧪 Comprehensive Tests	~243 passing tests, ~50% coverage
📊 Coverage Reports	HTML coverage reports available
🗑️ Removed setup_colleague.bat	Replaced by Docker and improved launchers
📝 Simple Instructions	Setup_Instructions_for_Users.txt - everyone can open
📄 Comprehensive Docs	Single HANDOFF.md with everything
🔧 Docker Compose	docker-compose.yml for orchestration
15. THE SETUP_COLLEAGUE.BAT SAGA - COMPLETE

The journey from broken setup to professional deployment:
Phase	Description	Status
❌ Before	setup_colleague.bat was broken with encoding issues	❌
🔧 Step 1	Removed the problematic file	✅
🎨 Step 2	Enhanced launchers with theme detection	✅
🐳 Step 3	Added Docker support	✅
🍎 Step 4	Added macOS support scripts	✅
🚀 Step 5	Created docker_setup.bat - one-click Windows setup	✅
🚀 Step 6	Created mac_docker_setup.sh - one-click macOS setup	✅
📁 Step 7	Restructured project to SOURCE_CODE/	✅
🧪 Step 8	Added comprehensive test suite (~243 tests)	✅
📖 Step 9	Completed all documentation	✅

Result: Colleagues can now go from zero to working app in 5 minutes on Windows or macOS!
16. CROSS-PLATFORM DOCKER SUPPORT SUMMARY
Platform	Setup Script	Interactive Menu	Quick CLI
Windows	docker_setup.bat	docker_menu.bat	docker_cli.bat
macOS	mac_docker_setup.sh	mac_docker_menu.sh	mac_docker_cli.sh
Manual	docker build -f docker/Dockerfile -t ai-kcmedicalresearch .	✓	✓

Handoff prepared: 2026-08-10
Version: v2.3.0-stable with cross-platform Docker support
Tests: ~243 passed, 3 skipped
Coverage: ~50%
Live App: https://ai-kcmedicalresearch.onrender.com
Repository: https://github.com/KW75/AI_kcMedicalResearch

Summary: The system is production-ready with Docker support, theme detection, enhanced launchers, full cross-platform support (Windows + macOS), and comprehensive test suite with ~243 passing tests. Colleagues can now run the app with ONE CLICK using docker_setup.bat (Windows) or mac_docker_setup.sh (macOS)! 🚀

🏆 THE SETUP_COLLEAGUE.BAT SAGA IS OFFICIALLY OVER! 🏆
'@

$handoffContent | Out-File -FilePath "Readme/HANDOFF.md" -Encoding UTF8 -NoNewline

Write-Host "✅ Updated HANDOFF.md with test coverage improvements"

