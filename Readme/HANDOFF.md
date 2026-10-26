# HANDOFF

Single source of truth for the next session. Read this, then work.
Session-by-session history (1-23) is in `Readme/HANDOFF_archive_pre_S19.md`
and git log; consult it only before reopening a closed issue.

Repository: https://github.com/KW75/AI_kcMedicalResearch
Live app:   https://ai-kcmedicalresearch.onrender.com
Health:     https://ai-kcmedicalresearch.onrender.com/_stcore/health

---

## Session-opening checklist

Before treating any Open Issue as work, and before ending the session:

1. **Test count check.** Grep `README.md` for `Tests: NNN passed`; run
   `python -m pytest -m "not live" --collect-only -q | tail -1` (or
   equivalent) and confirm the two match. Update README if not.
2. **Closed-issue citation grep.** For each issue number in
   `Readme/RESOLVED_ISSUES.md`, grep `README.md` and this file for
   `(#N)`. Any hit is a stale citation — replace with a positive
   description or a REVIEWER_GUIDE section reference.
3. **Open Issues table drift.** Confirm `Readme/HANDOFF.md`'s Open
   Issues table matches `README.md`'s Known Issues table (same numbers,
   same priorities). They live in two files and drift silently.
4. **Handoff-claim spot check.** Pick one Known Issue you plan to
   touch. Before starting, grep the affected source file for the
   claim's specific string (e.g. `SOURCE QUOTE CHECK`, `_number_in_text`).
   If the string isn't there, the claim is stale — verify before acting.

Session 25 caught four doc-lag items (test count; #12 never migrated
from S24 handoff to RESOLVED_ISSUES; #15 miscategorised as a bug;
"decimal separator" claim contradicted by `_number_in_text`). Session
26 caught three more at close: README cited closed #50 in parentheses
(missed by S25's grep), #66 was closed in S25 but never added to
RESOLVED_ISSUES (README still cited it in parentheses), and the "cheapest first:
temperature=0" item had sat for three sessions without anyone grepping
the call site, where the vision call was at 0.1. This checklist exists
so those catches happen at session open, not mid-work.

---

## Current State (Session 31, v2.5.0, 2026-10-26)


| Component      | Status |
|----------------|--------|
| Tests          | 743 passed, 3 skipped, 11 deselected (`python -m pytest -m "not live" --tb=short -q`) |
| CI             | green (455b2d8; 28e616e; 3a9081b and 6813b12 also confirmed green) |
| Render deploy  | <merge hash> live 2026-10-26; DEFAULT_PROVIDER=qwen + DASHSCOPE_API_KEY on the service's own Environment tab; qwen prompt OK on live app |
| SR pipeline    | working via CLI with Qwen; Ang 2010 verified against PDF (NFR week 6, unanimous N=3); text-fallback drops now surface in Stage 4 `[SKIP]` block |
| Providers      | Ollama (default, local) / DeepSeek / Qwen (SR) / OpenAI / Anthropic / Groq / Ollama (local, never falls back) |

Issue numbers below match `README.md` > Known Issues.

---

## Open Issues

| #  | Issue | Priority | What to do |
|----|-------|----------|------------|
| 19 | macOS install | RESOLVED | Fixed 2026-09-02. python.org 3.11.9 + requirements-local.txt (pyarrow 12.0.1, chromadb 0.5.23) verified end-to-end on Intel macOS 11. Launchers reject conda and guide to python.org. NOT yet run on Apple Silicon (reasoned from wheel tags). |
| 2  | WeasyPrint not installed; PDF report falls back to HTML | Medium | |
| 3  | Anthropic geo-restricted from dev machine | Low | VPN or skip. |


---

## Session 27 Summary

Three commits, all CI green: `6813b12` (docs — close #67, open #68/#69),
`3a9081b` (#68 fix + test), `28e616e` (#69 fix + tests). 565 → 569 tests.
Three issues resolved.

- **#67 closed: Ang 2010 verified.** Two post-handoff corpus runs
  (`20260829_122447` with Lami override, `20260829_124847` without)
  showed Ang unanimous across N=3 on `-20.2 (23.9)` CBT vs `-14.9
  (16.4)` UC, `nondet_flag=[]`, `outcome_selected="Pain rating at NFR
  threshold"`, `timepoint_selected="week 6"`. Reviewer opened PDF and
  confirmed values against the paper's NFR pain rating change score
  table at week 6. No `study_overrides.yaml` entry needed — the
  extractor is now stable on this paper and picks a valid outcome. The
  S26 handoff's "table_shift on FIQ Table 2, 5-vs-6-of-12" framing
  described an older pipeline state; something between S26 and S27
  changed Ang's outcome selection without documentation. Not
  investigated further because current behaviour is stable and
  correct; if Ang starts flapping again, `Readme/evidence/s26_issue11/`
  is the reference for the earlier behaviour.

- **#68 closed: Unicode minus / dash matcher gap.** The `-20.2` extracted
  value did not match `−20.2` (U+2212) in its source quote, firing the
  source-quote tripwire falsely on both arms of Ang in both S27 runs.
  Fix: `_number_in_text` translates U+2212, U+2013, U+2014, U+FE63,
  U+FF0D to ASCII `-` on both value and haystack before comparing.
  Pinned by `test_number_in_text_unicode_minus_matches_ascii_minus`
  with en/em-dash variants and a negative case. Same class of bug as
  the "decimal separator" gap the S25 lesson thought was fully closed
  — one flavour was, sign characters weren't. Left the S25 lesson as
  written; the shape is the point.

- **#69 closed: text-fallback drops surface in Stage 4.** Lami's run-2
  (`20260829_124847`, no override) had usable means/SDs from
  text_fallback but empty per-arm Ns; the effect-size loop raised
  "insufficient mean/SD/N", `logger.warning("Skip study: ...")` fired
  once mid-run, Lami dropped from the pooled estimate, and no
  Stage-4 summary line named it. New `[SKIP]` block in
  `_log_stage4_summary` separates missing-per-arm-N drops (the
  Lami-shaped failure typical of text_fallback) from other skip
  reasons and points the reviewer at `study_overrides.yaml`. Three
  tests: the Lami case, a clean run prints `0 of N`, and mixed
  reasons don't conflate. Automated N-recovery is deliberately out
  of scope: text_fallback returns means/SDs from one timepoint's
  source quote but the paper often reports Ns at multiple timepoints
  (Lami: 28/36 post vs 34/41 baseline), and a silent wrong N is
  worse than a missing one — see the durable lesson.

- **Two findings recorded in passing, not fixed.** McCrae's SDs came
  back as `None` on one of three vision runs in `20260829_124847`
  (unanimous in `20260829_122447` earlier the same day); the N=3 vote
  correctly recovered 2.36 / 2.27 from the other two and flagged
  `sd_intervention:majority`, `sd_control:majority`. This is the
  first post-#11-close real-run instance where the model returned
  `None` and the vote absorbed it — the mitigation works on live
  inputs, not just fixtures. The S25/#66 Stage-4 "cheapest first
  temperature=0" carryover is no longer relevant (closed in S26); the
  `.venv` housekeeping item from S26 was not re-verified this session.

## Session 28 Summary

Local-model recommendation changed from llama3.2 to qwen2.5:14b-instruct
(config only, no pipeline logic change). Reason: llama3.2 (3B) was too weak
for code generation - the coding Builder's Reviewer/Tester loop never
converged. qwen2.5:14b is strong on synopsis/appraisal prose (the
confidentiality-critical local use) and adequate for demo code.
qwen2.5:7b-instruct offered as the low-resource fallback.

- `.env.example`: OLLAMA_MODEL uncommented and set to qwen2.5:14b-instruct.
  Added confidentiality note on EMBEDDING_PROVIDER (keep = ollama; openai
  sends document chunks out). Added MAXITER_WARNING note for demo code.
- README: Step 2 Option A and Providers table updated to qwen2.5.
- `call_ollama_provider` (providers.py): friendlier errors - 404 now prints
  "run: ollama pull <model>"; connection-refused now says "make sure Ollama
  is running". [APPLY + add test pinning the 404->pull-message mapping;
  existing tests may assert the old "HTTP error 404" string - run suite.]

Verified by code review only: confirmed coding pipeline honours OLLAMA_MODEL
(coding.py uses an injected call_llm_fn, no hard-coded model); confirmed
Ollama never falls back to cloud (LOCAL_ONLY_PROVIDERS in providers.py);
confirmed DASHSCOPE_ANTHROPIC_URL / DASHSCOPE_OPENAI_URL are dead config
(unused in providers.py, main.py, streaming.py). NOT yet verified on real
hardware: a 14B pull and a demo run converging. Do before rollout.


## Next Session Priorities (Session 28)

1. **Vote `outcome_selected` / `timepoint_selected`.** Carryover from
   S26 priority 3 and now more urgent: today's Ang stability could be
   the extractor consistently picking the same *non-primary* outcome
   across runs, and the vote would not surface that. A normalised-label
   vote on these fields (like the group labels) with `majority` /
   `no_majority` flags would catch a run that silently switched
   outcomes. Sketch in S27's chat: normalise wording (strip
   punctuation, lowercase, whitespace), pick source string from a run
   whose normalised value matches the winner, add to
   `nondet_flag_to_cell` vocabulary. Test cases: cosmetic-only jitter
   ("FIQ pain rating" vs "FIQ pain score") is `majority` not
   MANDATORY; a real timepoint shift (week 6 vs week 12) is worth
   surfacing; three-way disagreement is `no_majority`.

2. **Investigate Ang's outcome-selection change between S26 and S27.**
   S26 evidence at `Readme/evidence/s26_issue11/` should show what Ang
   returned on those N=3 runs; S27 CSVs show `outcome_selected="Pain
   rating at NFR threshold"` unanimous. If S26's evidence shows FIQ,
   something changed (prompt, page selection, model behaviour) with
   no changelog entry. Worth understanding before priority 1 above,
   because whatever moved once can move again.

3. **Decoder `!`-for-space gap, low.** Unchanged from S26.

## Housekeeping (low priority, carry until done)

- Add `run_*.log` to `.gitignore` (two untracked from Session 24) and
  delete `input\s24_mccrae\` when done with it.
- Confirm `.venv\Scripts\` Python is the one resolving (a system Python
  was once seen behind a `(.venv)` prompt in S26; not re-verified in S27).
- Delete stale `%TEMP%\ai_km_run_*.bat` on any machine that ran the
  pre-v2.4.7 UI launcher (keys already rotated).
- Commit-message files: write them from an editor (UTF-8, no BOM).
  PowerShell `Out-File` adds a BOM to the subject line.

---

## Durable Lessons

- **Verify the artifact, not the summary.** Twelve documented instances
  now (Session 25 added the `main.py` ambiguity below and the "decimal
  separator differences" claim in REVIEWER_GUIDE that was already
  handled in `_number_in_text`). Session 24 added three in one file:
  a CI hash one commit stale, a cosmetic glitch that no longer
  existed, and a grep string that never existed — plus the branch
  count itself. Previously eight (Session 23 had added the phantom
  "Anthropic skips group/timepoint" claim that had been restated
  across at least two handoffs without being checked against
  `_coerce_extraction_result`). Before treating a Known Issue as
  work, read the current source of the affected file. Before citing
  a number from a prior handoff, confirm it appears in an audit CSV.
  This applies to your own outputs mid-session too.

- **When a handoff says "in main.py", verify which `main.py`.** The
  #66 item said "the four Stage-4 summary lines in main.py". The repo
  has two: the top-level CLI dispatcher (`SOURCE_CODE/main.py`) and
  the SR sub-pipeline (`SOURCE_CODE/pipelines/sr/main.py`). The
  Stage-4 code was in the latter; grepping the former for
  `SOURCE QUOTE CHECK` returned nothing. Filenames alone are not
  unique identifiers in this repo — always confirm which file a
  claim points to before starting work.

- **A silent wrong answer is worse than a crash.** Clean-looking CSV
  rows have carried wrong numbers (zsy234 g=-2.36; Ang -8.9).
  Plausibility is not evidence. Bind verification to the numbers
  (source quotes), not the labels.

- **Identical byte counts across different inputs mean a saturated cap.**

- **A fallback chain that ignores WHY a provider was chosen will violate
  the reason it was chosen.** Ollama is local-only for confidentiality;
  `LOCAL_ONLY_PROVIDERS` must never fall back. Do not undo.

- **Displayed claims that nothing re-verifies decay silently.** Parse
  version/test counts from source at display time, or do not display
  them. This applies to prose too: `REVIEWER_GUIDE.md` §2.2 described
  the source-quote tripwire as four branches when the extractor
  actually fires on five (branch 4 carrying three mutually exclusive
  sub-checks), because branches were added after the doc was last
  touched and nothing forced the doc to stay in sync. Same file, same
  session (S25): §6 listed "decimal separator differences" as a
  matcher gap that was closed in `_number_in_text` long enough ago
  that no one remembered. If a doc claims a specific count, list, or
  limitation, either derive it from source or accept that it will rot.
  (Session 24: HANDOFF said "six" while the S23 summary above said
  "five" — the same document contradicted itself one screen apart.)

- **A "confirm it works" item must name a test case that can reach the
  code.** #12 sat as High for three sessions with an instruction (run
  McCrae) that could not exercise the branch, and a grep string that
  did not exist. Before carrying a confirmation item, check: which
  input reaches this code path, and what exact line does it emit?

- **The help text is a claim too.** `--model` promised "provider's
  configured model" for as long as the flag existed; nothing delivered
  it. Handoffs said Qwen was the SR provider; the CLI had never
  completed a Qwen run.

- **A tripwire that only writes its key on failure makes "checked and
  clean" indistinguishable from "never ran".** Always set the key;
  print the zero. Corollary (S25/#66): a "clean" branch that asserts
  a positive property ("every extracted value was bound to a verbatim
  source quote") on an all-empty run does the same damage in the
  opposite direction — the assertion has no evidence behind it. The
  denominator has to say whether the zero means "checked and clean"
  or "nothing was there to check".

- **Pin the property a test exists to protect (sign, presence,
  ordering), not a specific number** — unless that number is itself
  the reviewer-verified artifact.

- **A regression fixture pins a known failure signature, not the
  failure rate.** Do not conflate "the shape is pinned" with "the
  paper extracts reliably". The fixtures only guarantee that a known
  good shape won't be falsely rejected and a known bad shape will
  still be caught; the S26 `nondet_flag` vote is what measures the
  rate on each run. The model's non-determinism itself is unchanged.

- **Measure a mitigation before carrying it.** "Try temperature=0 /
  seed" sat in the handoff for three sessions as the cheap fix for
  #11. Thirty calls showed the seed was ignored and `t=0` changed
  nothing. The vision call had also been at 0.1 the whole time — a
  fact that checklist item 4 (grep the call site) would have found in
  S24. A mitigation that has never been run is a hypothesis, and a
  hypothesis carried across sessions starts to read as a plan.

- **A majority is not evidence when the alternatives are structured.**
  Ang's two readings are the same numbers with the arms shifted; a
  2-of-3 vote picks either depending on the draw (5 vs 6 of 12). Tag
  the shape (`table_shift`) and treat it as a tie; do not trust the
  count. Corollary: a 3-of-4 field disagreement is NOT that shape —
  the 1-s2.0 paper jittered three fields by one digit with no shift,
  and a threshold rule would have false-positived it.

- **Overrides hide drift.** `MANUAL OVERRIDE` makes Lami read
  `unanimous`; the raw values in the override log line disagreed
  across runs. When a study is overridden, its `nondet_flag` describes
  the override, not the extractor. Read the log line.

- **A handoff describing a run's content is a snapshot, not an invariant.**
  S26 wrote "Ang shows table_shift on FIQ readings" as if it were a
  standing property; two S27 corpus runs on the same PDF showed
  unanimous N=3 on a different outcome entirely (NFR pain rating), no
  table_shift, and different competing readings than the S26 handoff
  named. Something changed between sessions with no changelog. A
  specific number, a specific flag, a specific competing value — none
  of these survive a code change; describe pipeline *behaviours* the
  reviewer must verify, not outputs from a run they can't reproduce.
  Bit us three times in one session (all three S27 issues turned out
  to be different problems than the S26 handoff described).

- **A patch delivered by prose across a session is fragile.** Mid-S27,
  #68's `_number_in_text` patch was written as "insert this at the top;
  the rest stays as it is." The user replaced through the `except`
  block cleanly and the tail — the entire matching logic — got
  deleted. Five previously-green tests failed. The problem is that
  "replace this region" and "keep everything else" are two
  instructions to a human diff editor and easy to conflate. Rule:
  when handing a code change across the session boundary, deliver the
  whole function, top to bottom, not a fragment plus a rule about
  what to keep.

---

- **A lookup default is a routing decision.** `dict.get(provider,
  urls["deepseek"])` looks like defensive coding, but it sends data to a
  company the user never chose. When the value decides where data goes,
  an unknown key must raise an error, not fall back. Found in SR screening
  (S29); safe only because a different file happened to call it correctly.


Handoff prepared: 2026-08-29, Session 27.
---

## Session - 2026-09-02 - macOS install (Issue #19) RESOLVED

Tested the macOS launchers on real hardware (Intel, macOS 11.7.11).

Root cause of #19 (chain):
- Launcher picked the first python.org/system python3.11 on PATH; on the
  test Mac only Anaconda's 3.11 existed. Anaconda's build reports platform
  tag macosx_10_9, below the floor of modern pyarrow wheels -> pip source
  build -> "can't find Rust compiler".
- pyarrow is pulled in by BOTH chromadb (requirements-base) and
  streamlit (unpinned). Even the pinned render file (streamlit 1.38.0)
  triggered a source build because the interpreter's 10.9 tag rejected the
  newer pyarrow wheel.
- MACOSX_DEPLOYMENT_TARGET was empty - the 10.9 tag came from the python.org
  3.11.9 build itself, not an env var.

Fix (generic, all Macs):
- Standardize on python.org 3.11.9 universal2 (Intel + Apple Silicon).
- New requirements-local.txt: fully pinned, pyarrow==12.0.1 (has prebuilt
  cp311 wheels for macosx_10_14_x86_64 AND macosx_11_0_arm64), chromadb==0.5.23.
  Installs with no Rust build.
- chromadb is a HARD dependency: utils/rag.py imports it at module top level;
  main.py imports the appraisal pipeline unconditionally -> app crashes on
  ModuleNotFoundError without it. (The requirements.txt comment claiming OCR/RAG
  degrade gracefully is wrong for chromadb - fix or note this.)

Launcher changes (all four scripts, v2.4.13):
- Reject conda/anaconda pythons; require genuine 3.11.
- If none found, print friendly "install Python 3.11" message + link, then
  stop (no hang).
- Install from requirements-local.txt, drop --quiet, add "screen may look
  frozen" reassurance line.
- macOS: build .venv from the python.org framework path; run via `bash`.

Verified: launcher -> menu -> Coding pipeline ran end to end, wrote output
and reports, returned to menu. (ollama "Connection refused" is expected -
Ollama not running; app fell back and completed, so plumbing is proven.)

Setup is now documented as two steps: (1) install app, (2) choose AI engine
(Ollama OR cloud API key).

Resolved this session:
- Ollama models (offline route):
  - Chat: app auto-detects the largest pulled model; falls back to "llama3.2"
    (providers.py:211). OLLAMA_MODEL in .env overrides.
  - Embeddings (RAG - appraisal/SR pipelines): defaults to "nomic-embed-text"
    (main.py:261, rag.py:30). EMBEDDING_MODEL in .env overrides.
  - README Step 2 tells colleagues to pull BOTH:
        ollama pull llama3.2
        ollama pull nomic-embed-text

Open follow-ups:
- Verify requirements-local.txt on Apple Silicon ...
- Consider wrapping `import chromadb` in try/except ...
- #28 Docker still unverified.

---

## Session 29 - 2026-10-22 - branch v2.5-major-updates

Goal for v2.5: local-first for confidentiality. Ollama is the default;
cloud is chosen per job with a warning; nothing ever switches from local
to cloud automatically.

On main before branching:
- `d20cae8`: Ollama fallback default llama3.2 -> `OLLAMA_DEFAULT_MODEL`
  (qwen2.5:14b-instruct) in providers.py. New test pins README and
  .env.example `OLLAMA_MODEL=` lines to the constant.
- Verified by reading the code: Ollama never falls back to cloud, on the
  streaming route (stream_ai -> _stream_ollama only) or the batch route
  (call_ai_with_fallback chain = [ollama]). The 2026-09-02 macOS note
  "app fell back and completed" cannot have been Ollama falling back to
  cloud; that run must have used another provider.

On branch:
- SR screening could send article text to DeepSeek.
  `RelevanceScreener.screen_by_pdf_path` used
  `provider_urls.get(provider, provider_urls["deepseek"])`, so
  provider="anthropic" or an unknown name POSTed the text to
  api.deepseek.com. The normal pipeline never reached it: for Anthropic,
  Stage 1 uploads every PDF (an upload failure stops the run) and
  screen_batch routes by file_id. So no past run leaked. The route is now
  refused with an error. Pinned by
  `tests/test_screener_provider_routing.py`, which failed before the fix.

Noted, not fixed:
- rob2_tool.py reads `OLLAMA_URL`; the rest of the app reads `OLLAMA_HOST`.
- main.py SR route uses raw `OLLAMA_MODEL`, not `_resolve_ollama_model()`.
- An Ollama SR run screens locally, then fails at extraction (no vision).
  It should stop at the start, like the DeepSeek warning.
- main.call_ai swallows streaming errors (`except Exception: pass`), so an
  Ollama failure waits through two timeouts. Revisit with time limits.
- RelevanceScreener defaults to provider="anthropic",
  model="claude-opus-4-7"; rct_search and main.py functions default to
  provider="deepseek".

- Local-first default: `providers.py` falls back to
  `CODE_DEFAULT_PROVIDER = "ollama"` when .env sets no DEFAULT_PROVIDER
  (or a blank one); README and .env.example now say
  `DEFAULT_PROVIDER=ollama`. Eight tests that compared the provider to
  the word "deepseek" now compare to `main.DEFAULT_PROVIDER`, so they pass
  whatever a machine's .env says (they passed before only because CI and
  the dev .env both set deepseek). New tests: the code default must be in
  LOCAL_ONLY_PROVIDERS; README and .env.example must match the code.
- Decided: Streamlit UI stays (option A). Only launcher menu item 8
  "Pipeline UI" is removed, swapped for OCR in update #5.
- Decided: cloud fallback stays (option B), but the cloud warning must
  list every provider the job may reach, built from FALLBACK_PROVIDERS.

Housekeeping added:
- CI uses `runs-on: ubuntu-latest`, moving to Ubuntu 26 from 2026-10-19.
  If "Install system dependencies" goes red with no code change, pin
  `ubuntu-24.04`.
- CI run shows 44 warnings that local runs don't (unpinned `>=` versions
  in requirements-base.txt). Not failing; look when convenient.
- main.py SR Anthropic warning cites "Known Issue #61", which is not in
  the Known Issues table; point it at REVIEWER_GUIDE.md section 6.
- Render UI provider dropdown starts on ollama (index=0) but Render has
  no Ollama; set a cloud default when running on Render.
- Cloud gate (v2.5 item 2 policy): `providers.provider_attempt_order()` is now the single source of fallback order and is used by `call_ai_with_fallback`. `main.data_destinations()` / `main.confirm_data_destinations()` list every external destination before a cloud job; `run_cli` refuses unless the user types y or passes `--confirm-cloud`; with no TTY and no flag, it refuses. SR lists only the chosen provider (no fallback chain). Search modes name PubMed / Europe PMC / DuckDuckGo even for local runs. New tests: tests/test_data_destinations.py (25). TestCliRouting tests now pass `--confirm-cloud`. Suite: 627 passed.

- UI cloud gate (commit 3): `ui/app.py` gets `_build_cli_cmd()` (one command for both launch paths; fixes dropped `--model` on Render and dropped `--sub` locally), `_cloud_destinations()` (via `main.data_destinations`, so UI and CLI cannot disagree), and a consent checkbox that disables Run until ticked. It passes `--confirm-cloud` only for cloud providers. The Render path uses `stdin=subprocess.DEVNULL`. If the destinations can't be worked out, cloud Run is disabled (fails closed). New tests: tests/test_ui_cloud_gate.py (24). Suite: 627 passed.
- Follow-ups (not urgent): Linux launcher `&& read` skips the pause when a job fails (the window closes before the error can be read); the Run success message says "new terminal window" even on Render; mojibake (`??`) in UI strings; `_is_cloud_environment()` treats `STREAMLIT_SERVER_PORT` as cloud; the UI has no Search sub-mode picker; 44 CI warnings; `rct_search.call_ai` returns a `[MOCK]` response on import failure; `.gitattributes` for CRLF.

# AI_kcMedicalResearch – v2.5 handoff (Session 29 close, 2026-10-22)

## How to work with me
- Windows, PowerShell, project root `D:\AI_kcMedicalResearch`. Every new window first:
  `cd D:\AI_kcMedicalResearch` then `.venv\Scripts\Activate.ps1` (prompt must show `(.venv)`).
- Give instructions ONE STEP AT A TIME. Read-only inspection before any edit. Test-first (failing tests, then code).
- Edit files in VS Code only, never PowerShell `Set-Content` etc. (BOM risk).
- Every change: `python scripts/check_no_bom.py` → `python -m pytest -m "not live" --tb=short -q` → update test count in README.md line 7 + Readme/HANDOFF.md → commit → push.
- If any check prints something unexpected, stop and paste it before committing.
- PowerShell: `Select-String` has no `-Recurse` (pipe from `Get-ChildItem`). CRLF→LF warnings are harmless.

## Product goal
Health professionals keep data confidential: local (Ollama) first. Cloud providers are optional, chosen per job,
with an explicit warning + consent. Local model choice exists so users can match the model to their hardware.

## Repo / branch state
- GitHub: https://github.com/KW75/AI_kcMedicalResearch ; Render (deploys from main): https://ai-kcmedicalresearch.onrender.com
- `main` at `d20cae8` (Ollama fallback default → OLLAMA_DEFAULT_MODEL = qwen2.5:14b-instruct). CI green, Render health ok.
- Working branch `v2.5-major-updates`; draft PR #1 "v2.5: local-first major updates": https://github.com/KW75/AI_kcMedicalResearch/pull/1
  (CI only runs on push to main / PRs into main.)
- Branch commits: `0640741` SR screener refuses unrouted providers (was sending text to DeepSeek) ·
  `8c7b97a` DEFAULT_PROVIDER falls back to ollama; tests independent of .env ·
  `7bbf1b4` CLI cloud gate ([y/N], `--confirm-cloud`, `provider_attempt_order`) ·
  `eb6661e` UI cloud gate (consent checkbox, `_build_cli_cmd`, stdin=DEVNULL on Render).
- Tests: 723 passed, 3 skipped, 11 deselected (local + CI). CI shows 44 warnings (not urgent).

## Open items to confirm first
1. DONE (Session 30): README test count corrected to 624 and committed together with this handoff block.
2. DONE (Session 30): browser check passed. ollama: no warning, Run enabled. deepseek: warning lists DeepSeek and Qwen (Alibaba), Run disabled until consent ticked.
3. Decide: merge PR #1 now (local-first work is complete) or keep it open until all 5 updates are done.

## Durable policies (decided)
- Ollama = code default (`providers.CODE_DEFAULT_PROVIDER`); never falls back to cloud (`LOCAL_ONLY_PROVIDERS`).
- Cloud only by explicit per-job choice. Warning lists every destination (chosen provider + FALLBACK_PROVIDERS backups,
  read at run time). Enter = cancel. With no keyboard and no `--confirm-cloud`, the job is refused. Consent is never saved.
- SR lists only the chosen provider (no fallback chain); SR needs vision (Qwen/OpenAI/Anthropic/Groq). Ollama/DeepSeek blocked.
- Search modes always send search terms to PubMed/Europe PMC (+DuckDuckGo for Search); the banner says so even for local runs.
- The UI reuses `main.data_destinations()` (one source of truth). If destinations can't be worked out, cloud Run is disabled (fails closed).
- Streamlit stays (option A): remove only launcher menu option 8 "Pipeline UI" (replaced by OCR, update #5). Keep `--ui` and Render.
- Lesson: a lookup default is a routing decision (`dict.get(provider, urls["deepseek"])` leaked data).

## Remaining v2.5 updates (suggested order)
1. **#1 Ollama model picker**: list pulled models with sizes (from `/api/tags`), skip embedding models (embed/nomic/all-minilm),
   default `OLLAMA_DEFAULT_MODEL`. Places: `scripts/launcher.py` `pick_provider` (~line 353), `SOURCE_CODE/ui/app.py` Provider selectbox (~line 926),
   `providers._ollama_detect_best_model`. Thinking mode DONE (Session 30): every Ollama request sends `think: false`. Measured on Ollama 0.40.8: qwen3:8b used 229 tokens without it and 3 with it, same answer; qwen2.5 accepts it without error.
   Review OLLAMA_CONTEXT=32768 for small hardware.
   Pulled locally: gemma4:e4b 6.6 GB, qwen3:8b 5.2 GB, qwen2.5:14b-instruct 9.0 GB, llama3.2:latest 2.0 GB, nomic-embed-text 274 MB.
2. **#3 Writing mode**: Topic and Article tracks offer only the stand-alone editor mode.
3. **#2 Time limit per action/iteration**: default 15 min; options 30 min, 1 hr, until finished; needs clean cancel.
   (UI cloud path currently uses `UIConfig.TIMEOUT`.)
4. **#5 OCR** replaces launcher option 8 "Pipeline UI" (pytesseract already used in `relevance_screener.py`).
5. **#4 Data Analysis pipeline** replaces Dry Run (launcher option 7 / `--dry-run`): data file → Python/R/Excel statistics →
   Ollama model explains/checks/reports.

## Follow-ups (not urgent)
- Linux launcher `&& read` skips the pause when a job fails (window closes before the error can be read).
- Run success message says "new terminal window" even on Render.
- Mojibake (`??`, odd characters) in app.py UI strings.
- `_is_cloud_environment()` treats `STREAMLIT_SERVER_PORT` as cloud.
- UI has no Search sub-mode picker.
- `rct_search.call_ai` returns a `[MOCK]` response if its import fails (should raise).
- 44 CI warnings (unpinned `>=` versions in requirements-base.txt).
- Add `.gitattributes` for line endings.
- ubuntu-latest moved to Ubuntu 26 (Oct 2026). If "Install system dependencies" fails, pin `runs-on: ubuntu-24.04`.

## Environment notes
- Local `.env`: DEFAULT_PROVIDER=deepseek (overrides code default; consider changing to ollama), FALLBACK_PROVIDERS=deepseek,qwen,
  EMBEDDING_PROVIDER=ollama. `.env` is never committed.
- `.env.example`: DEFAULT_PROVIDER=ollama, FALLBACK_PROVIDERS=deepseek,qwen,groq.

## First request for the new chat
"Confirm the open items above, then start update #1 (Ollama model picker), one step at a time, read-only first."

## Session 30 - 2026-10-23 - branch v2.5-major-updates

- `3485d34`: README test count 624; Session 29 handoff block committed.
- Browser check of the UI cloud gate passed (open item 2).
- Ollama thinking off: `"think": False` added to all three Ollama requests
  (`providers.ollama_probe_performance`, `providers.call_ollama_provider`,
  `streaming._stream_ollama`). qwen3 and gemma4 think by default
  (`ollama show`: thinking default true). Streaming especially needed it:
  while a model thinks, Ollama leaves `response` empty, so the user saw
  nothing. Tests: `TestOllamaThinkOff` (2) in test_providers.py and
  `test_ollama_streaming_sends_think_false`. Suite: 627 passed.
- Noted, not fixed: `_stream_ollama` uses raw `OLLAMA_MODEL`, not
  `_resolve_ollama_model()`, so it sends an empty model name when .env sets
  none. Fix in the model-picker commit.
- Next: update #1 model picker. Default becomes gemma4:e4b. Ranks come from
  the 2026-10 model comparison doc (1 = best); params, size, context,
  vision and thinking are read live from Ollama. gemma4 vision is not used
  yet: `call_ollama_provider` sends text only, so OCR waits for update #5.
- `f836106`: think=false commit (above).
- Default local model -> gemma4:e4b. New `SOURCE_CODE/ollama_models.py`
  (stdlib only, so the launcher can import it) holds OLLAMA_DEFAULT_MODEL,
  MODEL_RANKS (2026-10 comparison, 1 = best), list_ollama_models (/api/tags,
  skips embedding models, smallest first), model_capabilities (/api/show),
  choose_default (default if pulled, else largest), rank_label,
  missing_ranked, describe. providers.py imports the default from it;
  _ollama_detect_best_model now uses choose_default. README Step 2,
  Providers row, sample .env and .env.example now name gemma4:e4b
  (needs Ollama 0.30.9+; qwen3:4b as low-resource option). Docs do NOT
  mention the picker yet: it is not built. Tests: tests/test_ollama_models.py
  (21). Suite: 648 passed.
- Next: launcher picker (pick_provider returns
  '--provider ollama --model <name>'; caller at launcher.py ~614 joins and
  splits flags, so this is safe), then UI dropdown (app.py ~951 text box
  -> selectbox when provider is ollama and models are found; text box
  otherwise, e.g. Render), then fix _stream_ollama raw OLLAMA_MODEL.
- Noted: the launcher does not load .env, so ollama_models uses
  OLLAMA_HOST from the process environment or localhost:11434.
- `1df6081`: gemma4 default + ollama_models.py commit (above).
- Launcher model picker: `pick_ollama_model()` in scripts/launcher.py lists
  pulled models (describe line, `(default)` mark, `ollama pull` hints for
  ranked models not pulled). Enter = default. If Ollama is unreachable it
  warns and returns '' (no --model; the app picks). `pick_provider` asks
  only after the SR block, and returns '--provider ollama --model <name>'.
  The launcher imports ollama_models by appending SOURCE_CODE to sys.path.
  First launcher tests: tests/test_launcher_model_picker.py (9), which load
  the launcher by path with a dummy colorama. Checked by hand on the dev
  machine: 4 models listed, gemma4 default with Image/OCR yes, llama3.2 not
  ranked, pull hints shown, command included --model gemma4:e4b.
  README Step 2 item 5 mentions both the launcher and the UI. Suite: 657 passed.
- Next: UI dropdown (app.py ~951: selectbox when provider is ollama and
  models are found; text box otherwise, e.g. Render), then fix
  _stream_ollama raw OLLAMA_MODEL, then update #2 time limit.
  UI model picker: _ollama_model_choices() (lazy import of ollama_models, never queried for cloud providers or on Render); dropdown replaces the text box for Ollama; _local_run_blocked() disables Run when no local model is found. Bug found in browser check: local_block assigned inside the cloud-gate if (UnboundLocalError on every Ollama page). Fixed, and test_every_mode_page_renders_with_ollama_down (Streamlit AppTest) now renders every mode page so this kind of bug fails the suite. Tests tests/test_ui_model_picker.py (11). Suite: 668 passed.
  Time limit (backend): new stdlib-only time_limits.py (choices 15/30/60/none, default 15; wait_for() joins in 1 s steps so Ctrl+C works). main.parse_args() reads --time-limit and calls set_limit() once. The coding/writing watchdogs, the Ollama call and all three streaming urlopen timeouts read get_limit(); no hard-coded 900 s left. Error message names the actual limit. Limitations: (1) a timed-out call keeps running on its daemon thread, so Ollama keeps generating and the next call waits behind it; (2) a streaming timeout is the longest gap between chunks, not the total time; (3) with none, Ctrl+C may not interrupt a non-streaming Ollama call outside coding/writing on Windows, but closing the window always works. Launcher question and UI dropdown: next commit. Tests test_time_limits.py (23), test_time_limit_wiring.py (18). Suite: 709 passed.
  Time limit (launcher + UI): launcher pick_time_limit() asked after provider/model (Enter = 15 min adds no flag; skipped for --dry-run via time_limit_flag()); UI 'Time limit per AI call' dropdown (time_limits lazy-imported like ollama_models), passed through _launch_terminal to both _launch_terminal_local and _run_cli_cloud, then _build_cli_cmd(time_limit=...), which adds --time-limit only when not 15. Fixed during work: launcher from time_limits import had been indented inside the sys.path if-block. Tests: launcher +6, test_ui_time_limit.py (8). Suite: 723 passed.
  ## Session 31 handoff: OCR pipeline + Editor mode (written end of Session 30)

### State at end of Session 30
- Repo: D:\AI_kcMedicalResearch, Windows, PowerShell, `.venv`, Python 3.11.
- Branch `v2.5-major-updates`, HEAD `a375494`, PR #1 open with 8 commits.
- Tests: 723 passed, 3 skipped, 11 deselected (`python -m pytest -m "not live" --tb=short -q`).
  CI was green up to `f58bad6` (709). CI on `a375494` (723) not yet confirmed.
- Ollama 0.40.8. Pulled: gemma4:e4b (default, 7.5B, vision), qwen3:8b,
  qwen2.5:14b-instruct, nomic-embed-text.
- Done in v2.5 (all on PR #1):
  - local-first default and cloud gate;
  - `think: false` on all Ollama requests (`f836106`);
  - gemma4:e4b default and `ollama_models.py` (`1df6081`);
  - launcher model picker (`170c16b`);
  - UI model dropdown and Run blocked when no local model (`1acb851`);
  - time limit 15/30/60/none via `--time-limit`, `time_limits.py` (`f58bad6`);
  - launcher and UI time limit (`a375494`).

### Open items to settle first
1. Confirm CI green on `a375494` (expect 723 passed).
2. Decide: merge PR #1 into `main` before starting new work (recommended: OCR and
   Editor are new features, so they belong on a fresh branch, e.g. `v2.6-ocr-editor`),
   or keep adding to PR #1. Bump `Version: 2.4.13` in README/main.py at release.
3. Decide the order. Editor mode is text-only and touches fewer files; OCR needs
   design decisions first (see A1).

### Working rules (keep these)
- Read-only inspection first, then a failing test (check it fails for the right
  reason), then the code, then the full suite, docs, commit and push, then CI.
- Give edits as "select lines X-Y, paste this full block". Don't describe partial
  edits in words. When editing several places in one file, work from the bottom up.
- Don't claim a test result unless it was pasted. A page change needs both the
  AppTest render test and a browser check.
- After each commit: update the count in README.md line 7 and in the Current State
  table in HANDOFF.md (line 48) only. Counts inside session blocks are history:
  leave them, and add a new session note instead. Then run `python scripts/check_no_bom.py`.
- Modules the launcher imports must be stdlib-only (like `ollama_models.py`, `time_limits.py`).
- `ui/app.py` must lazy-import SOURCE_CODE modules (`_cli_module()`,
  `_ollama_models_module()`, `_time_limits_module()`). conftest.py hides a missing
  path, so tests pass but the real app crashes.
- Ollama is in `LOCAL_ONLY_PROVIDERS`: it never falls back to cloud. Keep it that way
  for any mode that handles patient documents.

### Task A: OCR pipeline (local, gemma4:e4b)
Known facts:
- `ollama show gemma4:e4b` lists capabilities: completion, vision, audio, tools,
  thinking, with a clip projector. Ollama `/api/generate` accepts `"images": [<base64>]`.
- The app sends no images to Ollama today. `call_ollama_provider`
  (providers.py) and `_stream_ollama` (streaming.py) send text only.
- `providers.PROVIDER_CAPABILITIES["ollama"]["vision"]` is False for every model.
  `ollama_models.model_capabilities(host, name)` (/api/show) already tells
  per model whether it has vision. Use that, not a fixed flag.
- Launcher `BLOCKED_FOR_SR = {'ollama','deepseek'}`; main.py ~1495-1520 warns that SR
  needs vision. Unblocking SR for vision-capable Ollama models is a separate decision.
- The time limit applies (images are slower; users may need 30/60/none).

Decisions needed (ask the user before writing code):
- A1. A new mode `--mode ocr` (input/ocr -> output/ocr), or OCR as a step inside other
  modes (e.g. scanned PDFs in SR/appraisal)? Or both: the mode first, reused later?
- A2. Input types: images only (png/jpg), or scanned PDFs too? PDFs need page
  rendering. Check which library is already installed before adding one.
- A3. Output: plain text, markdown, or both? One file per input, or per page?
- A4. Ollama only (confidential documents), or allow cloud vision providers behind the
  cloud gate?
- A5. If the chosen model has no vision: block Run with a warning, the same pattern
  as `_local_run_blocked()`.

First read-only commands:
    Get-ChildItem -Path SOURCE_CODE -Recurse -Include *.py | Select-String -Pattern "fitz|pdf2image|PIL|Image\.open|pytesseract|base64|supports_vision|\"images\"" | Select-Object Path, LineNumber, Line | Format-Table -Wrap
    Select-String -Path requirements*.txt -Pattern "pymupdf|fitz|pdf2image|pillow|tesseract" 
    Select-String -Path SOURCE_CODE\providers.py -Pattern "def call_\w+_provider|def call_ai|vision" | Select-Object LineNumber, Line

Places a new mode must be added (found in Session 30):
- main.py `--mode` choices (~line 2266) and the dispatch block (~2398-2442);
- launcher `MODES`, `_MODE_INPUT_MAP`, `show_help()` entries;
- ui/app.py `MODES` (the AppTest render test loops over it automatically);
- `main.data_destinations` / `SEARCH_SERVICES` (cloud gate);
- README modes table; help guide (`Readme/flashcard-help.html`).

### Task B: Editor mode (merge writing + editing + review)
Goal (user's words): simplify the writing mode, both the Topic track and the Article
track, into one "editor mode" that merges writing, editing and review.

Known facts:
- `SOURCE_CODE/pipelines/writing/writing.py`: `_call_llm` (~line 105) with the
  time-limit watchdog. Role calls: writer_out (~573), editor_out (~596), qa_out (~618),
  editor_out (~670), qa_out (~713). That looks like two flows (draft, and edit
  existing), but this is NOT verified.
- main.py imports from `pipelines.writing.writing` (~1908, ~1914); `--report` calls
  `generate_writing_report(provider, model)` (~2406).
- NOT yet seen: how the "Topic track" and "Article track" are chosen today.
  Note `--sub` 1=Topic Search / 2=Article Search belongs to SEARCH mode. Confirm with
  the user which "Topic/Article" is meant, and inspect before designing.

Decisions needed:
- B1. Name: rename `writing` to `editor` and keep `--mode writing` as an alias so
  existing scripts and docs work? Or keep the flag and just change the behaviour?
- B2. One combined LLM pass (write+edit+review in one prompt; fewer calls, faster
  on local models), or keep the internal roles but show the user one mode and one
  output? Trade-off: one pass is faster; separate review catches more.
- B3. Tracks become submodes of editor: Topic = draft from a topic/outline,
  Article = revise an existing manuscript. Same output shape for both?
- B4. Output: revised text + a short change log + review comments, in one file
  or separate files?

First read-only commands:
    Select-String -Path SOURCE_CODE\pipelines\writing\writing.py -Pattern "^def |topic|article|track|_call_llm\(" | Select-Object LineNumber, Line | Format-Table -Wrap
    Select-String -Path SOURCE_CODE\main.py -Pattern "writing|topic|article" | Select-Object LineNumber, Line | Format-Table -Wrap
    Select-String -Path SOURCE_CODE\ui\app.py -Pattern "writing|topic|article|submode" | Select-Object LineNumber, Line | Format-Table -Wrap
    Get-ChildItem -Path tests -Filter *.py | Select-String -Pattern "writing" | Group-Object Path | Select-Object Count, Name

Tests that will be affected:
- `tests/test_time_limit_wiring.py` imports `pipelines.writing.writing._call_llm`;
- `tests/test_ui_model_picker.py::test_every_mode_page_renders_with_ollama_down`
  (loops over MODES);
- `tests/test_ui_time_limit.py` (uses "writing" mode and key `time_limit_writing`);
- launcher tests; cloud gate tests (`data_destinations` per mode);
- whatever the last command above lists.

### Known limitations carried forward
- A timed-out call keeps running on its daemon thread. Ollama keeps generating and
  the next call waits behind it.
- A streaming timeout is the longest gap between chunks, not the total time.
- With `--time-limit none`, Ctrl+C may not interrupt a non-streaming Ollama call
  outside coding/writing on Windows. Closing the window always works.
- CI shows 44 warnings (unpinned versions); not urgent.

## Session 31 - 2026-10-26 - branch v2.5-major-updates

- `_stream_ollama` (streaming.py) now uses `_resolve_ollama_model()` instead
  of the raw `OLLAMA_MODEL`. Before, with no `--model` and no OLLAMA_MODEL in
  .env, streaming sent an empty model name, while the batch route
  auto-detected. The launcher and UI pickers usually pass `--model`, which hid
  the bug. Session 30 planned this fix for the model-picker commit, but it was
  never made; a grep at session open found it. Tests:
  `test_ollama_streaming_resolves_model_when_none_configured` (failed before
  the fix with `'' == 'sentinel-model:1b'`) and
  `test_ollama_streaming_explicit_model_wins`.
  Suite: 725 passed, 3 skipped, 11 deselected.
- Follow-up: streaming.py probably no longer uses `OLLAMA_MODEL`. If you drop
  it from the import, also remove the two
  `monkeypatch.setattr(streaming, "OLLAMA_MODEL", "")` lines in
  tests/test_streaming.py, or they fail with AttributeError.
- Doc drift noted, not fixed: line 479 (Session 29 close block) says
  723 passed, but the suite was about 624-627 then. The old rule "update lines
  48 and 479" overwrote it. Fix it in a separate docs commit.
- CI on `a375494` still not confirmed.
- Cleanup: `Readme/REVIEWER_GUIDE.md` moved to `docs/sr/REVIEWER_GUIDE.md`
  (exact copy, recorded as a rename). `tests/test_source_quote_doc_sync.py`
  finds it with rglob, so it needs no change, but it fails if two copies exist.
  The SR messages in `pipelines/sr/main.py` (3) and the comment in
  `data_extractor.py` still say just `REVIEWER_GUIDE.md`; add the folder later.
- `docker/` removed; #28 closed as Won't do (in RESOLVED_ISSUES). Render was
  confirmed as `runtime: python` in render.yaml. Removed with it: the README
  "Local with Docker" quick start and its "not verified" line, the "Ollama in
  Docker" note, and the flashcard Docker block (its two scripts were already
  missing).
- The archive, RESOLVED_ISSUES.md and the S26 evidence JSONs had been deleted
  by accident; restored. The evidence is needed for Session 28 priority 2.
- Noted, not fixed: the flashcard-help.html footer says v2.4.6, 401 tests and
  "DeepSeek default". Update it in its own commit.
- Noted, not fixed: `Get-Content -Index` and `Select-String` give different
  HANDOFF line numbers after line 48 (off by 2), probably a stray line-break
  character. Search by text, not by line number, until it is found.
- Hosted app's Provider dropdown no longer starts on Ollama. New
  `_default_provider_index()` in ui/app.py: locally always Ollama (even if
  .env sets DEFAULT_PROVIDER or STREAMLIT_SERVER_PORT is set); on Render (only
  the RENDER* variables count) a cloud DEFAULT_PROVIDER if set, else the first
  cloud provider in PROVIDERS. Before, Render visitors landed on Ollama with
  Run blocked. This closes the Session 29 follow-up "Render UI provider dropdown
  starts on ollama". render.yaml does not set DEFAULT_PROVIDER; check the
  Render dashboard, since the fallback (openai) needs an OpenAI key there.
  Tests: TestDefaultProviderIndex (6) and
  test_render_page_does_not_start_on_ollama (AppTest; failed before the fix
  with 'ollama' not in {'ollama'}). Browser check: local starts on ollama,
  RENDER=true starts on a cloud provider. Suite: 732 passed, 3 skipped, 11 deselected.
- Noted, not fixed: on the home page the Systematic Review card is taller
  than the other five (icon/text sit lower), so its buttons do not line up.
  Cosmetic; fix the card CSS in app.py in its own commit.
- Version bumped 2.4.13 -> 2.5.0 for the v2.5 merge: main.py VERSION, README
  line 6, and the four launcher scripts (header comment + banner each).
  Historical mentions of 2.4.13 (archive, RESOLVED_ISSUES, REVIEWER_GUIDE,
  test comments) left as they are. The flashcard footer still says v2.4.6.
- Merged PR #1 into main (`55d4fd3`); suite 732 on main. New branch
  `v2.6-ocr-editor` for the work below and for OCR / Editor mode.
- BOM checker blind spot: `check_no_bom.py` filtered by `path.suffix`, and
  Python gives dotfiles no suffix (`Path(".gitattributes").suffix == ""`), so
  no dotfile was ever checked. The real `.gitattributes` had a BOM: git read
  BOM + `#` as a rule and printed "Default: is not a valid attribute name" on
  every command. Fix: `CHECK_NAMES` (.gitattributes, .gitignore, .env.example,
  .editorconfig; never .env) in both check_no_bom.py and strip_bom.py.
  strip_bom.py had its own copy of the lists and the same blind spot, so the
  checker's "Fix with strip_bom.py" advice would have skipped the file.
  BOM removed with strip_bom.py itself. Tests:
  `test_dotfiles_without_a_suffix_are_scanned`, new tests/test_strip_bom.py
  (list sync with check_no_bom.py + dotfile strip). All failed before the fix.
  Suite: 735 passed, 3 skipped, 11 deselected.
- Corrects the follow-up "add .gitattributes for line endings": it exists
  (`* text=auto`, `*.sh eol=lf`, `*.bat eol=crlf`, ...); only the BOM was wrong.
- Render fix: utils/rag.py imported chromadb at module level; requirements-render.txt omits it, so the UI cloud gate (imports main -> pipelines -> utils.rag) failed and every hosted cloud run was blocked ("Could not determine where this job's data would be sent"). Import moved into _get_client(); all three RAG call sites in main.py already catch errors, so hosted runs print "[RAG] Indexing skipped" and continue. tests/test_render_without_chromadb.py hides chromadb in a subprocess (local and CI both install it, so nothing else could catch this). Suite: 737 passed.
- Lesson: render.yaml is not applied (service created by hand); the Render dashboard is the source of truth for env vars.
- Lesson: Render env vars go on the web service's own Environment tab (service → left menu → Environment → Edit), not a project environment, an env group, or the "+ New" service form. Changes need Save, rebuild, and deploy. Never paste keys into chat; one was exposed and rotated this session.
- input/ guard: tests/test_gitignore_input.py pins that user data in input/ is ignored and only input/sr/pico_sample.json and input/sr/study_overrides.yaml stay committable (rules were already in .gitignore). Verified by commenting out input/* (coding and writing paths then failed). Note: `git check-ignore input` tests the folder name and prints nothing for `input/*`; test a file path instead. Suite: 743 passed.
- Open: "Apply PICO" (ui/app.py ~line 1101) overwrites tracked SOURCE_CODE/pipelines/sr/config/prisma_criteria.yaml; should write to a user file instead. Until fixed, `git restore` it if it shows as modified.
