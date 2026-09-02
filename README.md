# AI kcMedical Research

A multi-mode AI assistant for medical research, critical appraisal, systematic review, coding, and writing. Uses cloud providers by default (DeepSeek, Qwen, OpenAI, Anthropic, Groq) with optional local Ollama support.

    Version: 2.4.13
    Tests: 569 passed, 3 skipped, 11 deselected
           (reproduce with `python -m pytest -m "not live" --tb=short -q`)
    CI: GitHub Actions - Green
    GitHub: https://github.com/KW75/AI_kcMedicalResearch
    Live App: https://ai-kcmedicalresearch.onrender.com
    Health Check: https://ai-kcmedicalresearch.onrender.com/_stcore/health
    Uptime: UptimeRobot (5-min monitoring, prevents cold starts)

**CONFIDENTIALITY:** the hosted app and every cloud provider transmit your
input to an external API. For patient-identifiable or confidential data, run
locally with `--provider ollama` (see Providers).

## Quick Start

Hosted app, nothing to install: https://ai-kcmedicalresearch.onrender.com

Local with Docker (supplies its own Python):

    git clone https://github.com/KW75/AI_kcMedicalResearch.git
    cd AI_kcMedicalResearch
    copy .env.example .env          # then add your API keys
    cd docker
    docker compose run --rm cli     # interactive CLI
    docker compose up ui            # Streamlit UI on :8501

The Docker route has not been verified end to end (#28).

Full instructions, including the pinned local install (requirements-local.txt): `Readme/Setup_Instructions_for_Users.txt`


## Local Setup (Windows and macOS)

Setup has two steps: (1) install the app, then (2) choose how it thinks
(a cloud provider with an API key, or the free local Ollama).

### Step 1 - Install the app

Requires python.org Python 3.11 (NOT Anaconda/conda - its macOS build
targets an old OS and forces source builds that fail, see #19).

1. Install Python 3.11:
   https://www.python.org/downloads/release/python-3119/
   - Windows: run the installer and tick "Add python.exe to PATH".
   - macOS: choose "macOS 64-bit universal2 installer" (covers Intel and
     Apple Silicon).

2. Get the code, then run the launcher:

       git clone https://github.com/KW75/AI_kcMedicalResearch.git
       cd AI_kcMedicalResearch

   - Windows:  double-click  scripts\windows\AI_kcMedicalResearch_CLI.bat

   - macOS:    open Terminal, then run BOTH lines below. The first moves into
               the project folder; the second starts the app. You must run it
               from the project root, or the file will not be found.

                   cd ~/AI_kcMedicalResearch
                   bash scripts/macos/Mac_kcMedicalResearch_CLI.sh

   The launcher builds `.venv`, installs the pinned dependencies from
   `requirements-local.txt`, and opens the menu. First run takes a few
   minutes; the screen may look frozen while packages download - this is
   normal, do not close the window. If a compatible Python 3.11 is not
   found, the launcher shows a short message with the download link and
   stops (it never hangs).

Use the UI launchers (`..._UI.bat` / `Mac_..._UI.sh`) for the web interface.

### Step 2 - Choose an AI engine (pick ONE)

The app runs after Step 1 but needs a model to produce output.

Option A - Free / local (Ollama), no API key:
1. Install Ollama:  https://ollama.com/download
2. Pull the two models the app uses:
       ollama pull llama3.2          (the chat model - used by all modes)
       ollama pull nomic-embed-text  (the embedding model - needed for the
                                      appraisal and SR pipelines / RAG)
   (You may pull a larger chat model instead - the app auto-detects and uses
    the largest one you have; if none is set in .env, it falls back to
    llama3.2. The embedding model must be nomic-embed-text unless you change
    EMBEDDING_MODEL in .env.)
3. Ollama runs in the background after install; the app connects automatically.


Option B - Cloud provider (DeepSeek, Qwen, OpenAI, Anthropic, Groq):
1. Copy `.env.example` to `.env`.
2. Paste your provider's API key into `.env` (see Providers table).
   Nothing to download; requires a provider account.


## Modes

| Mode       | Flag                | Roles                                |
|------------|---------------------|--------------------------------------|
| Coding     | `--mode coding`     | Builder, Reviewer, Tester            |
| Writing    | `--mode writing`    | Writer, Editor, QA                   |
| RCT Search | `--mode rct_search` | Formulator, Searcher, Validator      |
| Search     | `--mode search`     | Researcher                           |
| Appraisal  | `--mode appraisal`  | Appraiser, Methodologist, Summariser |
| SR         | `--mode sr`         | SR Methodologist                     |

## Providers

| Provider           | Flag                   | Env variable         | Notes                                       |
|--------------------|------------------------|----------------------|---------------------------------------------|
| DeepSeek (default) | `--provider deepseek`  | `DEEPSEEK_API_KEY`   | Fast, cost-efficient                        |
| Qwen               | `--provider qwen`      | `DASHSCOPE_API_KEY`  | Recommended for SR (auto-uses vision model) |
| OpenAI             | `--provider openai`    | `OPENAI_API_KEY`     | GPT-4 vision                                |
| Anthropic          | `--provider anthropic` | `ANTHROPIC_API_KEY`  | Claude vision - partial tripwires, see REVIEWER_GUIDE.md §6.  |
| Groq               | `--provider groq`      | `GROQ_API_KEY`       | Fast inference                              |
| Ollama (local)     | `--provider ollama`    | `OLLAMA_HOST`        | Free, slow, offline; no SR (no vision)      |

On transient errors (timeout, 429, 502, 503) the system tries the next
provider. Default chain: DeepSeek -> Qwen -> Groq (`FALLBACK_PROVIDERS`).
Auth errors (401, 403) never fall back.

**Ollama never falls back to a cloud provider**, even on timeout. It is the
only provider that keeps input on your own machine.

Ollama in Docker: `localhost` is the container. The Docker launchers set
`OLLAMA_HOST=http://host.docker.internal:11434`; set it yourself if running
a container by hand.

Qwen and vision: `QWEN_MODEL` (default `qwen-plus-latest`) is text-only. SR
automatically uses `QWEN_VISION_MODEL` (default `qwen-vl-max`); no `--model`
flag needed.

## Streaming

All providers stream tokens by default in a TTY. `--no-stream` disables;
non-TTY environments use batch mode automatically.

## Environment Variables (.env)

Copy `.env.example` to `.env`. `.env` is gitignored.

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

If you used the Streamlit UI before v2.4.7, rotate your API keys and delete
any `%TEMP%\ai_km_run_*.bat` files - that version wrote keys to disk in
plaintext. Clearing `.env` does not revoke a key.

## Running Tests

    python -m pytest -m "not live" --tb=short -q          # standard suite
    python -m pytest -q                                   # all markers incl. live
    python -m pytest --cov=SOURCE_CODE --cov-report=html  # with coverage
    python -m pytest -m live -v                           # live provider smoke tests

`scripts/check_no_bom.py` runs in CI before pytest and fails on any UTF-8 BOM
in source files. `scripts/strip_bom.py` removes them.

## SR Pipeline

**READ `Readme/REVIEWER_GUIDE.md` BEFORE USING SR OUTPUT IN A REVIEW.**

Extraction is LLM-based and cannot verify its own semantics. It will emit a
confident, precise effect size whether or not it understood the paper.
Extraction is also non-deterministic: the same PDF can yield different
means/SDs/Ns across runs, and (measured Session 26) neither `seed` nor
`temperature=0` changes that on qwen-vl-plus. Every vision extraction is
therefore run 3 times and majority-voted; disagreement is written to
`nondet_flag` (see Tripwire columns). Every extracted mean, SD, and N must
still be checked against the source PDF before any pooled estimate is
reported - agreement is stability, not correctness.

### Running it

    Windows:        copy *.pdf input\sr\
    macOS/Linux:    cp *.pdf input/sr/

    python SOURCE_CODE/main.py --mode sr --provider qwen
    python SOURCE_CODE/main.py --mode sr --provider qwen --n-agreement 1   # single call, no vote

Run directly (not via the launcher menu) so the interactive PICO prompts get a
real TTY. Outputs:

    reports/sr/<run_id>/    # systematic_review.docx/.html, forest_plot.png, audit CSVs
    output/sr/figures/      # mirror of forest_plot.png
    output/sr/reports/      # mirror of report files

### Tripwire columns in `results_csv`

These flag studies for a closer look. They never correct or exclude.

- `plausibility_flag` - implausible effect-size magnitude (|g| > 1.5).
- `sd_se_warning` - text path only: an SD value drawn from a line that also
  mentions SE/SEM.
- `group_timepoint_warning` - a group label that looks like a timepoint, or
  identical intervention/control labels.
- `source_quote_warning` - the schema requires a VERBATIM per-arm source
  quote on both extraction paths. Flags: missing quote; value absent from
  its own quote; SE/SEM in an SD's quote; multiple-timepoint or
  within-subject phrasing; tabular rows with 3+ mean(SD) cells; (text path)
  quote not found verbatim in the source.
- `nondet_flag` / `nondet_runs` - vision path runs N=3 and votes mean/SD/N
  per arm and both group labels. `unanimous`; `field:majority` (2 of 3);
  `field:no_majority` (all differed, run-1 value kept); `table_shift` (runs
  read different table cells - a majority here is a coin flip);
  `single_run` (`--n-agreement 1`, nothing voted); `not_checked` (error or
  Anthropic path). Per-run values are in `extracted_data.csv`
  (`nondet_detail.*`). See `REVIEWER_GUIDE.md` §3.5.

The quotes land in `extracted_data.csv`
(`primary_outcome.source_quote_intervention` / `_control`) so every number
can be audited without reopening the PDF. `extracted_data.csv` also records
`outcome_selected` and `timepoint_selected`, surfaced in the Stage 4
`[OUTCOME/TIMEPOINT]` provenance block.

Stage 4 prints a summary block for each check unconditionally - a clean run
prints "0 flagged of N extracted" with coverage notes. An empty run prints
"0 flagged of 0 extracted" so a silent-empty run cannot look like a clean
run. The `[AGREEMENT]` block counts voted studies only: an `--n-agreement 1`
run prints "not checked", never "0 flagged". Every audit CSV row carries `run_id`. Stage 2 prints a
`[SCREENING]` accounting block; screening retries transient network errors,
because an error-based drop is not a valid PRISMA exclusion.

These are deterministic pattern checks, not semantic verification. Manual
verification against the PDF is required regardless of whether any flag
fired. The Anthropic path runs the source-quote check and group/timepoint
check but not the text-line SD/SE check - a permanent limitation, see
`REVIEWER_GUIDE.md` §6.

### CMap offset-decode

Several corpus PDFs have text layers whose ToUnicode CMap is shifted by a
constant offset (every "H" reads as "I"). Screening tries offsets +/-1, +/-2
scored by English stopword counts before falling back to OCR. Decoder
behaviour pinned by `tests/test_cmap_offset_decode.py` (16 cases: all four
offsets, space-to-`!` failure shape, false-positive guards).

## Study Metadata and Manual Overrides

Study metadata (first author, year, DOI) is resolved in three stages, each
overriding the last:

1. Metadata returned by the extraction model.
2. Metadata derived from the PDF (PyMuPDF metadata, DOI regex, copyright
   year). Best-effort; flagged as `metadata_source = "pdf_auto (verify)"`.
3. Reviewer overrides from `input/sr/study_overrides.yaml`.

Overrides are keyed by PDF filename. Metadata fields fill only when
extraction left them blank; numeric outcome fields REPLACE whatever
extraction produced.

    "some_paper.pdf":
      first_author: Nguyen
      year: 2021
      n_intervention: 42
      n_control: 40
      mean_intervention: 4.10
      sd_intervention: 1.85
      note: "Table 2, 12-week endpoint. Verified from PDF p.7, 2026-08-17."

Extraction still runs when an override exists, so the log shows
`field(7.32->7.35)` (corrected), `field(confirmed 7.35)` (agreed), or
`field(absent->7.35)`. The "confirmed" case is a real cross-check; do not
disable extraction for overridden studies.

Overrides affect extraction and meta-analysis only. Screening and RoB 2.0
re-read the PDF independently — this is intentional; RoB is a bias
assessment about the same reviewer's data and should not be influenced by
reviewer-entered values. See `Readme/REVIEWER_GUIDE.md` §5-6.

The end of Stage 3 prints a DATA PROVENANCE SUMMARY listing every study with
overridden values or auto-derived metadata. Both must be described in the
review's data-collection methods.

## Deployment (Render)

- Auto-deploy on push to `main`
- Build: `pip install --upgrade pip && pip install --no-cache-dir --only-binary=:all: -r requirements-render.txt && pip install --no-cache-dir --no-deps docx2txt==0.8`
- UptimeRobot pings every 5 min

## Known Issues

Issue numbers are stable so that HANDOFF.md and commit messages can cite
them; gaps are closed issues. Closed issues: `Readme/RESOLVED_ISSUES.md`.

| #  | Issue | Priority | What to do |
|----|-------|----------|------------|
| 28 | Docker route never executed end to end | Won't do (for now) | Deprioritised - colleagues use the python.org 3.11 + venv route (see README Step 1), not Docker. Revisit only if a Docker deployment is actually needed. |
| 19 | macOS install | RESOLVED | Fixed 2026-09-02. python.org 3.11.9 + requirements-local.txt (pyarrow 12.0.1, chromadb 0.5.23) verified end-to-end on Intel macOS 11. Launchers reject conda and guide to python.org. NOT yet run on Apple Silicon (reasoned from wheel tags). |
| 2  | WeasyPrint not installed; PDF report falls back to HTML | Medium | |
| 3  | Anthropic geo-restricted from dev machine | Low | VPN or skip. |


#9 (SD/SE confusion) and #10 (within- vs between-group) are mitigated by the
tripwires above but still require the manual checks in `REVIEWER_GUIDE.md`
sections 3.1 and 2.2.

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Run tests: `python -m pytest -m "not live" --tb=short -q`
5. Commit and push
6. Create a pull request
