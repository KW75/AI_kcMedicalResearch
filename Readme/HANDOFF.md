AI kcMedicalResearch - Combined Handoff Document
Version 2.4.4 - SR Import Crash, Output Path, Cleanup

Date: 2026-08-14 Repository: https://github.com/KW75/AI_kcMedicalResearch Live App: https://ai-kcmedicalresearch.onrender.com Health Check: https://ai-kcmedicalresearch.onrender.com/_stcore/health Uptime Monitor: UptimeRobot, 5-minute interval, keeps free-tier Render instance warm Tests: 400 passed, 3 skipped, 11 deselected/live tests Coverage: 53% Latest Commit: aa0f210 Current Status: CI green, Render live, health endpoint returns ok
1. PROJECT OVERVIEW

AI kcMedicalResearch is a local-first Python application providing six specialised AI pipeline modes for medical research workflows. It supports multiple LLM providers, local and cloud inference, multi-agent iteration loops, file-based input/output, Docker deployment, checkpoint/resume, streaming CLI output, and a Streamlit web UI.

Target Users: Medical students, clinical researchers, academic writers. Default Provider: DeepSeek, configurable via .env DEFAULT_PROVIDER. Fallback Chain: DeepSeek -> Qwen -> Groq, configurable via FALLBACK_PROVIDERS. Live UI: https://ai-kcmedicalresearch.onrender.com
2. SESSION HISTORY
Session 1 - 2026-08-10 - v2.3.0: SOURCE_CODE Restructure and Docker

    Complete project reorganisation into SOURCE_CODE/ structure.
    Cross-platform Docker support; Windows/macOS one-click setup scripts.
    Test suite expanded from 127 to ~243 tests. Coverage ~26% to ~50%.
    Render.com deployment configured.

Session 2 - 2026-08-11 - v2.3.1: Stability and Auto-Detection

    Recovered from destructive commit via hard reset 62e412c to 9aef3e6.
    Launcher fix: removed CREATE_NEW_PROCESS_GROUP.
    Ollama auto-detection; Qwen -> qwen-plus-latest; LLM timeout 5 -> 15 min.
    MAX_ITERATIONS 5 -> 3. Default provider Ollama -> DeepSeek.
    Tests: 275 passed, 6 skipped.

Session 3 - 2026-08-13 - v2.4.0 to v2.4.1: CI/CD, Fallback, Streaming, Monitoring

    GitHub Actions CI fixed (Python 3.11, build-essential, cmake, python3-dev).
    pysqlite3 monkey-patch; conditional pytesseract import; live tests marked.
    Provider fallback chain (DeepSeek -> Qwen -> Groq, transient errors only).
    Streaming default on; --no-stream flag. Render health check + UptimeRobot.
    Actions updated to checkout@v5 / setup-python@v6.
    Removed 12 debug scripts, a backup file, and orphan scripts/.venv.
    Tests: 362 passed, 3 skipped, 11 deselected. CI green.

Session 4 - 2026-08-14 - v2.4.2: Render Recovery and Dashboard Configuration Fix

Render repeatedly failed with Exited with status 1 while the live app kept serving the last successful deploy. Root causes: dashboard used manual settings not render.yaml; Build Command installed requirements.txt (Windows-only pywin32==306); default Python 3.14.3; Start Command pointed to old src/ui/app.py; a partial Start Command began with $PORT. Final fixes: PYTHON_VERSION=3.11.9; Build Command uses requirements-render.txt with --only-binary=:all: plus separate docx2txt==0.8; Start Command uses SOURCE_CODE/ui/app.py; health endpoint verified returning ok.
Session 5 - 2026-08-14 - v2.4.3: Test Suite Repair, Coverage, Cleanup

    Fixed 7 failing tests in test_main_coverage.py. They blocked on input() (main() runs an interactive REPL) and asserted on run_* functions that main() never calls (the loop calls call_ai directly). Fixed by mocking input with a task + KeyboardInterrupt, and asserting on call_ai.
    Mocked utils.rag.index_uploads in tests, removing ~113 seconds of real PDF embedding (SR/appraisal modes). File runtime dropped 121s -> 8s.
    Added TestSessionManagement (16 tests) covering list_sessions, read_session, delete_session, export_session, rename_session, show_stats, plus interactive-loop tests for all six modes.
    main.py coverage 36% -> 41%; suite 362 -> 400 passing; overall ~53%.
    Removed dead code cli.py and session.py (abandoned refactor, superseded by main.py); coverage 52% -> 53%.
    Removed dead duplicate files sr/src/ui/__init__.py and sr/src/ui/app.py.
    Fully resolved the project_layout.py escape-sequence DeprecationWarning (5 docstrings now raw-strings).
    Removed scratch files (create_*.py, fix_*.py) and the empty gitignored data/ folder.

Session 6 - 2026-08-14 - v2.4.4: SR Import Crash, Output Path, Cleanup

    Fixed SR pipeline ImportError: attempted relative import with no known parent package. Root cause: outer main.py launched the inner sr/main.py by file path, so relative imports (from .src...) had no parent package. Fixed by (1) adding __init__.py across the package tree (SOURCE_CODE/, pipelines/, pipelines/sr/, sr/src/*, sr/config/) and (2) changing the Step-5 subprocess call in run_sr_launcher from file-path to module invocation: python -m SOURCE_CODE.pipelines.sr.main with cwd=BASE_DIR.
    Fixed SR output landing under SOURCE_CODE/. project_layout.py line 29 used five .parent hops (stopped at SOURCE_CODE/); changed to six so PROJECT_ROOT resolves to the repo root. SR outputs now correctly write to root reports/sr/<run_id>/ and mirror to output/sr/.
    Routed rct_search output from the reports/ root into reports/rct_search/ (call-site fix in main()); removed the unused reports/systematic_review/ entry from the startup folder-creation list.
    Cleanup: removed the stale duplicate SOURCE_CODE/docs/ (26 files, superseded by root docs/), SOURCE_CODE/main.py.bak, and the leftover SOURCE_CODE/output and SOURCE_CODE/reports folders (bug artifacts from the pre-fix output path).
    Verified: full SR run completes all 6 stages (upload -> screening -> extraction -> RoB2 -> meta-analysis -> reports) producing DOCX, HTML, forest_plot.png, and audit CSVs in the correct root location. Tests unaffected: 400 passed, 3 skipped. Committed aa0f210, pushed to main, Render redeployed green, health endpoint returns ok.

3. CURRENT STATUS
Component 	Status 	Details
GitHub Actions CI 	GREEN 	400 tests, Python 3.11, checkout@v5, setup-python@v6
Render Build 	GREEN 	Uses requirements-render.txt
Render Deploy 	LIVE 	Streamlit app live
Render Health Check 	ACTIVE 	/_stcore/health returns ok
UptimeRobot 	MONITORING 	5-minute pings
Provider Fallback 	ACTIVE 	DeepSeek -> Qwen -> Groq on transient errors
Streaming CLI 	DEFAULT 	--no-stream disables
All Pipelines 	WORKING 	coding, writing, appraisal, search, rct_search, sr
SR Pipeline 	WORKING 	Import crash fixed; outputs to root reports/sr/<run_id>/ + mirror output/sr/
Docker Support 	COMPLETE 	Windows and macOS one-click scripts
Documentation 	CURRENT 	README.md, HANDOFF.md, Setup Instructions
4. KNOWN ISSUES
# 	Issue 	Priority 	Status
1 	Lami extraction fails, Table 4, pages 12-13 	High 	Open
2 	WeasyPrint not installed; PDF falls back to HTML 	Medium 	Open
3 	Anthropic geo-restricted 	Low 	Use VPN or skip
4 	DeprecationWarning: escape sequence in project_layout.py 	Low 	RESOLVED (Session 5)
5 	Streamlit warning: theme.baseFontSize invalid config option 	Low 	RESOLVED (Session 5)
6 	cli.py and session.py dead code 	Low 	RESOLVED (Session 5) - deleted
7 	SR pipeline relative-import crash (-m invocation) 	High 	RESOLVED (Session 6)
8 	SR output written under SOURCE_CODE/ instead of repo root 	Medium 	RESOLVED (Session 6)
9 	Hardcoded qwen3.7-plus in _DEFAULT_MODELS (outer main.py) and inner sr/main.py argparse default; should read QWEN_MODEL 	Low 	Open
10 	Cosmetic [ollama] Auto-detected best model line fires even on Qwen SR runs (inner SR package); does not affect actual provider used 	Low 	Open
11 	Launcher completion message in run_sr_launcher still prints stale pipelines/sr/outputs path (inner log prints correct absolute paths) 	Low 	Open
5. AI PROVIDERS
Provider 	Flag 	Env Var 	Default Model 	Vision 	Streaming
DeepSeek 	--provider deepseek 	DEEPSEEK_API_KEY 	deepseek-v4-flash 	No 	Yes
Qwen 	--provider qwen 	DASHSCOPE_API_KEY 	qwen-plus-latest 	Yes 	Yes
OpenAI 	--provider openai 	OPENAI_API_KEY 	gpt-4o-mini 	Yes 	Yes
Anthropic 	--provider anthropic 	ANTHROPIC_API_KEY 	claude-sonnet-5 	Yes 	Yes
Groq 	--provider groq 	GROQ_API_KEY 	llama-3.3-70b-versatile 	Yes 	Yes
Ollama 	--provider ollama 	OLLAMA_HOST 	Auto-detected 	No 	Yes

Fallback: transient errors (timeout, 429, 502, 503) trigger next provider; auth errors (401, 403) raise immediately. SR pipeline blocks non-vision providers (DeepSeek/Ollama not usable for SR).

Note (Session 6): Inner SR main.py argparse default and outer _DEFAULT_MODELS still hardcode qwen3.7-plus for Qwen; the documented/intended model is qwen-plus-latest via QWEN_MODEL. SR runs succeed regardless, but see Known Issue #9.
6. TEST COVERAGE (Session 5, unchanged Session 6)
Module 	Coverage
writing.py 	89%
traice_integration.py 	98%
appraisal.py 	86%
coding.py 	78%
checkpoint.py 	73%
path_utils.py 	74%
search.py 	72%
rct_search.py 	63%
ui/app.py 	58%
rag.py 	57%
streaming.py 	55%
providers.py 	54%
main.py 	41%
document_reader.py 	24%
SR pipeline (src/*) 	~10-53% (low)
TOTAL 	53% (400 tests)
7. NEXT SESSION PRIORITIES
Priority 	Task 	Details
1 	Fix Lami extraction 	SR pipeline Table 4, pages 12-13 (Known Issue #1)
2 	Raise SR pipeline coverage 	Core screening/extraction logic (currently very low)
3 	Add SR -m invocation regression test 	Guards against recurrence of the Session 6 import crash; run inner pipeline via -m SOURCE_CODE.pipelines.sr.main --help, assert no ImportError / attempted relative import
4 	Replace hardcoded qwen3.7-plus with QWEN_MODEL 	Both _DEFAULT_MODELS (outer) and inner sr/main.py argparse default (Known Issue #9)
5 	Silence Ollama auto-detect on non-Ollama runs 	Cosmetic line in inner SR package (Known Issue #10)
6 	Fix launcher completion message path 	Remove stale pipelines/sr/outputs reference (Known Issue #11)
7 	Add visible app version/commit 	Streamlit sidebar
8 	PDF export via fpdf2 	Pure-Python, no GTK3 dependency
9 	Push Docker image 	Docker Hub for colleague sharing
10 	Track token usage/cost 	Per-session totals
8. LESSONS LEARNED

    Tests must mock utils.rag.index_uploads rather than doing real embedding (slow + non-deterministic, depends on PDFs in input/).
    Use single-quoted here-strings (@''...''@) when writing Python files from PowerShell to avoid $/quote/backtick escaping issues.
    main() runs an interactive input() loop and calls call_ai directly, NOT the run_* functions. Mock input with a task + KeyboardInterrupt to test it.
    Never use CREATE_NEW_PROCESS_GROUP for interactive CLI on Windows.
    Never hardcode model versions if *-latest aliases exist.
    Render dashboard settings can override/ignore render.yaml; always inspect Render logs.
    Render Linux must not install Windows-only packages (pywin32); use requirements-render.txt.
    docx2txt==0.8 has no wheel; install separately or allow from source.
    Streamlit app path is SOURCE_CODE/ui/app.py, not src/ui/app.py.
    Mark network tests @pytest.mark.live to avoid CI flakes.
    ChromaDB on Linux CI needs cmake, python3-dev, and pysqlite3.
    Raw-string (r""") docstrings when they contain backslashes (e.g. Windows paths) to avoid escape-sequence warnings.
    (Session 6) Never launch a package's module by file path via subprocess; use python -m package.module with cwd=<repo root> so relative imports resolve. A file-path invocation makes the script the top-level __main__ with no parent package, breaking from .x import y.
    (Session 6) Every directory in an import chain needs an __init__.py for -m module invocation to work (including nested src/* and config/ subpackages).
    (Session 6) When computing a repo root from Path(__file__), count .parent hops carefully against the file's actual depth. sr/src/utils/project_layout.py needs six hops to reach the repo root; a "go up to project root" comment stopping at five silently redirected all SR output under SOURCE_CODE/. Prefer parents[N] for readability/verifiability.
    (Session 6) SR nested input() prompts require a real interactive TTY; running SR via the menu launcher (subprocess without inherited console stdin) causes prompts to return empty and skip. Run python SOURCE_CODE/main.py --mode sr --provider qwen directly for interactive PICO selection.
    (Session 6) Git does not track empty directories; folders left behind after moving/deleting their files must be removed manually. Use git rm -r (not plain Remove-Item) for tracked folders so the deletion is recorded, otherwise git restores them.

9. FINAL VERIFIED RENDER SETTINGS

Build Command: pip install --upgrade pip && pip install --no-cache-dir --only-binary=:all: -r requirements-render.txt && pip install --no-cache-dir --no-deps docx2txt==0.8

Start Command: streamlit run SOURCE_CODE/ui/app.py --server.address=0.0.0.0 --server.port=$PORT --server.enableCORS=false --server.enableXsrfProtection=false

Env: PYTHON_VERSION=3.11.9 Health: https://ai-kcmedicalresearch.onrender.com/_stcore/health -> ok
10. SR PIPELINE - OUTPUT LOCATIONS (Session 6)

Run directly (not via menu launcher) for interactive PICO selection: python SOURCE_CODE/main.py --mode sr --provider qwen

Per-run output (timestamped, audit-friendly): reports/sr/<run_id>/ containing uploads/, data/screened/, data/extracted/, data/results/, output/figures/forest_plot.png, output/reports/systematic_review.docx and .html.

Mirror (always latest run): output/sr/figures/ and output/sr/reports/.

All paths are repo-root relative (no SOURCE_CODE/ prefix) after the Session 6 project_layout.py fix.

Handoff prepared: 2026-08-14 Version: v2.4.4 Single source of truth for next session.

