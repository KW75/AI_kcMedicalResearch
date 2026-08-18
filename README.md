AI kcMedical Research

A multi-mode AI assistant for medical research, critical appraisal, systematic review, coding, and writing. Uses cloud providers by default (DeepSeek, Qwen, OpenAI, Anthropic, Groq) with optional local Ollama support.

    Version: 2.4.10
    Tests: 423 passed, 3 skipped
    Coverage: ~53%
    CI: GitHub Actions - Green
    GitHub: https://github.com/KW75/AI_kcMedicalResearch
    Live App: https://ai-kcmedicalresearch.onrender.com
    Health Check: https://ai-kcmedicalresearch.onrender.com/_stcore/health
    Uptime: UptimeRobot (5-min monitoring, prevents cold starts)

Quick Start

Nothing to install - use the hosted app:

    https://ai-kcmedicalresearch.onrender.com

To run locally with Docker (supplies its own Python, so your installed
version does not matter):

    git clone https://github.com/KW75/AI_kcMedicalResearch.git
    cd AI_kcMedicalResearch
    copy .env.example .env          # then add your API keys
    cd docker
    docker compose run --rm cli     # interactive CLI
    docker compose up ui            # Streamlit UI on :8501

NOT YET VERIFIED: the Docker route has not been executed end to end. See
Known Issue #19.

Full instructions, including the venv route: Readme/Setup_Instructions_for_Users.txt

Local Development (Without Docker)

Requires Python 3.11 or 3.12. Newer versions are rejected at startup with a
download link - several pinned dependencies have no wheels for 3.13+.

Convenience launchers create .venv, install dependencies and start the app.
Windows and macOS behave identically; both use the virtualenv, not Docker:

    scripts\windows\AI_kcMedicalResearch_CLI.bat   /  scripts/macos/Mac_kcMedicalResearch_CLI.sh
    scripts\windows\AI_kcMedicalResearch_UI.bat    /  scripts/macos/Mac_kcMedicalResearch_UI.sh

Run all commands from the project root.

python SOURCE_CODE/main.py                            # coding mode (default)
python SOURCE_CODE/main.py --mode writing             # writing mode
python SOURCE_CODE/main.py --mode rct_search          # RCT search pipeline
python SOURCE_CODE/main.py --mode search              # PubMed search
python SOURCE_CODE/main.py --mode appraisal           # critical appraisal
python SOURCE_CODE/main.py --mode sr --provider qwen  # systematic review (needs vision)
python SOURCE_CODE/main.py --no-stream                # disable streaming
python SOURCE_CODE/main.py --resume                   # resume from checkpoint
python SOURCE_CODE/main.py --dry-run                  # test without API calls
python scripts/launcher.py                            # menu-driven launcher

Modes
Mode 	        Flag 	                Roles
Coding 	        --mode coding 	        Builder, Reviewer, Tester
Writing 	--mode writing 	        Writer, Editor, QA
RCT Search 	--mode rct_search 	Formulator, Searcher, Validator
Search 	        --mode search 	        Researcher
Appraisal 	--mode appraisal 	Appraiser, Methodologist, Summariser
SR 	        --mode sr 	        SR Methodologist

Providers
Provider 	        Flag 	                Environment Variable 	Notes
DeepSeek (DEFAULT) 	--provider deepseek 	DEEPSEEK_API_KEY 	Fast, cost-efficient
Qwen 	                --provider qwen 	DASHSCOPE_API_KEY 	Recommended for SR (auto-uses vision model)
OpenAI 	                --provider openai 	OPENAI_API_KEY 	GPT-4 vision
Anthropic 	        --provider anthropic 	ANTHROPIC_API_KEY 	Claude vision
Groq 	                --provider groq 	GROQ_API_KEY 	Fast inference
Ollama (local) 	        --provider ollama 	OLLAMA_HOST 	Free but slow; offline/testing only

On transient errors (timeout, 429, 502, 503), the system automatically tries the next provider. Default chain: DeepSeek -> Qwen -> Groq. Configure via FALLBACK_PROVIDERS. Authentication errors (401, 403) raise immediately and never fall back.

CONFIDENTIALITY: Ollama is the only provider that keeps your input on your own
machine. Every other provider transmits the prompt to an external API. If your
input contains patient-identifiable or otherwise confidential data, use
--provider ollama.

Requests to Ollama NEVER fall back to a cloud provider, even on a timeout.
Before v2.4.8 they did: an explicit --provider ollama produced the chain
[ollama, deepseek, qwen, groq], so an Ollama timeout silently sent the prompt
to DeepSeek and printed a success line. Ollama cannot run SR mode (no vision).

Note on Ollama in Docker: inside a container, localhost is the container, not your machine. The Docker launchers set OLLAMA_HOST=http://host.docker.internal:11434 for you; if you run a container by hand, set it yourself or Ollama will be unreachable.

Note on Qwen and vision: the Qwen text model (QWEN_MODEL, default qwen-plus-latest) is text-only. The SR pipeline requires image understanding, so it now automatically uses a separate vision model (QWEN_VISION_MODEL, default qwen-vl-max) — you do not need to pass a --model flag for SR.
Streaming

All providers support live token streaming, enabled by default in CLI terminals. Use --no-stream to disable. Non-TTY environments (pipes, CI) automatically use batch mode.

Environment Variables (.env)

Copy .env.example to .env and fill in the keys you need. .env is gitignored.

SECURITY: before v2.4.7 the Streamlit UI printed every API key into the
launched terminal window. If you used the UI before v2.4.7, rotate your keys
at the provider consoles and delete any leftover %TEMP%\ai_km_run_*.bat files.
Clearing .env does not revoke a key.

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
QWEN_VISION_MODEL=qwen-vl-max
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

SR_STUDY_OVERRIDES=input/sr/study_overrides.yaml

EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
CLI_THEME=dark

Startup Time

As of v2.4.9, the module-scope Ollama probe and the unconditional
pipelines.sr.main import described in earlier versions of this section are
both fixed (#17, #18): Ollama's model auto-detect now runs lazily on first
actual use instead of on every import, and coding/writing/search/appraisal
modes no longer pull in pipelines.sr.main's scipy/matplotlib/pymupdf chain
at all. Startup time was previously ~7 seconds cold; the actual new number
has not been re-measured after this change. On Windows, first-run antivirus
scanning of native extension modules adds noticeably more than subsequent
runs regardless.

Running Tests

python -m pytest -m "not live" --tb=short -q          # standard suite
python -m pytest -q                                   # all markers (410 passed, 5 skipped as of v2.4.5; not re-verified since)
python -m pytest --cov=SOURCE_CODE --cov-report=html  # with coverage
python -m pytest -m live -v                           # live provider smoke tests

Current status: 423 passed, 3 skipped, 11 deselected.

python scripts/check_no_bom.py                        # fail on UTF-8 BOMs in source
python scripts/strip_bom.py                           # remove them

SR Pipeline

READ Readme/REVIEWER_GUIDE.md BEFORE USING SR OUTPUT IN A REVIEW.

Extraction is LLM-based and cannot verify its own semantics. It will emit a
confident, precise effect size whether or not it understood the source paper.
Every extracted mean, SD, and N must be checked against the source PDF before
any pooled estimate is reported. See Known Issues #9 and #10 for documented
failure modes.

As of v2.4.10, results_csv carries three tripwire columns that flag (never
silently correct or exclude) studies worth a closer look:
plausibility_flag (#13, implausible effect-size magnitude), sd_se_warning
(#9, a value extracted into an SD field from a source line also mentioning
"SE"/"SEM"/standard error), and group_timepoint_warning (#10, a group label
that looks like a timepoint, or identical intervention/control labels). The
console prints a summary block for each at the end of Stage 4. These are
deterministic pattern checks, not semantic verification - they catch the
specific documented failure patterns, not every possible extraction error.
Manual verification against the source PDF is still required regardless of
whether any flag fired.

Place your PDFs in the SR input folder:

Windows:        copy *.pdf input\sr\
macOS/Linux:    cp *.pdf input/sr/

Run the pipeline directly (not via the launcher menu) so the interactive PICO prompts receive a real TTY:

python SOURCE_CODE/main.py --mode sr --provider qwen  # auto-uses qwen-vl-max (vision)

Outputs are written to a timestamped run folder and mirrored to the output tree:

reports/sr/<run_id>/    # systematic_review.docx/.html, forest_plot.png, audit CSVs
output/sr/figures/      # mirror of forest_plot.png
output/sr/reports/      # mirror of report files

To override the SR extraction model, set QWEN_VISION_MODEL in .env (default qwen-vl-max). Text-mode Qwen continues to use QWEN_MODEL (qwen-plus-latest).
Study Metadata and Manual Overrides (v2.4.6)

Study metadata (first author, year, DOI) is resolved in three stages, each
overriding the last:

    1. metadata returned by the extraction model
    2. metadata derived from the PDF itself (PyMuPDF metadata, DOI regex,
       copyright-line year). Best-effort only; flagged in the output as
       metadata_source = "pdf_auto (verify)"
    3. reviewer overrides from input/sr/study_overrides.yaml

Overrides are keyed by PDF filename. Metadata fields fill only when extraction
left them blank; numeric outcome fields REPLACE whatever extraction produced,
because the reason to record them is that extraction got them wrong.

"some_paper.pdf":
  first_author: Nguyen
  year: 2021
  n_intervention: 42
  n_control: 40
  mean_intervention: 4.10
  sd_intervention: 1.85
  note: "Table 2, 12-week endpoint. Verified from PDF p.7, 2026-08-17."

Extraction still runs in full when an override exists, so the log distinguishes:

  field(7.32->7.35)      extraction was wrong, override corrected it
  field(confirmed 7.35)  extraction independently agreed with the reviewer
  field(absent->7.35)    extraction produced nothing for this field

The "confirmed" case is a genuine cross-check. Do not disable extraction for
overridden studies or you lose it.

Overrides affect extraction and meta-analysis only. Screening (Stage 2) and
RoB 2.0 (Stage 3.5) re-read the PDF independently and are unaffected.

At the end of Stage 3 the log prints a DATA PROVENANCE SUMMARY listing every
study whose values were manually overridden or whose metadata was
auto-derived. Both must be described in the review's data-collection methods.
Deployment (Render)

    URL: https://ai-kcmedicalresearch.onrender.com
    Health: https://ai-kcmedicalresearch.onrender.com/_stcore/health
    Auto-deploy: push to main triggers deploy
    Build: pip install --upgrade pip && pip install --no-cache-dir --only-binary=:all: -r requirements-render.txt && pip install --no-cache-dir --no-deps docx2txt==0.8
    Monitoring: UptimeRobot pings every 5 min (prevents free-tier cold starts)

Known Issues
# 	Issue 	                        Priority 	                               Status
1 	Lami extraction fails — paper s10608 (Table 4, pages 12-13); 4/5 papers extract
                                        High 	                                       RESOLVED (v2.4.6) — text fallback + study_overrides.yaml; see #11 for the underlying instability
2 	WeasyPrint not installed 	Medium 	                                       PDF falls back to HTML
3 	Anthropic geo-restricted 	Low 	                                       Use VPN or skip
4 	Hard-coded qwen3.7-plus in _DEFAULT_MODELS overrides QWEN_MODEL
                                        Low 	                                       RESOLVED (v2.4.5)
5 	SR vision regression: launcher defaulted qwen to text-only qwen-plus-latest
                                        High 	                                       RESOLVED (v2.4.5) — now uses QWEN_VISION_MODEL (qwen-vl-max)
6 	Cosmetic [ollama] Auto-detected line prints on Qwen SR runs; no effect on provider used
                                        Low 	                                        RESOLVED (v2.4.9) — Ollama detection made lazy, see #17
7 	Inner sr/main.py argparse model default may still hardcode qwen3.7-plus
                                        Low 	                                        RESOLVED (v2.4.9) — verified: --model defaults to None, no hardcoded override found
8 	test_main_coverage.py references a nonexistent nested prompts/coding/*.txt layout (actual files are flat prompts/-prompt.md)
                                        Low 	                                        RESOLVED (v2.4.9) — corrected to flat prompts/<role>-prompt.md; side finding tracked as #29
9 	No SD/SE disambiguation. Extraction reads a reported SE as an SD, understating dispersion by up to ~sqrt(n) and inflating the effect size
                                        CRITICAL 	                                MITIGATED (v2.4.10) — deterministic tripwire added: flags sd_intervention/sd_control values pulled from a source line also containing "SE"/"SEM"/"standard error" (text-fallback path only; vision path relies on a prompt-level warning with no post-hoc check). Manual check via REVIEWER_GUIDE.md 3.1 is still required - this catches the documented failure pattern, not every possible SE/SD confusion
10 	No within- vs between-group detection. A within-subject pre/post contrast can be extracted as if it were intervention-vs-control, producing a large invalid effect with no warning
                                        CRITICAL 	                                MITIGATED (v2.4.10) — deterministic tripwire added: flags when intervention_group/control_group contains timepoint vocabulary (baseline/post-treatment/follow-up/etc.) or when both group labels are identical (runs on both extraction paths). Manual check via REVIEWER_GUIDE.md 2.2 is still required - this catches mislabeling visible in the group NAME itself, not a model that invents a plausible-but-wrong arm name
11 	Extraction is non-deterministic. The same PDF can yield different means/SDs/Ns on consecutive runs; observed in 2 of 5 test papers
                                        High 	                                        Open — run 3x and diff before trusting output
12 	Broken font CMaps misdetected as garbled text. Affected PDFs have a clean text layer recoverable with a fixed character-code offset, but the pipeline falls back to OCR, losing fidelity 	High 	Open — likely upstream cause of #11
13 	No effect-size plausibility bound. Implausible values (e.g. |g| > 1.5 from a psychotherapy trial) pass through unflagged 	Medium 	RESOLVED (v2.4.9) — flags |g/SMD|>1.5 or OR/RR beyond 10x/0.1x in results_csv + console; does not auto-exclude (tripwire only, not a fix for #9/#10)
14 	PICO file discovery differs between interfaces: the Streamlit UI globs output/rct_search/, the CLI globs input/sr/. A PICO saved in one is invisible to the other 	Low 	RESOLVED (v2.4.9) — description was inaccurate: CLI checked input/rct_search/ then output/rct_search/ (never input/sr/); UI checked output/rct_search/ only. UI now merges both
15 	RoB 2.0 assessment runs independently of study_overrides.yaml and may assess OCR text for a study whose outcome data was hand-entered 	Low 	Open — review RoB judgements separately
16 	Streamlit UI override fields place API keys in st.session_state, i.e. the server process. Safe locally; a shared deployment would hold user keys in a multi-user process 	Medium 	RESOLVED (v2.4.9, risk narrowed) — st.session_state is per-browser-session in Streamlit, not shared server-wide; no os.environ mutation or disk/echo leak found. Added a "Clear stored keys" button
17 	providers.py probes Ollama at module scope, so the auto-detect line fires on import for every run and every test regardless of --provider. A network call during import is also a latent hang 	Medium 	RESOLVED (v2.4.9) — resolution moved to lazy on-first-use; also resolves #6
18 	pipelines.sr.main (scipy, matplotlib, pymupdf; ~2.8s) is imported even for coding mode 	Low 	RESOLVED (v2.4.9) — removed 4 dead top-level imports that were never referenced
19 	macOS launchers are untested on macOS. They changed from Docker-based to venv-based in v2.4.8; the lsof port check and the Python 3.11/3.12 discovery loop need a real run 	Medium 	Open
20 	Old %TEMP%\ai_km_run_*.bat files from before v2.4.7 contain API keys in plaintext on any machine that ran the UI 	High 	Action required — delete and rotate keys
21 	call_ai_with_fallback sent prompts to cloud providers even when --provider ollama was requested, because the chain was built as [requested] + FALLBACK_PROVIDERS and a timeout counts as transient. Confidential input could reach a third party 	CRITICAL 	RESOLVED (v2.4.8) — LOCAL_ONLY_PROVIDERS never falls back
22 	23 Python source files began with a UTF-8 BOM. Python tolerates it on import but ast.parse() rejects it, and with an encoding mismatch it renders as garbage — previously misdiagnosed as corrupted comments 	Medium 	RESOLVED (v2.4.8) — stripped; scripts/check_no_bom.py guards
23 	A clean install on Python 3.14 fails across pywin32, textract, pillow, opencv-python and pymupdf. python.org now serves 3.14 by default 	High 	RESOLVED (v2.4.8) — main.py rejects unsupported versions with a 3.12 link and the Docker alternative
24 	OCR packages were installed but unusable: the image never provided Tesseract, Poppler or libGL, so ~2GB of PyTorch via easyocr bought nothing 	Medium 	RESOLVED (v2.4.8) — moved to requirements-ocr.txt
25 	_is_transient_error matches substrings, so an auth error mentioning "connection" is treated as retryable 	Low 	RESOLVED (v2.4.9) — checks HTTP status code explicitly (401/403 never transient); falls back only to the precise phrase "connection error"
26 	No regression test asserting that --provider ollama never reaches a cloud API 	Medium 	RESOLVED (v2.4.9) — added tests/test_provider_fallback.py, 4 tests, verified passing (405 total)
27 	Windows and macOS launchers used matching filenames but different mechanisms: the .bat files ran the virtualenv while the .sh files ran docker run 	Medium 	RESOLVED (v2.4.8) — both are now venv-based; Docker goes through docker compose
28 	Docker route has never been executed: not the build, not either compose service, not the .env-exclusion check. Docker is not installed on the dev machine 	High 	Open — gate before pointing colleagues at it
29 	test_main_sr_mode (test_main_coverage.py) exercises main.main(mode='sr', ...), a code path that cannot occur for real: ALL_MODES has no "sr" key (SR mode is dispatched straight to run_sr_launcher() at the entry point, never reaches choose_role()). Test only passes because choose_role is fully mocked 	Low 	Open — needs a decision: redesign to assert SR routes to run_sr_launcher, or remove
30 	Ctrl+C during the startup import chain (pandas/pytesseract, ~7s cold start) raised a raw traceback instead of the clean "Session stopped. Returning to menu..." message - the entry-point's try/except only wrapped code inside if __name__ == "__main__", not the imports above it 	Medium 	RESOLVED (v2.4.9) — imports wrapped in their own try/except KeyboardInterrupt
31 	Provider-select box in scripts/launcher.py misaligned on CJK-locale terminals: the Unicode checkmark is an ambiguous-width character and renders 2 columns instead of 1 there, throwing the right-hand border out of alignment 	Low 	RESOLVED (v2.4.9) — replaced with ASCII marker, fixed-width padding
32 	No visible wait notice before a slow provider call (Ollama model load, or any cloud provider taking 15s+); looked indistinguishable from a hang 	Low 	RESOLVED (v2.4.9) — call_ai() now prints a wait notice before dispatch
33 	relevance_screener.py and rob2_tool.py hardcoded a Windows-only absolute Tesseract path (C:\Program Files\Tesseract-OCR\tesseract.exe), breaking the OCR fallback entirely on macOS/Linux/Docker regardless of whether Tesseract was actually installed there 	Medium 	RESOLVED (v2.4.10) — now only overrides tesseract_cmd on Windows, and only if that default path exists; otherwise defers to pytesseract's normal PATH-based discovery
34 	RoB2Assessor defaulted to model="qwen3.7-plus", which matches nothing in providers.py's model registry. Currently unreachable via the documented pipeline (sr/main.py always passes model=args.model explicitly), but a landmine for direct construction (tests, scripts) that omit model 	Low 	RESOLVED (v2.4.10) — default corrected to qwen-plus-latest, matching providers.py's QWEN_MODEL; also found assess_by_pdf_path only ever calls _call_with_text (_call_with_images is defined but never invoked), confirming the text model, not the vision model, is the correct default
35 	_infer_group_timepoint_from_text hardcoded three literal arm names (CBT-IP, CBT-P, UMC) from one specific trial with no generic fallback - silently returned (None, None) for every other paper's table, giving the appearance of general group-inference machinery while only ever working for one study 	Medium 	RESOLVED (v2.4.10) — generalized to derive candidate arm names from each paper's own extraction output (intervention_group/control_group fields, or groups_n_by_timepoint-style rows) instead of hardcoded literals; verified the original trial still matches correctly and a completely different trial's names now match too
Contributing

    Fork the repository
    Create a feature branch: git checkout -b feature/your-feature
    Make your changes
    Run tests: python -m pytest -m "not live" --tb=short -q
    Commit and push
    Create a pull request

