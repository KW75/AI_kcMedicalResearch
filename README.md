# AI kcMedical Research

A multi-mode AI assistant for medical research, critical appraisal, systematic review, coding, and writing. Uses cloud providers by default (DeepSeek, Qwen, OpenAI, Anthropic, Groq) with optional local Ollama support.

    Version: 2.4.13
    Tests: 501 passed, 3 skipped, 11 deselected
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

Full instructions, including the venv route: `Readme/Setup_Instructions_for_Users.txt`

## Local Development (Without Docker)

Requires Python 3.11 or 3.12. Newer versions are rejected at startup
(several pinned dependencies have no wheels for 3.13+).

Launchers create `.venv`, install dependencies, and start the app
(macOS side untested, #19):

    scripts\windows\AI_kcMedicalResearch_CLI.bat   /  scripts/macos/Mac_kcMedicalResearch_CLI.sh
    scripts\windows\AI_kcMedicalResearch_UI.bat    /  scripts/macos/Mac_kcMedicalResearch_UI.sh

Run all commands from the project root:

    python SOURCE_CODE/main.py                            # coding mode (default)
    python SOURCE_CODE/main.py --mode writing
    python SOURCE_CODE/main.py --mode rct_search
    python SOURCE_CODE/main.py --mode search              # PubMed search
    python SOURCE_CODE/main.py --mode appraisal
    python SOURCE_CODE/main.py --mode sr --provider qwen  # systematic review (needs vision)
    python SOURCE_CODE/main.py --no-stream
    python SOURCE_CODE/main.py --resume                   # resume from checkpoint
    python SOURCE_CODE/main.py --dry-run                  # no API calls
    python scripts/launcher.py                            # menu-driven launcher

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
| Anthropic          | `--provider anthropic` | `ANTHROPIC_API_KEY`  | Claude vision - partial tripwires, see #50  |
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
Extraction is also non-deterministic (#11): the same PDF can yield different
means/SDs/Ns across runs. Every extracted mean, SD, and N must be checked
against the source PDF before any pooled estimate is reported. Run at least
3x and diff.

### Running it

    Windows:        copy *.pdf input\sr\
    macOS/Linux:    cp *.pdf input/sr/

    python SOURCE_CODE/main.py --mode sr --provider qwen

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

The quotes land in `extracted_data.csv`
(`primary_outcome.source_quote_intervention` / `_control`) so every number
can be audited without reopening the PDF. `extracted_data.csv` also records
`outcome_selected` and `timepoint_selected`, surfaced in the Stage 4
`[OUTCOME/TIMEPOINT]` provenance block.

Stage 4 prints a summary block for each check unconditionally - a clean run
prints "0 of N flagged" with coverage notes. Every audit CSV row carries
`run_id`. Stage 2 prints a `[SCREENING]` accounting block; screening retries
transient network errors, because an error-based drop is not a valid PRISMA
exclusion.

These are deterministic pattern checks, not semantic verification. Manual
verification against the PDF is required regardless of whether any flag
fired. The Anthropic path runs the source-quote check but not SD/SE or
group/timepoint (#50).

### CMap offset-decode

Several corpus PDFs have text layers whose ToUnicode CMap is shifted by a
constant offset (every "H" reads as "I"). Screening tries offsets +/-1, +/-2
scored by English stopword counts before falling back to OCR. Real-run
confirmation pending (#12).

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
re-read the PDF independently (#15).

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

| #  | Issue | Priority |
|----|-------|----------|
| 11 | Extraction is non-deterministic. Ang is bimodal between two value sets; Jensen's means vary in the first decimal; Lami's Ns are chaotic (override catches every variant); McCrae/Karlsson stable. Ang pinned by regression fixtures; Jensen and Lami fixtures pending. **Mitigation:** run 3x and diff, use source quotes. | High |
| 12 | CMap offset-decode fallback landed v2.4.13; not yet confirmed on a real shifted PDF. | High |
| 28 | Docker route never executed end to end (no Docker on dev machine). | High |
| 19 | macOS launchers untested on macOS. | Medium |
| 2  | WeasyPrint not installed; PDF report falls back to HTML. | Medium |
| 3  | Anthropic API geo-restricted from the dev machine. | Low |

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