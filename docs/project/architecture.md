# Architecture

## Overview
AI_kcMedicalResearch is a local-first Python command-line application (no web
UI since Session 33) built around specialised AI pipelines for medical
research and clinical decision support. The launcher (scripts/launcher.py)
starts SOURCE_CODE/main.py with --mode, --provider and --model. Ollama (local)
is the default provider and never falls back to cloud. A cloud provider runs
only after the cloud gate: the job lists every destination and needs a typed
"y" or --confirm-cloud.

## Project Structure

    AI_kcMedicalResearch/
    +-- SOURCE_CODE/
    |   +-- main.py            <- CLI (parse_args, run_cli), mode dispatch, cloud gate
    |   +-- providers.py       <- call_<provider>_provider, fallback order, LOCAL_ONLY_PROVIDERS
    |   +-- streaming.py       <- streamed replies
    |   +-- ollama_models.py   <- local model list, capabilities, shared vision picker (stdlib only)
    |   +-- cloud_models.py    <- Setup -> 4 Cloud AI models (stdlib only)
    |   +-- time_limits.py     <- --time-limit 15/30/60/none (stdlib only)
    |   +-- pipelines/
    |   |   +-- coding/        <- Builder -> Reviewer -> Tester loop
    |   |   +-- writing/       <- one pass: write + edit + review (Topic/Article/Report/Synopsis)
    |   |   +-- appraisal/     <- critical appraisal of papers
    |   |   +-- search/        <- literature search (PubMed, Europe PMC)
    |   |   +-- rct_search/    <- Formulator -> Searcher -> Validator
    |   |   +-- sr/            <- systematic review (self-contained)
    |   |   +-- ocr/           <- reader.py, engine.py, cli.py
    |   |   +-- samd/          <- SaMD clinical decision support (built Sessions 49-52; frozen)
    |   |   +-- data_analysis/ <- statistics computed in Python, no AI (Session 53)
    |   |   +-- shared/        <- cross-pipeline helpers (document reader)
    |   +-- utils/
    +-- scripts/
    |   +-- launcher.py        <- interactive menu
    |   +-- windows/           <- Windows launcher and setup
    |   +-- macos/             <- macOS launcher and setup
    +-- prompts/               <- role prompts (prompts/samd/ planned)
    +-- docs/                  <- mode guidelines injected into prompts
    |   +-- project/           <- architecture.md, decision-log.md, PRD.md
    |   +-- sr/                <- REVIEWER_GUIDE.md (what reviewers check by hand)
    +-- reference/             <- reference material developers use for standardisation
    |   +-- sr_cbt_fibromyalgia/  <- SR reference set and reviewer-checked values
    +-- assets/                <- icon files (.ico, .png) for desktop shortcuts:
    |                             app, input, output, reports
    +-- Readme/                <- HANDOFF.md, flashcard-help.html (launcher H),
    |                             readme_sr_pipeline.txt
    +-- input/<mode>/          <- user files (gitignored, except
    |                             input/sr/study_overrides.yaml)
    +-- output/<mode>/         <- final results (gitignored)
    +-- reports/<mode>/        <- run logs and intermediate steps (gitignored)
    +-- tests/                 <- pytest suite (count: README line 7)
    +-- .env                   <- keys and model settings (never committed)
    +-- .env.example           <- template for .env
    +-- requirements*.txt
    +-- README.md

## Core Components

### SOURCE_CODE/main.py
- CLI argument parsing (parse_args) and run_cli
- Mode dispatch on --mode: coding, writing, appraisal, search, rct_search,
  sr, ocr, samd, data_analysis
- Cloud gate: data_destinations() and confirm_data_destinations(). SR, OCR
  and SaMD call one provider directly (no fallback chain), so they list only
  the chosen provider. data_analysis calls no AI model, so it lists none
- Environment loading (.env via python-dotenv)

### Provider System (SOURCE_CODE/providers.py)
- One function per provider: call_ollama_provider, call_qwen_provider,
  call_deepseek_provider, call_openai_provider, call_anthropic_provider,
  call_groq_provider
- Ollama, OpenAI and Qwen calls accept page images (PNG) for vision work
- Ollama is in LOCAL_ONLY_PROVIDERS: it never falls back to cloud
- Ollama options (context, temperature, num_predict) are read from .env at
  call time; every Ollama request sends think: false

### Local models (SOURCE_CODE/ollama_models.py)
- Lists pulled models (/api/tags) and their capabilities (/api/show)
- Default text model: OLLAMA_MODEL in .env, else gemma4:e4b
- Shared vision picker for SR, OCR and SaMD; SR prefers
  qwen3-vl:30b-a3b-instruct when pulled

### Pipeline Pattern
Most pipelines follow the same pattern:
1. Load guidelines from docs/<mode>/
2. Load input files from input/<mode>/
3. Build the system prompt (guidelines as context) and the user prompt
4. Call the provider
5. Parse the reply, iterate if the mode does so
6. Write results to output/<mode>/ and, where the mode keeps them, logs and
   intermediate steps to reports/<mode>/

### Guidelines Injection
Each pipeline reads the .md files in its docs/<mode>/ folder, joins them
with section headers and puts them into the system prompt. Updating a .md
file in docs/ changes the AI's behaviour without a code change.

### scripts/launcher.py
Interactive menu: 1 Coding, 2 Writing, 3 Appraisal, 4 Search, 5 RCT Search,
6 SR Pipeline, 7 Data Analysis (Session 53), 8 OCR, 9 SaMD (Session 49;
was Dry Run - --dry-run stays a main.py flag, reachable through C Custom
flags), 10 Setup; C Custom flags, H Help, X Exit. It asks for the provider,
model and time limit (7 Data Analysis asks none: it uses no AI), then runs
main.py as a subprocess with stdin, stdout and stderr inherited. Modules the
launcher imports are stdlib only.

## SaMD Mode (built Sessions 49-52, frozen)
Clinical decision support for doctors. Intended use: decision support for a
clinician, for research and evaluation; not a cleared or certified medical
device. The clinician makes every decision.

Status: frozen from PR #126 (Session 52): bug fixes only. Known limits:
Readme/readme_SaMD_pipeline.txt (last section).

| Folder | Content |
|--------|---------|
| input/samd/ | clinical photos, photos of lab reports, .txt/.docx notes, PDFs |
| reports/samd/<run_id>/ | clinician input, image transcriptions, structured case, run.log |
| output/samd/<run_id>/ | final answer as .html (opened in the browser), .md, .docx |

Flow:

    launcher 9 -> main.py --mode samd --provider P --model M
      -> list files in input/samd/; doctor picks files, types extra information
      -> lab photos transcribed (no summary); clinical photos described
         (no diagnosis at this step)                   -> reports/samd/<run_id>/
      -> structured case (history, findings, labs with units and ranges)
                                                       -> reports/samd/<run_id>/
      -> working diagnosis, ranked differential diagnoses with findings for
         and against, red flags, suggested next tests
      -> check: every lab value cited must appear in the transcribed source
      -> output/samd/<run_id>/ .html (local file opened in the browser, no
         server), .md, .docx

Provider: Ollama by default (vision model from the shared picker); Qwen or
OpenAI only after the cloud gate. The cloud banner says clinical images and
case text leave the machine and asks the user to de-identify them.

## Data Analysis Mode (Session 53, being built)
Statistics on a table of data. Every number is computed by Python (pandas,
scipy; scikit-learn for the random forest). No AI model is called, so the data
never leaves the machine and the launcher asks no provider, model or time
limit.

| Folder | Content |
|--------|---------|
| input/data_analysis/ | data tables: .csv and Excel .xlsx |
| reports/data_analysis/<run_id>/ | run.log and intermediate steps (planned) |
| output/data_analysis/<run_id>/ | report as .html, .md, .docx (planned, B7) |

Flow:

    launcher 7 -> main.py --mode data_analysis   (no --provider, no --model)
      -> list .csv / .xlsx files in input/data_analysis/          (B1, built)
      -> load the table; each column categorical or continuous;
         missing values reported                                  (B2)
      -> submenus: Comparison (B3), Effect size (B4),
         Correlation (B5), Random forest (B6)
      -> report .html / .md / .docx                               (B7)

Not in the first version: paired tests; models other than random forest.

## Data Flow

    User input -> launcher.py -> main.py --mode X --provider Y --model Z
      -> cloud gate (cloud providers only)
      -> pipeline loads docs/X/*.md as guidelines
      -> pipeline loads input/X/* as source material
      -> pipeline builds the prompt and calls the provider
      -> reply parsed; iterate if the mode does so
      -> results written to output/X/; logs and steps to reports/X/

## Configuration
All runtime settings come from .env:
- DEFAULT_PROVIDER (empty = ollama), FALLBACK_PROVIDERS
- OLLAMA_HOST, OLLAMA_MODEL (empty = gemma4:e4b), OLLAMA_CONTEXT,
  OLLAMA_NUM_PREDICT, OLLAMA_TEMPERATURE
- Cloud models: QWEN_MODEL, DEEPSEEK_MODEL and the other *_MODEL values
  (launcher 10 Setup -> 4 Cloud AI models shows the active values)
- API keys: DASHSCOPE_API_KEY, DEEPSEEK_API_KEY, OPENAI_API_KEY,
  ANTHROPIC_API_KEY, GROQ_API_KEY
