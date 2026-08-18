AI kcMedicalResearch — Combined Handoff Document
Version 2.4.10 — SR Extraction Tripwires (SD/SE, Within/Between-Group), Cross-Platform OCR Fix

Date: 2026-08-18 (Session 12, following Session 11) Repository: https://github.com/KW75/AI_kcMedicalResearch Live App: https://ai-kcmedicalresearch.onrender.com Health Check: https://ai-kcmedicalresearch.onrender.com/_stcore/health Uptime Monitor: UptimeRobot, 5-minute interval, keeps free-tier Render instance warm Tests: 423 passed, 3 skipped, 11 deselected (up from 405 - 18 new tests in test_data_extractor_flags.py, verified passing against the real project venv, not just simulated) Coverage: ~53% (not re-measured this session) Current Status: local test suite green (423 passed); CI/Render status not re-verified this session (same caveat as Session 11 - neither has been re-run since v2.4.9's push)

CRITICAL READ FIRST (1): Session 10 found and fixed a confidentiality defect (Ollama fallback to cloud on timeout). Session 11 closed the regression-test gap and a related classifier bug. Unchanged this session.

CRITICAL READ FIRST (2): Session 8 found that SR extraction can produce a confident, precisely-quantified, entirely invalid effect size with no warning at any stage - see #15/#16 in this document's numbering (#9/#10 in README's numbering). Session 11 added a plausibility-magnitude tripwire. Session 12 adds two more: an SD/SE-confusion tripwire (text-fallback path only) and a within/between-group-confusion tripwire (both extraction paths). READ THE SCOPE CAREFULLY: these are deterministic pattern checks for the specific documented failure modes (zsy234.pdf's SE-as-SD and timepoint-as-group errors), not semantic verification. #15 and #16 remain CRITICAL and are NOT resolved - manual verification against the source PDF is still mandatory regardless of whether any tripwire fires. Do not treat a clean run through these three tripwires as evidence the extraction was correct.

======================================
1. PROJECT OVERVIEW
======================================
AI kcMedicalResearch is a local-first Python application providing six specialised AI pipeline modes for medical research workflows. It supports multiple LLM providers, local and cloud inference, multi-agent iteration loops, file-based input/output, Docker deployment, checkpoint/resume, streaming CLI output, and a Streamlit web UI.

Target Users: Medical students, clinical researchers, academic writers. Default Provider: DeepSeek, configurable via .env DEFAULT_PROVIDER. Fallback Chain: DeepSeek → Qwen → Groq, configurable via FALLBACK_PROVIDERS. Live UI: https://ai-kcmedicalresearch.onrender.com

======================================
2. SESSION HISTORY
======================================
Session 1 — 2026-08-10 — v2.3.0: SOURCE_CODE Restructure and Docker

    Complete project reorganisation into SOURCE_CODE/ structure.
    Cross-platform Docker support; Windows/macOS one-click setup scripts.
    Test suite expanded from 127 to ~243 tests. Coverage ~26% → ~50%.
    Render.com deployment configured.

Session 2 — 2026-08-11 — v2.3.1: Stability and Auto-Detection

    Recovered from destructive commit via hard reset 62e412c → 9aef3e6.
    Launcher fix: removed CREATE_NEW_PROCESS_GROUP.
    Ollama auto-detection; Qwen → qwen-plus-latest; LLM timeout 5 → 15 min.
    MAX_ITERATIONS 5 → 3. Default provider Ollama → DeepSeek.
    Tests: 275 passed, 6 skipped.

Session 3 — 2026-08-13 — v2.4.0 to v2.4.1: CI/CD, Fallback, Streaming, Monitoring

    GitHub Actions CI fixed (Python 3.11, build-essential, cmake, python3-dev).
    pysqlite3 monkey-patch; conditional pytesseract import; live tests marked.
    Provider fallback chain (DeepSeek → Qwen → Groq, transient errors only).
    Streaming default on; --no-stream flag. Render health check + UptimeRobot.
    Actions updated to checkout@v5 / setup-python@v6.
    Removed 12 debug scripts, a backup file, and orphan scripts/.venv.
    Tests: 362 passed, 3 skipped, 11 deselected. CI green.

Session 4 — 2026-08-14 — v2.4.2: Render Recovery and Dashboard Configuration Fix Render repeatedly failed with "Exited with status 1" while the live app kept serving the last successful deploy. Root causes: dashboard used manual settings not render.yaml; Build Command installed requirements.txt (Windows-only pywin32306); default Python 3.14.3; Start Command pointed to old src/ui/app.py; a partial Start Command began with $PORT. Final fixes: PYTHON_VERSION=3.11.9; Build Command uses requirements-render.txt with --only-binary=:all: plus separate docx2txt0.8; Start Command uses SOURCE_CODE/ui/app.py; health endpoint verified returning ok.

Session 5 — 2026-08-14 — v2.4.3: Test Suite Repair, Coverage, Cleanup

    Fixed 7 failing tests in test_main_coverage.py (blocked on input(); asserted on run_* functions main() never calls). Fixed by mocking input with task + KeyboardInterrupt, asserting on call_ai.
    Mocked utils.rag.index_uploads (removed ~113s of real PDF embedding); file runtime 121s → 8s.
    Added TestSessionManagement (16 tests) + interactive-loop tests for all six modes.
    main.py coverage 36% → 41%; suite 362 → 400; overall ~53%.
    Removed dead code cli.py, session.py; removed duplicate sr/src/ui files; resolved project_layout.py escape-sequence warning; removed scratch files + empty data/ folder.

Session 6 — 2026-08-14 — v2.4.4: SR Import Crash, Output Path, Cleanup

    Fixed SR pipeline ImportError (relative import with no parent package). Fixed by adding init.py across the package tree and switching Step-5 subprocess call in run_sr_launcher to python -m SOURCE_CODE.pipelines.sr.main with cwd=BASE_DIR.
    Fixed SR output landing under SOURCE_CODE/ (project_layout.py used five .parent hops; changed to six). Outputs now write to root reports/sr/<run_id>/ + mirror output/sr/.
    Routed rct_search output into reports/rct_search/; removed unused reports/systematic_review/ startup entry.
    Cleanup: removed stale SOURCE_CODE/docs/ (26 files), main.py.bak, leftover SOURCE_CODE/output and SOURCE_CODE/reports.
    Verified full SR run completes all 6 stages. Committed aa0f210, pushed, Render green.

Session 7 — 2026-08-15 — v2.4.5: Vision-Model Regression Fix, Prompt & Dead-Code Cleanup

    #9 (resolved) — Replaced hardcoded qwen3.7-plus in outer _DEFAULT_MODELS and wired model constants from providers.py (commit 3c2e51b).
    #3 (resolved) — Added -m invocation regression test guarding against the Session 6 import crash (commit 4b793ea).
    #11 (resolved) — Fixed stale pipelines/sr/outputs path in run_sr_launcher completion message; now points to real mirror paths output/sr/reports + output/sr/figures and adds HTML output line plus per-run audit-folder pointer (commit a83ec1c).
    Test hygiene (resolved) — test_sr_pipeline_dry_run no longer overwrites the real prisma_criteria.yaml; writes to pytest tmp_path (commit 5d6a8ca). Eliminates the recurring git restore step after full test runs.
    Vision regression (NEW issue, resolved) — After #9, the SR launcher resolved qwen to QWEN_MODEL = qwen-plus-latest, which is text-only, so all vision extraction returned empty (0/5 papers extracted, meta-analysis aborted with "< 2 studies"). Root cause: the qwen provider is marked vision-capable but its default model is not. Fixed by adding QWEN_VISION_MODEL (env QWEN_VISION_MODEL, default qwen-vl-max) in providers.py and pointing the SR launcher's _DEFAULT_MODELS["qwen"] + fallback default to it. Text modes keep QWEN_MODEL. Verified: 4/5 papers extract without a --model flag, pooled SMD ≈ −0.715 [−1.958, 0.528], I² ≈ 94.4%, forest plot + DOCX/HTML generated (commit 9c536e1).
    Prompt cleanup (resolved) — Investigated whether the top-level prompts/ folder was unused. Confirmed it is load-bearing: 14 of 15 files are referenced by the agent registry in main.py (AI_DIR / "*-prompt.md") and by rct_search.py. Deleting the folder would silently break every agent at runtime (not caught by tests). Removed only the one genuine orphan, prompts/sr-methodologist-prompt.md — referenced nowhere in code, tests, or the SR subtree (commit b1f4c48).
    Dead-code cleanup (resolved) — Removed the never-called get_prompt() / get_prompt_path() helpers from path_utils.py (agents load prompts via explicit AI_DIR paths, not this dynamic helper). Added sr_*.log to .gitignore (commit 1b6b9b0).
    Tests throughout: 401 passed, 3 skipped, 11 deselected. All commits pushed to main.


Session 8 — 2026-08-17 — v2.4.6: SR Extraction Provenance, Generic Overrides, Reviewer Guide

    #1 (resolved) — Lami extraction (s10608-017-9875-4.pdf). Text fallback now recovers Table 4 and the study is included. The metadata label was a separate bug: study_metadata was written nowhere in the codebase (only referenced in the prompt template at data_extractor.py:35), while corrections wrote top-level first_author. Reporting and Stage 4 read the nested block, so the forest plot showed "Hedges g for None". Fixed by mirroring resolved first_author/year into study_metadata before every return path of _apply_known_pdf_corrections.
    Dead code (resolved) — The except handler in extract_by_pdf_path spent 36 lines populating result["first_author"] etc., then returned a freshly-constructed dict that discarded all of it. Never had any effect. Removed.
    Hardcoding removed (resolved) — Lami-specific corrections had accumulated across three places in data_extractor.py, including numeric-signature matching (self._near(mi, 7.35) and self._near(sdi, 2.08) ...) that fired only when extraction was already correct and stayed silent exactly when it was wrong. On one run extraction returned 7.32/1.80, the signature missed, sample sizes were never set, and the study was dropped with "insufficient mean/SD/N". All of it replaced.
    New module (added) — SOURCE_CODE/pipelines/sr/src/extraction/study_overrides.py. Two mechanisms: resolve_pdf_metadata() derives first_author/year/doi from the PDF (PyMuPDF metadata, DOI regex, copyright-line year) for any paper; StudyOverrides applies reviewer-verified values from input/sr/study_overrides.yaml keyed by filename. Metadata fields fill only when blank; numeric outcome fields replace extraction output. Unknown YAML fields are rejected with a warning.
    Provenance (added) — Overrides that change numeric values log at WARNING. End of Stage 3 prints a DATA PROVENANCE SUMMARY listing every study that used overrides or auto-derived metadata. Per-field audit distinguishes field(7.32->7.35) (corrected), field(confirmed 7.35) (extraction independently agreed), and field(absent->7.35). Extraction still runs in full for overridden studies specifically to preserve the "confirmed" cross-check.
    McCrae invalid effect size (NEW issue, unresolved) — zsy234.pdf was contributing g = -2.356 [-2.853, -1.859] and driving the entire pooled estimate (SMD -0.514, I2 93.9%). Decoding the PDF text layer showed the source reads: "There were no significant group by time interactions for the morning and evening pain ratings ... Regardless of treatment condition, participants reported less morning pain at posttreatment (M = 47.14, SE = 2.36) relative to baseline (M = 52.67, SE = 2.27)". Three simultaneous errors: SE read as SD; a within-subject main effect of time read as a between-group contrast; group Ns fabricated by summing two arms (39+37=76) of a three-arm trial. The paper reports NO significant treatment effect on pain. Nothing in the pipeline flagged any of this.
    Broken font CMaps (NEW issue, unresolved) — All five test PDFs trigger "Garbled text detected - switching to OCR". The text layer is not garbled; it has a broken CMap with a fixed +1 character-code offset. "LbBq]d ds ]k-" decodes to "McCrae et al."; digits are shifted too, which is why searching for the literal "47.14" found nothing. The pipeline OCRs documents that have a clean recoverable text layer, likely the upstream cause of the extraction instability.
    Extraction non-determinism (NEW issue, unresolved) — Same PDF, same code, different values across consecutive runs. Lami returned 7.35/2.08/n=28 on one run and 7.32/1.80/n=absent on the next. Ang's CI moved between runs with no code change affecting it. 2 of 5 papers observed unstable; the other 3 are unverified rather than verified.
    Documentation (added) — Readme/REVIEWER_GUIDE.md: mandatory manual verification checklist, the two documented failure modes as worked examples, include/exclude decision rules at the extraction gate with PRISMA exclusion reasons, override file usage rules, and a minimum reporting statement for a methods section.
    Repo hygiene — .gitignore rewritten so input/ stays ignored but input/sr/study_overrides.yaml and input/sr/pico_sample.json are tracked (a bare negation does not work when the parent directory is excluded; git never descends into it). Test corpus PDFs removed from input/sr/ as copyrighted. Debug logs cleared.
    Tests: 401 passed, 3 skipped, 11 deselected throughout.


Session 9 — 2026-08-17 — v2.4.7: API Key Leak, Startup Performance, Launcher Repair

    SECURITY (resolved) — The Streamlit UI wrote every API key into a generated .bat as `set "KEY=value"` lines. cmd echoes each line, so all keys were printed on screen at every launch, and the file persisted in %TEMP% in plaintext. Popen was ALREADY passing env=env_vars, so the child inherited the keys regardless — the set lines were pure redundancy. Removed them, added @echo off, changed cmd /k to cmd /c (the script already ends with pause). The same redundant interpolation existed in the macOS and Linux launchers, where keys were additionally visible in ps output; removed there too. NOTE: keys exposed during this session must be rotated at the provider consoles — clearing .env does not invalidate them.
    Startup performance (resolved) — Startup was 15-20s. Profiled with `python -X importtime`: utils/__init__.py eagerly imported .rag (chromadb) and .document_reader (pymupdf, docx2txt), so `from utils.path_utils import ...` — three trivial path helpers — pulled the entire RAG and document stack, ~2.2s, on every run including every test. Converted to lazy loading via PEP 562 __getattr__. Public API unchanged; `from utils import DocumentReader` still works. Startup ~20s -> ~7s; test suite ~45s -> ~19s. Remaining chunks: providers ~2.2s (includes the module-scope Ollama probe, Issue #10) and pipelines.sr.main ~2.8s imported even for coding mode — same lazy treatment applies.
    Windows launchers (resolved) — UI launcher opened TWO browser tabs: --server.headless=false makes Streamlit open one itself, and the script also ran `start "" "http://localhost:8501"` after a fixed 3s ping wait — well before the ~7s startup, so that tab hit connection-refused. Removed the manual start. Both launchers now propagate the real exit code instead of always 0, check for the target script before venv setup, and upgrade pip before installing requirements.
    macOS launchers (resolved) — Three fixes. (1) OLLAMA_HOST was http://localhost:11434 while running inside Docker, where localhost is the container, not the Mac; Ollama was unreachable from all three scripts despite --add-host host.docker.internal:host-gateway. Now overridden per-container with -e OLLAMA_HOST=http://host.docker.internal:11434. (2) Mac_Setup.sh baked a private DashScope workspace endpoint (ws-uv5pi4kkqbrg1vpe...) into every colleague's generated .env; replaced with the generic intl endpoint. (3) QWEN_VISION_MODEL was absent from the generated .env, so any Mac user running SR would hit the Session 7 vision regression. Also: browser now polls /_stcore/health before opening instead of firing `open` immediately; `set -e` replaced with `set -uo pipefail` so the existing `if [ $? -ne 0 ]` handlers actually run (with set -e the script exited first, making them dead code); added Docker-daemon and port-in-use checks; switched `docker images | grep` to `docker image inspect` (grep matched substrings).
    .gitattributes (resolved) — Every rule still targeted the pre-v2.3.0 src/ tree and none covered *.sh. With core.autocrlf=true, shell scripts were being stored CRLF, which breaks the shebang on macOS ("bad interpreter: /bin/bash^M"). Rewritten for the SOURCE_CODE layout: LF forced on *.sh and source/config files, CRLF on *.bat/*.cmd/*.ps1, binaries marked binary. Applied repo-wide with git add --renormalize.
    .env.example (resolved) — Was 14 variables and stale. Missing the entire DashScope block, QWEN_VISION_MODEL, DEFAULT_PROVIDER, FALLBACK_PROVIDERS, SR_STUDY_OVERRIDES, and the Ollama tuning vars. Now 24 variables with comments on the vision-model requirement and the Docker localhost trap. Removed stale OLLAMA_MODEL=qwen2.5-coder:3b (the app auto-detects).
    Renamed scripts/windows/"PWD_activate virtual enviroment.bat" -> activate_venv.bat (space in filename, misspelling). Now fails clearly if .venv is absent, narrows -ExecutionPolicy Bypass to RemoteSigned, drops the dead pause (-NoExit already holds the window), and prints the resolved interpreter after activating — a direct diagnostic for the observed case where the prompt showed (.venv) while python resolved to C:\Users\user\...Python311.
    Tests: 401 passed, 3 skipped, 11 deselected throughout.
    Commit trail: 190ec9e (v2.4.6 docs + SR overrides) -> fb7b5ce (Windows launchers) -> ab77bb5 (lazy imports, key leak, macOS launchers, .gitattributes).


Session 10 — 2026-08-17 — v2.4.8: Confidentiality Fix, BOM Cleanup, Python Gate

    CONFIDENTIALITY (resolved, most serious defect found to date) — The app is intended to let clinicians process patient data locally via Ollama; every other provider transmits the prompt to an external API. But call_ai_with_fallback built its chain as `[provider] + [p for p in chain if p != provider]`, so an explicit --provider ollama became [ollama, deepseek, qwen, groq]. "timeout" and "connection" are both in _TRANSIENT_INDICATORS, and the project's own notes record that large Ollama models time out frequently on the coding and writing pipelines. So a routine local timeout sent patient data to DeepSeek, printed "[fallback] Succeeded with deepseek" among hundreds of log lines, and completed as though the run were normal. Fixed by introducing LOCAL_ONLY_PROVIDERS = {"ollama"}: requests to a local provider never fall back, and the resulting error states explicitly that nothing was sent to a cloud API. The "trying next..." log line is now conditional on a next provider existing. Verified by injecting a failing call_ai: ollama tried ['ollama'], deepseek tried ['deepseek','qwen','groq'].
    UTF-8 BOMs (resolved) — 23 files under SOURCE_CODE/ began with EF BB BF. Python tolerates a BOM on import so the code ran, but ast.parse() rejects it and, combined with an encoding mismatch, it renders as garbage characters. This is what earlier notes recorded as "corrupted Chinese comments" in sr/main.py and project_layout.py — not corruption, a BOM. Note some were self-inflicted: PowerShell 5 `Set-Content -Encoding UTF8` writes a BOM, and files generated that way during Sessions 8-9 acquired one. Added scripts/check_no_bom.py and scripts/strip_bom.py; check_no_bom.py should be wired into CI.
    Python version gate (resolved) — A clean install on Python 3.14 (now the python.org default) fails across pywin32 306, textract 1.6.5, pillow, opencv-python 4.8 and pymupdf, taking hours to diagnose from pip and import errors. main.py now checks the interpreter before any third-party import — critically, above `from dotenv import load_dotenv`, or the user hits ModuleNotFoundError first — and exits with the supported range, the detected version and path, a Python 3.12 download link, and the Docker alternative. Decision: support 3.11-3.12 rather than raise floors on numpy/scipy/pillow/pymupdf and gamble on chromadb wheels for an interpreter that cannot be tested here.
    Requirements split (resolved) — requirements-base.txt now holds the 18 shared runtime deps, referenced by requirements.txt and requirements-ci.txt via -r. requirements-render.txt deliberately left standalone and pinned: it had just recovered from a failed deploy and mixing floors with pins for marginal DRY benefit was not worth destabilising it. New requirements-ocr.txt holds the optional OCR stack. Key finding: the OCR packages were installed but could not work — the Dockerfile apt-gets only curl and wget, so no Tesseract, no Poppler, no libGL for cv2 — meaning ~2GB of PyTorch via easyocr bought nothing. Also resolved duplicate conflicting pins (python-docx >=1.0.0 vs ==1.1.0; pillow >=9.0.0 vs Pillow==10.1.0, where last-wins made the floors decorative) and dropped textract.
    Docker consolidation (resolved) — Nine files in docker/ reduced to two: Dockerfile and docker-compose.yml. The six deleted run scripts each carried their own copy of the docker run command, which is why the same bugs appeared six times over. Dockerfile now installs requirements-base.txt. Discovered in the process that Docker_setup.bat — the advertised one-click Windows setup — was non-functional: unescaped parentheses in echo text inside if-blocks (lines 110, 256, 288, 289) close the block early, so cmd exits with "was unexpected at this time" before any Docker command runs. mac_docker_setup.sh called goto_run_app, a leftover from batch translation that is not a bash construct and, under set -e, exited the script on the update path. Neither could ever have completed a setup.
    Docker still UNVERIFIED — Docker is not installed on the dev machine, which is why none of the above was ever caught. Nothing Docker-related has been executed: not the build, not either compose service, not the .env-exclusion check. This is the gate before pointing colleagues at that route (Issue #19).
    Windows/macOS launchers (resolved in Session 9, verified Session 10) — activate_venv.bat now prints the resolved interpreter after activating; confirmed D:\AI_kcMedicalResearch\.venv\Scripts\python.exe, 3.11.9. The earlier sighting of C:\Users\user\...Python311 was a non-activated shell, not a broken venv.
    Launcher parity (resolved) — Windows and macOS launchers shared filenames but not mechanisms: AI_kcMedicalResearch_CLI.bat ran the project virtualenv while Mac_kcMedicalResearch_CLI.sh ran `docker run`. Anyone comparing or documenting them together was describing two different things, and the setup instructions did exactly that. Both macOS launchers are now venv-based mirrors of their Windows counterparts: they create .venv from the first available Python 3.11/3.12, refuse with a `brew install python@3.12` hint plus the Docker alternative if neither is present, warn when .env is missing, run in the foreground so PICO prompts get a TTY, and return the real exit code. The UI launcher also checks port 8501 with lsof and lets Streamlit open the browser itself. Deleted Mac_Setup.sh, the macOS half of the Docker setup pair whose Windows half was already gone. Confirmed no setup script is needed at all: PATH_MANAGER creates input/, output/, reports/ and docs/ per mode via mkdir(parents=True, exist_ok=True) on import (path_utils.py:74-89), and everything else the scripts did is three documented commands.
    Documentation (resolved) — Setup_Instructions_for_Users.txt previously led with the hosted app as "the right choice for most people" with no confidentiality warning, in a tool intended for patient data. It now states plainly that the hosted app must not be used for confidential or patient-identifiable input, and the Providers section carries the Ollama local-only guarantee, the pre-v2.4.8 caveat, and the note that SR works on published papers so a cloud provider is appropriate there. Also documents the platform launchers, the version-gate message, and the BOM check.
    Commit trail: f0b678e (local-provider fallback) -> 1541b09 (requirements split, compose, docs) -> c851259 (delete broken setup scripts) -> 5439ede (BOM strip + guards) -> f64d84d (Python version gate) -> e332b3b (v2.4.8 docs) -> 8d2e110 (launcher parity, delete Mac_Setup.sh).

Session 11 — 2026-08-18 — v2.4.9: Startup Reliability, Provider Lazy-Init, PICO/UI Parity, SR Plausibility Flag

    Startup crash on Ctrl+C (resolved) — main.py's entry-point try/except KeyboardInterrupt only wrapped code inside `if __name__ == "__main__":`. The document_reader -> pytesseract -> pandas import chain runs at module load, before that block starts, so Ctrl+C during the ~7s cold start (a routine action per the on-screen tip "Press Ctrl+C ... to stop and return here") fell through to a raw traceback through pandas internals instead of the clean "Session stopped. Returning to menu..." message. Fixed by wrapping the import block in its own try/except KeyboardInterrupt with the same message.
    No wait notice during slow provider calls (resolved) — A user report showed the CLI appearing to hang for 15s+ after selecting Ollama, with real risk of an impatient Ctrl+C mid-generation. call_ai() now prints a visible notice ("Pulling LLM..." for Ollama, a lighter version for cloud providers) before dispatching, gated on sys.stdout.isatty() to stay silent in non-TTY/CI runs.
    #26 (RESOLVED) — pipelines.sr.main (~2.8s: scipy, matplotlib, pymupdf) was imported unconditionally at the top of main.py via `from pipelines.sr import run_sr`, alongside three sibling imports (run_coding, run_writing, run_search) — none of which were referenced anywhere else in the file. Every real handler (handle_coding_mode, handle_writing_mode, handle_search_mode, run_sr_launcher) already does its own local import from a different submodule path when it actually needs one. Deleted the four dead imports; every mode now only pays for the pipeline it actually uses.
    Provider-select box misalignment (resolved) — scripts/launcher.py's SR provider table used a Unicode checkmark (✓) for vision-capable providers and plain "x" for non-vision ones, padded with hand-counted trailing spaces. On a CJK-locale terminal, ✓ is an ambiguous-width character and renders as 2 columns instead of 1, so every checkmark row was a column wider than its character count implied — throwing the right-hand border out of alignment. Root-caused by testing the byte-length assumption directly rather than guessing at font metrics. Fixed by replacing ✓ with a plain-ASCII "+" and padding every badge variant to the same fixed width via ljust on the plain text before adding color codes.
    #10 / #25 (RESOLVED, same root cause) — providers.py auto-detected the best Ollama model at import time unconditionally, for every provider, every run: `if not OLLAMA_MODEL: OLLAMA_MODEL = _ollama_detect_best_model(OLLAMA_HOST)` at module scope. This did a live network probe (bounded by a 5s timeout, but still a latent hang per #25's own framing) and printed "[ollama] Auto-detected..." even on a pure Qwen SR run that never touches Ollama (#10's "cosmetic" framing undersold it — a network call during import is not merely cosmetic). Fixed by moving resolution into _resolve_ollama_model(), called lazily from call_ollama_provider() on first actual use. get_default_model("ollama") now returns "(auto-detected on first use)" instead of triggering the probe just to answer a status-display query.
    #34 (RESOLVED) — _is_transient_error matched the bare substring "connection" against the lowercased error message, so an auth error whose text happened to contain that word anywhere (e.g. a gateway saying "connection refused by auth proxy") would be misclassified as transient and incorrectly retried against a fallback provider — a mechanism that could have reopened the exact confidentiality hole #29 fixed in Session 10, since Ollama's own connection-failure messages contain that phrase. Fixed by parsing the actual HTTP status code when the message contains one (401/403 are never transient, full stop, regardless of wording) and falling back to a small set of specific phrases — the precise "connection error" (what this module's own URLError handlers actually produce), not the bare word "connection" — only when no status code is present.
    #35 (RESOLVED) — Added tests/test_provider_fallback.py: four regression tests covering (1) Ollama failure never reaching a cloud provider, (2) normal cloud-to-cloud fallback still working, (3) the #34 auth-error-mentions-"connection" edge case specifically, (4) import of providers.py doing no network I/O. Verified locally with a hand-rolled monkeypatch harness (no pytest available in the sandbox that authored the fix) before handoff; re-run and confirmed passing (4/4) in the real project venv.
    #13 (RESOLVED, verified not reproducible) — Checked SOURCE_CODE/pipelines/sr/main.py's --model argparse default directly: `default=None`, threaded through unchanged to every extractor/screener/assessor call (args.model appears 4 times, always passed straight through). No hardcoded qwen3.7-plus found anywhere in the file. Matches the documented QWEN_VISION_MODEL auto-resolution path from Session 7. Downgrading from "Open — verify" to RESOLVED.
    #14 (RESOLVED) — test_main_coverage.py hardcoded a nested prompts/<mode>/<role>.txt layout (e.g. 'prompts/coding/builder.txt') that has never existed on disk. Cross-checked against ALL_MODES in main.py, which builds every real prompt path as AI_DIR / "<role>-prompt.md" (flat, no mode subfolder) — e.g. Appraiser's file is "appraisal-prompt.md", not "appraiser-prompt.md" as the role name would suggest. All five reachable mode/role pairs corrected. Side finding, NOT yet fixed: ALL_MODES has no "sr" key at all — SR mode is dispatched straight to run_sr_launcher() at the entry point and never reaches choose_role(). test_main_sr_mode currently only "passes" because choose_role is fully mocked; with the mock removed it would raise KeyError on ALL_MODES['sr']. Tracked as new issue #43 — needs a decision (redesign the test to assert SR routes to run_sr_launcher, or drop it) rather than a code fix.
    #20 (RESOLVED) — Added an effect-size plausibility check to sr/main.py: |Hedges g / SMD| > 1.5 (the exact threshold this document's own #20 entry names) or OR/RR beyond 10x / below 0.1x. Does NOT auto-exclude the study — an unusual value might be genuine — it writes a plausibility_flag column into results_csv and prints a summary block at the end of Stage 4 listing every flagged study, feeding the manual-verification workflow #15/#16 already mandate. This is a tripwire for the zsy234-class failure (g=-2.356, would have been flagged), not a fix for #15/#16 themselves — those require actual SD-vs-SE and within/between-group detection logic, which is unimplemented.
    #21 (RESOLVED, description corrected) — This document's own entry read "Streamlit UI globs output/rct_search/, CLI globs input/sr/" — checked both files directly and that's not accurate. rct_search.py's CLI actually checks input/rct_search/pico_*.json first, falling back to output/rct_search/pico_*.json (never input/sr/ — that path is INPUT_SR, used only for a one-way opt-in copy-to-SR-input step, not read back for PICO discovery). app.py's UI checked output/rct_search/ only. The real gap: a PICO JSON existing solely in input/rct_search/ (e.g. manually placed) was invisible to the UI. Fixed app.py's _get_all_pico_files() to check both locations, merged and deduped, with input/rct_search/ winning on a filename collision to match the CLI's own precedence.
    #24 (RESOLVED, risk narrowed) — Verified the actual data flow before treating this as a straightforward fix: st.session_state is per-browser-session in Streamlit's execution model, not shared server-wide as this document's own framing implied ("i.e. into the server process"). _get_env_with_api_keys() does `os.environ.copy()` (never mutates the real os.environ) and the result is only ever passed via subprocess `env=`, never written to disk or echoed — confirmed the Session 9 .bat-file leak fix is durable and has an explicit guard comment against reintroducing it. The genuine remaining risk is narrower: an entered key sits in server-side session memory as plaintext for the whole session's lifetime with no way to clear it early. Added a "Clear stored keys" sidebar button; had to also reset each provider's text_input widget state (st.session_state.pop(f"api_{provider}")), not just the api_keys dict, since Streamlit repopulates api_keys from the still-filled widgets on the very next rerun otherwise.
    Local test suite: 405 passed, 3 skipped, 11 deselected (up from 401 — the four new tests in test_provider_fallback.py account for the difference). Commit trail (7 commits, one per file): 3bcecb4 (main.py: KeyboardInterrupt handler, wait notice, #26) -> d328b42 (launcher.py: box alignment) -> f032dc2 (providers.py: #10, #25, #34) -> 644365c (test_provider_fallback.py: #35) -> 43fc085 (test_main_coverage.py: #14) -> f40ee69 (app.py: #21, #24) -> c4aec59 (sr/main.py: #20).
    NOT done this session, still needs a human decision: whether to redesign test_main_sr_mode (#43), and everything in "IMMEDIATE ACTIONS BEFORE NEXT SESSION" below — none of it was touched this session (key rotation, temp-file deletion, spend limits, venv verification, macOS launcher testing).

Session 12 — 2026-08-18 — v2.4.10: SR Extraction Tripwires, Cross-Platform OCR Fix

    Cross-platform Tesseract path (RESOLVED) — relevance_screener.py and rob2_tool.py both hardcoded pytesseract.pytesseract.tesseract_cmd to a Windows-only absolute path (C:\Program Files\Tesseract-OCR\tesseract.exe), unconditionally, in both files. On macOS/Linux/Docker this silently broke the OCR fallback entirely regardless of whether Tesseract was actually installed and working there - not a "package installed but unusable" problem like #24 in this document's numbering, a straight-up wrong-path problem masking as one. Fixed in both files: only overrides tesseract_cmd on Windows, and only if that default path actually exists; otherwise defers to pytesseract's normal PATH-based discovery (the correct behavior on macOS/Linux where Tesseract is installed via apt-get/brew).
    RoB2Assessor stale model default (RESOLVED) — Constructor defaulted to model="qwen3.7-plus", which matches nothing in providers.py's model registry (QWEN_MODEL=qwen-plus-latest, QWEN_VISION_MODEL=qwen-vl-max). Currently unreachable via the documented pipeline since sr/main.py always passes model=args.model explicitly (even when that's None), but a landmine for any direct construction that omits model - would send a request to Qwen naming a model that doesn't exist. While fixing this, found assess_by_pdf_path() only ever calls _call_with_text() - _call_with_images() exists on this class but is never invoked from any code path, dead code. Confirms the text model, not a vision model, is the correct default here (my first attempt got this wrong, assumed vision was needed without checking which method actually gets called - corrected before committing). New default: qwen-plus-latest.
    #9/#15 SD/SE tripwire (MITIGATED, not resolved) — The only existing SE-vs-SD guidance lived in _text_extraction_prompt() (the fallback path); EXTRACTION_PROMPT_TEMPLATE (the primary vision path, run first on every paper) had no such instruction at all. Added the same warning to both prompts. More importantly, added a deterministic post-hoc check, _flag_possible_se_as_sd(): on the text-fallback path only (needs literal source text to check against - the vision path has no text), flags any value extracted into sd_intervention/sd_control that shares a source line with the literal word "SE"/"SEM"/"standard error". Tested directly against the documented zsy234 failure text ("M = 47.14, SE = 2.36") - fires correctly on both intervention and control values, stays silent on a clean SD-only negative control. Sets result["sd_se_warning"] (top-level, not nested in primary_outcome - the extraction restructuring step doesn't move this key, unlike the fields it does know about). Wired into sr/main.py: audit_row gets a new sd_se_warning column, results_csv carries it, console prints a [SD/SE CHECK] summary block at end of Stage 4, same pattern as the #13/#20 plausibility flag from Session 11. Does NOT catch every SE/SD confusion - only the specific same-line co-occurrence pattern, and only on the text-fallback path.
    #10/#16 group/timepoint tripwire (MITIGATED, not resolved) — No existing check anywhere validated that a "group" label represented an actual randomized arm rather than a mislabeled timepoint - the exact zsy234 failure (baseline/posttreatment extracted as if they were intervention/control). Added _flag_group_timepoint_confusion(): two checks, both narrow and low-false-positive by design. (1) intervention_group or control_group contains timepoint vocabulary (baseline, post-treatment, follow-up, week N, T1/T2/T3, etc.) - real arm names essentially never look like this. (2) intervention_group and control_group are literally the same value - structurally impossible for a genuine between-group contrast. Called from _coerce_extraction_result, so it runs on BOTH extraction paths (vision and text-fallback), unlike the SD/SE check - it only needs the group labels the model already extracted, not literal source text. Tested against 8 cases including the exact zsy234 pattern (flags), two genuine two-arm trials with different naming conventions (stays silent), and a deliberate trap ("Waitlist Control" containing the word "Control" but no timepoint word - correctly stays silent). Wired into sr/main.py the same way as the SD/SE flag: group_timepoint_warning column, [GROUP/TIMEPOINT CHECK] console summary. Scope limit stated explicitly in the docstring: only catches mislabeling visible in the group NAME itself - a model that invents a plausible-but-wrong arm name (rather than reusing an obvious timepoint word) is not caught.
    Hardcoded trial-specific group matching (RESOLVED) — _infer_group_timepoint_from_text hardcoded three literal arm names from one specific trial (CBT-IP, CBT-P, UMC) with NO generic fallback - for every other paper, group_name stayed None and the function returned (None, None) unconditionally. This gave the appearance of general group-inference machinery while only ever working for the one study it was written against. Fixed by adding _collect_candidate_group_names(), which derives candidate arm names from whatever the model already extracted for THIS specific paper (intervention_group/control_group fields, or group/arm/name/label values inside any groups_n_by_timepoint-style rows) instead of hardcoded literals. Verified both that the original trial still matches correctly (now driven by data, not string literals) and that a completely different trial's arm names - previously impossible to match at all - now work. Separately reviewed _sample_size_from_text_for_group, which ALSO hardcodes those same three literal names: left it alone and just documented why it's safe - its hardcoding only activates when group_norm exactly equals "cbtip"/"cbtp"/"umc" (guarded), with a working generic substring-match fallback (`else: matches_group = group_norm in normalized_line`) already in place for everything else, unlike _infer_group_timepoint_from_text which had no fallback at all.
    New regression tests (added) — tests/test_data_extractor_flags.py, 18 tests covering all of the above: the SD/SE tripwire (3 tests, including the exact zsy234 text), the group/timepoint tripwire (8 parametrized cases + 1 wiring-integration check confirming it actually runs as part of _coerce_extraction_result, not just callable in isolation), and the generalized group-name matching (4 tests, including confirming the original hardcoded trial's paper still works and a different trial's names now match too). Import path required correction: initially wrote `from data_extractor import DataExtractor`, which doesn't match this project's actual package layout - confirmed against tests/test_sr.py's own import (`from pipelines.sr.src.extraction import data_extractor`) and corrected to `from pipelines.sr.src.extraction.data_extractor import DataExtractor`. All 18 pass against the real project venv (not just simulated logic) - local suite now 423 passed (up from 405), 3 skipped, 11 deselected.
    Files touched this session: SOURCE_CODE/pipelines/sr/src/screening/relevance_screener.py, SOURCE_CODE/pipelines/sr/src/screening/rob2_tool.py, SOURCE_CODE/pipelines/sr/src/extraction/data_extractor.py, SOURCE_CODE/pipelines/sr/main.py, tests/test_data_extractor_flags.py (new).
    Verification limits, stated plainly: everything in this session was verified by (a) synthetic unit-level tests exercising the isolated logic, later confirmed passing against the real project venv, and (b) tracing the actual code paths and call sites by hand. NONE of it was verified against a real SR pipeline run on real PDFs - no live extraction, no live provider call, no confirmation that these tripwires actually fire (or stay silent) on the five-paper test corpus this document's earlier sessions used. That is the natural next verification step before treating #9/#15 and #10/#16 as meaningfully de-risked in practice, not just in unit tests.

======================================
3. CURRENT STATUS
======================================
Component 	                      Status 	                Details
GitHub Actions CI 	              not re-verified 	      Local suite 423 tests passing, Python 3.11.9; CI not re-run this session
Render Build 	                      not re-verified 	      Unchanged from Session 10; not re-deployed this session
Render Deploy 	                      not re-verified 	      Unchanged from Session 10; not re-checked this session
Render Health Check 	              ACTIVE 	                /_stcore/health returns ok
UptimeRobot 	                      MONITORING 	        5-minute pings
Provider Fallback 	              ACTIVE 	                DeepSeek → Qwen → Groq on transient errors
Streaming CLI 	                      DEFAULT 	                --no-stream disables
All Pipelines 	                      WORKING 	                coding, writing, appraisal, search, rct_search, sr
SR Pipeline 	                      WORKING WITH CAVEATS 	5/5 papers extract; outputs to root reports/sr/<run_id>/ + mirror output/sr/. Extraction is non-deterministic and has no semantic validation - see Known Issues #15-#18. Output requires manual verification before use.
Docker Support 	                      COMPLETE 	                Windows and macOS one-click scripts
Documentation 	                      CURRENT 	                README.md, HANDOFF.md, REVIEWER_GUIDE.md, Setup Instructions

======================================
4. KNOWN ISSUES
======================================
# 	Issue 	                                                                               Priority 	       Status
1 	Lami extraction fails — paper s10608-017-9875-4.pdf, Table 4, pages 12-13
                                                                                               High 	               RESOLVED (Session 8) — text fallback + study_overrides.yaml; underlying instability tracked as #17
2 	WeasyPrint not installed; PDF falls back to HTML                                       Medium 	               Open
3 	Anthropic geo-restricted 	                                                       Low 	               Use VPN or skip
4 	DeprecationWarning: escape sequence in project_layout.py 	                       Low 	               RESOLVED (Session 5)
5 	Streamlit warning: theme.baseFontSize invalid config option 	                       Low 	               RESOLVED (Session 5)
6 	cli.py and session.py dead code 	                                               Low 	               RESOLVED (Session 5) — deleted
7 	SR pipeline relative-import crash (-m invocation) 	                               High 	               RESOLVED (Session 6)
8 	SR output written under SOURCE_CODE/ instead of repo root 	                       Medium 	               RESOLVED (Session 6)
9 	Hardcoded qwen3.7-plus in _DEFAULT_MODELS (outer main.py); should read model constants Low 	               RESOLVED (Session 7)
10 	Cosmetic [ollama] Auto-detected best model line fires even on Qwen SR runs; does not affect actual provider used
                                                                                               Low 	               RESOLVED (Session 11) — see #25, same root cause (module-scope probe made lazy)
11 	Launcher completion message in run_sr_launcher printed stale pipelines/sr/outputs path Low 	               RESOLVED (Session 7)
12 	Vision regression: SR launcher defaulted qwen to text-only qwen-plus-latest, breaking all extraction
                                                                                               High 	               RESOLVED (Session 7) — now defaults to qwen-vl-max via QWEN_VISION_MODEL
13 	Inner sr/main.py argparse default may still hardcode qwen3.7-plus (only the outer launcher was verified fixed this session)
                                                                                               Low 	               RESOLVED (Session 11) — verified: --model defaults to None, threaded through unchanged everywhere; no hardcoded override found
14 	test_main_coverage.py references a nested prompts/coding/*.txt layout (with .txt) that does not exist on disk; actual files are flat prompts/-prompt.md. Tests pass against mocked paths, not real files
                                                                                               Low 	               RESOLVED (Session 11) — corrected to flat prompts/<role>-prompt.md; side finding tracked as new #43
15 	No SD/SE disambiguation. A reported SE is read as an SD, understating dispersion by up to sqrt(n) and inflating the effect size. Observed 8x understatement in zsy234.pdf
                                                                                               CRITICAL 	        MITIGATED (Session 12) — deterministic tripwire on the text-fallback path (see Session 12 notes); manual check via REVIEWER_GUIDE.md 3.1 still required, root cause not fixed
16 	No within- vs between-group detection. A within-subject pre/post contrast can be extracted as intervention-vs-control, producing a large invalid effect with no warning. Observed in zsy234.pdf
                                                                                               CRITICAL 	        MITIGATED (Session 12) — deterministic tripwire on both extraction paths (see Session 12 notes); manual check via REVIEWER_GUIDE.md 2.2 still required, root cause not fixed
17 	Extraction is non-deterministic. Same PDF yields different means/SDs/Ns on consecutive runs; observed in 2 of 5 test papers
                                                                                               High 	                Open — run 3x and diff before trusting output
18 	Broken font CMaps misdetected as garbled text. Affected PDFs have a clean text layer recoverable with a fixed +1 character offset, but the pipeline falls back to OCR
                                                                                               High 	                Open — likely upstream cause of #17
19 	zsy234.pdf still included in the test corpus results as a valid study despite reporting no between-group pain effect
                                                                                               High 	                Open — exclude with documented reason, or extract correct group-level values
20 	No effect-size plausibility bound. |g| > 1.5 from a psychotherapy trial passes unflagged
                                                                                               Medium 	                RESOLVED (Session 11) — flags |g/SMD|>1.5 or OR/RR beyond 10x/0.1x in results_csv + console; does not auto-exclude (tripwire only, not a fix for #15/#16)
21 	PICO discovery differs between interfaces: Streamlit UI globs output/rct_search/, CLI globs input/sr/. A PICO saved in one is invisible to the other
                                                                                               Low 	                RESOLVED (Session 11) — description was inaccurate: CLI actually checked input/rct_search/ then output/rct_search/ (never input/sr/); UI checked output/rct_search/ only. UI now merges both, matching CLI precedence
22 	RoB 2.0 runs independently of study_overrides.yaml and may assess OCR text for a study whose outcome data was hand-entered
                                                                                               Low 	                Open
23 	No regression fixtures for the five-paper test corpus. Ground truth exists only in REVIEWER_GUIDE.md prose
                                                                                               Medium 	                Open

24 	Streamlit UI override fields put API keys into st.session_state, i.e. into the server process. Safe locally; a shared/Render deployment would place user keys in a multi-user process 	Medium 	RESOLVED (Session 11, risk narrowed) — st.session_state is per-browser-session in Streamlit, not shared server-wide as originally framed; verified no os.environ mutation and no disk/echo leak (Session 9 fix confirmed durable). Added a "Clear stored keys" button to shorten the plaintext-in-memory exposure window
25 	providers.py probes Ollama at MODULE scope: the "[ollama] Auto-detected best model" line fires on import, on every run and every test, regardless of --provider. A network call during import is also a latent hang if Ollama is installed but unresponsive 	Medium 	RESOLVED (Session 11) — resolution moved to _resolve_ollama_model(), called lazily from call_ollama_provider() on first real use; also resolves #10
26 	pipelines.sr.main (~2.8s: scipy.stats, matplotlib, pymupdf) is imported even for coding mode 	Low 	RESOLVED (Session 11) — removed 4 dead top-level imports (run_coding, run_writing, run_search, run_sr) that were never referenced anywhere in main.py
27 	macOS launcher changes are untested on macOS. The curl /_stcore/health poll loop and the lsof port check need a real run 	Medium 	Open — verify before relying on them
28 	Old %TEMP%\ai_km_run_*.bat files from before the v2.4.7 fix still contain API keys in plaintext on any machine that ran the UI 	High 	Action required — delete them and rotate affected keys
29 	call_ai_with_fallback sent prompts to cloud providers even when --provider ollama was requested. Confidential input could reach a third party on a routine timeout 	CRITICAL 	RESOLVED (Session 10) — LOCAL_ONLY_PROVIDERS never falls back
30 	23 source files began with a UTF-8 BOM; previously misdiagnosed as corrupted comments 	Medium 	RESOLVED (Session 10) — stripped; check_no_bom.py guards
31 	Clean install on Python 3.14 fails across five packages 	High 	RESOLVED (Session 10) — main.py gates 3.11-3.12 with a download link
32 	OCR packages installed but unusable: no Tesseract/Poppler/libGL in the image, so ~2GB of PyTorch bought nothing 	Medium 	RESOLVED (Session 10) — moved to requirements-ocr.txt
33 	Docker_setup.bat and mac_docker_setup.sh were both non-functional and were the advertised one-click setup routes 	High 	RESOLVED (Session 10) — deleted; replaced by docker compose
34 	_is_transient_error matches substrings, so an auth error mentioning "connection" is treated as retryable and triggers fallback 	Low 	RESOLVED (Session 11) — checks HTTP status code explicitly (401/403 never transient); falls back only to the precise phrase "connection error", not the bare word "connection"
35 	No regression test asserting --provider ollama never reaches a cloud API. The fix for #29 is verified only by a manual check 	Medium 	RESOLVED (Session 11) — added tests/test_provider_fallback.py, 4 tests, verified passing in the real project venv (405 total)
36 	check_no_bom.py is not wired into CI, so BOMs can return silently 	Low 	Open
37 	Windows and macOS launchers used matching filenames but different mechanisms: the .bat files ran the virtualenv, the .sh files ran docker run 	Medium 	RESOLVED (Session 10) — both venv-based; Docker via docker compose only
38 	Setup instructions led with the hosted app and carried no confidentiality warning, in a tool intended for patient data 	High 	RESOLVED (Session 10) — explicit warning added to Option 1 and the Providers section
39 	macOS launchers are untested on macOS. Rewritten from Docker-based to venv-based in v2.4.8; the lsof port check and the Python 3.11/3.12 discovery loop need a real run 	Medium 	Open
40 	Ctrl+C during the startup import chain (pandas/pytesseract, ~7s cold start) raised a raw traceback through pandas internals instead of the clean "Session stopped. Returning to menu..." message - the entry-point's try/except KeyboardInterrupt only wrapped code inside if __name__ == "__main__", not the module-level imports above it 	Medium 	RESOLVED (Session 11) — imports wrapped in their own try/except KeyboardInterrupt
41 	Provider-select box in scripts/launcher.py misaligned on CJK-locale terminals: the Unicode checkmark (✓) is an ambiguous-width character and renders as 2 columns instead of 1, throwing every vision-capable provider row a column wider than its "x no vision" counterpart 	Low 	RESOLVED (Session 11) — replaced ✓ with ASCII "+", padded all badge variants to a fixed width before adding color codes
42 	No visible wait notice before a slow provider call (Ollama model load, or any cloud provider taking 15s+); looked indistinguishable from a hang, risking an impatient Ctrl+C mid-generation 	Low 	RESOLVED (Session 11) — call_ai() now prints a wait notice before dispatch, gated on sys.stdout.isatty()
43 	test_main_sr_mode (test_main_coverage.py) exercises main.main(mode='sr', ...), a code path that cannot occur for real: ALL_MODES has no "sr" key (SR mode is dispatched straight to run_sr_launcher() at the entry point, never reaches choose_role()). The test only passes because choose_role is fully mocked; with the mock removed it would raise KeyError on ALL_MODES['sr'] 	Low 	Open — needs a decision: redesign to assert SR routes to run_sr_launcher, or remove
44 	relevance_screener.py and rob2_tool.py both hardcoded a Windows-only absolute Tesseract path (C:\Program Files\Tesseract-OCR\tesseract.exe), unconditionally, in both files. Broke the OCR fallback entirely on macOS/Linux/Docker regardless of whether Tesseract was actually installed and working there - distinct from #32 (OCR packages installed but unusable due to missing system binaries), this was a straight wrong-path bug 	Medium 	RESOLVED (Session 12) — only overrides tesseract_cmd on Windows and only if that default path exists; otherwise defers to pytesseract's normal PATH-based discovery
45 	RoB2Assessor defaulted to model="qwen3.7-plus", matching nothing in providers.py's model registry. Unreachable via the documented pipeline (sr/main.py always passes model=args.model explicitly) but a landmine for direct construction that omits model 	Low 	RESOLVED (Session 12) — corrected to qwen-plus-latest, matching providers.py's QWEN_MODEL; also found _call_with_images() on this class is dead code, never actually invoked - assess_by_pdf_path() only ever calls _call_with_text()
46 	_infer_group_timepoint_from_text (data_extractor.py) hardcoded three literal arm names (CBT-IP, CBT-P, UMC) from one specific trial with NO generic fallback - silently returned (None, None) for every other paper's table, giving the appearance of general group-inference machinery while only ever working for one study 	Medium 	RESOLVED (Session 12) — generalized via _collect_candidate_group_names(), deriving candidate arm names from each paper's own extraction output instead of hardcoded literals; verified both the original trial and a different trial's names now match correctly
======================================
5. AI PROVIDERS
======================================
Provider 	                      Flag 	                Env Var 	        Default Model 	                Vision 	Streaming
DeepSeek 	                      --provider deepseek 	DEEPSEEK_API_KEY 	deepseek-v4-flash 	        No 	Yes
Qwen (text) 	                      --provider qwen 	        DASHSCOPE_API_KEY 	qwen-plus-latest (QWEN_MODEL) 	No* 	Yes
Qwen (vision/SR) 	              --provider qwen 	        DASHSCOPE_API_KEY 	qwen-vl-max (QWEN_VISION_MODEL) Yes 	Yes
OpenAI 	                              --provider openai 	OPENAI_API_KEY 	        gpt-4o-mini 	                Yes 	Yes
Anthropic 	                      --provider anthropic 	ANTHROPIC_API_KEY 	claude-sonnet-5 	        Yes 	Yes
Groq 	                              --provider groq 	        GROQ_API_KEY 	        llama-3.3-70b-versatile 	Yes 	Yes
Ollama 	                              --provider ollama 	OLLAMA_HOST 	        Auto-detected 	                No 	Yes

*The qwen provider is registered as vision-capable in providers.py, but its default text model (qwen-plus-latest) is text-only. SR extraction now uses QWEN_VISION_MODEL (qwen-vl-max) so vision works without a --model flag.

Fallback: transient errors (timeout, 429, 502, 503) trigger next provider; auth errors (401, 403) raise immediately. SR pipeline blocks non-vision providers (DeepSeek/Ollama not usable for SR).

======================================
6. TEST COVERAGE (per-module % not re-measured this session; total test count did change)
======================================
Module 	Coverage
writing.py 	        89%
traice_integration.py 	98%
appraisal.py 	        86%
coding.py 	        78%
checkpoint.py 	        73%
path_utils.py 	        74%
search.py 	        72%
rct_search.py 	        63%
ui/app.py 	        58%
rag.py 	                57%
streaming.py 	        55%
providers.py 	        54%
main.py 	        41%
document_reader.py 	24%
SR pipeline (src/*) 	~10-53% (low)
TOTAL 	~53% (423 tests, not re-measured this session - up from 405)

======================================
7. NEXT SESSION PRIORITIES
Priority 	Task 	Details
1 	Verify Session 12's tripwires against the real 5-paper test corpus (NEW, top priority) 	Everything in Session 12 (#9/#15 SD/SE tripwire, #10/#16 group/timepoint tripwire) was verified via unit tests only - synthetic text and mocked results, confirmed passing against the real project venv, but never run through an actual SR pipeline pass on real PDFs. Run the pipeline on the 5-paper corpus and confirm the tripwires fire (or correctly stay silent) as expected on real extraction output, especially zsy234.pdf.
2 	SD-vs-SE disambiguation (#15, CRITICAL) 	MITIGATED not resolved: Session 12 added a same-line co-occurrence tripwire (text-fallback path only) and a prompt-level warning (both paths). Root-cause detection (parsing the actual statistical meaning of a table, not just checking for the word "SE" nearby) is still not implemented. The tripwire will miss a "SE" label on a different line from its value, and has no coverage at all on the vision path.
3 	Within- vs between-group detection (#16, CRITICAL) 	MITIGATED not resolved: Session 12 added two narrow checks (timepoint vocabulary in a group label; identical intervention/control labels) on both extraction paths. A model that invents a plausible-but-wrong arm name instead of reusing an obvious timepoint word is not caught - this needs a stronger signal (e.g. cross-referencing against how the paper itself describes its study design) that hasn't been designed yet.
4 	Test Docker on the laptop (#19 in this doc) 	docker compose build; docker compose run --rm cli; docker images for size; and the .env-exclusion check. Still nothing Docker-related has ever been executed. Unchanged since Session 10.
5 	Verify the macOS launchers (#39) 	Still untested on a real Mac. Unchanged since Session 9/10.
6 	Resolve zsy234.pdf (#19 in README numbering) 	Still in SR results as a valid study at g=-2.36. Session 11's plausibility flag would flag the magnitude; Session 12's group/timepoint tripwire should now also flag the mislabeled baseline/posttreatment groups directly, if this study is re-run through extraction. Not yet re-run - see priority 1 above. The study itself is still not excluded or corrected either way.
7 	Fix font CMap decode (#18 in README numbering) 	All five test PDFs decode cleanly with a fixed +1 character offset yet are OCR'd unnecessarily. Likely upstream cause of extraction non-determinism (#17 in README numbering).
8 	Decide on test_main_sr_mode (#43) 	Either redesign to assert SR mode routes to run_sr_launcher(), or remove - it currently tests a code path (ALL_MODES['sr']) that cannot occur outside the mock. Unchanged since Session 11.
9 	Add regression fixtures for the five-paper corpus (#23) 	Including expected FAILURES: zsy234 must not be silently included with a large effect. Session 12's test_data_extractor_flags.py covers the tripwire logic in isolation but is not a substitute for corpus-level fixtures with known-correct expected output.
10 	Raise SR pipeline coverage 	Core screening/extraction still ~10-53%, not re-measured this session.
11 	Re-verify CI/Render after pushing Session 11+12's commits 	Local suite is green (423/3/11) but CI and the Render deployment were not re-run this session - confirm both before relying on this handoff's "current status."
12 	Wire check_no_bom.py into CI (#36) 	Still open, unchanged since Session 10. One step in the workflow.

8. LESSONS LEARNED
======================================
    Tests must mock utils.rag.index_uploads rather than doing real embedding (slow + non-deterministic).
    Use single-quoted here-strings when writing Python files from PowerShell to avoid $/quote/backtick escaping.
    main() runs an interactive input() loop and calls call_ai directly, NOT the run_* functions. Mock input with task + KeyboardInterrupt.
    Never use CREATE_NEW_PROCESS_GROUP for interactive CLI on Windows.
    Never hardcode model versions if *-latest aliases exist.
    Render dashboard settings can override render.yaml; always inspect Render logs.
    Render Linux must not install Windows-only packages (pywin32); use requirements-render.txt.
    docx2txt==0.8 has no wheel; install separately or allow from source.
    Streamlit app path is SOURCE_CODE/ui/app.py, not src/ui/app.py.
    Mark network tests @pytest.mark.live to avoid CI flakes.
    ChromaDB on Linux CI needs cmake, python3-dev, and pysqlite3.
    Raw-string (r""") docstrings when they contain backslashes to avoid escape-sequence warnings.
    (Session 6) Never launch a package's module by file path via subprocess; use python -m package.module with cwd= so relative imports resolve.
    (Session 6) Every directory in an import chain needs an init.py for -m module invocation.
    (Session 6) When computing a repo root from Path(file), count .parent hops carefully; prefer parents[N] for verifiability. sr/src/utils/project_layout.py needs six hops.
    (Session 6) SR nested input() prompts require a real interactive TTY; run python SOURCE_CODE/main.py --mode sr --provider qwen directly for PICO selection.
    (Session 6) Git does not track empty directories; use git rm -r for tracked folders so deletion is recorded.
    (Session 7) A provider being "vision-capable" is not the same as its default model being vision-capable. After centralising model constants (#9), the qwen provider stayed marked vision-capable while its default (qwen-plus-latest) is text-only — silently breaking all SR extraction with HTTP 200 + empty results. Keep a separate QWEN_VISION_MODEL for image work.
    (Session 7) A silent extraction failure looks like success: the pipeline completed all stages, wrote CSVs, and produced reports/forest plot while extracting zero data. Watch for meta-analysis "< 2 studies with usable data" as the real signal.
    (Session 7) Verify "unused" before deleting. The prompts/ folder looked deletable but 14/15 files are load-bearing agent persona files loaded via explicit AI_DIR paths that a naive grep for the folder can miss. Always cross-reference against the actual loader/registry, widen the search beyond one subtree, and remove individual orphans rather than whole folders. The test suite would NOT have caught deletion of the folder.
    *(Session 7) Diagnostic .log files clutter git status; gitignore them (sr_*.log) rather than committing.
    (Session 8) A silent wrong answer is worse than a crash. Lami failed loudly (dropped off the forest plot, immediately visible). zsy234 failed silently: confident magnitude, symmetric CI, clean CSV row, passed six stages and a DOCX report while being entirely invalid. Plausibility is not evidence of correctness.
    (Session 8) Never gate a correction on the value it is correcting. The numeric-signature match (self._near(mi, 7.35) ...) fired only when extraction was already right and went silent exactly when it was wrong — turning a wrong-number failure into a missing-study failure, and risking mislabelling any other study whose means landed nearby.
    (Session 8) Find the reader before patching the writer. Three patches wrote result["first_author"] while every consumer read result["study_metadata"]["first_author"], which nothing in the codebase ever wrote. Grep for the consumer first.
    (Session 8) Verify a patch actually applied. Two patch scripts printed success while writing nothing (one searched for "result = self._derive_missing_sample_sizes(result)"; the actual line has no assignment). Any patch script must assert its anchors before writing and abort loudly otherwise.
    (Session 8) Apply multi-edit patches bottom-up (highest line number first) so earlier line numbers stay valid.
    (Session 8) "Garbled text" may be a broken font CMap, not a scan. Check for a fixed character-code offset before falling back to OCR — decoding is lossless, OCR is not.
    (Session 8) A bare negation in .gitignore cannot re-include a file inside an excluded directory; git never descends into it. Use input/*, !input/sr/, input/sr/*, !input/sr/file.
    (Session 8) git check-ignore reports the matching rule whether it excludes or re-includes; a leading ! means the file is tracked. Use --no-index to test the rule rather than the index state.
    (Session 8) Do not paste Python at a PowerShell prompt. Use @' ... '@ | Set-Content file.py, then run the file.
    (Session 9) Popen's env= already passes variables to the child. Writing them into a generated script as well is redundant AND leaks them — cmd echoes every line, and the file persists on disk. Secrets belong in env=, never on a command line or in a script body (a command line is also visible in ps / Task Manager details).
    (Session 9) Clearing .env does not revoke a key. Anything that reached a screen, a screenshot, a temp file, or shell history must be rotated at the provider.
    (Session 9) An unescaped ( or ) in echo text inside a batch if ( ... ) block closes the block early. cmd parses the whole block before executing it, so "... was unexpected at this time" appears before the block would even run — and the parenthetical text can be far from where the error is reported. Escape as ^( / ^) or reword.
    (Session 9) A package __init__.py that eagerly imports heavy submodules makes every consumer pay for them. Importing three path helpers cost 2.2s of chromadb and pymupdf. PEP 562 __getattr__ gives lazy loading with no API change. Verify mock.patch targets still resolve — patch("utils.rag.X") works because patch imports the submodule; patch("utils.X") would not.
    (Session 9) Inside a container, localhost is the container. --add-host host.docker.internal:host-gateway only creates the route; the app still needs the host-facing URL. This silently broke Ollama on macOS.
    (Session 9) set -e makes subsequent `if [ $? -ne 0 ]` handlers dead code — the script exits before reaching them. Use set -uo pipefail when the script does its own error checking.
    (Session 9) .gitattributes must force LF on *.sh. With core.autocrlf=true, a Windows commit stores CRLF and the shebang breaks on macOS. Check with git check-attr text eol -- path, not by reading the warnings.
    (Session 9) git check-ignore reports a file as tracked (not ignored) once it is in the index; use --no-index to test the rule itself. And a bare ! negation cannot re-include a file inside an excluded directory — git never descends into it.
    (Session 10) Matching filenames across platforms imply matching behaviour. Mac_kcMedicalResearch_CLI.sh and AI_kcMedicalResearch_CLI.bat looked like a pair and were not - one ran the venv, the other ran Docker. Parity in naming without parity in mechanism is worse than obviously different names, because the documentation then describes both as one thing.
    (Session 10) Check what the default path in the documentation actually recommends. The setup instructions led with a third-party hosted app as "the right choice for most people" in a tool built so that patient data could stay local. Nobody had reread that sentence against the tool's purpose.
    (Session 10) A fallback chain that ignores WHY a provider was chosen will eventually violate the reason it was chosen. Ollama was selected for confidentiality; the chain treated it as merely first in a list. Any mechanism that substitutes one provider for another must know which properties of the original were load-bearing.
    (Session 10) A timeout is not consent. Retry logic that changes WHERE data goes is not the same as retry logic that changes WHEN it is sent.
    (Session 10) The most dangerous failures print a success message. "[fallback] Succeeded with deepseek" scrolled past in a 200-line log while patient data left the machine. Compare Session 8's zsy234: a confident g=-2.36 with a clean CI. Neither looked like an error.
    (Session 10) Code paths nobody executes do not work. Both advertised one-click setup scripts were broken, unnoticed, because Docker was never installed on the dev machine. Documentation asserting that an untested path works is worse than no documentation.
    (Session 10) PowerShell 5 `Set-Content -Encoding UTF8` writes a BOM. Use `-Encoding utf8NoBOM` (PS7), `Out-File -Encoding ascii`, or [System.IO.File]::WriteAllText with UTF8Encoding($false). Files generated during Sessions 8-9 acquired BOMs this way.
    (Session 10) Put a version gate above the first third-party import, not merely near the top. Below `from dotenv import load_dotenv` the user gets ModuleNotFoundError and never sees the message.
    (Session 10) When a dependency needs system binaries pip cannot install, installing the Python package alone is worse than not installing it: it looks supported, costs disk, and fails at runtime. The image carried ~2GB of PyTorch for OCR it could not perform.
    (Session 9) Profile before optimising. The 15-20s startup was assumed to be an Ollama network probe; importtime showed it was eager imports. Measured 3.2s of imports against 15-20s observed, so filesystem/AV cold cache accounts for the remainder — no code change fixes that part.
    (Session 11) An entry-point's try/except doesn't cover module-level code. Wrapping `if __name__ == "__main__":` in try/except KeyboardInterrupt looks complete but doesn't catch Ctrl+C during the imports that run before that block starts. If startup is slow enough to interrupt, the imports need their own handler.
    (Session 11) "Ambiguous width" Unicode characters are locale-dependent, not font-dependent in the way you'd assume. A checkmark that's 1 column in an English-locale terminal can render as 2 columns in a CJK-locale terminal (East Asian Width property), silently breaking any layout that counts characters instead of accounting for this. Prefer plain ASCII for anything alignment-critical.
    (Session 11) When a document names an exact number as a bug example ("|g| > 1.5"), use that number, not a substitute you consider more defensible. A plausibility bound of 2.0 felt more principled but would have silently failed to catch the document's own cited case at g=1.51-1.99.
    (Session 11) Verify a Known Issue's literal claim against the code before fixing it, not just its symptom. #21's description ("CLI globs input/sr/") was wrong — checking rct_search.py directly showed the real behavior (input/rct_search/ then output/rct_search/). Fixing the described-but-nonexistent bug would have left the real, narrower gap in place.
    (Session 11) A named risk mechanism doesn't always match the real one. #24 described API keys landing in "the server process" as if shared across users; st.session_state is per-browser-session in Streamlit by default. Trace the actual data flow (here: os.environ.copy(), never mutated; subprocess env= only) before implementing a fix for the risk as originally framed — the real, narrower risk (plaintext duration-of-exposure) still needed addressing, just not the way the description implied.
    (Session 11) Fixing a hardcoded test path can surface a design bug the test was hiding. Correcting test_main_sr_mode's mocked prompt path revealed that ALL_MODES has no "sr" key at all — the test exercises a code path that cannot happen outside its own mock. A mechanical path fix is not the same as validating the test still tests something real; flag the deeper finding rather than silently patch past it.

======================================
9. FINAL VERIFIED RENDER SETTINGS
======================================
Build Command: pip install --upgrade pip && pip install --no-cache-dir --only-binary=:all: -r requirements-render.txt && pip install --no-cache-dir --no-deps docx2txt==0.8

Start Command: streamlit run SOURCE_CODE/ui/app.py --server.address=0.0.0.0 --server.port=$PORT --server.enableCORS=false --server.enableXsrfProtection=false

Env: PYTHON_VERSION=3.11.9 Health: https://ai-kcmedicalresearch.onrender.com/_stcore/health → ok
10. SR PIPELINE — OUTPUT LOCATIONS & VISION MODEL

Run directly (not via menu launcher) for interactive PICO selection: python SOURCE_CODE/main.py --mode sr --provider qwen (defaults to vision model qwen-vl-max after the Session 7 fix — no --model flag needed).

Per-run output (timestamped, audit-friendly): reports/sr/<run_id>/ containing uploads/, data/screened/, data/extracted/, data/results/, output/figures/forest_plot.png, output/reports/systematic_review.docx and .html.

Mirror (always latest run): output/sr/figures/ and output/sr/reports/.

All paths are repo-root relative (no SOURCE_CODE/ prefix) after the Session 6 project_layout.py fix.

Vision model override: set env QWEN_VISION_MODEL to change the SR extraction model (default qwen-vl-max). Text-mode Qwen still uses QWEN_MODEL (qwen-plus-latest).

Commit trail Session 7: 3c2e51b (#9) → 4b793ea (#3) → a83ec1c (#11) → 5d6a8ca (test hygiene) → 9c536e1 (vision fix) → b1f4c48 (orphan prompt) → 1b6b9b0 (dead-code + gitignore).
11. SR STUDY METADATA AND MANUAL OVERRIDES (Session 8)

Metadata resolves in three stages, each overriding the last: (1) model output, (2) PDF-derived via resolve_pdf_metadata() and flagged metadata_source = "pdf_auto (verify)", (3) reviewer overrides from input/sr/study_overrides.yaml (env SR_STUDY_OVERRIDES).

Override file format, keyed by PDF filename:

"some_paper.pdf":
  first_author: Nguyen
  year: 2021
  n_intervention: 42
  n_control: 40
  mean_intervention: 4.10
  sd_intervention: 1.85
  note: "Table 2, 12-week endpoint. Verified from PDF p.7, 2026-08-17."

Allowed fields: first_author, year, doi, study, study_id, n_intervention, n_control, mean_intervention, sd_intervention, mean_control, sd_control, note. Unknown fields are ignored with a warning.

Metadata fields fill only when extraction left them blank. Numeric fields replace extraction output. Extraction still runs in full so the log can report field(7.32->7.35) versus field(confirmed 7.35) — do not add a fast path that skips extraction for overridden studies or the cross-check is lost.

Overrides affect extraction and meta-analysis only. Screening (Stage 2) and RoB 2.0 (Stage 3.5) re-read the PDF independently.

Reviewer rules (full version in Readme/REVIEWER_GUIDE.md): read the source table before entering a value; always fill note with table, page, and date; verify symmetrically rather than only checking studies whose results surprise you; never edit the override file after looking at the forest plot.

======================================
12. IMMEDIATE ACTIONS BEFORE NEXT SESSION
======================================

1. ROTATE API KEYS. (Still outstanding as of Session 10.) Anthropic, DeepSeek, and DashScope keys were displayed in
   plaintext by the pre-v2.4.7 UI launcher and appeared in screenshots.
   Clearing .env does not revoke them. Rotate at each provider console, then
   put the new keys in .env (which is gitignored).

2. Delete stale temp files: Remove-Item "$env:TEMP\ai_km_run_*.bat"

3. Set spend limits at each provider so a future leak is bounded.

4. Verify the venv: python -c "import sys; print(sys.executable)" should
   resolve under .venv\Scripts\. It was observed resolving to
   C:\Users\user\...Python311 while the prompt showed (.venv).

5. Test the macOS launchers on an actual Mac (Issue #27).

6. Decide on test_main_sr_mode (#43): redesign to assert SR mode routes to
   run_sr_launcher(), or remove it - it currently tests a code path
   (ALL_MODES['sr']) that only "passes" because choose_role is fully mocked.

7. Push Session 11+12's commits and re-verify CI (GitHub Actions) and the
   Render deployment - neither has been re-run since v2.4.9. Local suite is
   green (423 passed, 3 skipped, 11 deselected) but that is not the same
   guarantee as CI passing in a clean environment.

8. Run the SR pipeline against the real 5-paper test corpus to verify
   Session 12's tripwires (#9/#15 SD/SE, #10/#16 group/timepoint) actually
   fire correctly on real extraction output, not just unit-test fixtures -
   see NEXT SESSION PRIORITIES item 1.

Handoff prepared: 2026-08-18 · Version: v2.4.10 · Single source of truth for next session.
