# AI kcMedicalResearch - Combined Handoff Document

## Version 2.4.2 - Render Recovery, Health Check, UptimeRobot Stability

**Date:** 2026-08-14  
**Repository:** https://github.com/KW75/AI_kcMedicalResearch  
**Live App:** https://ai-kcmedicalresearch.onrender.com  
**Health Check:** https://ai-kcmedicalresearch.onrender.com/_stcore/health  
**Uptime Monitor:** UptimeRobot, 5-minute interval, keeps free-tier Render instance warm  
**Tests:** 362 passed, 3 skipped, 11 deselected/live tests  
**Coverage:** ~50%  
**Latest Render Fix Commit:** 139d42d  
**Latest Documentation Commit:** 035eee1
**Latest Documentation Commit Message:** docs: update HANDOFF.md to v2.4.2 with Render recovery  
**Current Status:** CI green, Render live, health endpoint returns ok  

---

## 1. PROJECT OVERVIEW

AI kcMedicalResearch is a local-first Python application providing six specialised AI pipeline modes for medical research workflows. It supports multiple LLM providers, local and cloud inference, multi-agent iteration loops, file-based input/output, Docker deployment, checkpoint/resume, streaming CLI output, and a Streamlit web UI.

**Target Users:** Medical students, clinical researchers, academic writers.

**Default Provider:** DeepSeek, configurable via `.env` `DEFAULT_PROVIDER`.

**Fallback Chain:** DeepSeek -> Qwen -> Groq, configurable via `FALLBACK_PROVIDERS`.

**Live UI:** https://ai-kcmedicalresearch.onrender.com

---

## 2. SESSION HISTORY

### Session 1 - 2026-08-10 - v2.3.0: SOURCE_CODE Restructure and Docker

- Complete project reorganisation into `SOURCE_CODE/` structure.
- Cross-platform Docker support added.
- Windows and macOS one-click setup scripts added.
- Enhanced CLI/UI launchers with theme detection.
- Test suite expanded from 127 to ~243 tests.
- Render.com deployment configured.
- Coverage improved from ~26% to ~50%.

### Session 2 - 2026-08-11 - v2.3.1: Stability and Auto-Detection

- Recovered from destructive commit via hard reset from `62e412c` to `9aef3e6`.
- Launcher fix: removed `CREATE_NEW_PROCESS_GROUP`.
- Ollama auto-detection added: queries `/api/tags`, selects largest non-embedding model.
- Qwen model changed to `qwen-plus-latest`.
- LLM timeout increased from 5 minutes to 15 minutes.
- Ollama context settings:
  - `OLLAMA_CONTEXT=32768`
  - `OLLAMA_NUM_PREDICT=8192`
- `MAX_ITERATIONS` reduced from 5 to 3.
- Default provider changed from Ollama to DeepSeek.
- Tests: 275 passed, 6 skipped.

### Session 3 - 2026-08-13 - v2.4.0 to v2.4.1: CI/CD, Fallback, Streaming, Monitoring

- GitHub Actions CI fixed:
  - Python 3.11
  - `build-essential`
  - `cmake`
  - `python3-dev`
- `pysqlite3` monkey-patch added for ChromaDB on Linux CI.
- `pytesseract` import made conditional.
- 5 network-dependent tests marked `@pytest.mark.live`.
- Provider fallback chain added:
  - DeepSeek -> Qwen -> Groq
  - Transient errors only.
- Streaming enabled by default.
- `--no-stream` flag added to disable streaming.
- Render build fixes attempted:
  - `--no-cache-dir`
  - `--prefer-binary`
- Render health check configured:
  - `/_stcore/health`
- UptimeRobot configured:
  - 5-minute pings
  - prevents cold starts
- GitHub Actions updated:
  - `actions/checkout@v5`
  - `actions/setup-python@v6`
- README.md and HANDOFF.md updated to v2.4.1.
- Removed 12 debug/scaffolding `.py` files from project root.
- Removed stray `main_backup_20260813_141714.py` from `SOURCE_CODE/`.
- Removed orphan `scripts/.venv` directory.
- Tests: 362 passed, 3 skipped, 11 deselected.
- CI green.

### Session 4 - 2026-08-14 - v2.4.2: Render Recovery and Dashboard Configuration Fix

Render was repeatedly failing with:

`Exited with status 1`

The live app stayed up because Render kept serving the last successful deployment, but newer commits were not becoming live.

Root causes identified from Render logs:

1. Existing Render service was using dashboard-level manual settings instead of the repo `render.yaml`.
2. Render Build Command was incorrectly using:

   `pip install --upgrade pip && pip install -r requirements.txt`

3. This installed the local/Windows dependency file, which contains Windows-only packages such as:

   `pywin32==306`

4. Render Linux failed with:

   `ERROR: No matching distribution found for pywin32==306`

5. Render initially used default Python 3.14.3.
6. Render Start Command pointed to the old path:

   `src/ui/app.py`

   instead of:

   `SOURCE_CODE/ui/app.py`

7. A later partial Start Command caused:

   `bash: line 1: 10000: command not found`

   because the command started with `$PORT` instead of `streamlit run`.

Final fixes applied:

- Render Python version set to:

  `PYTHON_VERSION=3.11.9`

- Render dashboard Build Command changed to:

  `pip install --upgrade pip && pip install --no-cache-dir --only-binary=:all: -r requirements-render.txt && pip install --no-cache-dir --no-deps docx2txt==0.8`

- Render dashboard Start Command changed to:

  `streamlit run SOURCE_CODE/ui/app.py --server.address=0.0.0.0 --server.port=$PORT --server.enableCORS=false --server.enableXsrfProtection=false`

- `requirements-render.txt` pinned for free-tier stability.
- `docx2txt==0.8` removed from binary-only requirements and installed separately because it has no published wheel.
- Latest successful deploy confirmed live.
- Health endpoint verified:

  `https://ai-kcmedicalresearch.onrender.com/_stcore/health` returns `ok`.

---

## 3. CURRENT STATUS

| Component | Status | Details |
|-----------|--------|---------|
| GitHub Actions CI | GREEN | 362 tests, Python 3.11, checkout@v5, setup-python@v6 |
| Render Build | GREEN | Build successful using `requirements-render.txt` |
| Render Deploy | LIVE | Streamlit app live on Render |
| Render Health Check | ACTIVE | `/_stcore/health` returns `ok` |
| UptimeRobot | MONITORING | 5-minute pings, prevents cold starts |
| Provider Fallback | ACTIVE | DeepSeek -> Qwen -> Groq on transient errors |
| Streaming CLI | DEFAULT | Tokens stream live; `--no-stream` disables |
| DeepSeek Provider | DEFAULT | Fast, cheap, reliable default |
| Ollama Provider | WORKING | Auto-detects best local non-embedding model |
| Qwen Provider | WORKING | `qwen-plus-latest` |
| All Pipelines | WORKING | coding, writing, appraisal, search, rct_search, sr |
| Docker Support | COMPLETE | Windows and macOS one-click scripts |
| Documentation | CURRENT | README.md, HANDOFF.md, Setup Instructions |

---

## 4. KNOWN ISSUES

| # | Issue | Priority | Status |
|---|-------|----------|--------|
| 1 | Lami extraction fails, Table 4, pages 12-13 | High | Open |
| 2 | WeasyPrint not installed; PDF falls back to HTML | Medium | Open |
| 3 | Anthropic geo-restricted | Low | Use VPN or skip |
| 4 | DeprecationWarning: invalid escape sequence in `project_layout.py` | Low | Open |
| 5 | Streamlit warning: `theme.baseFontSize` invalid config option | Low | Non-blocking |

---

## 5. AI PROVIDERS

| Provider | Flag | Env Var | Default Model | Vision | Streaming |
|----------|------|---------|---------------|--------|-----------|
| DeepSeek | `--provider deepseek` | `DEEPSEEK_API_KEY` | `deepseek-v4-flash` | No | Yes |
| Qwen | `--provider qwen` | `DASHSCOPE_API_KEY` | `qwen-plus-latest` | Yes | Yes |
| OpenAI | `--provider openai` | `OPENAI_API_KEY` | `gpt-4o-mini` | Yes | Yes |
| Anthropic | `--provider anthropic` | `ANTHROPIC_API_KEY` | `claude-sonnet-5` | Yes | Yes |
| Groq | `--provider groq` | `GROQ_API_KEY` | `llama-3.3-70b-versatile` | Yes | Yes |
| Ollama | `--provider ollama` | `OLLAMA_HOST` | Auto-detected | No | Yes |

Fallback behaviour:

- Transient errors trigger fallback:
  - timeout
  - 429
  - 502
  - 503
- Auth errors raise immediately:
  - 401
  - 403

SR pipeline vision requirement:

- SR blocks non-vision providers.
- DeepSeek and Ollama should not be used for SR unless vision support is added.

---

## 6. ENVIRONMENT VARIABLES

Local `.env` example. Do not commit real API keys.

```env
DEFAULT_PROVIDER=deepseek
FALLBACK_PROVIDERS=deepseek,qwen,groq
OLLAMA_HOST=http://localhost:11434
OLLAMA_CONTEXT=32768
OLLAMA_NUM_PREDICT=8192
OLLAMA_TEMPERATURE=0.3

DEEPSEEK_API_KEY=sk-...
GROQ_API_KEY=gsk_...
DASHSCOPE_API_KEY=sk-...
DASHSCOPE_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus-latest
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
CLI_THEME=dark
```

Render dashboard environment variables:

```env
PYTHON_VERSION=3.11.9
DASHSCOPE_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
```

Do not paste the full local `.env` into Render unless intentionally adding API keys.

---

## 7. PROJECT STRUCTURE

```text
AI_kcMedicalResearch/
|-- SOURCE_CODE/
|   |-- main.py                      Core engine
|   |-- providers.py                 Provider registry and fallback chain
|   |-- streaming.py                 SSE streaming for all providers
|   |-- checkpoint.py                Pipeline checkpoint/resume
|   |-- traice_integration.py        PRISMA-trAIce disclosure generator
|   |-- pipelines/
|   |   |-- coding/                  Builder > Reviewer > Tester
|   |   |-- writing/                 Writer > Editor > QA
|   |   |-- appraisal/               Appraiser > Methodologist > Summariser
|   |   |-- search/                  Researcher
|   |   |-- rct_search/              Formulator > Searcher > Validator
|   |   |-- sr/                      6-stage Systematic Review
|   |   +-- shared/                  Shared utilities
|   |-- ui/
|   |   +-- app.py                   Streamlit web UI
|   +-- utils/
|       |-- path_utils.py            Path management
|       |-- document_reader.py       Multi-format reader
|       +-- rag.py                   RAG utilities
|-- scripts/
|   |-- launcher.py                  Interactive TUI launcher
|   |-- windows/                     Windows batch scripts
|   +-- macos/                       macOS shell scripts
|-- docker/
|   |-- Dockerfile
|   |-- docker-compose.yml
|   |-- docker_setup.bat
|   +-- mac_docker_setup.sh
|-- docs/                            Mode guidelines
|-- prompts/                         Role prompt files
|-- input/                           Input files by mode
|-- output/                          Generated outputs by mode
|-- reports/                         Generated reports by mode
|-- tests/                           Test suite
|-- Readme/
|   |-- HANDOFF.md
|   +-- Setup_Instructions_for_Users.txt
|-- .github/workflows/ci.yml
|-- render.yaml
|-- requirements.txt                 Local/Windows dependencies
|-- requirements-ci.txt              CI dependencies
|-- requirements-render.txt          Render dependencies
|-- pytest.ini
+-- README.md
```

---

## 8. CI/CD PIPELINE

### GitHub Actions

- Trigger: push/PR to `main`
- Runner: `ubuntu-latest`
- Python: 3.11
- System dependencies:
  - `build-essential`
  - `cmake`
  - `python3-dev`
- Actions:
  - `actions/checkout@v5`
  - `actions/setup-python@v6`
- Test command:

```bash
python -m pytest -m "not live" --tb=short -q
```

- Coverage: ~50%

### Render

Important: existing Render service uses dashboard-level manual settings. Do not assume `render.yaml` is the only source of truth.

Render dashboard Build Command:

```bash
pip install --upgrade pip && pip install --no-cache-dir --only-binary=:all: -r requirements-render.txt && pip install --no-cache-dir --no-deps docx2txt==0.8
```

Render dashboard Start Command:

```bash
streamlit run SOURCE_CODE/ui/app.py --server.address=0.0.0.0 --server.port=$PORT --server.enableCORS=false --server.enableXsrfProtection=false
```

Render Python version:

```text
PYTHON_VERSION=3.11.9
```

Health check:

```text
/_stcore/health
```

Plan:

```text
Free tier
```

### UptimeRobot

- URL: https://ai-kcmedicalresearch.onrender.com/_stcore/health
- Interval: 5 minutes
- Purpose: prevent Render free-tier cold starts
- Current status: monitoring

---

## 9. KEY FIXES APPLIED

| Fix | Commit/Location | Issue |
|-----|-----------------|-------|
| Pin Python 3.11 and build-essential in CI | 4ff2979 | ChromaDB compilation |
| Add cmake and python3-dev | ad602d3 | hnswlib compilation |
| pysqlite3 monkey-patch | d298f71 | ChromaDB sqlite3 on CI |
| Conditional pytesseract import | fa2e618 | CI collection error |
| Mark live tests | e75ae6f | Network-dependent tests |
| Add no-cache pip install | 463b337 | Render memory pressure |
| Update GitHub Actions v5/v6 | 555674f | Node.js 20 deprecation |
| Add health check endpoint | 239ecae | Render health checks |
| Add prefer-binary | 361cdd5 | Reduce source builds |
| Remove debug scripts | eed80c0 | Clean project root |
| Remove backup file | ef16acd | Clean SOURCE_CODE |
| Pin Render deps and force binary wheels | e3df5be | Render dependency drift |
| Allow docx2txt source install | f522b95 | docx2txt has no wheel |
| Install docx2txt separately | 139d42d | Avoid mixed binary/source resolver issue |
| Correct Render dashboard Build Command | Dashboard | Use requirements-render.txt, not requirements.txt |
| Correct Render dashboard Start Command | Dashboard | Use SOURCE_CODE/ui/app.py |

---

## 10. STREAMING

Files:

```text
SOURCE_CODE/streaming.py
```

Functions:

- `stream_ai()`
- `stream_to_console()`
- `tee_stream()`

Behaviour:

- All providers support streaming.
- Streaming is enabled by default.
- Disable with:

```bash
--no-stream
```

- Non-TTY output auto-disables streaming.
- On streaming error, fallback to non-streaming.

---

## 11. PROVIDER FALLBACK CHAIN

`call_ai()` reads:

```env
FALLBACK_PROVIDERS=deepseek,qwen,groq
```

Behaviour:

- Transient failures attempt next provider.
- Auth failures raise immediately.
- Logs example:

```text
[fallback] provider_x failed (...), trying next...
```

- If all providers fail, raises RuntimeError with full chain.

---

## 12. TEST COVERAGE

| Module | Coverage | Tests |
|--------|----------|-------|
| writing.py | 89% | 36 |
| appraisal.py | 86% | 22 |
| coding.py | 78% | 41 |
| search.py | 72% | 25 |
| path_utils.py | 67% | - |
| rct_search.py | 63% | 27 |
| ui/app.py | 58% | 33 |
| rag.py | 57% | - |
| providers.py | ~55% | 15 |
| streaming.py | ~45% | 12 |
| main.py | 39% | 40 |
| SR pipeline | ~16% | 19 |
| traice_integration.py | ~60% | 8 |
| Total | ~50% | 362 |

---

## 13. SETUP

### Docker - Recommended

Windows:

```cmd
git clone https://github.com/KW75/AI_kcMedicalResearch.git
cd AI_kcMedicalResearch
docker\docker_setup.bat
```

macOS:

```bash
git clone https://github.com/KW75/AI_kcMedicalResearch.git
cd AI_kcMedicalResearch
chmod +x docker/mac_*.sh
./docker/mac_docker_setup.sh
```

### Local Development

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe SOURCE_CODE\main.py --mode coding
.\.venv\Scripts\python.exe SOURCE_CODE\main.py --mode writing
.\.venv\Scripts\python.exe SOURCE_CODE\main.py --mode appraisal
.\.venv\Scripts\python.exe SOURCE_CODE\main.py --mode search
.\.venv\Scripts\python.exe SOURCE_CODE\main.py --mode rct_search
.\.venv\Scripts\python.exe SOURCE_CODE\main.py --mode sr --provider qwen
.\.venv\Scripts\python.exe SOURCE_CODE\main.py --no-stream
.\.venv\Scripts\python.exe SOURCE_CODE\main.py --resume
.\.venv\Scripts\python.exe SOURCE_CODE\main.py --dry-run
```

### Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -m "not live" --tb=short -q
.\.venv\Scripts\python.exe -m pytest --cov=SOURCE_CODE --cov-report=html
```

---

## 14. KEY CONFIGURATION

| Setting | Value | Location |
|---------|-------|----------|
| `DEFAULT_PROVIDER` | deepseek | `.env` |
| `FALLBACK_PROVIDERS` | deepseek,qwen,groq | `.env` |
| `OLLAMA_CONTEXT` | 32768 | `.env` |
| `OLLAMA_NUM_PREDICT` | 8192 | `.env` |
| `MAX_ITERATIONS` | 3 | `pipelines/coding/coding.py` |
| LLM timeout | 900s / 15 min | coding/writing pipeline files |
| Streaming | Default on | `--no-stream` disables |
| Health check | `/_stcore/health` | Render |
| Uptime monitor | 5-minute interval | UptimeRobot |
| Render Python | 3.11.9 | Render dashboard env var |
| Render build deps | `requirements-render.txt` | Render dashboard Build Command |

---

## 15. TROUBLESHOOTING

| Issue | Solution |
|-------|----------|
| Ollama timeout | Use `--provider deepseek` or reduce model size |
| Empty LLM response | Increase `OLLAMA_NUM_PREDICT` |
| CI fails: chromadb | Check pysqlite3 patch in `conftest.py` |
| CI fails: network tests | Ensure live tests marked `@pytest.mark.live` |
| Render installs `requirements.txt` | Fix dashboard Build Command to use `requirements-render.txt` |
| Render fails on `pywin32==306` | It is using the wrong requirements file |
| Render fails on `src/ui/app.py` | Fix Start Command to `SOURCE_CODE/ui/app.py` |
| Render runs `$PORT ... command not found` | Start Command is missing `streamlit run SOURCE_CODE/ui/app.py` |
| Render build OOM | Use pinned `requirements-render.txt` and `--only-binary=:all:` |
| Render cold start | UptimeRobot pings every 5 minutes |
| Fallback not working | Check `FALLBACK_PROVIDERS` is not empty |
| Streaming broken | Check stdout is TTY; check `--no-stream` |
| Streamlit `theme.baseFontSize` warning | Remove invalid config key from Streamlit config |

---

## 16. NEXT SESSION PRIORITIES

| Priority | Task | Details |
|----------|------|---------|
| 1 | Fix Lami extraction | SR pipeline Table 4, pages 12-13 |
| 2 | Add visible app version/commit | Show current commit/version in Streamlit sidebar |
| 3 | Raise coverage to 60% | Focus: `main.py` and SR pipeline |
| 4 | PDF export via fpdf2 | Pure-Python, no GTK3 dependency |
| 5 | Fix escape sequence warning | Raw-string prefix in `project_layout.py` |
| 6 | Remove invalid Streamlit config key | `theme.baseFontSize` warning |
| 7 | Push Docker image | Docker Hub for colleague sharing |
| 8 | Track token usage/cost | Per-session totals |

---

## 17. LESSONS LEARNED

- Never use `CREATE_NEW_PROCESS_GROUP` for interactive CLI on Windows.
- Never hardcode model versions if `*-latest` aliases are available.
- Large local models, such as 36B, need 15-minute timeouts.
- DeepSeek is better as default provider than large local Ollama for production.
- Render dashboard settings can override or ignore assumptions from `render.yaml`.
- Always inspect Render logs; `Exited with status 1` is only a summary.
- Render Linux must not install Windows-only packages such as `pywin32`.
- Use `requirements-render.txt` for Render, not `requirements.txt`.
- Use pinned Render dependencies to avoid dependency drift.
- `docx2txt==0.8` has no published wheel and must be installed separately or allowed from source.
- Streamlit app path is `SOURCE_CODE/ui/app.py`, not `src/ui/app.py`.
- Render Start Command must begin with `streamlit run`, not `$PORT`.
- UptimeRobot 5-minute monitoring keeps Render free-tier instances warm.
- Streamlit has built-in `/_stcore/health`.
- Provider fallback prevents single-provider outages.
- Streaming should be opt-out for better UX.
- Multi-line PowerShell replacement can be unreliable; verify files with `Get-Content`.
- Mark network tests as `@pytest.mark.live` to avoid CI flakes.
- ChromaDB on Linux CI needs `cmake`, `python3-dev`, and `pysqlite3`.

---

## 18. ENVIRONMENT SUMMARY

| Item | Value |
|------|-------|
| Python | 3.11.9 |
| Virtual env | `D:\AI_kcMedicalResearch\.venv` or `D:\AI_kcMedicalResearch.venv` depending on local setup |
| Default Provider | DeepSeek |
| Default Model | `deepseek-v4-flash` |
| Fallback | DeepSeek -> Qwen -> Groq |
| Streaming | Default on, `--no-stream` disables |
| OS | Windows 11, PowerShell |
| Render | Free tier, dashboard-configured build/start commands |
| Tests | 362 passed, 3 skipped, 11 deselected |
| Coverage | ~50% |
| CI | GitHub Actions green |
| Repo | https://github.com/KW75/AI_kcMedicalResearch |
| Live | https://ai-kcmedicalresearch.onrender.com |
| Health | https://ai-kcmedicalresearch.onrender.com/_stcore/health |
| Latest Commit | 139d42d |

---

## 19. FINAL VERIFIED RENDER SETTINGS

Render dashboard Build Command:

```bash
pip install --upgrade pip && pip install --no-cache-dir --only-binary=:all: -r requirements-render.txt && pip install --no-cache-dir --no-deps docx2txt==0.8
```

Render dashboard Start Command:

```bash
streamlit run SOURCE_CODE/ui/app.py --server.address=0.0.0.0 --server.port=$PORT --server.enableCORS=false --server.enableXsrfProtection=false
```

Render environment variable:

```env
PYTHON_VERSION=3.11.9
```

Health endpoint:

```text
https://ai-kcmedicalresearch.onrender.com/_stcore/health
```

Expected response:

```text
ok
```

---

Handoff prepared: 2026-08-14  
Version: v2.4.2  
Single source of truth for next session.