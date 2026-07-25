HANDOFF — AI kcMedical Research
For new chat session — Step 89 onwards
Project Location

    Local (desktop): D:\AI_kcMedicalResearch
    GitHub: https://github.com/KW75/AI_kcMedicalResearch (private)
    VERSION: 2.2.0
    Last commit: 8b74188 (Step 88c)
    Tests: 300 passing, 0 failing, ~85% coverage
    Python: 3.11+, virtual env at .venv
    Launch: double-click AI_kcMedicalResearch_run.bat

Working Providers (confirmed live tested)
Provider 	Status 	Notes
Qwen (DashScope) 	✅ Working 	Default, geo-unrestricted
DeepSeek 	✅ Working 	thinking mode disabled
Ollama 	✅ Working 	Local
Anthropic 	✅ Working 	VPN required
OpenAI 	⏭️ No key
Groq 	⏭️ No key

DashScope endpoints (Singapore workspace):

    OpenAI-compatible: https://ws-uv5pi4kkqbrg1vpe.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1
    Anthropic-compatible: https://ws-uv5pi4kkqbrg1vpe.ap-southeast-1.maas.aliyuncs.com/apps/anthropic

Current Folder Structure

D:\AI_kcMedicalResearch\
  src\main.py              ← main CLI tool (all 6 modes)
  launcher.py              ← interactive menu launcher
  AI_kcMedicalResearch_run.bat  ← double-click to start
  sr\                      ← SR pipeline (separate module)
    main.py                ← SR CLI entry point
    src\ui\app.py          ← SR Streamlit UI (standalone, to be retired)
    data\uploads\          ← SR PDF input
    outputs\               ← SR pipeline outputs
  uploads\
    coding\                ← input files for coding mode
    writing\               ← input files for writing mode
    appraisal\             ← input articles for appraisal
    rct_search\            ← input files for RCT search
  reports\                 ← ALL current outputs (session transcripts + reports)
  outputs\                 ← DOES NOT EXIST YET — next step to create
  tests\                   ← pytest suite (300 tests)
  docs\                    ← standing guidance files
  requirements.txt
  .env                     ← API keys (gitignored)

Six Modes
Mode 	Flag 	Input 	Current output
Coding 	--mode coding 	uploads/coding/ 	reports/session_{ts}.md
Writing 	--mode writing 	uploads/writing/ 	reports/writing_report_{ts}.md/.docx
Appraisal 	--mode appraisal 	uploads/appraisal/ 	reports/session_{ts}.md
RCT Search 	--mode rct_search 	uploads/rct_search/ 	reports/rct_search_{ts}.md/.docx
Search 	--mode search 	none 	reports/search_{ts}.md
SR 	--mode sr 	sr/data/uploads/ 	sr/outputs/...
Next Major Task — Step 89: Output Folder Restructure

Goal: separate operation logs from actual deliverable outputs.

New structure to create:

outputs\
  coding\       ← extracted code blocks as .py/.html/.js etc (auto-saved during session)
  writing\      ← writing_report_{ts}.md/.docx
  appraisal\    ← appraisal_{ts}.md/.docx (merged from all 3 agents)
  rct_search\   ← rct_search_{ts}.md/.docx + uri_list_{ts}.md
  search\       ← search_{ts}.md/.docx + uri_list_{ts}.md
reports\        ← session transcripts only (operation logs, unchanged)

New constants to add in src/main.py after line 61:

OUTPUTS_DIR         = BASE_DIR / "outputs"
OUTPUTS_CODING      = OUTPUTS_DIR / "coding"
OUTPUTS_WRITING     = OUTPUTS_DIR / "writing"
OUTPUTS_APPRAISAL   = OUTPUTS_DIR / "appraisal"
OUTPUTS_RCT_SEARCH  = OUTPUTS_DIR / "rct_search"
OUTPUTS_SEARCH      = OUTPUTS_DIR / "search"

Changes per mode:

    Writing — change generate_writing_report() output from reports/ to outputs/writing/
    RCT Search — change output to outputs/rct_search/, add separate uri_list_{ts}.md
    Search — change output to outputs/search/, add DOCX, add uri_list_{ts}.md
    Appraisal — at end of session merge all 3 agent outputs into outputs/appraisal/appraisal_{ts}.md/.docx
    Coding — add extract_code_blocks() helper, auto-save code files to outputs/coding/ during session

Implementation order (simplest to most complex):

    Writing (folder change only)
    Search topic (folder change + add DOCX)
    RCT Search (folder change + URI list)
    Appraisal (merge 3 agents + MD/DOCX)
    Coding (code block extraction)

Step 90 (after 89): Main Streamlit UI

Goal: build src/ui/app.py — single Streamlit app covering all 6 modes.

    Landing page with 6 mode cards (2×3 grid)
    Each mode → single page form with: collapsible instructions, settings (provider/model), file upload, Run button, live output, download buttons
    Back to menu + Exit buttons on every page
    SR page replaces standalone sr/src/ui/app.py
    Launch via python src/main.py --ui

Key Commands

# Run tests
.venv\Scripts\python.exe -m pytest --tb=short -q

# Live provider smoke test
.venv\Scripts\python.exe test_live_providers.py

# Run a mode
.venv\Scripts\python.exe src\main.py --mode writing --provider qwen

# SR CLI mode
.venv\Scripts\python.exe src\main.py --mode sr --pdf-dir sr\data\uploads --provider qwen

# Git commit pattern
git add -A
git status
git commit -m "Step XX: description"
git push

Important Rules for New Chat

    Always run pytest before committing — expect 300 passed
    Never commit .env — it is gitignored at line 5
    Check git status before git add — avoid double-staging
    LF/CRLF warnings on Windows are harmless — ignore them
    DeepSeek requires thinking: disabled in payload
    Qwen requires enable_thinking: False in extra_body
    Anthropic requires VPN in current region
    src/main.py has sys.path fix after load_dotenv() — do not remove it
    SR Streamlit UI launches in separate cmd window (menu option 6) — closing window returns to menu
    300 tests must stay green after every change
