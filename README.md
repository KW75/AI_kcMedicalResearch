@'
# AI Automation Tool

A multi-mode AI assistant for coding, writing, medical research, systematic review, and critical appraisal.
Runs locally via Ollama or via cloud providers (OpenAI, Anthropic, DeepSeek, Groq).

## Quick Start

```powershell
cd D:\ai-automation-tool
python src\main.py                          # coding mode (Ollama default)
python src\main.py --mode writing           # writing mode
python src\main.py --mode rct_search        # RCT search strategy
python src\main.py --mode search            # medical topic search (PubMed)
python src\main.py --mode appraisal         # critical appraisal of articles
python src\main.py --mode sr                # systematic review pipeline launcher
python src\main.py --provider deepseek      # use DeepSeek instead of Ollama
python src\main.py --dry-run                # simulate without AI calls
python src\main.py --list-roles             # show roles and prompt files
python src\main.py --help-guide             # open HTML flashcard guide

Modes
Mode 	Flag 	Roles 	Input 	Output
Coding 	--mode coding 	Builder, Reviewer, Tester 	.py/.js/.ts files in uploads/coding/ 	Session transcript in reports/
Writing 	--mode writing 	Writer, Editor, QA 	.md/.txt/.pdf in uploads/writing/ 	Report in reports/
RCT Search 	--mode rct_search 	Formulator, Searcher, Validator 	docs/rct_search/pico-framework.md 	Search links in reports/
Search 	--mode search 	Researcher 	Interactive topic prompt 	PubMed report in reports/
Appraisal 	--mode appraisal 	Appraiser, Methodologist, Summariser 	Articles in uploads/appraisal/ 	Appraisal report in reports/
SR 	--mode sr 	Full pipeline 	PDFs in sr/data/uploads/ 	DOCX + HTML + forest plot
Providers
Provider 	Flag 	Notes
Ollama 	--provider ollama 	Default — runs locally, no API key needed
OpenAI 	--provider openai 	Requires OPENAI_API_KEY in .env
Anthropic 	--provider anthropic 	Requires ANTHROPIC_API_KEY in .env
DeepSeek 	--provider deepseek 	Requires DEEPSEEK_API_KEY in .env — geo-unrestricted
Groq 	--provider groq 	Requires GROQ_API_KEY in .env — fast inference
SR Pipeline (Systematic Review)

The SR pipeline lives in sr/ and runs independently of the main tool. It uses the Anthropic Files API to screen, extract, and meta-analyse RCT PDFs.

# 1. Edit PICO criteria
notepad sr\config\prisma_criteria.yaml

# 2. Place RCT PDFs
copy *.pdf sr\data\uploads\

# 3. Set API key
$env:ANTHROPIC_API_KEY = "sk-ant-..."

# 4. Run pipeline
python sr\main.py --pdf-dir sr\data\uploads --effect-measure SMD

Outputs:

    sr/data/screened/screening_log.csv
    sr/data/extracted/extracted_data.csv
    sr/data/extracted/rob2_assessment.csv
    sr/data/results/meta_analysis_results.csv
    sr/outputs/figures/forest_plot.png
    sr/outputs/reports/systematic_review.html ← full record
    sr/outputs/reports/systematic_review.docx ← summary

    ⚠️ Research accelerator only. All outputs require human verification before publication. PRISMA 2020 requires dual independent reviewers — this pipeline provides single-reviewer LLM screening only.

RAG (Retrieval-Augmented Generation)

Place files in the relevant uploads folder before starting a session. Supported formats: .txt, .md, .pdf, .py, .js, .ts, .json, .yaml URLs on their own line in .txt/.md files are fetched and indexed automatically.
Mode 	Upload folder
coding 	uploads/coding/
writing 	uploads/writing/
rct_search 	uploads/rct_search/
appraisal 	uploads/appraisal/
search 	uploads/search/
Environment Variables (.env)

OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-5
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_MODEL=deepseek-chat
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.3-70b-versatile
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text

Project Structure

ai-automation-tool/
├── src/
│   ├── main.py              # main CLI — all interactive modes
│   └── rag.py               # RAG: chunking, embedding, ChromaDB
├── sr/                      # SR pipeline (standalone)
│   ├── main.py              # pipeline orchestrator (6 stages)
│   ├── config/              # prisma_criteria.yaml, config.yaml
│   ├── data/                # uploads/, screened/, extracted/, results/
│   ├── outputs/             # figures/, reports/
│   └── src/                 # upload/, screening/, extraction/,
│                            # analysis/, visualization/, reporting/
├── ai/                      # prompt files (one per role)
├── docs/
│   ├── flashcard-help.html  # interactive help guide
│   ├── coding/              # PRD, architecture, coding standards
│   ├── writing/             # project brief, style guide
│   └── rct_search/          # PICO framework, database guide
├── uploads/                 # RAG input files (git-ignored)
├── reports/                 # session outputs (git-ignored)
├── tests/
│   ├── test_main.py         # 205 tests for src/main.py
│   └── test_sr.py           # 21 tests for sr/ pipeline
├── .env                     # API keys (git-ignored)
└── requirements.txt         # main tool dependencies

Tests

python -m pytest -v                                    # run all 226 tests
python -m pytest tests/test_main.py -v                 # main tool only
python -m pytest tests/test_sr.py -v                   # SR pipeline only
python -m pytest -v --cov=src --cov-report=term-missing # with coverage

Current status: 226 tests · 0 failures · 87% coverage
AI Roles
Mode 	Roles
coding 	Builder, Reviewer, Tester
writing 	Writer, Editor, QA
rct_search 	Formulator, Searcher, Validator
search 	Researcher
appraisal 	Appraiser, Methodologist, Summariser
sr 	SR Methodologist (advisor role in appraisal mode)
Known Gaps

    SR Streamlit UI (sr/src/ui/app.py) not yet integrated
    SR placeholder modules: heterogeneity.py, funnel_plot.py, prisma_flow.py, cochrane_search.py, embase_search.py
    PDF OCR not supported (text-based PDFs only)
    WeasyPrint PDF output requires native Pango/GObject libraries on Windows
    Interactive input() paths not unit-tested
    Writing docs templates need project-specific content '@ | Set-Content -Path "D:\ai-automation-tool\README.md" -Encoding UTF8

