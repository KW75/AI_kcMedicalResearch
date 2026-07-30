will handoff this together with this session's handoff to new chat

# HANDOFF — AI kcMedical Research SR Pipeline
## Session: 2026-07-30  |  Continues from: HANDOFF_Session_2026.07.29.md

---

## 1. REPOSITORY

**GitHub:** https://github.com/KW75/AI_kcMedicalResearch  
**Local:**   D:\AI_kcMedicalResearch

**Branch structure:**

main ← commit 4f035fd — PROVEN WORKING — never edit directly fix/sr-extraction-means-sds ← all next-session work goes here origin/main ← in sync with local main as of 2026-07-30


**To start next session:**
```powershell
cd D:\AI_kcMedicalResearch
git checkout fix/sr-extraction-means-sds
git pull origin fix/sr-extraction-means-sds
.venv\Scripts\python.exe -m pytest --tb=short -q
# Must show: 291 passed, 9 skipped

To recover proven working state at any time:

git checkout main
.venv\Scripts\python.exe -m pytest --tb=short -q
.venv\Scripts\python.exe src/main.py --mode sr --provider deepseek

2. CURRENT PIPELINE STATUS
What is proven working ✅
Item 	Detail
Full 6-stage pipeline 	Runs end-to-end without crashing
Stage 1 Upload 	Local PDF paths, non-Anthropic provider
Stage 2 Screening 	All 5 PDFs screened, OCR fallback active, audit CSV written
Stage 3 Extraction 	Three-tier extraction working (see below)
Stage 3.5 RoB 2.0 	Completes for all 5 studies, retry logic active
Stage 4 Meta-analysis 	2-study pooled result (see below)
Stage 5 Forest plot 	PNG generated correctly
Stage 6 Reports 	DOCX + HTML generated; PDF needs WeasyPrint
Project layout 	Timestamped folders under reports\sr\YYYYMMDD_HHMMSS\
Audit CSVs 	Written at stages 2, 3, 3.5, 4
Mirror 	Outputs copied to output\sr\ and sr\outputs\ after each run
Git 	Initialised, .gitignore clean, both branches pushed to GitHub
Tests 	291 passing, 9 skipped
Current meta-analysis result (fibromyalgia / CBT / SMD)
Study 	Hedges g 	95% CI 	How
Ang 2010 	+0.057 	[−0.618, 0.733] 	n_total=32 split evenly (n=16/arm fallback)
McCrae (zsy234) 	−0.234 	[−0.687, 0.218] 	OCR tier 3, full means/SDs extracted
Pooled SMD 	−0.144 	[−0.520, 0.232] 	I² = 0.0%
What is proven NOT working ❌
Study 	Problem 	Root cause
Karlsson (PDF 3, Lami 2015) 	means/SDs always null 	OCR captures 16,519 chars but result table values not returned by DeepSeek
Lami / s10608 	means/SDs always null 	pymupdf captures 17,935 chars but Table 4 (pages 12–13 of 17) not extracted
Jensen (PDF 2) 	outcome_match=False 	VAS post-intervention means/SDs may be genuinely absent from paper
Ang 2010 	n_intervention/n_control never extracted 	Only n_total=32 found; true arm allocation unknown
WeasyPrint 	PDF output falls back to HTML 	Not installed; needs GTK3 runtime on Windows
RCT Search 	Does not find the 5 fibromyalgia papers 	See Section 5
3. FILES MODIFIED THIS SESSION

All changes are committed on main (commit 4f035fd).
Modified files
File 	What changed
sr/main.py 	n_total fallback (lines 205–209); project layout integration; INPUT_SR as pdf-dir
sr/src/extraction/data_extractor.py 	Three-tier extraction; \x00 null-byte guard line 174; per-page cap removed
sr/src/screening/rob2_tool.py 	Full file replacement; retry logic in _call_with_text; OCR fallback
sr/src/screening/relevance_screener.py 	OCR fallback; 6,000-char truncation cap
src/main.py 	Removed copy-to-uploads block; passes INPUT_SR as --pdf-dir to sr/main.py
tests/test_sr.py 	Renamed test_launcher_copies_pdfs → test_launcher_passes_input_sr_as_pdf_dir
docs/flashcard-help.html 	Updated with current SR pipeline status, known issues, meta-analysis result
HANDOFF_Session_2026.07.29.md 	Previous session handoff (read-only reference)
New files
File 	Purpose
sr/src/utils/project_layout.py 	Timestamped run folders under reports\sr; initialise(), mirror_all()
sr/src/utils/audit_logger.py 	Writes screening, extraction, RoB2, results CSVs
sr/src/utils/json_utils.py 	Strips markdown fences, repairs JSON from DeepSeek responses
sr/src/utils/__init__.py 	Package init
4. THREE-TIER PDF EXTRACTION — HOW IT WORKS

All five PDFs use CID-font encoding so pdfplumber always returns garbled text. The pipeline falls through the tiers automatically:

Tier 1: pdfplumber
  → if garbled (no spaces, "(cid:" present) → Tier 2

Tier 2: pymupdf (fitz)
  → accepts output only if: non-empty AND ≥20 spaces AND no \x00 null bytes
  → zsy234.pdf is Caesar-shifted (all chars offset), produces \x00 bytes → rejected
  → if rejected → Tier 3

Tier 3: Tesseract OCR (pytesseract)
  → renders each page to 2x pixel image, OCR reads clean text
  → page selection: all pages if ≤6 pages, else first 3 + next 9 pages
  → per-page cap: 1,500 chars
  → total cap: 14,000 chars (data_extractor.py) / 6,000 chars (relevance_screener.py)

Key file: sr/src/extraction/data_extractor.py lines 139–220
Key guard: line 174 — if candidate and candidate.count(" ") >= 20 and "\x00" not in candidate:
5. DIRECTORY STRUCTURE

D:\AI_kcMedicalResearch\
├── input\sr\                    ← PDFs go here (5 fibromyalgia papers)
├── src\main.py                  ← launcher; calls sr\main.py as subprocess
├── sr\
│   ├── main.py                  ← SR pipeline (6 stages)
│   ├── config\prisma_criteria.yaml
│   ├── src\
│   │   ├── analysis\
│   │   ├── extraction\data_extractor.py
│   │   ├── reporting\
│   │   ├── screening\relevance_screener.py, rob2_tool.py
│   │   ├── upload\file_manager.py
│   │   ├── utils\audit_logger.py, json_utils.py, project_layout.py
│   │   └── visualization\
│   └── outputs\                 ← mirror target (legacy compatibility)
├── reports\sr\YYYYMMDD_HHMMSS\  ← timestamped run folders
│   ├── uploads\
│   ├── data\screened\, extracted\, results\
│   └── output\figures\, reports\
├── output\sr\                   ← second mirror target
├── tests\
└── docs\flashcard-help.html     ← interactive help guide

6. NEXT SESSION PRIORITIES
Priority 1 — Fix Karlsson and Lami means/SDs (branch: fix/sr-extraction-means-sds)

These two papers have correct N values but null means/SDs every run. The OCR text is being captured (16k–18k chars) but DeepSeek is not returning the numeric table values.

Diagnosis steps:

# Inspect what OCR text is actually captured for s10608
.venv\Scripts\python.exe -c "
import fitz, pytesseract, io
from PIL import Image
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
doc = fitz.open(r'D:\AI_kcMedicalResearch\input\sr\s10608-017-9875-4.pdf')
for i in [9,10,11,12,13]:  # pages 10-14 where Table 4 should be
    pix = doc[i].get_pixmap(matrix=fitz.Matrix(2,2))
    img = Image.open(io.BytesIO(pix.tobytes('png')))
    text = pytesseract.image_to_string(img)
    print(f'--- PAGE {i+1} ---')
    print(text[:500])
"

If Table 4 text is present → the extraction prompt needs strengthening. Add this instruction to EXTRACTION_PROMPT_TEMPLATE in data_extractor.py:

8. Search EVERY table row by row. Look specifically for rows labelled:
   pain, VAS, NRS, FIQ, MPQ, BPI, PSQI, or any pain scale abbreviation.
   Extract the numeric cell values as mean_intervention and mean_control.
9. If a table has columns labelled CBT/intervention/treatment and
   control/waitlist/usual care, those columns map to
   mean_intervention and mean_control respectively.

If Table 4 text is absent → the page selection range is wrong. Change the OCR page selection in data_extractor.py from:

selected = list(range(3)) + list(range(3, total_pages))[:9]

To a smarter selection that always includes the last 4 pages:

first = list(range(min(3, total_pages)))
last  = list(range(max(3, total_pages-4), total_pages))
mid   = list(range(3, total_pages-4))[::max(1,(total_pages-7)//5)]
selected = sorted(set(first + mid + last))

Priority 2 — Fix Jensen means/SDs

Jensen (PDF 2, Cognitive Behavioral Therapy increases pain-evoked activation...) Run the same page inspection for that PDF. If VAS means/SDs genuinely do not appear anywhere in the paper's tables, the study should remain excluded and a note added to the report explaining why.
Priority 3 — Ang per-arm N

The true allocation for Ang 2010 needs to be confirmed. Check page 1-2 of the PDF for CONSORT flow diagram or Table 1. If arms are unequal the n_total/2 fallback introduces bias. The correct fix is to hardcode the known allocation in a study-specific override dict in sr/main.py.
Priority 4 — WeasyPrint PDF output

.venv\Scripts\python.exe -m pip install weasyprint
# Then download and install GTK3 runtime:
# https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases

Priority 5 — Merge and tag when 3+ studies pass Stage 4

git checkout main
git merge fix/sr-extraction-means-sds
git tag -a v1.1.0 -m "SR pipeline: 3+ study pooled meta-analysis"
git push origin main --tags

7. RCT SEARCH — DIRECTION OF DEVELOPMENT

The five fibromyalgia papers selected by the researcher were NOT found by the RCT Search pipeline. Three separate problems combine to cause this:

Problem 1 — Publication type filter too strict Current query appends AND randomized controlled trial[pt] which only matches papers where PubMed has explicitly assigned the RCT publication type. Several CBT fibromyalgia trials are indexed as "Clinical Trial" or "Controlled Clinical Trial" not "Randomized Controlled Trial".

Fix: Change the PubMed filter logic in src/modes/rct_search.py (or wherever the PubMed query is assembled) to use:

AND (randomized controlled trial[pt] OR clinical trial[pt] OR
     random*[tiab] OR RCT[tiab])

Problem 2 — Only 20 results fetched The pipeline fetches 20 PubMed results then AI-ranks them. If the target papers are not in the top 20 hits they are invisible.

Fix: Increase the fetch limit to 100. Add a parameter --pubmed-max-results (default 100) to the rct_search launcher.

Problem 3 — Only PubMed searched via API The Searcher agent generates Boolean strings for 7 databases (EMBASE, PsycINFO, CINAHL, Cochrane CENTRAL, Web of Science, Scopus, PubMed) but only PubMed is actually queried via API. Several CBT fibromyalgia papers are more prominently indexed in PsycINFO and Cochrane CENTRAL.

Fix (phased):

    Phase A: Add Cochrane CENTRAL REST API (free, no key needed, covers all registered RCTs) Endpoint: https://www.cochranelibrary.com/api/v1/search
    Phase B: Add Europe PMC API as a second free source Endpoint: https://www.ebi.ac.uk/europepmc/webservices/rest/search
    Phase C: Display the 6 non-PubMed search strings in the report with a note "Run these manually in EMBASE/PsycINFO/CINAHL"

Problem 4 — Study design too narrow The PICO study_design field is set to "Randomised controlled trials (RCTs)". CBT fibromyalgia literature includes crossover RCTs, waitlist-controlled trials, and quasi-experimental designs that are clinically valid but may not be indexed as RCTs.

Fix: Change the prisma_criteria.yaml study_design field to:

study_design: "RCT, crossover trial, or controlled clinical trial"

And update the Validator agent prompt to accept these designs.
8. WORKFLOW REMINDER

Run SR pipeline:
  .venv\Scripts\python.exe src/main.py --mode sr --provider deepseek

Run tests:
  .venv\Scripts\python.exe -m pytest --tb=short -q

Check latest run output:
  Get-ChildItem D:\AI_kcMedicalResearch\reports\sr | Sort-Object Name -Descending | Select-Object -First 1

Save work to branch:
  git add .
  git commit -m "fix(sr): <description>"
  git push origin fix/sr-extraction-means-sds

When extraction reaches 3+ studies, merge to main:
  git checkout main
  git merge fix/sr-extraction-means-sds
  git push origin main

9. ENVIRONMENT
Item 	Value
Python 	3.11
Virtual env 	D:\AI_kcMedicalResearch.venv\
Tesseract 	C:\Program Files\Tesseract-OCR\tesseract.exe
Primary provider 	DeepSeek (deepseek-v4-flash)
API keys 	In .env file (never committed to Git)
OS 	Windows (PowerShell — use utf8 not utf8NoBOM for Out-File)
WeasyPrint 	NOT installed — PDF output is HTML only

Handoff prepared: 2026-07-30
Previous handoff: HANDOFF_Session_2026.07.29.md
Repo: https://github.com/KW75/AI_kcMedicalResearch
Branch for next session: fix/sr-extraction-means-sds