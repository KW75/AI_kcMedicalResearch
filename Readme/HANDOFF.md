AI kcMedicalResearch — Combined Handoff Document
Version 2.4.6 — SR Extraction Provenance, Generic Study Overrides, Reviewer Guide

Date: 2026-08-17 Repository: https://github.com/KW75/AI_kcMedicalResearch Live App: https://ai-kcmedicalresearch.onrender.com Health Check: https://ai-kcmedicalresearch.onrender.com/_stcore/health Uptime Monitor: UptimeRobot, 5-minute interval, keeps free-tier Render instance warm Tests: 401 passed, 3 skipped, 11 deselected/live tests (410 passed, 5 skipped with no marker filter) Coverage: ~53% Current Status: CI green, Render live, health endpoint returns ok

CRITICAL READ FIRST: Session 8 found that SR extraction can produce a confident, precisely-quantified, entirely invalid effect size with no warning at any stage. See Session 8 notes, Known Issues #15 and #16, and Readme/REVIEWER_GUIDE.md. Do not report any pooled estimate from this pipeline without manual source verification.

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

======================================
3. CURRENT STATUS
======================================
Component 	                      Status 	                Details
GitHub Actions CI 	              GREEN 	                401 tests, Python 3.11, checkout@v5, setup-python@v6
Render Build 	                      GREEN 	                Uses requirements-render.txt
Render Deploy 	                      LIVE 	                Streamlit app live
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
                                                                                               Low 	               Open
11 	Launcher completion message in run_sr_launcher printed stale pipelines/sr/outputs path Low 	               RESOLVED (Session 7)
12 	Vision regression: SR launcher defaulted qwen to text-only qwen-plus-latest, breaking all extraction
                                                                                               High 	               RESOLVED (Session 7) — now defaults to qwen-vl-max via QWEN_VISION_MODEL
13 	Inner sr/main.py argparse default may still hardcode qwen3.7-plus (only the outer launcher was verified fixed this session)
                                                                                               Low 	               Open — verify
14 	test_main_coverage.py references a nested prompts/coding/*.txt layout (with .txt) that does not exist on disk; actual files are flat prompts/-prompt.md. Tests pass against mocked paths, not real files
                                                                                               Low 	               Open
15 	No SD/SE disambiguation. A reported SE is read as an SD, understating dispersion by up to sqrt(n) and inflating the effect size. Observed 8x understatement in zsy234.pdf
                                                                                               CRITICAL 	        Open — manual check required
16 	No within- vs between-group detection. A within-subject pre/post contrast can be extracted as intervention-vs-control, producing a large invalid effect with no warning. Observed in zsy234.pdf
                                                                                               CRITICAL 	        Open — manual check required
17 	Extraction is non-deterministic. Same PDF yields different means/SDs/Ns on consecutive runs; observed in 2 of 5 test papers
                                                                                               High 	                Open — run 3x and diff before trusting output
18 	Broken font CMaps misdetected as garbled text. Affected PDFs have a clean text layer recoverable with a fixed +1 character offset, but the pipeline falls back to OCR
                                                                                               High 	                Open — likely upstream cause of #17
19 	zsy234.pdf still included in the test corpus results as a valid study despite reporting no between-group pain effect
                                                                                               High 	                Open — exclude with documented reason, or extract correct group-level values
20 	No effect-size plausibility bound. |g| > 1.5 from a psychotherapy trial passes unflagged
                                                                                               Medium 	                Open
21 	PICO discovery differs between interfaces: Streamlit UI globs output/rct_search/, CLI globs input/sr/. A PICO saved in one is invisible to the other
                                                                                               Low 	                Open
22 	RoB 2.0 runs independently of study_overrides.yaml and may assess OCR text for a study whose outcome data was hand-entered
                                                                                               Low 	                Open
23 	No regression fixtures for the five-paper test corpus. Ground truth exists only in REVIEWER_GUIDE.md prose
                                                                                               Medium 	                Open

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
6. TEST COVERAGE (unchanged this session)
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
TOTAL 	~53% (401 tests)

======================================
7. NEXT SESSION PRIORITIES
======================================
Priority 	                                                        Task 	Details
1 	Fix font CMap decode (Issue #18) 	                        Highest value remaining. All five test PDFs decode cleanly with a fixed +1 character-code offset yet are OCR'd unnecessarily. Detect the offset (decode a sample and score against common English words), apply it, and only fall back to OCR if the decoded text still scores poorly. Likely resolves or reduces #17. Entry point: the "Garbled text detected" check in relevance_screener.py and rob2_tool.py.
2 	Resolve zsy234.pdf (Issue #19) 	                                Either exclude with a documented PRISMA reason ("no between-group effect estimate available for the review outcome") or extract correct group-level post-treatment pain values from Table 3 / Figure 4. Record the decision in study_overrides.yaml with the page reference.
3 	Add semantic validators (Issues #15, #16, #20) 	                Prompt the model to return the dispersion measure verbatim (SD/SE/SEM/CI) and refuse SE without conversion; require distinct intervention_group_label and control_group_label and reject when equal or empty; flag |g| > 1.5 for review. These three would have caught the zsy234 failure.
4 	Add regression fixtures (Issue #23) 	                        Encode expected outcomes for the five-paper corpus, including expected FAILURES (zsy234 must not be silently included with a large effect). Turns Session 8 debugging into a permanent test.
5 	Raise SR pipeline coverage 	                                Core screening/extraction logic still ~10-53%
6 	Verify inner sr/main.py model default (Issue #13) 	        Confirm the inner argparse default reads a model constant, not hardcoded qwen3.7-plus
7 	Silence Ollama auto-detect on non-Ollama runs (Issue #10) 	Cosmetic [ollama] line in inner SR package
8 	Reconcile test_main_coverage.py prompt paths (Issue #14) 	Tests reference nonexistent nested prompts/coding/*.txt
9 	PDF export via fpdf2 	                                        Pure-Python, no GTK3 dependency (addresses Issue #2)
10 	Add visible app version/commit 	                                Streamlit sidebar

======================================
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

Handoff prepared: 2026-08-17 · Version: v2.4.6 · Single source of truth for next session.
