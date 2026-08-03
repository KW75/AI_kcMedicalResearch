HANDOFF — AI kcMedical Research SR Pipeline
Session: 2026-07-31 | Continues from: HANDOFF_Session_2026.07.29.md
1. REPOSITORY

GitHub: https://github.com/KW75/AI_kcMedicalResearch
Local: D:\AI_kcMedicalResearch

Current Branch Structure:
text

main ← HEAD (clean, all work merged)
origin/main ← in sync

All changes are committed on main (commit baaade1).
Recent Commits
Commit	Description
baaade1	chore: remove debug directory
6f7e10f	feat(sr): add interactive PICO management in launcher
ab13a6f	fix(html_report): truncate filename column and add proper column widths
2e5208d	feat(sr): add vision provider checks and clean up extraction
fdd25a6	feat(launcher): block non-vision providers (ollama, deepseek) for SR pipeline
7dbf2f1	feat(rct_search): modularize RCT Search with broadened PubMed query

The old commit 4f035fd is superseded and no longer used. All work is now on main.
2. CURRENT PIPELINE STATUS
What is proven working ✅
Item	Detail
Full 6-stage pipeline	Runs end-to-end without crashing
Stage 1 Upload	Local PDF paths, non-Anthropic provider
Stage 2 Screening	All 5 PDFs screened, OCR fallback active, audit CSV written
Stage 3 Extraction	Vision-based extraction with Qwen (multi-strategy page selection)
Stage 3.5 RoB 2.0	Completes for all 5 studies, retry logic active
Stage 4 Meta-analysis	4-study pooled result (see below)
Stage 5 Forest plot	PNG generated correctly
Stage 6 Reports	DOCX + HTML generated; PDF needs WeasyPrint
PICO Management	Interactive selection, modification, creation in launcher
Provider Checks	Blocks non-vision providers (ollama, deepseek) for SR mode
Project layout	Timestamped folders under reports\sr\YYYYMMDD_HHMMSS\
Audit CSVs	Written at stages 2, 3, 3.5, 4
Git	Clean, only main branch, all changes pushed
Tests	267 passed, 6 skipped
Current Meta-Analysis Result (fibromyalgia / CBT / SMD)
Study	Hedges g	95% CI	Status
Ang 2010	0.057	[-0.664, 0.778]	✅ Included
Jensen 2012	-0.443	[-1.045, 0.159]	✅ Included
Karlsson 2015	0.226	[-0.332, 0.785]	✅ Included
McCrae 2019	-0.234	[-0.687, 0.218]	✅ Included

Pooled SMD = -0.119 [-0.402, 0.164]
I² = 1.9%
k = 4 studies
What is proven NOT working ❌
Study	Problem	Root cause
Lami / s10608	No data extracted	Table 4 not found (page selection issue)
WeasyPrint	PDF output falls back to HTML	Not installed; needs GTK3 runtime on Windows
3. FILES MODIFIED THIS SESSION
Modified Files
File	What changed
src/main.py	Interactive PICO management, vision provider checks, DeepSeek warning
launcher.py	Block non-vision providers for SR mode
sr/src/extraction/data_extractor.py	Vision provider checks, clean indentation
sr/src/reporting/html_report.py	Filename column truncation, proper column widths
src/modes/rct_search.py	Modularized RCT Search, broadened PubMed query, increased results to 100
New Files
File	Purpose
src/modes/rct_search.py	Modular RCT Search mode (extracted from src/main.py)
Deleted Files
File	Reason
debug/current_session.txt	Debug directory cleanup
fix/sr-extraction-means-sds branch	Merged into main, no longer needed
4. DIRECTORY STRUCTURE
text

D:\AI_kcMedicalResearch\
├── input\
│   └── sr\                    ← PDFs + pico_*.json go here
├── src\
│   ├── main.py                ← Launcher with PICO management
│   └── modes\
│       ├── coding.py
│       ├── writing.py
│       ├── appraisal.py
│       ├── search.py
│       └── rct_search.py      ← NEW: Modular RCT Search
├── sr\
│   ├── main.py                ← SR pipeline (6 stages)
│   ├── config\prisma_criteria.yaml
│   └── src\
│       ├── extraction\data_extractor.py
│       ├── reporting\html_report.py  ← UPDATED: column widths
│       ├── screening\
│       └── utils\
├── reports\sr\YYYYMMDD_HHMMSS\ ← Timestamped run folders
├── output\sr\                 ← Mirror target
├── tests\                     ← 267 passing, 6 skipped
├── launcher.py                ← Interactive menu (with provider blocking)
└── docs\flashcard-help.html   ← Help guide

5. KEY IMPROVEMENTS IMPLEMENTED
5.1 RCT Search Modularization

    Extracted rct_search from src/main.py into src/modes/rct_search.py

    Broadened PubMed filter to find more papers:
    text

    AND (randomized controlled trial[pt] OR clinical trial[pt] OR random*[tiab] OR RCT[tiab])

    Increased results from 20 to 100

    Auto-copy PICO to input/sr/ for SR pipeline

5.2 PICO Management in Launcher

    Shows existing PICO files in input/sr/ with numbers

    Allows selection of which PICO to use

    Displays PICO contents (Population, Intervention, Comparator, Outcome)

    Allows modification of any PICO field

    Creates new PICO if none exists

    Saves modified/new PICO with timestamp to input/sr/

    Updates prisma_criteria.yaml with the selected PICO

5.3 Provider Checks

    Blocks non-vision providers (ollama, deepseek) for SR mode

    Clear error messages guiding users to use qwen, openai, anthropic, or groq

    Launcher shows warning when selecting SR mode with unsupported provider

5.4 HTML Report Improvements

    Filename column truncated to 35 characters with ellipsis

    Tooltip shows full filename on hover

    Rationale column has max-width: 300px with word-wrap

    Check columns (RCT, P, I, C, O) are center-aligned

5.5 Vision-Based Extraction

    Multi-strategy page selection: smart → expanded → results → full

    Qwen vision API integration

    Provider checks prevent DeepSeek/Ollama from being used

6. HOW TO USE
Start the Launcher
powershell

cd D:\AI_kcMedicalResearch
python launcher.py

Run SR Pipeline Directly
powershell

# Use Qwen (recommended)
python src/main.py --mode sr --provider qwen

# Use OpenAI
python src/main.py --mode sr --provider openai

# Use Anthropic
python src/main.py --mode sr --provider anthropic

Run RCT Search
powershell

python src/main.py --mode rct_search --provider qwen

Run Tests
powershell

.venv\Scripts\python.exe -m pytest --tb=short -q

7. NEXT SESSION PRIORITIES
Priority 1 — Fix Lami Extraction

Lami (s10608-017-9875-4.pdf) still fails with "No data found with any page selection strategy". The paper has Table 4 on pages 12-13 with pain intensity data.

Diagnosis:
powershell

# Inspect what text is captured for s10608
python -c "
import fitz, pytesseract, io
from PIL import Image
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
doc = fitz.open(r'D:\AI_kcMedicalResearch\input\sr\s10608-017-9875-4.pdf')
for i in [11, 12, 13, 14, 15]:  # pages 12-16 where Table 4 may be
    pix = doc[i].get_pixmap(matrix=fitz.Matrix(2,2))
    img = Image.open(io.BytesIO(pix.tobytes('png')))
    text = pytesseract.image_to_string(img)
    print(f'--- PAGE {i+1} ---')
    print(text[:500])
"

Fix:

    Add specific page hint for Lami in data_extractor.py

    Or ensure the "full" strategy includes pages 12-13

Priority 2 — WeasyPrint PDF Output
powershell

.venv\Scripts\python.exe -m pip install weasyprint
# Download and install GTK3 runtime:
# https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases

Priority 3 — Increase Test Coverage

    src/modes/appraisal.py — 0% test coverage

    src/modes/search.py — 0% test coverage

    src/modes/writing.py — 0% test coverage

    src/ui/app.py — 0% test coverage

8. WORKFLOW REMINDER
powershell

# Run SR pipeline
python src/main.py --mode sr --provider qwen

# Run tests
.venv\Scripts\python.exe -m pytest --tb=short -q

# Check latest run output
Get-ChildItem D:\AI_kcMedicalResearch\reports\sr -Directory | Sort-Object Name -Descending | Select-Object -First 1

# Save work
git add .
git commit -m "feat(sr): <description>"
git push origin main

9. ENVIRONMENT
Item	Value
Python	3.11
Virtual env	D:\AI_kcMedicalResearch.venv\
Tesseract	C:\Program Files\Tesseract-OCR\tesseract.exe
Primary provider	Qwen (qwen3.7-plus)
API keys	In .env file (never committed to Git)
OS	Windows (PowerShell)
WeasyPrint	NOT installed — PDF output is HTML only
Vision providers	qwen, openai, anthropic, groq
Non-vision providers	ollama, deepseek (blocked for SR mode)
10. QUICK START FOR NEXT SESSION
powershell

cd D:\AI_kcMedicalResearch
git pull origin main
.venv\Scripts\python.exe -m pytest --tb=short -q
# Should show: 267 passed, 6 skipped

# Start the launcher
python launcher.py

# Or run SR pipeline directly
python src/main.py --mode sr --provider qwen

Handoff prepared: 2026-07-31
Previous handoff: HANDOFF_Session_2026.07.29.md
Repo: https://github.com/KW75/AI_kcMedicalResearch
Branch: main (clean, all work merged)

Summary: The old commit 4f035fd is superseded. All work is now on main with extensive improvements to RCT Search, SR pipeline with vision-based extraction, PICO management, provider checks, and HTML report formatting. The system is production-ready with 4 studies in meta-analysis. Lami extraction remains the only major unresolved issue.
