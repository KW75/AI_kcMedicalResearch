# Product Requirements Document

## Project Name
AI kcMedicalResearch - Multi-Mode AI Pipeline for Medical Research and
Clinical Decision Support

## Version
3.0.0 (target release with SaMD mode; the code reports 2.7.0 until then)

## Goal
A local-first Python application that helps medical students, researchers
and doctors with structured research and clinical workflows. It provides
eight modes, each built on an AI pipeline, with a ninth (Data Analysis)
planned.

The application runs locally with Ollama by default, so confidential
documents and patient data stay on the machine. Cloud providers are
optional, chosen per job, and run only after the user confirms where the
data will be sent.

## Target Users
- Medical students learning research methodology
- Clinical researchers performing literature searches, appraisals and
  systematic reviews
- Academic writers producing evidence-based reports
- Doctors seeking decision support on a clinical case (SaMD mode)

## Supported Modes

### 1. Coding Mode
Three-agent pipeline for code generation and review.
- Builder AI - generates or modifies code based on task description
- Reviewer AI - reviews code for bugs, standards compliance, and improvements
- Tester AI - generates test plans and assesses deployment readiness
- Iterative loop: Builder > Reviewer > Tester (max 3 iterations)

### 2. Writing Mode
One AI pass that writes, edits and reviews.
- Tracks: Topic (800 words), Article (3,500), Report (500), Synopsis (1,500,
  one document from all files in input/writing/)
- Output: the document (.docx and .md) and a separate review file

### 3. Appraisal Mode
Three-agent pipeline for critical appraisal of research papers.
- Appraiser AI - produces a structured 7-section appraisal report
- Methodologist AI - applies risk-of-bias scoring (RoB 2, CASP, AMSTAR 2)
- Summariser AI - produces a plain-language summary (max 200 words)

### 4. Search Mode
Single-agent mode for medical literature searching.
- Researcher AI - searches PubMed and Europe PMC, produces structured
  citation reports
- Supports paper search (specific article) and clinical topic search (narrative)

### 5. RCT Search Mode
Three-agent pipeline for building systematic review search strategies.
- Formulator AI - structures research topic into formal PICO question
- Searcher AI - builds Boolean search strategies across 7 SR databases
- Validator AI - checks PICO alignment and database coverage

### 6. Systematic Review (SR) Mode
Self-contained pipeline for the systematic review workflow.
- Screening, data extraction, risk-of-bias assessment, forest plots
- Reviewer-assisted: reviewer values are required before pooling

### 7. OCR Mode
Reads PDFs, images, .txt and .docx files from input/ocr/.
- Text layer read directly; scanned pages sent to a local vision model
- One record per file plus a SUMMARY (Papers) or one SYNOPSIS of all files

### 8. SaMD Mode (Software as a Medical Device)
Clinical decision support for doctors (launcher menu 9).
- Input: clinical data, clinical questions, lab results and clinical
  photos or photos of lab reports in input/samd/; the doctor can add
  extra information in the terminal
- Output: working diagnosis, ranked differential diagnoses with supporting
  and contradicting findings, red flags, suggested next tests and other
  clinically important information
- Results shown in the browser (local .html file) and saved to
  output/samd/ as .html, .md and .docx; intermediate steps saved to
  reports/samd/
- Every lab value cited must appear in the transcribed source, else it is
  flagged
- Intended use: decision support for a clinician, for research and
  evaluation; not a cleared or certified medical device. The clinician
  makes every decision, and every output says so

## AI Provider Support

| Provider | Type | Default Model | API Key Required |
|----------|------|---------------|-----------------|
| Ollama | Local (default) | OLLAMA_MODEL in .env, else gemma4:e4b | No |
| Qwen/DashScope | Cloud | qwen-plus-latest | DASHSCOPE_API_KEY |
| DeepSeek | Cloud | deepseek-flash | DEEPSEEK_API_KEY |
| OpenAI | Cloud | gpt-4o-mini | OPENAI_API_KEY |
| Anthropic | Cloud | claude-sonnet-5 | ANTHROPIC_API_KEY |
| Groq | Cloud | llama-3.3-70b-versatile | GROQ_API_KEY |

Provider selection: --provider ollama|qwen|deepseek|openai|anthropic|groq.
Vision modes (SR, OCR, SaMD) accept Ollama, Qwen and OpenAI only.

## Key Features
- Local first: Ollama is the default and never falls back to cloud
- Cloud gate: every cloud job lists its destinations and needs a typed "y"
  or --confirm-cloud; consent is never saved
- Local model picker; shared vision picker for SR, OCR and SaMD
- Time limit per AI call: 15, 30 or 60 minutes, or none
- All model names configurable via .env
- Cross-platform: Windows, macOS, Linux
- Interactive launcher menu (scripts/launcher.py) with Setup for API keys,
  local models and cloud models

## Non-Goals (current version)
- Multi-agent parallel execution
- Real-time clinical data feeds or EHR integration
- Automated paper downloading (legal constraints)
- Regulatory clearance of SaMD mode, or any autonomous clinical decision
- A hosted web service (removed Session 33)

## Success Criteria
- All modes produce structured, standards-compliant output
- Full test suite green: python -m pytest -m "not live"
- Ollama demo completes Builder to Reviewer to Tester in under 15 minutes
- Provider switching works cleanly via --provider flag
- Guidelines from docs/ are injected into prompts automatically
- SaMD: every output carries the intended-use statement, and no patient
  data leaves the machine without the cloud gate
