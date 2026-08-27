# AI kcMedical Research

A multi-mode AI assistant for medical research, critical appraisal, systematic review, coding, and writing. Uses cloud providers by default (DeepSeek, Qwen, OpenAI, Anthropic, Groq) with optional local Ollama support.

    Version: 2.4.13
    Tests: 477 passed, 3 skipped, 11 deselected as of v2.4.13
           (reproduce with `python -m pytest -m "not live" --tb=short -q`)
    Coverage: ~53% (not re-measured this session)
    CI: GitHub Actions - Green
    GitHub: https://github.com/KW75/AI_kcMedicalResearch
    Live App: https://ai-kcmedicalresearch.onrender.com
    Health Check: https://ai-kcmedicalresearch.onrender.com/_stcore/health
    Uptime: UptimeRobot (5-min monitoring, prevents cold starts)

## Quick Start

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
Known Issue #28.

Full instructions, including the venv route: `Readme/Setup_Instructions_for_Users.txt`

## Local Development (Without Docker)

Requires Python 3.11 or 3.12. Newer versions are rejected at startup with a
download link - several pinned dependencies have no wheels for 3.13+.

Convenience launchers create `.venv`, install dependencies and start the app.
Windows and macOS behave identically; both use the virtualenv, not Docker
(macOS side is untested - see #19):

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

## Modes

| Mode      | Flag              | Roles                              |
|-----------|-------------------|------------------------------------|
| Coding    | `--mode coding`   | Builder, Reviewer, Tester          |
| Writing   | `--mode writing`  | Writer, Editor, QA                 |
| RCT Search| `--mode rct_search` | Formulator, Searcher, Validator  |
| Search    | `--mode search`   | Researcher                         |
| Appraisal | `--mode appraisal`| Appraiser, Methodologist, Summariser |
| SR        | `--mode sr`       | SR Methodologist                   |

## Providers

| Provider           | Flag                  | Environment Variable | Notes                                        |
|--------------------|-----------------------|----------------------|----------------------------------------------|
| DeepSeek (DEFAULT) | `--provider deepseek` | `DEEPSEEK_API_KEY`   | Fast, cost-efficient                         |
| Qwen               | `--provider qwen`     | `DASHSCOPE_API_KEY`  | Recommended for SR (auto-uses vision model)  |
| OpenAI             | `--provider openai`   | `OPENAI_API_KEY`     | GPT-4 vision                                 |
| Anthropic          | `--provider anthropic`| `ANTHROPIC_API_KEY`  | Claude vision - but see #50                  |
| Groq               | `--provider groq`     | `GROQ_API_KEY`       | Fast inference                               |
| Ollama (local)     | `--provider ollama`   | `OLLAMA_HOST`        | Free but slow; offline/testing only          |

On transient errors (timeout, 429, 502, 503), the system automatically tries
the next provider. Default chain: DeepSeek -> Qwen -> Groq. Configure via
`FALLBACK_PROVIDERS`. Authentication errors (401, 403) raise immediately and
never fall back.

**CONFIDENTIALITY:** Ollama is the only provider that keeps your input on your
own machine. Every other provider transmits the prompt to an external API. If
your input contains patient-identifiable or otherwise confidential data, use
`--provider ollama`.

Requests to Ollama NEVER fall back to a cloud provider, even on a timeout.
Before v2.4.8 they did: an explicit `--provider ollama` produced the chain
`[ollama, deepseek, qwen, groq]`, so an Ollama timeout silently sent the
prompt to DeepSeek and printed a success line (see #21). Ollama cannot run
SR mode (no vision).

Note on Ollama in Docker: inside a container, `localhost` is the container,
not your machine. The Docker launchers set
`OLLAMA_HOST=http://host.docker.internal:11434` for you; if you run a
container by hand, set it yourself or Ollama will be unreachable.

Note on Qwen and vision: the Qwen text model (`QWEN_MODEL`, default
`qwen-plus-latest`) is text-only. The SR pipeline requires image
understanding, so it now automatically uses a separate vision model
(`QWEN_VISION_MODEL`, default `qwen-vl-max`) - you do not need to pass a
`--model` flag for SR.

## Streaming

All providers support live token streaming, enabled by default in CLI
terminals. Use `--no-stream` to disable. Non-TTY environments (pipes, CI)
automatically use batch mode.

## Environment Variables (.env)

Copy `.env.example` to `.env` and fill in the keys you need. `.env` is
gitignored.

**SECURITY:** before v2.4.7 the Streamlit UI printed every API key into the
launched terminal window. If you used the UI before v2.4.7, rotate your keys
at the provider consoles and delete any leftover `%TEMP%\ai_km_run_*.bat`
files. Clearing `.env` does not revoke a key. (On this repo's dev machine,
rotation was completed in Session 15 - see #20.)

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

## Startup Time

As of v2.4.9, the module-scope Ollama probe (#17) and the unconditional
`pipelines.sr.main` import (#18) described in earlier versions of this
section are both fixed: Ollama's model auto-detect now runs lazily on first
actual use instead of on every import, and coding/writing/search/appraisal
modes no longer pull in `pipelines.sr.main`'s scipy/matplotlib/pymupdf chain
at all.

As of v2.4.12, `SOURCE_CODE/pipelines/sr/__init__.py` also re-exports
`run_sr` lazily (PEP 562, #48), so importing the sr package no longer pulls
the ~2.8s scipy/matplotlib/pymupdf chain - and the `RuntimeWarning` that
runpy printed at the top of every SR run ("found in sys.modules after
import of package") is gone: the eager import created a second live
instance of `sr.main` before runpy executed it as `__main__`.

Startup time was previously ~7 seconds cold; the actual new number has not
been re-measured after this change. On Windows, first-run antivirus scanning
of native extension modules adds noticeably more than subsequent runs
regardless.

## Running Tests

    python -m pytest -m "not live" --tb=short -q          # standard suite
    python -m pytest -q                                   # all markers incl. live
    python -m pytest --cov=SOURCE_CODE --cov-report=html  # with coverage
    python -m pytest -m live -v                           # live provider smoke tests

Current status: 477 passed, 3 skipped, 11 deselected as of v2.4.13
(471 at Session 18 start; Session 18 added six regression tests for the
BOM guard - see #49).

`scripts/check_no_bom.py` scans the whole repo (excluding `.git`, `.venv`,
`output/`, `reports/`, caches, and build artifacts) and runs in CI before
pytest. Regression-tested by `tests/test_check_no_bom.py`.

    python scripts/check_no_bom.py                        # fail on UTF-8 BOMs in source
    python scripts/strip_bom.py                           # remove them

## SR Pipeline

**READ `Readme/REVIEWER_GUIDE.md` BEFORE USING SR OUTPUT IN A REVIEW.**

Extraction is LLM-based and cannot verify its own semantics. It will emit a
confident, precise effect size whether or not it understood the source paper.
Every extracted mean, SD, and N must be checked against the source PDF before
any pooled estimate is reported. See #9 and #10 for documented failure modes.

### Tripwire columns in `results_csv`

As of v2.4.12, `results_csv` carries FOUR tripwire columns that flag (never
silently correct or exclude) studies worth a closer look:

- `plausibility_flag` (#13) - implausible effect-size magnitude.
- `sd_se_warning` (#9, text-fallback path) - a value extracted into an SD
  field from a source line also mentioning "SE"/"SEM"/standard error.
- `group_timepoint_warning` (#10) - a group label that looks like a
  timepoint, or identical intervention/control labels.
- `source_quote_warning` (#38, v2.4.12; extended v2.4.13 for tabular
  multi-timepoint rows, #52) - the extraction schema now requires a
  VERBATIM per-arm source quote on BOTH extraction paths. Flags values with
  no quote, values absent from their own quote, SE/SEM labels in an SD's
  quote (extends #9 to the vision path), multiple-timepoint or
  within-subject phrasing, tabular rows with three or more mean(SD) cells
  regardless of timepoint vocabulary, and (text path) quotes not found
  verbatim in the source.

### New in v2.4.13: outcome/timepoint provenance

`extracted_data.csv` now records `outcome_selected` and `timepoint_selected`
(#51) - which outcome and which timepoint the model chose. Ang's bimodal
outcome flip (pain-change g=-0.248 vs NFR g=+0.075, see #11) and Lami's
timepoint-picking were previously invisible in audit output. The fields are
recorded but not yet surfaced in the Stage 4 provenance summary
(carried forward).

### Console summary

The verbatim quotes land in `extracted_data.csv`
(`primary_outcome.source_quote_intervention` / `_control`) so every number
can be audited without reopening the PDF.

The console prints a summary block for each check at the end of Stage 4,
UNCONDITIONALLY as of v2.4.12: a clean run prints "0 of N flagged" with
coverage notes (e.g. how many studies the SD/SE text check could apply to),
so silence can no longer be mistaken for verification.

Every audit CSV row also carries a `run_id` column (v2.4.12, #45) -
extraction is non-deterministic (#11), so a CSV without a run identifier is
silently conflatable across runs.

Stage 2 prints a `[SCREENING]` accounting block
(INCLUDE/EXCLUDE/UNCERTAIN/ERROR counts); screening calls retry transient
network errors (v2.4.12, #46) because a single dropped connection previously
excluded a paper from the entire review with no visible trace, and an
error-based drop is not a valid PRISMA exclusion.

### What these checks are not

These are deterministic pattern checks, not semantic verification - they
catch the documented failure patterns, not every possible extraction error.
Manual verification against the source PDF is still required regardless of
whether any flag fired.

The Anthropic provider path runs the source-quote tripwire as of v2.4.13
(#61) but still bypasses SD/SE and group/timepoint checks (#50).

### CMap offset-decode (v2.4.13, #12)

Several corpus PDFs have text layers where the ToUnicode CMap is shifted by
a constant offset (every "H" reads as "I", etc.). As of v2.4.13, the
screening path attempts offsets (+1, -1, +2, -2) scored by English stopword
counts BEFORE falling back to OCR; a hit above baseline + 15 stopword
occurrences replaces the garbled text and skips OCR. Real-run confirmation
on a known-shifted PDF is still pending.

### NOTE (history)

From v2.4.10 through the first real-corpus test, the first three tripwire
columns were silently absent from `results_csv` despite existing in the code
(#36, hardcoded fieldnames; fixed v2.4.11 - the same pattern recurred in
`write_screens`, whose `pico_*` columns had been empty in every
`screening_log.csv` ever written, fixed v2.4.12, #44). v2.4.11's testing
found #9/#10 had never been exercised against `zsy234.pdf`, the paper they
were built for. v2.4.12's source-quote check closed that: in real run
`20260826_113816`, zsy234's own quotes fired the SE-as-SD and
multiple-timepoint flags on the vision path (4 flags + #13's plausibility
bound), and a second study was flagged because its extracted values did not
appear in its own quotes.

### Running the pipeline

Place your PDFs in the SR input folder:

    Windows:        copy *.pdf input\sr\
    macOS/Linux:    cp *.pdf input/sr/

Run the pipeline directly (not via the launcher menu) so the interactive
PICO prompts receive a real TTY:

    python SOURCE_CODE/main.py --mode sr --provider qwen  # auto-uses qwen-vl-max (vision)

Outputs are written to a timestamped run folder and mirrored to the output
tree:

    reports/sr/<run_id>/    # systematic_review.docx/.html, forest_plot.png, audit CSVs
    output/sr/figures/      # mirror of forest_plot.png
    output/sr/reports/      # mirror of report files

To override the SR extraction model, set `QWEN_VISION_MODEL` in `.env`
(default `qwen-vl-max`). Text-mode Qwen continues to use `QWEN_MODEL`
(`qwen-plus-latest`).

## Study Metadata and Manual Overrides (v2.4.6)

Study metadata (first author, year, DOI) is resolved in three stages, each
overriding the last:

1. Metadata returned by the extraction model.
2. Metadata derived from the PDF itself (PyMuPDF metadata, DOI regex,
   copyright-line year). Best-effort only; flagged in the output as
   `metadata_source = "pdf_auto (verify)"`.
3. Reviewer overrides from `input/sr/study_overrides.yaml`.

Overrides are keyed by PDF filename. Metadata fields fill only when
extraction left them blank; numeric outcome fields REPLACE whatever
extraction produced, because the reason to record them is that extraction
got them wrong.

    "some_paper.pdf":
      first_author: Nguyen
      year: 2021
      n_intervention: 42
      n_control: 40
      mean_intervention: 4.10
      sd_intervention: 1.85
      note: "Table 2, 12-week endpoint. Verified from PDF p.7, 2026-08-17."

Extraction still runs in full when an override exists, so the log
distinguishes:

    field(7.32->7.35)      extraction was wrong, override corrected it
    field(confirmed 7.35)  extraction independently agreed with the reviewer
    field(absent->7.35)    extraction produced nothing for this field

The "confirmed" case is a genuine cross-check. Do not disable extraction for
overridden studies or you lose it.

Overrides affect extraction and meta-analysis only. Screening (Stage 2) and
RoB 2.0 (Stage 3.5) re-read the PDF independently and are unaffected.

At the end of Stage 3 the log prints a DATA PROVENANCE SUMMARY listing every
study whose values were manually overridden or whose metadata was
auto-derived. Both must be described in the review's data-collection
methods.

## Deployment (Render)

- **URL:** https://ai-kcmedicalresearch.onrender.com
- **Health:** https://ai-kcmedicalresearch.onrender.com/_stcore/health
- **Auto-deploy:** push to `main` triggers deploy
- **Build:** `pip install --upgrade pip && pip install --no-cache-dir --only-binary=:all: -r requirements-render.txt && pip install --no-cache-dir --no-deps docx2txt==0.8`
- **Monitoring:** UptimeRobot pings every 5 min (prevents free-tier cold starts)

## Known Issues

Issues are numbered in the order they were discovered; the number is stable
across sessions so that HANDOFF.md and commit messages can cite them. The
list below is grouped by current status for readability.

### Open

| #  | Issue                                                                                          | Priority |
|----|------------------------------------------------------------------------------------------------|----------|
| 11 | Extraction is non-deterministic. Same PDF yields different means/SDs/Ns across runs. Characterized in v2.4.12: Ang is BIMODAL between two exact value sets (g=+0.075 vs -0.248; pooled -0.514 vs -0.576); Jensen bimodal, once returned ROUNDED values its own source quotes did not contain (caught by #38); Lami's Ns chaotic (override catches every variant); McCrae/Karlsson stable. v2.4.12 quotes identify WHICH table each run drew from - use for #23-style fixtures. **Mitigation:** run 3x and diff. | High |
| 12 | Broken font CMaps misdetected as garbled text. Confirmed on ALL FIVE corpus papers at every stage. | High - MITIGATED (v2.4.13) |
| 15 | RoB 2.0 assessment runs independently of `study_overrides.yaml` and may assess OCR text for a study whose outcome data was hand-entered. | Low |
| 19 | macOS launchers are untested on macOS. Changed from Docker-based to venv-based in v2.4.8; the `lsof` port check and Python 3.11/3.12 discovery loop need a real run. | Medium |
| 28 | Docker route has never been executed: not the build, not either compose service, not the `.env`-exclusion check. Docker is not installed on the dev machine. | High |
| 50 | Anthropic provider path (`_extract_anthropic`, `assess_by_file_id`) runs most tripwires only partially. Source-quote check added v2.4.13 (#61); SD/SE and group/timepoint flags still absent. Plausibility inputs are computed at Stage 4 regardless. | Medium |

### Mitigated (deterministic tripwire; manual verification still required)

| #  | Issue                                                                                          | Status |
|----|------------------------------------------------------------------------------------------------|--------|
| 9  | No SD/SE disambiguation. Extraction reads a reported SE as an SD, understating dispersion and inflating the effect size. | MITIGATED (v2.4.10, extended v2.4.12): SD/SE flag on text path; source-quote check catches SE labels in an SD's verbatim quote on both paths. Real-run: fired on zsy234.pdf's own quotes in run 20260826_113816. Manual check via `REVIEWER_GUIDE.md` 3.1 still required. |
| 10 | No within- vs between-group detection. A within-subject pre/post contrast can be extracted as if it were intervention-vs-control. | MITIGATED (v2.4.10, extended v2.4.12/2.4.13): group/timepoint flag; source-quote multiple-timepoint detection now catches tabular rows with three or more mean(SD) cells even without timepoint keywords (#52). Manual check via `REVIEWER_GUIDE.md` 2.2 still required. |

### Resolved

| #  | Issue                                                                                          | Resolved |
|----|------------------------------------------------------------------------------------------------|----------|
| 1  | Lami extraction fails - paper s10608 (Table 4, pages 12-13)                                    | v2.4.6 - text fallback + `study_overrides.yaml`; underlying instability tracked as #11 |
| 4  | Hard-coded `qwen3.7-plus` in `_DEFAULT_MODELS` overrode `QWEN_MODEL`                           | v2.4.5 |
| 5  | SR vision regression: launcher defaulted qwen to text-only `qwen-plus-latest`                  | v2.4.5 - now uses `QWEN_VISION_MODEL` |
| 6  | Cosmetic `[ollama] Auto-detected` line on Qwen SR runs                                         | v2.4.9 - see #17 |
| 7  | Inner `sr/main.py` argparse `--model` default may still hardcode `qwen3.7-plus`                | v2.4.9 - verified: defaults to None |
| 8  | `test_main_coverage.py` referenced a nonexistent nested `prompts/coding/*.txt` layout           | v2.4.9 - corrected to flat `prompts/<role>-prompt.md`; side finding tracked as #29 |
| 13 | No effect-size plausibility bound. Implausible `|g| > 1.5` values passed through unflagged     | v2.4.9 - tripwire only, does not auto-exclude |
| 14 | PICO file discovery differs between UI and CLI                                                 | v2.4.9 - CLI checked `input/rct_search/` then `output/rct_search/`; UI checked `output/rct_search/` only. UI now merges both. |
| 16 | Streamlit UI stored API keys in `st.session_state`                                             | v2.4.9 - risk narrowed: per-browser-session, no `os.environ` mutation or disk/echo leak. Added "Clear stored keys" button. |
| 17 | `providers.py` probed Ollama at module scope on every import                                   | v2.4.9 - lazy on first use; also resolves #6 |
| 18 | `pipelines.sr.main` (scipy, matplotlib, pymupdf) imported even for coding mode                 | v2.4.9 - removed 4 dead top-level imports |
| 20 | Pre-v2.4.7 `%TEMP%\ai_km_run_*.bat` files contained API keys in plaintext                      | Session 15 - all three keys rotated. Housekeeping: `Remove-Item "$env:TEMP\ai_km_run_*.bat"` |
| 21 | `call_ai_with_fallback` sent prompts to cloud providers even when `--provider ollama` requested | v2.4.8 - `LOCAL_ONLY_PROVIDERS` never falls back |
| 22 | 23 Python source files began with a UTF-8 BOM                                                  | v2.4.8 - stripped; `scripts/check_no_bom.py` guards |
| 23 | Clean install on Python 3.14 failed across pywin32, textract, pillow, opencv-python, pymupdf   | v2.4.8 - `main.py` rejects unsupported versions with a 3.12 link |
| 24 | OCR packages installed but unusable: no Tesseract/Poppler/libGL in the image                   | v2.4.8 - moved to `requirements-ocr.txt` |
| 25 | `_is_transient_error` matched substrings; an auth error mentioning "connection" was retried    | v2.4.9 - checks HTTP status code (401/403 never transient); falls back only on the phrase "connection error" |
| 26 | No regression test asserting `--provider ollama` never reaches a cloud API                     | v2.4.9 - `tests/test_provider_fallback.py`, 4 tests |
| 27 | Windows and macOS launchers used matching filenames but different mechanisms (`.bat` = venv, `.sh` = `docker run`) | v2.4.8 - both venv-based; Docker goes through `docker compose` |
| 29 | `test_main_sr_mode` exercised `main.main(mode='sr', ...)`, a code path that cannot occur       | v2.4.12 - dispatch chain extracted from `__main__` into `run_cli(args)`; impossible-path test replaced by `TestCliRouting`; undispatched mode now raises `ValueError` |
| 30 | Ctrl+C during startup import chain raised a raw traceback                                      | v2.4.9 - imports wrapped in their own try/except KeyboardInterrupt |
| 31 | Provider-select box misaligned on CJK-locale terminals                                         | v2.4.9 - ASCII marker, fixed-width padding |
| 32 | No visible wait notice before a slow provider call                                             | v2.4.9 - `call_ai()` prints a wait notice before dispatch |
| 33 | `relevance_screener.py` and `rob2_tool.py` hardcoded a Windows-only absolute Tesseract path    | v2.4.10 - only overrides `tesseract_cmd` on Windows, and only if that default path exists |
| 34 | `RoB2Assessor` defaulted to `model="qwen3.7-plus"`, matching nothing in the registry           | v2.4.10 - corrected to `qwen-plus-latest`; verified `assess_by_pdf_path` only calls `_call_with_text` |
| 35 | `_infer_group_timepoint_from_text` hardcoded three literal arm names (CBT-IP, CBT-P, UMC)      | v2.4.10 - generalized to derive candidate arm names from each paper's own extraction output |
| 36 | `audit_logger.py`'s `write_results()` used a hardcoded `fieldnames` list with `extrasaction="ignore"`, silently dropping tripwire columns | v2.4.11 - added the three field names; verified against real pipeline output |
| 37 | Real `.env` `DASHSCOPE_BASE_URL` pointed at a decommissioned private workspace endpoint         | v2.4.11 - user corrected local `.env`; noted here since mistaken for a regression |
| 38 | The v2.4.11 group-label follow-up validated arm NAMES, not whether extracted numbers belonged to a between-group comparison of those arms | v2.4.12 - verbatim per-arm source quotes on both paths; `_flag_suspect_source_quotes` checks presence, SE labels, timepoint phrasing, verbatim presence. Real-run: zsy234.pdf flagged 4x on vision path in run 20260826_113816. |
| 39 | No regression test for the v2.4.11 group-label follow-up mechanism                             | v2.4.12 - `tests/test_data_extractor_source_quotes.py` covers `_needs_group_labels`; Priority 1 harness scenarios ported in commit 26ebd7d |
| 40 | Screening OCR capped each page at `t[:800]` over 8 pages, saturating at 6414 chars             | v2.4.12 - one shared 6000-char budget filled front-to-back with early stop; ~15-19s -> ~3s per paper |
| 41 | RoB2 OCR capped chunks at `t[:1500]` over up to 12 pages                                       | v2.4.12 - same budget/early-stop; Stage 3.5 ~2m50s -> ~60-80s. Garble detection now inspects only the budget window - see commit note |
| 42 | `run_sr_launcher` printed all four artifact paths unconditionally                              | v2.4.12 - each line prints only if the file exists AND was modified at/after this run's start |
| 43 | `scripts/launcher.py` banner hardcoded "Version 2.4.3 / Tests 400 passed - 3 skipped"          | v2.4.12 - banner parses `VERSION` and `MIN/MAX_PYTHON` live via regex; unverifiable test count removed; BOM stripped |
| 44 | `write_screens` used fixed fieldnames expecting flat `pico_*` keys never written; PICO columns EMPTY in every `screening_log.csv` ever produced | v2.4.12 - flattens on a copy; SCHEMA CHANGE |
| 45 | Audit CSVs carried no run identifier; combined with #11 made cross-run conflation inevitable   | v2.4.12 - `sr/main.py` stamps `run_id` into every row of all four audit CSVs |
| 46 | A transient network error during screening silently removed a paper from the ENTIRE review    | v2.4.12 - screening retries transient failures (3 attempts, backoff); `[SCREENING]` accounting block; PRISMA-invalid drops flagged under the pooled estimate |
| 47 | Group-label follow-up returned the QUOTED STRING `'null'`; stored as a real label              | v2.4.12 - `_clean_group_label()` treats null/none/n-a/not reported/unknown/etc. as declines; prompt demands unquoted JSON null explicitly |
| 48 | `python -m SOURCE_CODE.pipelines.sr.main` printed a runpy RuntimeWarning on every run          | v2.4.12 - lazy PEP 562 `__getattr__` re-export; warning verified absent |
| 49 | `check_no_bom.py` scanned only `SOURCE_CODE/`, missing BOMs in `tests/` and `scripts/`         | Session 16 (`32e0098`) widened scan root to repo root with IGNORE_DIRS; Session 16 (`0ede7bd`) wired into CI before pytest. Session 18 (`4b03fed`) added `tests/test_check_no_bom.py` (6 regression tests covering BOM detection at repo root and in tests/scripts subdirs, IGNORE_DIRS respect, suffix contract, clean-tree exit 0, offender exit 1). |
| 51 | `outcome_selected` / `timepoint_selected` not recorded, so Ang's bimodal flip (#11) and Lami's timepoint-picking were invisible in audit output | v2.4.13 - fields added to `EXTRACTION_PROMPT_TEMPLATE`, both flat-key lists (`extract_by_pdf_path` and `_extract_anthropic`), and `_text_extraction_prompt`. Not yet surfaced in Stage 4 provenance summary. |
| 52 | Tabular multi-timepoint quote rows (e.g. Lami "CBT-P 7.58 (1.75) 7.35 (2.08) 7.21 (1.79)") contain three mean(SD) cells but no timepoint keywords, so #38's check went silent on them | v2.4.13 - `_flag_suspect_source_quotes` now flags three or more mean(SD) cells in one quote via regex regardless of timepoint vocabulary; regression test `test_tabular_multi_timepoint_row_is_flagged` covers Lami's exact pattern. |

### Interim (partial resolution)

| #  | Issue                                                                                          | Status |
|----|------------------------------------------------------------------------------------------------|--------|
| 61 | Anthropic path bypassed source-quote / SD-SE / group-timepoint verification (interim warning added Session 16) | PARTIAL (v2.4.13, source-quote scope) - `_extract_anthropic` now coerces, restructures nested `primary_outcome`/`participants`, and invokes `_flag_suspect_source_quotes`. Startup warning can be removed once SD/SE + group/timepoint are also ported (see #50). |

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Run tests: `python -m pytest -m "not live" --tb=short -q`
5. Commit and push
6. Create a pull request
