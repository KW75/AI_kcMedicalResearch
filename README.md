# AI kcMedical Research

A multi-mode AI assistant for medical research, critical appraisal, systematic review, coding, and writing. Uses cloud providers by default (DeepSeek, Qwen, OpenAI, Anthropic, Groq) with optional local Ollama support.

- **Version:** 2.4.4
- **Tests:** 400 passed, 3 skipped
- **Coverage:** ~53%
- **CI:** GitHub Actions - Green
- **GitHub:** https://github.com/KW75/AI_kcMedicalResearch
- **Live App:** https://ai-kcmedicalresearch.onrender.com
- **Health Check:** https://ai-kcmedicalresearch.onrender.com/_stcore/health
- **Uptime:** UptimeRobot (5-min monitoring, prevents cold starts)

---

## Quick Start

### One-Click Setup (Recommended for Colleagues)

Windows:

    git clone https://github.com/KW75/AI_kcMedicalResearch.git
    cd AI_kcMedicalResearch
    docker\docker_setup.bat

macOS:

    git clone https://github.com/KW75/AI_kcMedicalResearch.git
    cd AI_kcMedicalResearch
    chmod +x docker/mac_*.sh
    ./docker/mac_docker_setup.sh

Total time: ~5 minutes. No Python setup required.

### Local Development (Without Docker)

Run all commands from the project root.

    python SOURCE_CODE/main.py                            # coding mode (default)
    python SOURCE_CODE/main.py --mode writing             # writing mode
    python SOURCE_CODE/main.py --mode rct_search          # RCT search pipeline
    python SOURCE_CODE/main.py --mode search              # PubMed search
    python SOURCE_CODE/main.py --mode appraisal           # critical appraisal
    python SOURCE_CODE/main.py --mode sr --provider qwen  # systematic review (needs vision)
    python SOURCE_CODE/main.py --no-stream                # disable streaming
    python SOURCE_CODE/main.py --resume                   # resume from checkpoint
    python SOURCE_CODE/main.py --dry-run                  # test without API calls
    python scripts/launcher.py                            # menu-driven launcher

## Modes

| Mode | Flag | Roles |
|------|------|-------|
| Coding | --mode coding | Builder, Reviewer, Tester |
| Writing | --mode writing | Writer, Editor, QA |
| RCT Search | --mode rct_search | Formulator, Searcher, Validator |
| Search | --mode search | Researcher |
| Appraisal | --mode appraisal | Appraiser, Methodologist, Summariser |
| SR | --mode sr | SR Methodologist |

## Providers

| Provider | Flag | Environment Variable | Notes |
|----------|------|----------------------|-------|
| DeepSeek (DEFAULT) | --provider deepseek | DEEPSEEK_API_KEY | Fast, cost-efficient |
| Qwen | --provider qwen | DASHSCOPE_API_KEY | Recommended for SR (vision) |
| OpenAI | --provider openai | OPENAI_API_KEY | GPT-4 vision |
| Anthropic | --provider anthropic | ANTHROPIC_API_KEY | Claude vision |
| Groq | --provider groq | GROQ_API_KEY | Fast inference |
| Ollama (local) | --provider ollama | OLLAMA_HOST | Free but slow; offline/testing only |

On transient errors (timeout, 429, 502, 503), the system automatically tries the next provider. Default chain: DeepSeek -> Qwen -> Groq. Configure via FALLBACK_PROVIDERS.

## Streaming

All providers support live token streaming, enabled by default in CLI terminals. Use --no-stream to disable. Non-TTY environments (pipes, CI) automatically use batch mode.

## Environment Variables (.env)

    DEFAULT_PROVIDER=deepseek
    FALLBACK_PROVIDERS=deepseek,qwen,groq

    OLLAMA_HOST=http://localhost:11434
    OLLAMA_CONTEXT=32768
    OLLAMA_NUM_PREDICT=8192
    OLLAMA_TEMPERATURE=0.3

    DEEPSEEK_API_KEY=sk-...
    GROQ_API_KEY=gsk_...
    DASHSCOPE_API_KEY=sk-...
    DASHSCOPE_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
    QWEN_MODEL=qwen-plus-latest
    OPENAI_API_KEY=sk-...
    ANTHROPIC_API_KEY=sk-ant-...

    EMBEDDING_PROVIDER=ollama
    EMBEDDING_MODEL=nomic-embed-text
    CLI_THEME=dark

## Running Tests

    python -m pytest -m "not live" --tb=short -q          # standard suite
    python -m pytest --cov=SOURCE_CODE --cov-report=html  # with coverage
    python -m pytest -m live -v                           # live provider smoke tests

Current status: 400 passed, 3 skipped, 11 deselected.

## SR Pipeline

Place your PDFs in the SR input folder:

    Windows:        copy *.pdf input\sr\
    macOS/Linux:    cp *.pdf input/sr/

Run the pipeline directly (not via the launcher menu) so the interactive PICO prompts receive a real TTY:

    python SOURCE_CODE/main.py --mode sr --provider qwen  # needs vision provider

Outputs are written to a timestamped run folder and mirrored to the output tree:

    reports/sr/<run_id>/    # systematic_review.docx/.html, forest_plot.png, audit CSVs
    output/sr/figures/      # mirror of forest_plot.png
    output/sr/reports/      # mirror of report files

Note: the .env value QWEN_MODEL=qwen-plus-latest is correct, but the code still hard-codes qwen3.7-plus in _DEFAULT_MODELS (see Known Issues #4).

## Deployment (Render)

- URL: https://ai-kcmedicalresearch.onrender.com
- Health: https://ai-kcmedicalresearch.onrender.com/_stcore/health
- Auto-deploy: push to main triggers deploy
- Build: pip install --upgrade pip && pip install --no-cache-dir --only-binary=:all: -r requirements-render.txt && pip install --no-cache-dir --no-deps docx2txt==0.8
- Monitoring: UptimeRobot pings every 5 min (prevents free-tier cold starts)

## Known Issues

| # | Issue | Priority | Status |
|---|-------|----------|--------|
| 1 | Lami extraction fails (Table 4) | High | Open |
| 2 | WeasyPrint not installed | Medium | PDF falls back to HTML |
| 3 | Anthropic geo-restricted | Low | Use VPN or skip |
| 4 | Hard-coded qwen3.7-plus in _DEFAULT_MODELS overrides QWEN_MODEL | Low | Open |

## Contributing

1. Fork the repository
2. Create a feature branch: git checkout -b feature/your-feature
3. Make your changes
4. Run tests: python -m pytest -m "not live" --tb=short -q
5. Commit and push
6. Create a pull request
