# HANDOFF - AI kcMedical Research

## Project Location
- Local: D:\AI_kcMedicalResearch
- GitHub: https://github.com/KW75/AI_kcMedicalResearch
- VERSION: 2.1.0

## Current Status (Step 74 complete)
- Commit: 0f682c7 (Step 72b)
- Tests: 258 passing, 0 failing, 87% coverage
- All six modes implemented and tested
- All docs folders populated with guidance templates
- File-based I/O active for search, rct_search, and appraisal modes

---

## Completed Steps

| Step | Description | Commit |
|------|-------------|--------|
| 1-51 | Core tool, providers, RAG, all base modes | multiple |
| 56 | rct_search mode (Formulator, Searcher, Validator) | - |
| 64 | SR pipeline (sr/main.py, PRISMA, meta-analysis) | f8b588a |
| 65 | Appraisal word limit 1500 words | - |
| 66 | Writing mode PDF/DOCX output | - |
| 68 | RCT search single-pass pipeline | - |
| 69 | Rename project to AI_kcMedicalResearch, VERSION 2.0.0 to 2.1.0 | ea06c40 |
| 70 | Update README and HANDOFF for all 6 modes and new flags | f2f2136 |
| 71 | File-based I/O: topic.md for search/rct_search, direct article injection for appraisal | 4afcd2d |
| 72a | Writing templates: project-brief, style-guide, editorial-standards, qa-checklist | - |
| 72b | Appraisal templates: appraisal-guide, scoring-criteria; search-guide output standards | 0f682c7 |
| 73 | Remove HANDOFF.md from .gitignore | 435b1bd |
| 74 | Update README and HANDOFF to document docs/ structure and file-based I/O | current |

---

## Six Modes

| Mode | Flag | Key roles | Input files | Output |
|------|------|-----------|-------------|--------|
| Coding | --mode coding | Builder, Reviewer, Tester | uploads/coding/ | reports/session_*.md/.docx |
| Coding revise | --mode coding --revise | Builder, Reviewer, Tester | docs/coding/*.md | reports/session_*.md/.docx |
| Writing | --mode writing | Writer, Editor, QA | docs/writing/project-brief.md | reports/writing_report_*.md/.docx |
| RCT Search | --mode rct_search | Formulator, Searcher, Validator | docs/rct_search/topic.md (optional) | reports/rct_search_*.md |
| Search | --mode search | Researcher | docs/search/topic.md (optional) | reports/search_*.md |
| Appraisal | --mode appraisal | Appraiser, Methodologist, Summariser | uploads/appraisal/ | reports/session_*.md/.docx |
| SR | --mode sr | SR Methodologist | sr/data/uploads/*.pdf | sr/outputs/reports/ |

---

## Docs Folder - What Each File Does

### docs/appraisal/
- appraisal-guide.md: Mandatory 7-section structure, per-section word limits, plain-language summary rules, study-type notes
- scoring-criteria.md: RoB 2 domain table, CASP cohort checklist, AMSTAR 2 key items, GRADE levels with upgrade/downgrade rules

### docs/coding/
- architecture.md, coding-standards.md, decision-log.md, PRD.md, test-strategy.md: injected as RAG context for coding sessions

### docs/rct_search/
- database-guide.md, pico-framework.md, validation-criteria.md: guidance for the search pipeline roles
- topic.md.example: copy to topic.md and edit to enable file-based topic input

### docs/search/
- search-guide.md: output format for paper search and clinical topic search; no-fabrication rule; 1500-word limit
- topic.md.example: copy to topic.md and edit to enable file-based topic input

### docs/writing/
- project-brief.md: edit the Current Job section before each writing session
- style-guide.md: voice, sentence length, medical accuracy rules, plain-language replacements, referencing style
- editorial-standards.md: accuracy, completeness, word limits, ethical requirements
- qa-checklist.md: 25-item checklist used by the QA role

---

## File-Based I/O

| Mode | File | Format | Fallback |
|------|------|--------|---------|
| rct_search | docs/rct_search/topic.md | Single line: research topic | runtime input() |
| search | docs/search/topic.md | Line 1: paper or topic; Line 2: query | runtime input() |
| appraisal | uploads/appraisal/*.{txt,md,pdf,docx} | Up to 8000 chars = direct inject; over 8000 = RAG | empty context |

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

- SR pipeline is a separate module (sr/main.py) to keep it independently runnable
- All providers are patchable via monkeypatch in tests via src.main.call_ai
- Per-session RAG uses mode-specific ChromaDB collections; cleared between sessions
- URL fetching supported in RAG (paste a URL as a source)
- All reports output as .md and .docx
- RCT search runs as a single-pass pipeline (no interactive loop)
- Appraisal articles up to 8000 chars injected directly; larger files use RAG chunking
- File-based topic input checked before falling back to interactive input()
- docs/ holds standing guidance (committed); uploads/ holds session working documents (gitignored)

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

---

## Known Gaps / Next Steps

| # | Gap | Priority |
|---|-----|----------|
| 75 | GitHub Actions CI (pytest on every push) | High |
| 76 | End-to-end mode testing with real templates | High |
| 77 | Appraisal prompt file updated to reference 7-section guide | Medium |
| 78 | SR Streamlit UI integration | Low |
| 79 | PDF OCR support | Low |
| 80 | WeasyPrint native Windows libs for PDF export | Low |
| 81 | Interactive input() paths fully unit-tested | Low |