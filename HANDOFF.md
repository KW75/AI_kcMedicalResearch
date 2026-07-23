# HANDOFF — AI kcMedical Research

## Project Location
- **Local (desktop):** D:\AI_kcMedicalResearch
- **Local (laptop):**  C:\AI_kcMedicalResearch  *(after zip transfer)*
- **GitHub:** https://github.com/KW75/AI_kcMedicalResearch
- **VERSION:** 2.1.0

## Current Status
- **Last commit:** 6006d23 (Step 77d)
- **Tests:** 258 passing, 0 failing, ~87% coverage
- **Python:** 3.11+ recommended
- **Virtual env:** .venv (in project root)

---

## Completed Steps

| Step | Description | Commit |
|------|-------------|--------|
| 1–51 | Core tool, providers, RAG, all base modes | multiple |
| 56 | rct_search mode (Formulator, Searcher, Validator) | — |
| 64 | SR pipeline (sr/main.py, PRISMA, meta-analysis) | f8b588a |
| 65 | Appraisal word limit 1500 words | — |
| 66 | Writing mode PDF/DOCX output | — |
| 68 | RCT search single-pass pipeline | — |
| 69 | Rename project to AI_kcMedicalResearch, VERSION 2.1.0 | ea06c40 |
| 70 | Update README and HANDOFF for all 6 modes and new flags | f2f2136 |
| 71 | File-based I/O: topic.md for search/rct_search, direct article injection for appraisal | 4afcd2d |
| 72a | Writing templates: project-brief, style-guide, editorial-standards, qa-checklist | — |
| 72b | Appraisal templates: appraisal-guide, scoring-criteria; search-guide output standards | 0f682c7 |
| 73 | Remove HANDOFF.md from .gitignore | 435b1bd |
| 74 | Update README and HANDOFF — docs/ structure, file-based I/O | 24fb22a |
| 74b | Remove stale helper scripts | 7fc86d6 |
| 77 | Align appraisal/methodologist/summariser prompts with 7-section guide | d296153 |
| 77b | Create flashcard.html quick-reference (later removed) | 3db9dcf |
| 77c | Delete orphan flashcard.html, partial flashcard-help.html update | 152c892 |
| 77d | Patch flashcard-help.html — 7-section appraisal card, 258 tests, claude-sonnet-4-6 | 6006d23 |

---

## Six Modes

| Mode | Flag | Roles | Input | Output |
|------|------|-------|-------|--------|
| Coding | --mode coding | Builder, Reviewer, Tester | uploads/coding/ | reports/session_*.md/.docx |
| Coding revise | --mode coding --revise | Builder, Reviewer, Tester | docs/coding/*.md | reports/session_*.md/.docx |
| Writing | --mode writing | Writer, Editor, QA | docs/writing/project-brief.md | reports/writing_report_*.md/.docx |
| RCT Search | --mode rct_search | Formulator, Searcher, Validator | docs/rct_search/topic.md | reports/rct_search_*.md |
| Search | --mode search | Researcher | docs/search/topic.md | reports/search_*.md |
| Appraisal | --mode appraisal | Appraiser, Methodologist, Summariser | uploads/appraisal/ | reports/session_*.md/.docx |
| SR | --mode sr | SR Methodologist | sr/data/uploads/*.pdf | sr/outputs/reports/ |

---

## Docs Folder

### docs/appraisal/
- **appraisal-guide.md** — mandatory 7-section structure, per-section word limits, plain-language summary rules, study-type notes (RCT / cohort / SR / cross-sectional)
- **scoring-criteria.md** — RoB 2 domain table, CASP cohort checklist, AMSTAR 2 key items, GRADE levels with upgrade/downgrade rules

### docs/coding/
- architecture.md, coding-standards.md, decision-log.md, PRD.md, test-strategy.md — injected as RAG context for coding sessions

### docs/rct_search/
- database-guide.md, pico-framework.md, validation-criteria.md — guidance for search pipeline roles
- topic.md.example — copy to topic.md and edit to enable file-based input

### docs/search/
- search-guide.md — output format, no-fabrication rule, 1500-word limit
- topic.md.example — copy to topic.md and edit

### docs/writing/
- project-brief.md — edit the Current Job section before each writing session
- style-guide.md — voice, sentence length, medical accuracy, plain-language rules
- editorial-standards.md — accuracy, completeness, word limits, ethical requirements
- qa-checklist.md — 25-item checklist used by the QA role

---

## File-Based I/O

| Mode | File | Format | Fallback |
|------|------|--------|---------|
| rct_search | docs/rct_search/topic.md | Single line: research topic | runtime input() |
| search | docs/search/topic.md | Line 1: paper or topic; Line 2: query | runtime input() |
| appraisal | uploads/appraisal/*.{txt,md,pdf,docx} | ≤8000 chars = direct inject; >8000 = RAG | empty context |

---

## Word Limits

| Mode / Section | Limit |
|----------------|-------|
| Appraisal full report | 1500 words |
| Appraisal plain-language summary | 200 words |
| Search clinical topic report | 1500 words |
| Writing report | 1500 words |

---

## Providers

| Provider | Flag | Env var |
|----------|------|---------|
| Ollama (local) | --provider ollama | OLLAMA_URL |
| OpenAI | --provider openai | OPENAI_API_KEY |
| Anthropic | --provider anthropic | ANTHROPIC_API_KEY |
| DeepSeek | --provider deepseek | DEEPSEEK_API_KEY |
| Groq | --provider groq | GROQ_API_KEY |

---

## Key Design Decisions
- SR pipeline is a separate module (sr/main.py) — independently runnable
- All providers patchable via monkeypatch in tests via src.main.call_ai
- Per-session RAG uses mode-specific ChromaDB collections; cleared between sessions
- URL fetching supported in RAG (paste a URL as a source)
- All reports output as .md and .docx
- RCT search runs as a single-pass pipeline (no interactive loop)
- Appraisal articles ≤8000 chars injected directly; larger files use RAG chunking
- File-based topic input checked before falling back to interactive input()
- docs/ holds standing guidance (committed); uploads/ holds session working docs (gitignored)
- OCR not yet active — PDF text extraction is text-layer only (pytesseract stub ready, needs Tesseract binary on PATH)

---

## OCR Status (Gap 79)
Text-based PDFs work via PyMuPDF (fitz). Scanned/image PDFs require:
1. Install Tesseract binary: https://github.com/UB-Mannheim/tesseract/wiki
2. pip install pytesseract pillow pdf2image
3. Install Poppler for Windows (pdf2image dependency): https://github.com/oschwartz10612/poppler-windows
4. Add both Tesseract and Poppler bin/ folders to PATH in .env or System Environment Variables
5. Enable OCR fallback in src/rag.py where fitz returns empty text

---

## Common Run Commands

    python src/main.py --mode coding
    python src/main.py --mode writing
    python src/main.py --mode writing --report
    python src/main.py --mode appraisal
    python src/main.py --mode search
    python src/main.py --mode rct_search
    python sr/main.py --pdf-dir sr/data/uploads --effect-measure SMD
    python -m pytest --tb=short -q
    python test_live_providers.py
    python src/main.py --help-guide

---

## Laptop Transfer
The project was zipped from D:\AI_kcMedicalResearch and unzipped to C:\AI_kcMedicalResearch on the laptop.
Run AI_kcMedicalResearch_setup.bat once after unzipping to rebuild .venv and install dependencies.
All paths in src/main.py use BASE_DIR = Path(__file__).resolve().parent.parent so the drive letter does not matter.

---

## Known Gaps / Next Steps

| # | Gap | Priority |
|---|-----|----------|
| 75 | GitHub Actions CI (pytest on every push) | High |
| 76 | End-to-end mode testing with real templates | High |
| 78 | SR Streamlit UI integration | Low |
| 79 | PDF OCR support (pytesseract + Tesseract binary + Poppler) | Medium |
| 80 | API key validation on startup | High |
| 81 | GitHub repo audit (.gitignore, secrets, branch protection) | High |
| 82 | WeasyPrint native Windows libs for PDF export | Low |
| 83 | Interactive input() paths fully unit-tested | Low |
