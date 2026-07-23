**Part 3 — Update `HANDOFF.md`:**

```powershell
@'
# AI kcMedical Research — HANDOFF

## Project Location
`D:\AI_kcMedicalResearch`
GitHub: https://github.com/KW75/AI_kcMedicalResearch

## Current Status
- **Step 64 complete** — commit `f8b588a`
- **226 tests, 0 failures, 87% coverage**
- All six modes implemented and tested

## Completed Steps

| Step | Description |
|---|---|
| 1–51 | Core tool: arg parsing, providers, session management, transcripts |
| 52–55 | Fix dispatcher tests, add `--list-roles`, update README |
| 56 | Add `rct_search` mode: Formulator, Searcher, Validator |
| 57 | README update: rct_search docs, workflow diagram, role table |
| 58 | RAG module (`src/rag.py`): chunking, embedding, ChromaDB, session collections |
| 59 | Add DeepSeek and Groq providers, fix `parse_args` signature |
| 60 | Writing report generation, appraisal mode stub, rct_search PICO reminder |
| 61 | Code file support in RAG, Methodologist and Summariser roles |
| 62 | URL fetching in RAG, rct_search link output (`save_rct_search_links`) |
| 63 | Medical search mode with PubMed E-utilities fetch, Researcher role |
| 64 | SR pipeline integration: `sr/` module, 21 SR tests, `run_sr_launcher` stub |

## Test Summary

| File | Tests | Coverage |
|---|---|---|
| `tests/test_main.py` | 205 | `src/main.py` 87% |
| `tests/test_sr.py` | 21 | `sr/` pure-Python logic |
| **Total** | **226** | **87% overall** |

## Six Modes

| Mode | Flag | Key function | Output |
|---|---|---|---|
| coding | `--mode coding` | `main()` | `reports/session_*.md` |
| writing | `--mode writing` | `main()` / `generate_writing_report()` | `reports/writing_report_*.md` |
| rct_search | `--mode rct_search` | `main()` + `save_rct_search_links()` | `reports/rct_search_*.md` |
| search | `--mode search` | `run_search_mode()` | `reports/search_*.md` |
| appraisal | `--mode appraisal` | `main()` | `reports/session_*.md` |
| sr | `--mode sr` | `run_sr_launcher()` → `sr/main.py` | `sr/outputs/reports/` |

## Five Providers

| Provider | Constant | API key env var |
|---|---|---|
| ollama | `call_ollama_provider` | none (local) |
| openai | `call_openai_provider` | `OPENAI_API_KEY` |
| anthropic | `call_anthropic_provider` | `ANTHROPIC_API_KEY` |
| deepseek | `call_deepseek_provider` | `DEEPSEEK_API_KEY` |
| groq | `call_groq_provider` | `GROQ_API_KEY` |

## SR Pipeline (`sr/`)

Standalone PRISMA 2020 / Cochrane Handbook v6.5 pipeline.
Uses Anthropic Files API — requires `ANTHROPIC_API_KEY`.

**Run:**
```powershell
python sr\main.py --pdf-dir sr\data\uploads --effect-measure SMD

Stages:

    Upload (SHA-256 dedup, SQLite registry)
    Relevance screening (INCLUDE/EXCLUDE/UNCERTAIN + PICO match)
    Data extraction (PICO-anchored, null not fabricated) 3.5. RoB 2.0 (five Cochrane domains)
    Meta-analysis (DerSimonian-Laird RE, Hedges g fallback)
    Forest plot (matplotlib, weight-scaled)
    Reports (DOCX skeleton + full HTML + PDF if WeasyPrint available)

Config: Edit sr/config/prisma_criteria.yaml before every new review.

Placeholder modules (Phase 2): heterogeneity.py, funnel_plot.py, prisma_flow.py, cochrane_search.py, embase_search.py
Key Design Decisions

    SR pipeline is a sibling module (sr/) not merged into src/main.py — keeps heavy deps (scipy, PyMuPDF, WeasyPrint) isolated
    Providers are patch-able via PROVIDERS dict — enables unit testing without API calls
    RAG is per-session and mode-specific — ChromaDB collection named {mode}_{session_id}
    URL fetching in RAG: bare URLs in .txt/.md files are fetched and indexed at session start
    --mode sr prints launch instructions; actual pipeline runs via python sr/main.py
    effect_measure resolution: CLI flag > prisma_criteria.yaml field > fallback OR (with warning)
    DataExtractor anchors on review PICO outcome, not paper's own primary outcome
    WeasyPrint failure catches any Exception (not just ImportError) — covers Windows DLL errors

File Structure

AI_kcMedicalResearch/
├── src/main.py              # 628 statements, 87% coverage
├── src/rag.py               # 159 statements, 87% coverage
├── sr/                      # SR pipeline
│   ├── main.py
│   ├── config/prisma_criteria.yaml   ← edit per review
│   ├── data/uploads/                 ← place PDFs here
│   └── src/{upload,screening,extraction,analysis,visualization,reporting}/
├── ai/                      # 15 prompt files
├── docs/flashcard-help.html # interactive help guide
├── tests/test_main.py       # 205 tests
├── tests/test_sr.py         # 21 tests
└── requirements.txt

Run Commands

# Main tool
python src\main.py                          # coding (Ollama)
python src\main.py --mode writing --report  # writing report
python src\main.py --mode rct_search        # RCT search
python src\main.py --mode search            # PubMed search
python src\main.py --mode appraisal         # article appraisal
python src\main.py --mode sr                # SR launcher
python src\main.py --provider deepseek      # DeepSeek provider
python src\main.py --dry-run                # no AI calls
python src\main.py --help-guide             # open HTML guide

# SR pipeline
python sr\main.py --pdf-dir sr\data\uploads --effect-measure SMD

# Tests
python -m pytest -v --cov=src --cov-report=term-missing

Known Gaps / Next Steps

    SR Streamlit UI (sr/src/ui/app.py) not integrated into main tool
    SR placeholder modules need Phase 2 implementation
    GitHub Actions CI (Step 65) — not yet added
    PDF OCR not supported (text-layer PDFs only)
    WeasyPrint requires Pango/GObject native libs on Windows for PDF output
    Writing docs templates need project-specific content
    nomic-embed-text must be pulled manually: ollama pull nomic-embed-text
    Interactive input() paths not unit-tested (covered by dry-run tests only) '@ | Set-Content -Path "D:\AI_kcMedicalResearch\HANDOFF.md" -Encoding UTF8


---

**Part 4 — Commit the cleanup and docs:**

```powershell
cd D:\AI_kcMedicalResearch
git add .
git commit -m "Step 64 docs: update README and HANDOFF for all six modes, remove fix helper scripts"
git push origin main

Paste the confirmation and I will deliver the updated docs/flashcard-help.html as the final piece.
