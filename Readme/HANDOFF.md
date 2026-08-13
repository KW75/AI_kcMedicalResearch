$handoff = @'
# AI kcMedicalResearch - Combined Handoff Document
## Version 2.4.1 - Health Check, UptimeRobot, Render Stability

**Date:** 2026-08-13
**Repository:** https://github.com/KW75/AI_kcMedicalResearch
**Live App:** https://ai-kcmedicalresearch.onrender.com
**Health Check:** https://ai-kcmedicalresearch.onrender.com/_stcore/health
**Uptime Monitor:** UptimeRobot (5-min interval, keeps free-tier instance warm)
**Tests:** 362 passed, 3 skipped, 11 deselected (live tests)
**Coverage:** ~50%
**Last Commit:** 361cdd5

---

## 1. PROJECT OVERVIEW

AI kcMedicalResearch is a local-first Python application providing six specialised AI pipeline modes for medical research workflows. It supports multiple LLM providers (local and cloud), multi-agent iteration loops, file-based input/output, Docker deployment, and a Streamlit web UI.

**Target Users:** Medical students, clinical researchers, academic writers.

**Default Provider:** DeepSeek (configurable via .env DEFAULT_PROVIDER)

**Fallback Chain:** DeepSeek → Qwen → Groq (configurable via FALLBACK_PROVIDERS env var)

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

### Session 3 (2026-08-13) - v2.4.0 → v2.4.1: CI/CD, Fallback Chain, Streaming, Monitoring
- **GitHub Actions CI fixed:** Pinned Python 3.11, added build-essential/cmake/python3-dev for chromadb/hnswlib compilation
- **pysqlite3 monkey-patch:** Added to tests/conftest.py for chromadb compatibility on Linux
- **pytesseract import made conditional:** Prevents CI collection errors (OCR not available on runners)
- **5 network-dependent tests marked as `@pytest.mark.live`:** Skipped in CI (require real API/Ollama)
- **Provider fallback chain:** `call_ai()` now retries on transient errors (timeout, 429, 502, 503); default chain: deepseek → qwen → groq
- **Streaming enabled by default:** CLI now streams tokens live; use `--no-stream` to disable
- **Render build fixes:** Added `--no-cache-dir` and `--prefer-binary` to pip install for free-tier memory limits
- **Render health check:** Added `healthCheckPath: /_stcore/health` to render.yaml (Streamlit built-in endpoint)
- **UptimeRobot configured:** Pings health endpoint every 5 min; prevents free-tier cold starts (30-60s sleep)
- **CI actions updated:** checkout@v5, setup-python@v6 (fixes Node.js 20 deprecation)
- **Documentation updated:** README.md, Setup_Instructions_for_Users.txt, HANDOFF.md all reflect DeepSeek default
- **Root README.md added:** GitHub now displays project overview on landing page
- **Duplicate Readme/README.md removed:** Single source of truth at repo root
- **Tests:** 362 passed, 3 skipped, 11 deselected (live)
- **CI:** Green (GitHub Actions passing)
- **Render:** Live and serving (health check: ok)

---

## 3. CURRENT STATUS

### What's Working
| Component | Status | Details |
|-----------|--------|---------|
| GitHub Actions CI | ✓ Green | 362 tests passing, Python 3.11 |
| Render Deployment | ✓ Live | Auto-deploy, --no-cache-dir --prefer-binary |
| Health Check | ✓ Active | /_stcore/health returns "ok" |
| UptimeRobot | ✓ Monitoring | 5-min pings, prevents cold starts, 100% uptime |
| Provider Fallback | ✓ Active | deepseek → qwen → groq on transient errors |
| Streaming CLI | ✓ Default | Tokens stream live; --no-stream to disable |
| DeepSeek Provider | DEFAULT | Fast, cheap, reliable for all modes |
| Ollama Provider | Fixed | Auto-detects best local model (offline/testing only) |
| Qwen Provider | Fixed | Uses `qwen-plus-latest` |
| LLM Timeouts | Fixed | 15 min for coding/writing pipelines |
| Context Window | Fixed | 32768 tokens for Ollama |
| All Tests | Passing | 362 passed, 3 skipped, 11 deselected |
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
| 4 | DeprecationWarning: invalid escape sequence in project_layout.py | Low | Add raw-string prefix |

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

**Common flags:** `--provider`, `--model`, `--mode`, `--report`, `--revise`, `--role`, `--sub`, `--dry-run`, `--no-stream`, `--resume`, `--help-guide`, `--ui`, `--list-sessions`, `--list-roles`, `--stats`, `--version`

---

## 5. AI PROVIDERS

| Provider | Flag | Env Var | Default Model | Vision | Streaming |
|----------|------|---------|---------------|--------|-----------|
| DeepSeek (DEFAULT) | `--provider deepseek` | `DEEPSEEK_API_KEY` | deepseek-v4-flash | No | Yes |
| Qwen | `--provider qwen` | `DASHSCOPE_API_KEY` | qwen-plus-latest | Yes | Yes |
| OpenAI | `--provider openai` | `OPENAI_API_KEY` | gpt-4o-mini | Yes | Yes |
| Anthropic | `--provider anthropic` | `ANTHROPIC_API_KEY` | claude-sonnet-5 | Yes | Yes |
| Groq | `--provider groq` | `GROQ_API_KEY` | llama-3.3-70b-versatile | Yes | Yes |
| Ollama (local) | `--provider ollama` | `OLLAMA_HOST` | Auto-detected (largest non-embedding) | No | Yes |

**Fallback Chain:** On transient errors (timeout, 429, 502, 503), the system automatically tries the next provider in the chain. Auth errors (401, 403) raise immediately. Default chain: `deepseek,qwen,groq`. Configure via `FALLBACK_PROVIDERS` env var. Set to empty string to disable.

**Vision requirement:** SR pipeline blocks non-vision providers (DeepSeek, Ollama).

---

## 6. ENVIRONMENT VARIABLES (.env)

```env
# Default provider (change to ollama for offline use)
DEFAULT_PROVIDER=deepseek

# Fallback chain (comma-separated, empty to disable)
FALLBACK_PROVIDERS=deepseek,qwen,groq

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
|   |-- main.py                      Core engine (~2100 lines)
|   |-- providers.py                 Provider registry, fallback chain
|   |-- streaming.py                 SSE streaming for all providers
|   |-- checkpoint.py                Pipeline checkpoint/resume
|   |-- traice_integration.py        PRISMA-trAIce disclosure generator
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
|       +-- rag.py                   RAG utilities (ChromaDB)
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
|-- tests/                           362 tests across 12 files
|-- Readme/                          Documentation and help
|   |-- HANDOFF.md                   This file (developer handoff)
|   |-- Setup_Instructions_for_Users.txt  User setup guide
|   +-- flashcard-help.html          Interactive help
|-- .github/workflows/ci.yml         GitHub Actions CI pipeline
|-- .env                             Local config (gitignored)
|-- .env.template                    Template for colleagues
|-- pytest.ini                       Pytest configuration
|-- requirements.txt                 Python dependencies (local/Windows)
|-- requirements-ci.txt              CI dependencies (Ubuntu/chromadb)
|-- requirements-render.txt          Lean requirements (Render cloud)
|-- render.yaml                      Render deployment config
+-- README.md                        Project README (GitHub landing page)

8. CI/CD PIPELINE
GitHub Actions (.github/workflows/ci.yml)

    Trigger: Push/PR to main
    Runner: ubuntu-latest, Python 3.11
    System deps: build-essential, cmake, python3-dev (for chromadb)
    Requirements: requirements-ci.txt (includes chromadb, pysqlite3-binary)
    Tests: pytest -m "not live" (excludes 5 network-dependent tests + 6 live provider tests)
    Coverage: ~50% reported via pytest-cov
    Actions: checkout@v5, setup-python@v6

Render (render.yaml)

    Trigger: Auto-deploy on push to main
    Runtime: Python 3.11.9
    Build: pip install --no-cache-dir --prefer-binary -r requirements-render.txt
    Start: streamlit run SOURCE_CODE/ui/app.py --server.port $PORT
    Health check: /_stcore/health (Streamlit built-in, returns "ok")
    Plan: Free tier
    Uptime: UptimeRobot pings every 5 min to prevent cold-start sleep

UptimeRobot Configuration

    Monitor type: HTTP(s)
    URL: https://ai-kcmedicalresearch.onrender.com/_stcore/health
    Interval: 5 minutes
    Purpose: Keeps free-tier instance warm (prevents 30-60s cold start after inactivity)
    Status: 100% uptime

Key CI/Render Fixes Applied
Fix 	Commit 	Issue
Pin Python 3.11, add build-essential 	4ff2979 	chromadb wheel compilation
Add cmake, python3-dev 	ad602d3 	hnswlib compilation
pysqlite3 monkey-patch in conftest.py 	d298f71 	chromadb sqlite3 version
Conditional pytesseract import 	fa2e618 	ModuleNotFoundError on CI
Mark 5 tests as @pytest.mark.live 	e75ae6f 	Network-dependent tests
Remove debug step, finalize 	ec72643 	Clean workflow
--no-cache-dir for Render 	463b337 	Free-tier memory limits
Update actions to v5/v6 	555674f 	Node.js 20 deprecation
Health check endpoint 	239ecae 	Zero-downtime deploys
--prefer-binary for Render 	361cdd5 	Prevent OOM source compilation
9. STREAMING
Architecture

    SOURCE_CODE/streaming.py provides stream_ai(), stream_to_console(), and tee_stream()
    All six providers support SSE streaming (OpenAI-compatible format + Anthropic + Ollama native)
    stream_to_console() prints tokens as they arrive, falls back to non-streaming on error
    tee_stream() supports custom display functions (e.g., Streamlit st.write_stream)

CLI Behavior

    Default: Streaming enabled (tokens appear live in terminal)
    Disable: --no-stream flag for batch output
    Non-TTY: Automatically disabled when stdout is not a terminal (pipes, CI)
    Fallback: If streaming connection fails, falls back to non-streaming call_ai()

10. PROVIDER FALLBACK CHAIN
How It Works

    call_ai() in main.py reads FALLBACK_PROVIDERS env var (default: deepseek,qwen,groq)
    On transient errors (timeout, 502, 503, 429, rate limit, connection refused), tries next provider
    Auth errors (401, 403) raise immediately — no wasted retries
    Prints [fallback] provider_x failed (...), trying next... warnings
    If all providers fail, raises RuntimeError with full chain attempted

Configuration

# Default fallback chain
FALLBACK_PROVIDERS=deepseek,qwen,groq

# Disable fallback (single provider only)
FALLBACK_PROVIDERS=

# Custom chain
FALLBACK_PROVIDERS=openai,anthropic,deepseek

11. TEST COVERAGE
Summary

362 passed, 3 skipped, 11 deselected in ~20s. Overall coverage: ~50%
By Module
Module 	Coverage 	Tests
writing.py 	89% 	36
appraisal.py 	86% 	22
coding.py 	78% 	41
search.py 	72% 	25
path_utils.py 	67% 	-
rct_search.py 	63% 	27
ui/app.py 	58% 	33
rag.py 	57% 	-
providers.py 	~55% 	15
streaming.py 	~45% 	12
main.py 	39% 	40
SR pipeline 	~16% 	19
traice_integration.py 	~60% 	8
Total 	~50% 	362
Running Tests

# Standard suite (excludes live provider tests)
.\.venv\Scripts\python.exe -m pytest -m "not live" --tb=short -q

# All tests including live
.\.venv\Scripts\python.exe -m pytest --tb=short -q

# Only live provider smoke tests
.\.venv\Scripts\python.exe -m pytest -m live -v

# With coverage report
.\.venv\Scripts\python.exe -m pytest --cov=SOURCE_CODE --cov-report=html

12. SETUP INSTRUCTIONS
12.1 For Colleagues - Docker (Recommended)

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
12.2 Local Development (No Docker)

# Via launcher menu
.\.venv\Scripts\python.exe scripts\launcher.py

# Direct mode execution (DeepSeek default, streaming enabled)
.\.venv\Scripts\python.exe SOURCE_CODE\main.py --mode coding
.\.venv\Scripts\python.exe SOURCE_CODE\main.py --mode writing
.\.venv\Scripts\python.exe SOURCE_CODE\main.py --mode rct_search
.\.venv\Scripts\python.exe SOURCE_CODE\main.py --mode search
.\.venv\Scripts\python.exe SOURCE_CODE\main.py --mode appraisal
.\.venv\Scripts\python.exe SOURCE_CODE\main.py --mode sr --provider qwen

# Override provider
.\.venv\Scripts\python.exe SOURCE_CODE\main.py --provider qwen
.\.venv\Scripts\python.exe SOURCE_CODE\main.py --provider ollama

# Disable streaming
.\.venv\Scripts\python.exe SOURCE_CODE\main.py --no-stream

# Resume from checkpoint
.\.venv\Scripts\python.exe SOURCE_CODE\main.py --resume

# Dry run (no LLM call)
.\.venv\Scripts\python.exe SOURCE_CODE\main.py --dry-run

# Help
.\.venv\Scripts\python.exe SOURCE_CODE\main.py --help-guide

12.3 Render.com (Cloud Web App)

    Live URL: https://ai-kcmedicalresearch.onrender.com
    Health: https://ai-kcmedicalresearch.onrender.com/_stcore/health
    Auto-deploy: Enabled (push to main triggers deploy)
    API Keys: Set in Render dashboard > Environment Variables
    Users: Enter their own keys in sidebar, or use admin-configured keys
    Uptime: UptimeRobot monitors every 5 min (prevents cold starts)

13. COMMIT HISTORY (Session 3)

361cdd5 (HEAD -> main) fix(render): add --prefer-binary to pip install to prevent OOM on free tier
239ecae ops: add health check endpoint for Render (/_stcore/health)
555674f ci: update actions to v5/v6 - fix Node.js 20 deprecation failure
d6f0833 docs: update HANDOFF.md to v2.4.0 - CI/CD, fallback, streaming
7c1707e docs: update README.md to v2.4.0 - fallback chain, streaming, updated test counts
d983be1 feat: enable streaming by default in CLI (use --no-stream to disable)
463b337 fix(render): add --no-cache-dir to prevent free-tier memory exhaustion
6755b49 feat: enable provider fallback chain by default (deepseek,qwen,groq)
ec72643 ci: remove debug step, finalize green CI workflow
e75ae6f ci: mark 5 network-dependent tests as live (skipped in CI)
fa2e618 ci: make pytesseract import conditional - fixes CI collection error
d298f71 ci: add pysqlite3 monkey-patch in conftest.py for chromadb on Linux
ad602d3 ci: add cmake and python3-dev for chromadb/hnswlib compilation
4ff2979 ci: pin Python 3.11, add build-essential, fix chromadb for CI
dad8f75 docs: update HANDOFF.md - DeepSeek default provider
b20a20c docs: update Setup Instructions - DeepSeek default, Ollama opt-in
910f465 docs: add README.md to repo root for GitHub display
73a43c2 docs: remove duplicate Readme/README.md (now at repo root)

14. KEY CONFIGURATION
Setting 	Value 	Location
DEFAULT_PROVIDER 	deepseek 	.env
FALLBACK_PROVIDERS 	deepseek,qwen,groq 	.env
OLLAMA_CONTEXT 	32768 	.env
OLLAMA_NUM_PREDICT 	8192 	.env
OLLAMA_TEMPERATURE 	0.3 	.env
MAX_ITERATIONS 	3 	SOURCE_CODE/pipelines/coding/coding.py
LLM Timeout 	900s (15 min) 	coding.py, writing.py
Streaming 	Enabled by default 	--no-stream to disable
Health Check 	/_stcore/health 	render.yaml
Uptime Monitor 	UptimeRobot (5 min) 	External service
15. TROUBLESHOOTING
Issue 	Solution
Docker not found 	Install Docker Desktop
Docker not running 	Start Docker Desktop
Ollama timeout 	Use --provider deepseek instead; or reduce model size
Empty LLM response 	Increase OLLAMA_NUM_PREDICT in .env
Launcher stdin broken 	Ensure no CREATE_NEW_PROCESS_GROUP in launcher.py
Theme wrong colours 	Set CLI_THEME=dark or CLI_THEME=light
CI fails: pytesseract 	Already conditional; check document_reader.py
CI fails: chromadb sqlite 	pysqlite3 patch in conftest.py handles this
CI fails: network tests 	Marked @pytest.mark.live, excluded with -m "not live"
Pipeline timeout 	36B models need 15 min; use cloud provider instead
App not loading on Render 	Check render.yaml uses SOURCE_CODE/ui/app.py
Render build OOM 	Uses --no-cache-dir --prefer-binary (commit 361cdd5)
Render cold start 	UptimeRobot pings every 5 min to keep instance warm
API key not working 	Check for extra spaces; verify env var name
Fallback not working 	Check FALLBACK_PROVIDERS is not empty in .env
Streaming not working 	Ensure stdout is a TTY; check --no-stream not set
16. NEXT SESSION PRIORITIES
Priority 	Task 	Details
1 	Fix Lami Extraction 	SR pipeline - Table 4 not found (pages 12-13)
2 	Raise test coverage to 60% 	Focus on main.py dispatch logic and SR pipeline
3 	Install WeasyPrint or fpdf2 	PDF export (fpdf2 is pure-Python, no GTK3 needed)
4 	Fix escape sequence warning 	Add raw-string prefix in project_layout.py
5 	Push Docker image 	Docker Hub for easier colleague sharing
6 	Integrate prompts/ into pipeline 	Load role definitions from .md files
7 	Track token usage/cost 	Display totals per session
17. LESSONS LEARNED

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
    CI requires conditional imports for system-level packages (pytesseract, easyocr, cv2)
    chromadb on Linux CI needs cmake + python3-dev + pysqlite3-binary monkey-patch
    Mark network-dependent tests as @pytest.mark.live to avoid CI flakes
    Provider fallback prevents single-point-of-failure outages
    Streaming should be opt-out (default on) for better UX
    Use --no-cache-dir --prefer-binary on memory-constrained build environments (Render free tier)
    Multi-line string replacement in PowerShell is unreliable; use line-by-line edits
    UptimeRobot free tier (50 monitors, 5-min interval) keeps Render instances warm
    Streamlit has a built-in health endpoint at /_stcore/health - no code changes needed
    Render health checks enable zero-downtime deploys (waits for healthy before routing traffic)

18. ENVIRONMENT SUMMARY
Item 	Value
Python 	3.11.9
Virtual env 	D:\AI_kcMedicalResearch\.venv
Default Provider 	DeepSeek (deepseek-v4-flash)
Fallback Chain 	deepseek → qwen → groq
Streaming 	Enabled by default (--no-stream to disable)
Ollama model 	qwen3.6:latest (36B, offline/testing only)
Qwen model 	qwen-plus-latest
OS 	Windows 11 (PowerShell 7)
Render 	Free tier, auto-deploy enabled, health check active
UptimeRobot 	5-min monitoring, 100% uptime
Docker 	Available (containerized deployment)
Tests 	362 passed, 3 skipped, 11 deselected
Coverage 	~50%
CI 	GitHub Actions - Green (checkout@v5, setup-python@v6)
Repository 	https://github.com/KW75/AI_kcMedicalResearch
Live App 	https://ai-kcmedicalresearch.onrender.com
Health Check 	https://ai-kcmedicalresearch.onrender.com/_stcore/health

Handoff prepared: 2026-08-13 Version: v2.4.1 Combines all prior handoff documents into a single source of truth. '@

[System.IO.File]::WriteAllText("PWD\Readme\HANDOFF.md", $handoff, [System.Text.UTF8Encoding]::new(false)) Write-Host "HANDOFF.md written: $((Get-Item 'Readme\HANDOFF.md').Length) bytes"


After verifying the file size, commit and push:

```powershell
git add Readme/HANDOFF.md
git commit -m "docs: update HANDOFF.md to v2.4.1 - health check, UptimeRobot, --prefer-binary"
git push origin main

This gives you a clean handoff for a new chat session. All current state is captured, including UptimeRobot monitoring, the --prefer-binary fix, health check endpoint, updated commit history, and the resolved Node.js deprecation issue.
