# Product Requirements Document

## Project Name

AI Automation Tool - Local Multi-Mode AI Pipeline

## Version

2.0.0

## Goal

Build a local Python multi-role AI pipeline that supports multiple workflow
modes. Each mode defines three AI roles that work together in sequence -
a generator, a reviewer, and a quality checker. The tool runs entirely on
the local machine with no cloud APIs required by default, but supports
cloud AI providers via a --provider flag.

## Supported Modes

### Coding Mode (default)

1. Builder AI  - creates or modifies code based on task description
2. Reviewer AI - reviews code and gives structured feedback
3. Tester AI   - suggests tests and assesses deployment readiness

### Writing Mode

1. Writer AI - generates articles, documents, and written content
2. Editor AI - reviews for clarity, structure, tone, and accuracy
3. QA AI     - fact-checks, finds gaps, and assesses readiness

## Target Workflow

Role 1 generates a first attempt at the task
Role 2 reviews and gives feedback
Role 1 (or human) applies fixes based on feedback
Role 3 performs final quality check
Human approves before output is used

## AI Provider Support

The tool supports multiple AI providers via the --provider flag:

- ollama (default) - local inference, no cloud, no API key required
- openai           - OpenAI API, requires OPENAI_API_KEY in .env
- anthropic        - Anthropic API, requires ANTHROPIC_API_KEY in .env

## Non-Goals (current version)

- RAG / vector database retrieval (planned for future)
- Automated test execution for non-coding modes (planned for future)
- Real-time market data or live API integrations
- Multi-agent parallel execution
- Docker containerisation (planned for future)
- GitHub Actions CI/CD (planned for future)

## Success Criteria

- All three roles work correctly in each supported mode
- Forward context passing works across all modes
- Session transcripts saved correctly for all modes
- Provider switching works cleanly via --provider flag
- All existing tests pass after changes
- Coverage remains above 90%
