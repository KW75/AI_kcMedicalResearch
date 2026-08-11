# Product Requirements Document

## Project Name
AI kcMedicalResearch - Multi-Mode AI Pipeline for Medical Research

## Version
2.3.1

## Goal
A local-first Python application that assists medical students and researchers
with structured research workflows. The tool provides six specialised modes,
each implementing a multi-agent AI pipeline where roles collaborate in sequence
to produce high-quality, evidence-based output.

The application runs locally with Ollama (no cloud required) but supports
multiple cloud AI providers for enhanced quality when available.

## Target Users
- Medical students learning research methodology
- Clinical researchers performing literature searches and appraisals
- Academic writers producing evidence-based reports

## Supported Modes

### 1. Coding Mode
Three-agent pipeline for code generation and review.
- Builder AI - generates or modifies code based on task description
- Reviewer AI - reviews code for bugs, standards compliance, and improvements
- Tester AI - generates test plans and assesses deployment readiness
- Iterative loop: Builder > Reviewer > Tester (max 3 iterations)

### 2. Writing Mode
Three-agent pipeline for medical writing.
- Writer AI - generates articles, summaries, or reports from a project brief
- Editor AI - reviews for clarity, structure, tone, accuracy, and referencing
- QA AI - fact-checks, applies QA checklist, assesses publication readiness

### 3. Appraisal Mode
Three-agent pipeline for critical appraisal of research papers.
- Appraiser AI - produces a structured 7-section appraisal report
- Methodologist AI - applies risk-of-bias scoring (RoB 2, CASP, AMSTAR 2)
- Summariser AI - produces a plain-language summary (max 200 words)

### 4. Search Mode
Single-agent mode for medical literature searching.
- Researcher AI - searches PubMed, produces structured citation reports
- Supports paper search (specific article) and clinical topic search (narrative)

### 5. RCT Search Mode
Three-agent pipeline for building systematic review search strategies.
- Formulator AI - structures research topic into formal PICO question
- Searcher AI - builds Boolean search strategies across 7 SR databases
- Validator AI - checks PICO alignment and database coverage

### 6. Systematic Review (SR) Mode
Self-contained pipeline for full systematic review workflow.
- Screening, data extraction, risk-of-bias assessment, forest plots
- Separate UI (Streamlit-based)

## AI Provider Support

| Provider | Type | Default Model | API Key Required |
|----------|------|---------------|-----------------|
| Ollama | Local | Auto-detected (largest non-embedding model) | No |
| Qwen/DashScope | Cloud | qwen-plus-latest | DASHSCOPE_API_KEY |
| DeepSeek | Cloud | deepseek-chat | DEEPSEEK_API_KEY |
| OpenAI | Cloud | gpt-4o-mini | OPENAI_API_KEY |
| Anthropic | Cloud | claude-sonnet-4-20250514 | ANTHROPIC_API_KEY |
| Groq | Cloud | llama-3.1-8b-instant | GROQ_API_KEY |

Provider selection: --provider ollama|qwen|deepseek|openai|anthropic|groq

## Key Features
- Ollama auto-detection: queries /api/tags, selects largest local model
- All model names configurable via .env (no hard-coded versions)
- RAG support via document reader and embedding utilities
- Session transcripts saved to reports/ folder
- Cross-platform: Windows, macOS, Linux
- Interactive launcher menu (scripts/launcher.py)
- Web UI available via Streamlit (SOURCE_CODE/ui/app.py)
- Docker support for deployment

## Non-Goals (current version)
- Multi-agent parallel execution
- Real-time clinical data feeds
- Automated paper downloading (legal constraints)
- GitHub Actions CI/CD (planned)

## Success Criteria
- All modes produce structured, standards-compliant output
- 275+ tests passing with 0 warnings
- Ollama demo completes Builder to Reviewer to Tester in under 15 minutes
- Provider switching works cleanly via --provider flag
- Guidelines from docs/ are injected into prompts automatically
