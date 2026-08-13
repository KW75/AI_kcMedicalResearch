# AI kcMedicalResearch - Combined Handoff Document
## Version 2.3.1 - Stability, Auto-Detection & Documentation Update

**Date:** 2026-08-13
**Repository:** https://github.com/KW75/AI_kcMedicalResearch
**Live App:** https://ai-kcmedicalresearch.onrender.com
**Tests:** 275 passed, 6 skipped, 0 warnings
**Coverage:** ~48%
**Last Commit:** 68ce91f

---

## 1. PROJECT OVERVIEW

AI kcMedicalResearch is a local-first Python application providing six specialised AI pipeline modes for medical research workflows. It supports multiple LLM providers (local and cloud), multi-agent iteration loops, file-based input/output, Docker deployment, and a Streamlit web UI.

**Target Users:** Medical students, clinical researchers, academic writers.

**Default Provider:** DeepSeek (configurable via .env DEFAULT_PROVIDER)

---

## 2. SESSION HISTORY

### Session 1 (2026-08-10) - v2.3.0: SOURCE_CODE Restructure & Docker
- Complete project reorganisation into `SOURCE_CODE/` structure
- Cross-platform Docker support (Windows + macOS one-click scripts)
- Enhanced CLI/UI launchers with theme detection
- Removed broken `setup_colleague.bat`
- Test suite expanded from 127 to ~243 tests
- Render.com deployment configured
- Coverage improved from ~26% to ~50%

### Session 2 (2026-08-11) - v2.3.1: Stability & Auto-Detection
- **Destructive commit recovery:** Commit `62e412c` deleted 2027 lines from main.py; recovered via hard reset to `9aef3e6`, force pushed, reflog pruned
- **Launcher fix:** Removed `CREATE_NEW_PROCESS_GROUP` (detached stdin); added explicit `stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr`
- **Ollama auto-detection:** Queries `/api/tags`, selects largest non-embedding model (36B qwen3.6)
- **Qwen model:** Changed from hardcoded `qwen3.7-plus` to `qwen-plus-latest`
- **LLM timeout:** Increased from 5 min to 15 min for large local models
- **Context window:** Increased `OLLAMA_CONTEXT` to 32768, `OLLAMA_NUM_PREDICT` to 8192
- **MAX_ITERATIONS:** Reduced from 5 to 3 (prevents timeouts with 36B models)
- **Test rewrite:** `test_live_providers.py` rewritten for pytest compatibility; root `pytest.ini` added
- **Documentation restructure:** `docs/` reorganised with `docs/project/` for PRD/architecture/decision-log, expanded `docs/coding/` standards, fixed all path references in `prompts/`
- **Default provider changed:** ollama -> deepseek (Ollama 36B too slow for production)
- **Render fix:** startCommand path corrected, lean requirements-render.txt created
- **Tests:** 275 passed, 6 skipped, 0 warnings

---

## 3. CURRENT STATUS

### What's Working
| Component | Status | Details |
|-----------|--------|---------|
| Launcher | Fixed | stdin properly inherited by subprocess |
| DeepSeek Provider | DEFAULT | Fast, cheap, reliable for all modes |
| Ollama Provider | Fixed | Auto-detects best local model (offline/testing only) |
| Qwen Provider | Fixed | Uses `qwen-plus-latest` |
| LLM Timeouts | Fixed | 15 min for coding/writing pipelines |
| Context Window | Fixed | 32768 tokens for Ollama |
| All Tests | Passing | 275 passed, 6 skipped, 0 warnings |
| Render Deployment | Live | Auto-deploy from main branch |
| Docker Support | Complete | Windows + macOS scripts |
| CLI/UI Launchers | Complete | Theme detection, error handling |
| All Pipelines | Working | coding, writing, appraisal, search, rct_search, sr |
| Documentation | Complete | All modes have docs injected into prompts |

### Known Issues
| # | Issue | Priority | Status |
|---|-------|----------|--------|
| 1 | Lami extraction fails (Table 4) | High | Open |
| 2 | WeasyPrint not installed | Medium | PDF falls back to HTML |
| 3 | Anthropic geo-restricted | Low | Use VPN or skip |

---

## 4. SUPPORTED MODES

| Mode | Flag | Roles | Input | Output |
|------|------|-------|-------|--------|
| Coding | `--mode coding` | Builder > Reviewer > Tester (3 iterations) | `input/coding/` | `output/coding/` + `reports/coding/` |
| Coding Revise | `--mode coding --revise` | Builder > Reviewer > Tester | `input/coding/` | same |
| Writing | `--mode writing` | Writer > Editor > QA | `input/writing/` | `output/writing/` + `reports/writing/` |
| Writing Report | `--mode writing --report` | Writer > Editor > QA | `input/writing/` | same |
| Appraisal | `--mode appraisal` | Appraiser > Methodologist > Summariser | `input/appraisal/` | `output/appraisal/` + `reports/appraisal/` |
| Search | `--mode search` | Researcher | interactive | `output/search/` + `reports/search/` |
| RCT Search | `--mode rct_search` | Formulator > Searcher > Validator | `input/rct_search/` | `output/rct_search/` |
| SR | `--mode sr` | SR Methodologist (6-stage) | `input/sr/` (.pdf) | `output/sr/` + `reports/sr/` |

**Common flags:** `--provider`, `--model`, `--report`, `--revise`, `--role`, `--sub`, `--dry-run`, `--help-guide`, `--ui`, `--list-sessions`, `--list-roles`, `--stats`

---

## 5. AI PROVIDERS

| Provider | Flag | Env Var | Default Model | Vision |
|----------|------|---------|---------------|--------|
| DeepSeek (DEFAULT) | `--provider deepseek` | `DEEPSEEK_API_KEY` | deepseek-v4-flash | No |
| Qwen | `--provider qwen` | `DASHSCOPE_API_KEY` | qwen-plus-latest | Yes |
| OpenAI | `--provider openai` | `OPENAI_API_KEY` | gpt-4o-mini | Yes |
| Anthropic | `--provider anthropic` | `ANTHROPIC_API_KEY` | claude-haiku-4-5 | Yes |
| Groq | `--provider groq` | `GROQ_API_KEY` | llama-3.1-8b-instant | Yes |
| Ollama (local) | `--provider ollama` | `OLLAMA_HOST` | Auto-detected (largest non-embedding) | No |

**Note:** Ollama with large models (36B) is too slow for production use (timeouts on coding and writing pipelines). DeepSeek is the default. Use `--provider ollama` only for offline/testing scenarios with small models.

**Ollama auto-detection:** If `OLLAMA_MODEL` is unset, queries `http://localhost:11434/api/tags` and selects the largest non-embedding model.

**Vision requirement:** SR pipeline blocks non-vision providers (DeepSeek, Ollama).

---

## 6. ENVIRONMENT VARIABLES (.env)

```env
# Default provider (change to ollama for offline use)
DEFAULT_PROVIDER=deepseek

# Local Ollama (for offline/testing)
OLLAMA_HOST=http://localhost:11434
# OLLAMA_MODEL=                        # leave empty for auto-detect
OLLAMA_CONTEXT=32768
OLLAMA_NUM_PREDICT=8192
OLLAMA_TEMPERATURE=0.3

# Cloud Providers
DEEPSEEK_API_KEY=sk-...
GROQ_API_KEY=gsk_...
DASHSCOPE_API_KEY=sk-...
DASHSCOPE_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus-latest
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# RAG
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text

# Theme
CLI_THEME=dark

7. PROJECT STRUCTURE

AI_kcMedicalResearch/
|-- SOURCE_CODE/                     Main source code
|   |-- main.py                      Core engine (2438 lines)
|   |-- pipelines/
|   |   |-- coding/                  Builder > Reviewer > Tester
|   |   |-- writing/                 Writer > Editor > QA
|   |   |-- appraisal/              Appraiser > Methodologist > Summariser
|   |   |-- search/                  Researcher
|   |   |-- rct_search/             Formulator > Searcher > Validator
|   |   |-- sr/                      6-stage Systematic Review
|   |   +-- shared/                  Shared utilities
|   |-- ui/
|   |   +-- app.py                   Streamlit web UI
|   +-- utils/
|       |-- path_utils.py            Path management
|       |-- document_reader.py       Multi-format reader (PDF, DOCX, images)
|       +-- rag.py                   RAG utilities
|-- scripts/
|   |-- launcher.py                  Interactive TUI launcher
|   |-- windows/                     Windows batch scripts
|   +-- macos/                       macOS shell scripts
|-- docker/
|   |-- Dockerfile                   Container definition
|   |-- docker-compose.yml           Orchestration
|   |-- docker_setup.bat             One-click Windows setup
|   |-- mac_docker_setup.sh          One-click macOS setup
|   +-- (other docker scripts)
|-- docs/                            MODE GUIDELINES (injected into LLM prompts)
|   |-- project/                     PRD, architecture, decision-log
|   |-- coding/                      coding-standards, test-strategy
|   |-- writing/                     editorial-standards, style-guide, qa-checklist, project-brief
|   |-- appraisal/                   appraisal-guide, scoring-criteria
|   |-- search/                      search-guide, topic.md.example
|   +-- rct_search/                  database-guide, pico-framework, validation-criteria
|-- prompts/                         15 role prompt files (reference only, not loaded)
|-- input/                           Input files per mode
|-- output/                          Generated output per mode
|-- reports/                         Generated reports per mode
|-- tests/                           275 tests across 9 files
|-- Readme/                          Documentation and help
|-- .env                             Local config (gitignored)
|-- .env.template                    Template for colleagues
|-- pytest.ini                       Pytest configuration
|-- requirements.txt                 Python dependencies (local/Windows)
|-- requirements-render.txt          Lean requirements (Render cloud)
|-- render.yaml                      Render deployment config
+-- README.md                        Project README

8. DOCUMENTATION STRUCTURE

Guidelines are automatically loaded from docs/<mode>/ and injected into the LLM system prompt for each pipeline.

docs/
|-- project/              (project-level, not injected)
|   |-- PRD.md            Product requirements (all 6 modes, 6 providers)
|   |-- architecture.md   Actual SOURCE_CODE/pipelines structure
|   +-- decision-log.md   Key decisions from sessions
|-- coding/               (injected into Builder/Reviewer/Tester)
|   |-- coding-standards.md   Python, HTML/JS, AI agent rules, output format
|   +-- test-strategy.md      Tester role, test plan, PASS/FAIL criteria
|-- writing/              (injected into Writer/Editor/QA)
|   |-- editorial-standards.md
|   |-- style-guide.md
|   |-- qa-checklist.md
|   +-- project-brief.md
|-- appraisal/            (injected into Appraiser/Methodologist/Summariser)
|   |-- appraisal-guide.md
|   +-- scoring-criteria.md
|-- search/               (injected into Researcher)
|   |-- search-guide.md
|   +-- topic.md.example
+-- rct_search/           (injected into Formulator/Searcher/Validator)
    |-- database-guide.md
    |-- pico-framework.md
    |-- validation-criteria.md
    +-- topic.md.example

Note: The prompts/ folder contains 15 role definition markdown files but these are NOT loaded by any pipeline. Pipelines use hard-coded role definitions via _build_system_prompt(). The prompts/ folder serves as reference documentation only.
9. TEST COVERAGE
Summary

275 passed, 6 skipped in ~106s
Overall coverage: ~48%

By Module
Module 	Coverage 	Tests
writing.py 	89% 	36
appraisal.py 	86% 	22
coding.py 	78% 	41
search.py 	72% 	25
path_utils.py 	67% 	-
rct_search.py 	63% 	27
ui/app.py 	59% 	33
rag.py 	57% 	-
main.py 	39% 	40
SR pipeline 	~16% 	19
test_live_providers.py 	- 	6 (live)
Total 	~48% 	275
Running Tests

# Standard suite (excludes live provider tests)
.\.venv\Scripts\python.exe -m pytest -m "not live" --tb=short -q

# All tests including live
.\.venv\Scripts\python.exe -m pytest --tb=short -q

# Only live provider smoke tests
.\.venv\Scripts\python.exe -m pytest -m live -v

# With coverage report
.\.venv\Scripts\python.exe -m pytest --cov=SOURCE_CODE --cov-report=html

10. SETUP INSTRUCTIONS
10.1 For Colleagues - Docker (Recommended)

Windows:

git clone https://github.com/KW75/AI_kcMedicalResearch.git
cd AI_kcMedicalResearch
docker\docker_setup.bat

macOS:

git clone https://github.com/KW75/AI_kcMedicalResearch.git
cd AI_kcMedicalResearch
chmod +x docker/mac_*.sh
./docker/mac_docker_setup.sh

Total setup ~5 minutes. No Python install needed - just Docker Desktop.
10.2 Docker Manual Commands

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

# UI mode (Streamlit)
docker run -it --rm -p 8501:8501 \
    -v $(pwd)/input:/app/input \
    -v $(pwd)/output:/app/output \
    -v $(pwd)/reports:/app/reports \
    --env-file .env \
    --add-host host.docker.internal:host-gateway \
    ai-kcmedicalresearch \
    streamlit run SOURCE_CODE/ui/app.py --server.port=8501 --server.address=0.0.0.0

10.3 Local Development (No Docker)

# Via launcher menu
.\.venv\Scripts\python.exe scripts\launcher.py

# Direct mode execution (DeepSeek is default provider)
.\.venv\Scripts\python.exe SOURCE_CODE\main.py --mode coding
.\.venv\Scripts\python.exe SOURCE_CODE\main.py --mode writing
.\.venv\Scripts\python.exe SOURCE_CODE\main.py --mode rct_search
.\.venv\Scripts\python.exe SOURCE_CODE\main.py --mode search
.\.venv\Scripts\python.exe SOURCE_CODE\main.py --mode appraisal
.\.venv\Scripts\python.exe SOURCE_CODE\main.py --mode sr --provider qwen

# Override provider
.\.venv\Scripts\python.exe SOURCE_CODE\main.py --provider qwen
.\.venv\Scripts\python.exe SOURCE_CODE\main.py --provider ollama

# Dry run (no LLM call)
.\.venv\Scripts\python.exe SOURCE_CODE\main.py --dry-run

# Help
.\.venv\Scripts\python.exe SOURCE_CODE\main.py --help-guide

10.4 Render.com (Cloud Web App)

    Live URL: https://ai-kcmedicalresearch.onrender.com
    Auto-deploy: Enabled (push to main triggers deploy)
    API Keys: Set in Render dashboard > Environment Variables
    Users: Enter their own keys in sidebar, or use admin-configured keys

11. COMMIT HISTORY

68ce91f (HEAD -> main) feat: change default provider from ollama to deepseek
5f944cc docs: replace dated handoff with combined HANDOFF.md, update README
5b1054b docs: replace dated handoff with combined HANDOFF.md, update README
af488dd test: update MAX_ITERATIONS assertion from 5 to 3
794416f docs: restructure docs/, add all mode guidelines, fix prompt paths
90d6c3d fix: increase Ollama context to 32768, num_predict to 8192
a0cde58 fix: increase LLM timeout from 5 to 15 minutes
d42f82b fix: rewrite test_live_providers.py for pytest compatibility
2d71bfc feat: auto-detect best Ollama model, make Qwen model configurable
428e190 fix: remove CREATE_NEW_PROCESS_GROUP from launcher
9aef3e6 fix: resolve path issues, encoding, launcher, and UI frame alignment

Note: Destructive commit 62e412c has been permanently purged from history.
12. KEY CONFIGURATION
Setting 	Value 	Location
DEFAULT_PROVIDER 	deepseek 	.env (override with --provider flag)
OLLAMA_CONTEXT 	32768 	.env
OLLAMA_NUM_PREDICT 	8192 	.env
OLLAMA_TEMPERATURE 	0.3 	.env
MAX_ITERATIONS 	3 	SOURCE_CODE/pipelines/coding/coding.py
LLM Timeout 	900s (15 min) 	coding.py, writing.py
13. OLLAMA MODEL AUTO-DETECTION

The system queries http://localhost:11434/api/tags at startup and selects the largest non-embedding model:
Model 	Size 	Selected?
qwen3.6:latest 	36.0B 	Yes (largest)
llama3.2:latest 	3.2B 	Skipped
nomic-embed-text:latest 	137M 	Skipped (embedding)
qwen2.5-coder:3b 	3.1B 	Skipped

Override: Set OLLAMA_MODEL=your-model-name in .env

Warning: Ollama with 36B models times out on coding (Builder+Reviewer+Tester iterations) and writing (long-form generation). Use DeepSeek or Qwen for production work.
14. TROUBLESHOOTING
Issue 	Solution
Docker not found 	Install Docker Desktop
Docker not running 	Start Docker Desktop
Ollama timeout 	Use --provider deepseek instead; or reduce model size
Empty LLM response 	Increase OLLAMA_NUM_PREDICT in .env
Launcher stdin broken 	Ensure no CREATE_NEW_PROCESS_GROUP in launcher.py
Theme wrong colours 	Set CLI_THEME=dark or CLI_THEME=light
Tests fail on MAX_ITERATIONS 	Ensure test asserts == 3 not == 5
Tests fail on default provider 	Ensure test asserts == "deepseek" not == "ollama"
Pipeline timeout 	36B models need 15 min; use cloud provider instead
App not loading on Render 	Check render.yaml uses SOURCE_CODE/ui/app.py
Render build fails 	Uses requirements-render.txt (no pywin32/textract/easyocr)
API key not working 	Check for extra spaces; verify env var name
15. NEXT SESSION PRIORITIES
Priority 	Task 	Details
1 	Fix Lami Extraction 	SR pipeline - Table 4 not found (pages 12-13)
2 	Install WeasyPrint 	pip install weasyprint + GTK3 runtime for PDF
3 	Improve main.py coverage 	Largest file at 39%, biggest impact
4 	Push Docker image 	Docker Hub for easier colleague sharing
5 	Target 60% overall coverage 	Focus on SR pipeline modules
6 	Integrate prompts/ into pipeline 	Load role definitions from .md files instead of hard-coding
16. LESSONS LEARNED

    Never use CREATE_NEW_PROCESS_GROUP for interactive CLI tools on Windows - it detaches stdin
    Never hardcode model versions - use auto-detection or *-latest aliases
    Test files must not call sys.exit() at module level - pytest imports all test files
    Always verify line counts after any "optimization" commit that claims small changes
    Force push + reflog prune is the correct recovery for destructive commits on single-developer repos
    Large local models (36B) need longer timeouts - 5 min is too short for complex prompts
    Context window must accommodate full prompt - 8192 tokens is too small; 32768 works
    Reduce iteration count for local models - 3 iterations sufficient; 5 causes timeouts
    Documentation belongs in docs/<mode>/ - project-level docs go in docs/project/
    prompts/ folder is dead weight unless explicitly loaded by pipeline code
    Ollama 36B is NOT viable for production - use DeepSeek as default provider
    Render requires lean requirements - no pywin32, textract, easyocr, opencv on Linux

17. ENVIRONMENT SUMMARY
Item 	Value
Python 	3.11.9
Virtual env 	D:\AI_kcMedicalResearch.venv
Default Provider 	DeepSeek (deepseek-v4-flash)
Ollama model 	qwen3.6:latest (36B, offline/testing only)
Qwen model 	qwen-plus-latest
OS 	Windows 11 (PowerShell 7)
Render 	Free tier, auto-deploy enabled
Docker 	Available (containerized deployment)
Tests 	275 passed, 6 skipped
Coverage 	~48%
Repository 	https://github.com/KW75/AI_kcMedicalResearch
Live App 	https://ai-kcmedicalresearch.onrender.com

Handoff prepared: 2026-08-13 Version: v2.3.1-stable Combines all prior handoff documents into a single source of truth. '@

[System.IO.File]::WriteAllText("PWD\Readme\HANDOFF.md", $handoff, [System.Text.UTF8Encoding]::new(false))
Verify

Write-Host "HANDOFF.md written: $((Get-Item 'Readme\HANDOFF.md').Length) bytes"

