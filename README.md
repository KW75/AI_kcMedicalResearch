# AI kcMedical Research

A multi-mode AI assistant for medical research, critical appraisal, systematic review, coding, and writing.
Runs locally via Ollama or via cloud providers (OpenAI, Anthropic, DeepSeek, Groq).

- **Version**: 2.1.0
- **Tests**: 258 passing, 0 failing
- **GitHub**: https://github.com/KW75/AI_kcMedicalResearch

---

## Quick Start

Run all commands from: D:\AI_kcMedicalResearch

    python src/main.py                            # coding mode (Ollama default)
    python src/main.py --mode writing             # writing mode
    python src/main.py --mode writing --report    # single-pass writing report
    python src/main.py --mode rct_search          # RCT search pipeline
    python src/main.py --mode search              # PubMed search
    python src/main.py --mode appraisal           # critical appraisal
    python src/main.py --mode sr                  # systematic review pipeline
    python src/main.py --provider anthropic       # use Anthropic instead of Ollama
    python src/main.py --dry-run                  # test without API calls

---

## Modes

| Mode | Flag | Roles | Output |
|------|------|-------|--------|
| Coding | --mode coding | Builder, Reviewer, Tester | reports/session_*.md + .docx |
| Coding revise | --mode coding --revise | Builder, Reviewer, Tester | reports/session_*.md + .docx |
| Writing | --mode writing | Writer, Editor, QA | reports/writing_report_*.md + .docx |
| Writing report | --mode writing --report | Writer, Editor, QA | reports/writing_report_*.md + .docx |
| RCT Search | --mode rct_search | Formulator, Searcher, Validator | reports/rct_search_*.md |
| Search | --mode search | Researcher | reports/search_*.md |
| Appraisal | --mode appraisal | Appraiser, Methodologist, Summariser | reports/session_*.md + .docx |
| SR | --mode sr | SR Methodologist | sr/outputs/reports/ |

---

## Flags

| Flag | Description |
|------|-------------|
| --mode | Select mode (coding, writing, rct_search, search, appraisal, sr) |
| --provider | AI provider: ollama, openai, anthropic, deepseek, groq |
| --report | Writing mode: single-pass report from docs/writing/ files |
| --revise | Coding mode: Builder to Reviewer to Tester pipeline |
| --role | Override the starting role |
| --dry-run | Run without making real API calls |

---

## File-Based Input

Avoid interactive prompts by placing input files in the relevant folder before running.

### RCT Search
Create docs/rct_search/topic.md with one line: the research topic.
Example: Effect of metformin on HbA1c in type 2 diabetes
If absent, the mode prompts at runtime.

### Search
Create docs/search/topic.md with two lines.
Line 1: paper (find a specific paper) or topic (clinical topic summary).
Line 2: your query.
If absent, the mode prompts at runtime.

### Appraisal
Place article files in uploads/appraisal/
Supported formats: .txt .md .pdf .docx
Files up to 8000 characters are injected directly into the prompt.
Files over 8000 characters are handled via RAG chunking.
Multiple files are each labelled and appended in sequence.

---

## Docs Folder Structure

Guidance files are loaded as context for each mode. Edit to customise AI behaviour.

    docs/
      appraisal/
        appraisal-guide.md       <- 7-section structure, word limits, study-type notes
        scoring-criteria.md      <- RoB 2, CASP, AMSTAR 2, GRADE tables
      coding/
        architecture.md
        coding-standards.md
        decision-log.md
        PRD.md
        test-strategy.md
      rct_search/
        database-guide.md
        pico-framework.md
        topic.md.example         <- copy to topic.md and edit
        validation-criteria.md
      search/
        search-guide.md          <- output format and quality standards
        topic.md.example         <- copy to topic.md and edit
      writing/
        editorial-standards.md
        project-brief.md         <- edit before each writing session
        qa-checklist.md
        style-guide.md

---

## Upload Folders (RAG)

| Mode | Upload folder | Notes |
|------|--------------|-------|
| coding | uploads/coding/ | Source files for code review |
| writing | uploads/writing/ | Reference documents |
| rct_search | uploads/rct_search/ | Background literature |
| appraisal | uploads/appraisal/ | Article files to appraise |
| sr | sr/data/uploads/ | PDFs for SR pipeline |

---

## Providers

| Provider | Flag | Environment variable |
|----------|------|---------------------|
| Ollama (local) | --provider ollama | OLLAMA_URL (default: http://localhost:11434) |
| OpenAI | --provider openai | OPENAI_API_KEY |
| Anthropic | --provider anthropic | ANTHROPIC_API_KEY |
| DeepSeek | --provider deepseek | DEEPSEEK_API_KEY |
| Groq | --provider groq | GROQ_API_KEY |

Set keys in .env at the project root.

---

## SR Pipeline

    notepad sr\config\prisma_criteria.yaml
    copy *.pdf sr\data\uploads\
    python sr\main.py --pdf-dir sr\data\uploads --effect-measure SMD

SR outputs:
  sr/data/screened/screening_log.csv
  sr/data/extracted/extracted_data.csv
  sr/outputs/reports/systematic_review.html
  sr/outputs/reports/systematic_review.docx

---

## Word Limits

| Mode / Section | Limit |
|----------------|-------|
| Appraisal full report | 1500 words |
| Appraisal plain-language summary | 200 words |
| Search clinical topic report | 1500 words |
| Writing report | 1500 words |

---

## AI Roles

| Mode | Roles |
|------|-------|
| coding | Builder, Reviewer, Tester |
| writing | Writer, Editor, QA |
| rct_search | Formulator, Searcher, Validator |
| search | Researcher |
| appraisal | Appraiser, Methodologist, Summariser |

---

## Environment Variables (.env)

    OLLAMA_URL=http://localhost:11434
    OLLAMA_MODEL=llama3
    OPENAI_API_KEY=sk-...
    ANTHROPIC_API_KEY=sk-ant-...
    DEEPSEEK_API_KEY=sk-...
    GROQ_API_KEY=gsk_...
    UPLOAD_DIR=uploads

---

## Project Structure

    AI_kcMedicalResearch/
      src/
        main.py          <- entry point, all modes
        rag.py           <- RAG indexing and retrieval
      sr/
        main.py          <- SR pipeline entry point
        config/
          prisma_criteria.yaml
      docs/              <- guidance files per mode
      uploads/           <- working documents per mode
      reports/           <- all generated reports
      tests/
        test_main.py     <- 258 tests
      ai/                <- role prompt files
      .env               <- API keys (not committed)
      requirements.txt

---

## Running Tests

    python -m pytest -v
    python -m pytest --tb=short -q
    python -m pytest -k appraisal
    python test_live_providers.py

Current status: 258 tests, 0 failures, 87% coverage

---

## Known Gaps

- SR Streamlit UI not yet integrated
- PDF OCR not supported (text-based PDFs only)
- WeasyPrint requires native Windows libs for PDF export
- GitHub Actions CI not yet configured
- Interactive input() paths not fully unit-tested