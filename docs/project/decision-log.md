# Decision Log

Record of significant architectural and technical decisions.

---

## 2026-08-11: Remove CREATE_NEW_PROCESS_GROUP from launcher
**Context:** Launcher subprocess calls to main.py failed because
CREATE_NEW_PROCESS_GROUP on Windows detaches stdin, causing EOFError.
**Decision:** Remove the flag; pass stdin/stdout/stderr explicitly.
**Commit:** 428e190

## 2026-08-11: Auto-detect Ollama model at startup
**Context:** Hard-coded model name (llama3.2) broke when users pulled
different models. Small models (3B) produced unusable output.
**Decision:** Query /api/tags, pick largest non-embedding model. Override
via OLLAMA_MODEL env var.
**Commit:** 2d71bfc

## 2026-08-11: Use qwen-plus-latest for Qwen Cloud
**Context:** Hard-coded qwen3.7-plus broke when Alibaba updated versions.
**Decision:** Default to qwen-plus-latest (always points to current best).
Override via QWEN_MODEL env var.
**Commit:** 2d71bfc

## 2026-08-11: Increase LLM timeout from 5 to 15 minutes
**Context:** 36B model timed out on complex coding prompts within 5 minutes.
**Decision:** Increase thread join timeout to 900s in coding.py and writing.py.
**Commit:** a0cde58

## 2026-08-11: Increase Ollama context to 32768 tokens
**Context:** Builder output (approx 250 lines HTML) plus Reviewer prompt exceeded
8192 context window, causing empty responses.
**Decision:** Set OLLAMA_CONTEXT=32768 in .env, pass num_ctx in provider call.
**Commit:** 90d6c3d

## 2026-08-11: Reduce MAX_ITERATIONS from 5 to 3
**Context:** By iteration 5, accumulated prompt context caused timeouts with
large local models.
**Decision:** Reduce to 3 iterations (sufficient for demo and feedback loop).
**Status:** Pending commit

## 2026-08-11: Rewrite test_live_providers.py
**Context:** Original test file called sys.exit(1) at import time, crashing
pytest collection.
**Decision:** Rewrite with proper pytest skip/assert patterns and register
live mark.
**Commit:** d42f82b

## 2026-08-11: Purge destructive commit 62e412c
**Context:** Commit deleted 2027 lines from main.py under Ollama optimization.
**Decision:** Hard reset to 9aef3e6, force-push, reflog expire + gc prune.
**Result:** Commit permanently removed from history.

## 2026-08-11: Restructure docs/ folder
**Context:** docs/coding/ contained PRD.md, architecture.md, decision-log.md
which are project-level, not coding-mode guidelines. They were incorrectly
injected into coding prompts as if they were coding standards.
**Decision:** Create docs/project/ for project docs. Keep docs/coding/ for
actual coding standards injected into Builder/Reviewer/Tester prompts.
**Status:** Pending commit
