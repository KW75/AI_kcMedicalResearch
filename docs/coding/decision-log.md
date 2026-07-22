## Data Flow

User input
¢x ¡¿ choose_role() - selects role based on mode
¢x ¡¿ build_project_context() - mode-aware doc injection
¢x ¡¿ full_prompt assembled with role prompt + context + task
¢x ¡¿ call_ai() - dispatches to active provider
¢x ¡¿ Response printed, saved to report, appended to transcript
¢x ¡¿ truncate_context() - prepares context for next step


## Planned Future Components

- RAG retrieval layer - replaces manual context pasting
- Real testing tools - automated quality checking per mode
- Docker containerisation
- GitHub Actions CI/CD

Updated docs/decision-log.md

# Decision Log

## Decision 1 - Use Ollama for local inference

Date: 2026-06
Decision: Use Ollama as the default AI provider running locally.
Reason: No cloud costs, no data leaving the machine, simple API,
supports model swapping via --model flag.
Alternatives considered: OpenAI API, Anthropic API.
Status: Implemented. Cloud providers added as optional via --provider flag.

## Decision 2 - Single module architecture

Date: 2026-06
Decision: Keep all application code in src/main.py as a single module.
Reason: Project is early stage. Single module is easier to test, easier
to hand off, and easier to reason about. Split into packages when
complexity justifies it.
Status: Implemented.

## Decision 3 - Truncate forward context at 2000 chars

Date: 2026-06
Decision: Truncate previous AI response to 2000 characters before
including in next prompt.
Reason: Prevent prompt size from growing unboundedly across steps.
Small local models degrade significantly with very large prompts.
Status: Implemented. Will be revisited when RAG is added.

## Decision 4 - Reports folder excluded from Git

Date: 2026-06
Decision: Never commit reports/ to Git.
Reason: Reports contain session transcripts which may include sensitive
task content. Keep local only.
Status: Implemented via .gitignore.

## Decision 5 - HANDOFF.md excluded from Git

Date: 2026-06
Decision: Never commit HANDOFF.md to Git.
Reason: HANDOFF.md is a local continuity document for AI-assisted
development sessions. It is not part of the deployable product.
Status: Implemented via .gitignore.

## Decision 6 - Multi-mode architecture

Date: 2026-07
Decision: Extend the tool to support multiple workflow modes via
a --mode flag. Each mode defines three AI roles via a ROLE_FILES
dictionary. The active mode is resolved at runtime.
Reason: The three-role pipeline - generator, reviewer, quality checker -
is a universal pattern that applies to any domain. Coding was the first
domain but writing, finance, legal, and research are all valid targets.
Making the tool mode-agnostic costs one flag and one dictionary lookup.
Status: Implemented. Coding and writing modes live. Finance and legal
modes ready to add via prompt files only.

## Decision 7 - Multi-provider architecture

Date: 2026-07
Decision: Abstract AI provider communication behind a PROVIDERS
dictionary. Each provider is a separate caller function. The active
provider is selected via --provider flag.
Reason: Ollama is the default but users may want to switch to OpenAI
or Anthropic for higher quality responses on complex tasks without
changing the tool architecture.
Status: Implemented. ollama, openai, and anthropic supported.

## Decision 8 - Mode-aware context injection

Date: 2026-07
Decision: build_project_context() injects only documentation files
relevant to the active mode.
Reason: Injecting coding-standards.md and test-strategy.md into a
writing mode prompt wastes tokens and sends conflicting instructions
to the model.
Status: Implemented.

## Decision 9 - RAG deferred

Date: 2026-07
Decision: Defer RAG and vector database implementation to a later step.
Reason: RAG requires a vector database dependency, an embedding model,
and a document indexing pipeline. This is a substantial step that belongs
together with real testing tool development. The mode-switching and
provider-abstraction work is self-contained and ships cleanly without it.
Status: Deferred. Planned for future step alongside real testing tools.


