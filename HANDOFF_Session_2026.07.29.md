AI kcMedical Research — Session Handoff

Date: 2026-07-30 | Branch: main | Latest commit: 81e16a4
Session Summary:

This session completed the RCT Search pipeline (Stage 4) and resolved all related bugs. The pipeline is now fully operational end-to-end from PICO input through PubMed fetch, AI ranking, and split report generation.
Commits This Session:
Commit 	Description
1913c8b 	PICO from input folder, P/I/C/O parser, PICO-based PubMed query, split intermediate/final reports
c6bc6d6 	Generate ranked articles DOCX in output/rct_search/ for easy review
e0971d2 	Show all 20 articles sorted by score, add ranking explanation note
46289fc 	Fix retmax hardcoded to 5, add ranking fallback and diagnostics
5bc5fed 	Sanitise PICO terms — strip parenthetical qualifiers and special chars
d3c0849 	Strengthen ranking prompt with few-shot examples for Qwen/Ollama
cdbab6f 	Remove debug diagnostic prints
81e16a4 	Update flashcard-help.html — 291 tests, 6 providers, RCT Stage 4
Current State:

Tests: 291 passed, 9 skipped, 0 failed Coverage: 65% (src/main.py), 33% overall Providers: ollama, openai, anthropic, deepseek, groq, qwen (6 total) Modes: coding, writing, rct_search, appraisal, search, sr (6 total)
RCT Search Pipeline — Final Behaviour:

Stage 1 — PICO Input:

    Scans input/rct_search/ for pico_*.json first, falls back to output/rct_search/
    Offers numbered import menu (up to 5 files) or manual P/I/C/O entry
    PICO terms sanitised before PubMed query — parenthetical qualifiers and special characters stripped

Stage 2 — AI Pipeline (Formulator → Searcher → Validator):

    Formulator structures topic into formal PICO question, saves pico_*.json to output/rct_search/
    Searcher builds Boolean search strings for 7 SR databases
    Validator checks alignment, returns APPROVED FOR DOWNLOAD or REQUIRES REFINEMENT

Stage 3 — PubMed Fetch + AI Ranking:

    Fetches up to 20 articles via NCBI E-utilities (no API key required)
    AI ranks each article 1–10 for PICO relevance using few-shot structured prompt
    Fallback ranking by fetch order if AI returns unparseable format
    pico_*.json updated with ranked_articles list

Stage 4 — Split Output:
File 	Location 	Contents
rct_search_*.md 	reports/rct_search/ 	Full transcript — all stage outputs
rct_search_*.docx 	reports/rct_search/ 	Full Word report (~38 KB)
rct_search_*.md 	output/rct_search/ 	Lean — Ranked Article List + Final Status
rct_search_*.docx 	output/rct_search/ 	Ranked article list Word doc for easy review
pico_*.json 	output/rct_search/ 	PICO fields + ranked_articles with scores
Known Issues / Not Yet Done:

    src/modes/appraisal.py — 0% test coverage
    src/modes/search.py — 0% test coverage
    src/modes/writing.py — 0% test coverage
    src/ui/app.py — 0% test coverage
    SR pipeline smoke test not yet run end-to-end with real PDFs
    PubMed query does not yet filter for RCT-only articles (AND randomized controlled trial[pt] not applied)
    PICO JSON not yet auto-copied from output/rct_search/ to input/sr/ after RCT Search completes

Suggested Next Steps:

    Add RCT filter to PubMed query — append AND randomized controlled trial[pt] to _pubmed_query in run_rct_search_pipeline so only RCTs are returned
    SR pipeline smoke test — place 3–5 PDFs in input/sr/, run launcher option 6, verify all 6 stages complete
    Auto-copy PICO JSON to input/sr/ — after RCT Search completes, offer to copy pico_*.json to input/sr/ so SR pipeline can import it directly
    Increase test coverage — add tests for appraisal.py, search.py, writing.py modes
    PICO JSON viewer in launcher — add a menu option to display the latest pico_*.json without running the full pipeline

File Structure Reference:

D:\AI_kcMedicalResearch\
├── src\
│   ├── main.py                  # core pipeline (65% coverage)
│   ├── rag.py                   # RAG indexing (70% coverage)
│   ├── modes\
│   │   ├── coding.py
│   │   ├── writing.py
│   │   ├── appraisal.py
│   │   └── search.py
│   └── ui\
│       └── app.py               # Streamlit SR UI
├── input\                       # per-mode input folders
│   └── rct_search\              # place pico_*.json here to import
├── output\                      # deliverables
│   └── rct_search\              # lean MD + DOCX + pico_*.json
├── reports\                     # full transcripts
│   └── rct_search\              # full MD + DOCX
├── docs\
│   ├── flashcard-help.html      # updated this session
│   └── rct_search\              # pico-framework, database-guide, validation-criteria
├── ai\                          # prompt files per role
├── tests\                       # 291 tests
├── launcher.py                  # interactive menu
└── conftest.py

Quick Start for Next Session:

cd D:\AI_kcMedicalResearch
.venv\Scripts\python.exe -m pytest --tb=short -q   # confirm 291 passed
git log --oneline -8                                # confirm latest commits
.venv\Scripts\python.exe launcher.py               # start launcher

