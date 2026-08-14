# AI kcMedicalResearch - Combined Handoff Document

## Version 2.4.3 - Test Suite Repair, Coverage, Cleanup

**Date:** 2026-08-14
**Repository:** https://github.com/KW75/AI_kcMedicalResearch
**Live App:** https://ai-kcmedicalresearch.onrender.com
**Health Check:** https://ai-kcmedicalresearch.onrender.com/_stcore/health
**Uptime Monitor:** UptimeRobot, 5-minute interval, keeps free-tier Render instance warm
**Tests:** 400 passed, 3 skipped, 11 deselected/live tests
**Coverage:** 53%
**Latest Render Fix Commit:** 139d42d
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
- Cross-platform Docker support; Windows/macOS one-click setup scripts.
- Test suite expanded from 127 to ~243 tests. Coverage ~26% to ~50%.
- Render.com deployment configured.

### Session 2 - 2026-08-11 - v2.3.1: Stability and Auto-Detection
- Recovered from destructive commit via hard reset `62e412c` to `9aef3e6`.
- Launcher fix: removed `CREATE_NEW_PROCESS_GROUP`.
- Ollama auto-detection; Qwen -> `qwen-plus-latest`; LLM timeout 5 -> 15 min.
- `MAX_ITERATIONS` 5 -> 3. Default provider Ollama -> DeepSeek.
- Tests: 275 passed, 6 skipped.

### Session 3 - 2026-08-13 - v2.4.0 to v2.4.1: CI/CD, Fallback, Streaming, Monitoring
- GitHub Actions CI fixed (Python 3.11, build-essential, cmake, python3-dev).
- `pysqlite3` monkey-patch; conditional `pytesseract` import; live tests marked.
- Provider fallback chain (DeepSeek -> Qwen -> Groq, transient errors only).
- Streaming default on; `--no-stream` flag. Render health check + UptimeRobot.
- Actions updated to checkout@v5 / setup-python@v6.
- Removed 12 debug scripts, a backup file, and orphan `scripts/.venv`.
- Tests: 362 passed, 3 skipped, 11 deselected. CI green.

### Session 4 - 2026-08-14 - v2.4.2: Render Recovery and Dashboard Configuration Fix
Render repeatedly failed with `Exited with status 1` while the live app kept serving the last successful deploy. Root causes: dashboard used manual settings not `render.yaml`; Build Command installed `requirements.txt` (Windows-only `pywin32==306`); default Python 3.14.3; Start Command pointed to old `src/ui/app.py`; a partial Start Command began with `$PORT`.
Final fixes: `PYTHON_VERSION=3.11.9`; Build Command uses `requirements-render.txt` with `--only-binary=:all:` plus separate `docx2txt==0.8`; Start Command uses `SOURCE_CODE/ui/app.py`; health endpoint verified returning `ok`.

### Session 5 - 2026-08-14 - v2.4.3: Test Suite Repair, Coverage, Cleanup
- Fixed 7 failing tests in `test_main_coverage.py`. They blocked on `input()` (main() runs an interactive REPL) and asserted on `run_*` functions that `main()` never calls (the loop calls `call_ai` directly). Fixed by mocking `input` with a task + `KeyboardInterrupt`, and asserting on `call_ai`.
- Mocked `utils.rag.index_uploads` in tests, removing ~113 seconds of real PDF embedding (SR/appraisal modes). File runtime dropped 121s -> 8s.
- Added `TestSessionManagement` (16 tests) covering `list_sessions`, `read_session`, `delete_session`, `export_session`, `rename_session`, `show_stats`, plus interactive-loop tests for all six modes.
- `main.py` coverage 36% -> 41%; suite 362 -> 400 passing; overall ~53%.
- Removed dead code `cli.py` and `session.py` (abandoned refactor, superseded by main.py); coverage 52% -> 53%.
- Removed dead duplicate files `sr/src/ui/__init__.py` and `sr/src/ui/app.py`.
- Fully resolved the `project_layout.py` escape-sequence DeprecationWarning (5 docstrings now raw-strings).
- Removed scratch files (`create_*.py`, `fix_*.py`) and the empty gitignored `data/` folder.

---

## 3. CURRENT STATUS

| Component | Status | Details |
|-----------|--------|---------|
| GitHub Actions CI | GREEN | 400 tests, Python 3.11, checkout@v5, setup-python@v6 |
| Render Build | GREEN | Uses `requirements-render.txt` |
| Render Deploy | LIVE | Streamlit app live |
| Render Health Check | ACTIVE | `/_stcore/health` returns `ok` |
| UptimeRobot | MONITORING | 5-minute pings |
| Provider Fallback | ACTIVE | DeepSeek -> Qwen -> Groq on transient errors |
| Streaming CLI | DEFAULT | `--no-stream` disables |
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
| 4 | DeprecationWarning: escape sequence in `project_layout.py` | Low | RESOLVED (Session 5) |
| 5 | Streamlit warning: `theme.baseFontSize` invalid config option | Low | RESOLVED (Session 5) |
| 6 | `cli.py` and `session.py` dead code | Low | RESOLVED (Session 5) - deleted |


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

Fallback: transient errors (timeout, 429, 502, 503) trigger next provider; auth errors (401, 403) raise immediately. SR pipeline blocks non-vision providers (DeepSeek/Ollama not usable for SR).

---

## 6. TEST COVERAGE (Session 5)

| Module | Coverage |
|--------|----------|
| writing.py | 89% |
| traice_integration.py | 98% |
| appraisal.py | 86% |
| coding.py | 78% |
| checkpoint.py | 73% |
| path_utils.py | 74% |
| search.py | 72% |
| rct_search.py | 63% |
| ui/app.py | 58% |
| rag.py | 57% |
| streaming.py | 55% |
| providers.py | 54% |
| main.py | 41% |
| document_reader.py | 24% |
| SR pipeline (src/*) | ~10-53% (low) |
| TOTAL | 53% (400 tests) |

---

## 7. NEXT SESSION PRIORITIES

| Priority | Task | Details |
|----------|------|---------|
| 1 | Fix Lami extraction | SR pipeline Table 4, pages 12-13 |
| 2 | Raise SR pipeline coverage | Core screening/extraction logic (currently very low) |
| 3 | Add visible app version/commit | Streamlit sidebar |
| 4 | PDF export via fpdf2 | Pure-Python, no GTK3 dependen |
| 5 | Push Docker image | Docker Hub for colleague sharing |
| 6 | Track token usage/cost | Per-session totals |

---

## 8. LESSONS LEARNED

- Tests must mock `utils.rag.index_uploads` rather than doing real embedding (slow + non-deterministic, depends on PDFs in `input/`).
- Use single-quoted here-strings (`@''...''@`) when writing Python files from PowerShell to avoid `$`/quote/backtick escaping issues.
- `main()` runs an interactive `input()` loop and calls `call_ai` directly, NOT the `run_*` functions. Mock `input` with a task + `KeyboardInterrupt` to test it.
- Never use `CREATE_NEW_PROCESS_GROUP` for interactive CLI on Windows.
- Never hardcode model versions if `*-latest` aliases exist.
- Render dashboard settings can override/ignore `render.yaml`; always inspect Render logs.
- Render Linux must not install Windows-only packages (`pywin32`); use `requirements-render.txt`.
- `docx2txt==0.8` has no wheel; install separately or allow from source.
- Streamlit app path is `SOURCE_CODE/ui/app.py`, not `src/ui/app.py`.
- Mark network tests `@pytest.mark.live` to avoid CI flakes.
- ChromaDB on Linux CI needs `cmake`, `python3-dev`, and `pysqlite3`.
- Raw-string (`r"""`) docstrings when they contain backslashes (e.g. Windows paths) to avoid escape-sequence warnings.

---

## 9. FINAL VERIFIED RENDER SETTINGS

Build Command:
`pip install --upgrade pip && pip install --no-cache-dir --only-binary=:all: -r requirements-render.txt && pip install --no-cache-dir --no-deps docx2txt==0.8`

Start Command:
`streamlit run SOURCE_CODE/ui/app.py --server.address=0.0.0.0 --server.port=$PORT --server.enableCORS=false --server.enableXsrfProtection=false`

Env: `PYTHON_VERSION=3.11.9`
Health: `https://ai-kcmedicalresearch.onrender.com/_stcore/health` -> `ok`

---

Handoff prepared: 2026-08-14
Version: v2.4.3
Single source of truth for next session.
