# AI kcMedical Research - HANDOFF

## Project Location
D:\\AI_kcMedicalResearch
GitHub: https://github.com/KW75/AI_kcMedicalResearch

## Current Status
- Step 69 complete - commit ea06c40
- VERSION 2.1.0
- 248 tests, 0 failures, 87% coverage
- All six modes implemented and tested

## Completed Steps

| Step | Description | Commit |
|---|---|---|
| 1-51 | Core tool: arg parsing, providers, session management, transcripts | - |
| 52-55 | Fix dispatcher tests, add --list-roles, update README | - |
| 56 | Add rct_search mode: Formulator, Searcher, Validator | - |
| 57 | README update: rct_search docs, workflow diagram, role table | - |
| 58 | RAG module (src/rag.py): chunking, embedding, ChromaDB | - |
| 59 | Add DeepSeek and Groq providers, fix parse_args signature | - |
| 60 | Writing report generation, appraisal mode stub, rct_search PICO reminder | - |
| 61 | Code file support in RAG, Methodologist and Summariser roles | - |
| 62 | URL fetching in RAG, rct_search link output | - |
| 63 | Medical search mode with PubMed E-utilities fetch, Researcher role | - |
| 64 | SR pipeline integration: sr/ module, 21 SR tests, run_sr_launcher | c2b4e46 |
| 65 | Search mode runtime prompt (paper vs topic), appraisal 1500-word limit, summariser word limits | 09bad54 |
| 65b | Appraisal mode word limit increased to 1500 words | e974005 |
| 65c | Researcher prompt word limits aligned to summariser format | 649b521 |
| 66 | Write mode: PDF/DOCX input (PyMuPDF), .docx output, 1500-word limit | d1219f5 |
| 67 | Code revision pipeline: --revise/--role flags, Builder->Review->Test, 15 new tests | 2326a59 |
| 68 | RCT search single-pass pipeline: Formulator->Searcher->Validator, 9 new tests | 5abec06 |
| 69 | Rename project to AI_kcMedicalResearch, bump VERSION 2.0.0->2.1.0 | ea06c40 |
| 70 | Update README and HANDOFF for all six modes, new flags, word limits | pending |

## Test Summary

| File | Tests | Coverage |
|---|---|---|
| tests/test_main.py | 227 | src/main.py 87% |
| tests/test_sr.py | 21 | sr/ pure-Python logic |
| Total | 248 | 87% overall |

## Six Modes

| Mode | Flag | Key function | Output |
|---|---|---|---|
| coding | --mode coding | main() | reports/session_*.md |
| coding revise | --mode coding --revise | generate_code_revision() | reports/code_revision_*.md + .docx |
| writing | --mode writing | generate_writing_report() | reports/writing_report_*.md + .docx |
| rct_search | --mode rct_search | run_rct_search_pipeline() | reports/rct_search_*.md + .docx |
| search | --mode search | run_search_mode() | reports/search_*.md + .docx |
| appraisal | --mode appraisal | main() | reports/session_*.md |
| sr | --mode sr | run_sr_launcher() | sr/outputs/reports/ |

## Word Limits

| Mode / Section | Limit |
|---|---|
| Appraisal full report | 1500 words |
| Summariser plain-language section | 200 words |
| Summariser full report | 1500 words |
| Search paper plain-language section | 200 words |
| Search paper full report | 1500 words |
| Search clinical topic | Thorough but concise |
| Writing report | 1500 words |

## Five Providers

| Provider | API key env var |
|---|---|
| ollama | none (local) |
| openai | OPENAI_API_KEY |
| anthropic | ANTHROPIC_API_KEY |
| deepseek | DEEPSEEK_API_KEY |
| groq | GROQ_API_KEY |

## Key Design Decisions

- SR pipeline is a sibling module (sr/) not merged into src/main.py - keeps heavy deps isolated
- Providers are patch-able via PROVIDERS dict - enables unit testing without API calls
- RAG is per-session and mode-specific - ChromaDB collection named {mode}_{session_id}
- URL fetching in RAG: bare URLs in .txt/.md files are fetched and indexed at session start
- --mode sr prints launch instructions; actual pipeline runs via python sr/main.py
- Search mode asks at runtime: paper (structured appraisal) vs clinical topic (reviewer format)
- Code revision (--revise) outputs suggested changes only - developer applies manually
- RCT search pipeline is single-pass: Formulator->Searcher->Validator, no appraisal stage
- All report modes output both .md and .docx

## Run Commands

  python src/main.py                                   # coding (Ollama)
  python src/main.py --mode writing --report           # writing report
  python src/main.py --mode writing                    # interactive writing
  python src/main.py --mode rct_search                 # RCT search pipeline
  python src/main.py --mode search                     # PubMed search
  python src/main.py --mode appraisal                  # article appraisal
  python src/main.py --mode sr                         # SR launcher
  python src/main.py --mode coding --revise            # code revision
  python src/main.py --mode coding --revise --role Reviewer
  python src/main.py --provider deepseek               # DeepSeek provider
  python src/main.py --dry-run                         # no AI calls
  python src/main.py --help-guide                      # open HTML guide
  python sr/main.py --pdf-dir sr/data/uploads --effect-measure SMD
  python -m pytest -v --cov=src --cov-report=term-missing

## Known Gaps / Next Steps

- SR Streamlit UI (sr/src/ui/app.py) not integrated into main tool
- SR placeholder modules need Phase 2 implementation
- GitHub Actions CI not yet added
- PDF OCR not supported (text-layer PDFs only)
- WeasyPrint requires Pango/GObject native libs on Windows for PDF output
- Writing docs templates need project-specific content
- nomic-embed-text must be pulled manually: ollama pull nomic-embed-text
- Interactive input() paths not unit-tested (covered by dry-run tests only)
- Step 71: move all modes to file-based I/O
- Step 72: writing templates, live provider API key testing