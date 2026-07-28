AI kcMedicalResearch — Project Handoff Document Generated: 2026-07-28

Project Overview

AI kcMedicalResearch is a Python-based CLI research assistant that connects to multiple LLM providers (Ollama, Qwen, Groq, DeepSeek) and runs specialised AI pipelines for medical research tasks. The project is structured as a launcher-driven menu system with independent mode engines in src/modes/.

Repository

    URL: https://github.com/KW75/AI_kcMedicalResearch.git
    Branch: main
    Latest commit: de4b782
    Entry point: launcher.py
    Core engine: src/main.py
    Mode engines: src/modes/coding.py, src/modes/writing.py, src/modes/appraisal.py

Completed Modes

Coding Mode (src/modes/coding.py) is fully implemented with three sub-modes. The Builder sub-mode runs a multi-iteration pipeline: Builder agent generates code → Reviewer agent checks it → Tester agent validates it, with up to 5 iterations per loop. The Reviewer sub-mode runs standalone code review against guidelines in docs/coding/. The Tester sub-mode runs standalone testing. All three sub-modes auto-load input files from input/coding/, write outputs to output/coding/, and write iteration reports to reports/coding/.

Writing Mode (src/modes/writing.py) implements a two-track pipeline (Topic track and Article track) with three sub-modes. The Writer sub-mode generates new content. The Editor sub-mode edits existing documents loaded from input/writing/. The QA sub-mode performs quality assurance review. Outputs go to output/writing/ as both .md and .docx, with process logs in reports/writing/. Guidelines are loaded from docs/writing/topic/ and docs/writing/article/.

Appraisal Mode (src/modes/appraisal.py) implements CASP + GRADE + optional custom checklist appraisal of research articles. Input articles (PDF, DOCX, MD) are loaded from input/appraisal/. Full appraisal reports are written to output/appraisal/ as both .md and .docx. Process logs go to reports/appraisal/. Guidelines are in docs/appraisal/ including appraisal-guide.md, scoring-criteria.md, grade-guidance.md, and custom-checklist.md.

Key Architecture Decisions

The project uses a strict folder convention across all modes: input/{mode}/ for source files, output/{mode}/ for final deliverables, reports/{mode}/ for process logs and iteration reports. The input/ folder is excluded from Git via .gitignore. All output filenames include a timestamp in the format YYYYMMDD_HHMMSS and the source file stem, for example EDITOR_ARTICLE_mystudy_20260728_133857.md.

The _load_input_files() function in writing.py and appraisal.py returns a list of (stem, content, suffix) tuples. PDF reading uses PyMuPDF (fitz). DOCX reading uses python-docx. Both are installed in the .venv.

The call_llm_fn is injected from src/main.py into each mode engine, keeping mode engines fully decoupled from provider selection logic. Provider selection happens once in the launcher and is passed down through handle_*_mode() functions.

Coding Mode — Truncation Handling

This was the major debugging effort of this session. The _ensure_complete() function in coding.py detects and repairs truncated LLM output. It is called in three places: after the initial Builder generation (line 652), after each Tester loop regeneration (line 714), and as a final safety net immediately before the output file is written (line 779).

The _is_truncated() function detects truncation by content type. For HTML files it checks that the last non-empty line equals </html> exactly, and that all <script> blocks are balanced (using regex extraction and brace counting). For Python files it checks that the last line does not end with a hanging operator or open bracket. For generic JS/CSS it checks for unbalanced braces.

The continuation prompt deliberately omits any instruction to close the file. The LLM is asked to write only the missing middle code. After all continuation attempts finish, _ensure_complete() appends the correct closing sequence (</script>, </body>, </html>) if still missing. This prevents the earlier bug where the LLM would append </html> to each continuation, making _is_truncated() return False prematurely on the next check.

Commit History (This Session)
Commit 	Description
9d49c7e 	Remove stray auto_load_input_files() call in writing mode
bb2d5f4 	Launcher checks input/ folder before each session
d351986 	Appraisal mode engine added
11563e6 	No-truncation rules in Builder system prompt
3bb5938 	Single-file output rule enforced in Builder prompt
8690d47 	_ensure_complete() continuation calls added
f63da27 	Stronger continuation prompt with 800-char context
60c9220 	_is_truncated() validates <script> block braces
6bef6f5 	_ensure_complete() strips closing tags from continuations
aa541d3 	_ensure_complete() added after tester regen and before final write
db2d8b2 	Builder scratch prompt enforces DOM/JS id matching
de4b782 	Repo housekeeping — .gitignore updated

Test Suite

    Total tests: 300
    Status: All 300 passing as of commit de4b782
    Run command: .venv\Scripts\python.exe -m pytest --tb=short -q
    Test file: tests/test_main.py

Pending / Not Started

The following modes are specified but not yet implemented: Search mode, RCT Search mode, and SR Pipeline mode. The Appraisal mode has not yet had a live smoke test with a real article. CRLF warnings on Windows (LF will be replaced by CRLF) are cosmetic and do not affect functionality — .gitattributes enforces eol=lf for Python and Markdown files but the warning still appears on some files during git add.

Environment

    Python: 3.11
    Virtual environment: D:\AI_kcMedicalResearch\.venv\
    Key packages: python-docx, pymupdf (fitz), pytest, requests
    Activate venv: .venv\Scripts\Activate.ps1
    Project root: D:\AI_kcMedicalResearch\

Next Session Starting Points

Option A is to smoke test Appraisal mode with a real PDF article placed in input/appraisal/. Option B is to begin the Search mode specification. Option C is to begin the RCT Search mode specification. Option D is to begin the SR Pipeline mode specification which chains Search → Appraisal → Writing into a single automated workflow.
