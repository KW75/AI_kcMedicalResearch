# HANDOFF

Single source of truth for the next session. Read this, then work.
Session-by-session history (1-23) is in `Readme/HANDOFF_archive_pre_S19.md`
and git log; consult it only before reopening a closed issue.

Repository: https://github.com/KW75/AI_kcMedicalResearch
Live app:   https://ai-kcmedicalresearch.onrender.com
Health:     https://ai-kcmedicalresearch.onrender.com/_stcore/health

---

## Current State (Session 25, v2.4.13, 2026-08-29)

| Component      | Status |
|----------------|--------|
| Tests          | 526 passed, 3 skipped, 11 deselected (`python -m pytest -m "not live" --tb=short -q`) |
| CI             | green (64a043d; 19a583e, 7791f43, and 1458834 all confirmed green) |
| Render deploy  | green — health returns `ok` on 7791f43 (19a583e and 64a043d are CLI/docs only, no UI impact) |
| SR pipeline    | working via CLI with Qwen (#65 fixed S24); extraction non-deterministic (#11), verify every number |
| Providers      | DeepSeek (default) / Qwen (SR) / OpenAI / Anthropic / Groq / Ollama (local, never falls back) |

Issue numbers below match `README.md` > Known Issues.

---

## Open Issues

| #  | Issue | Priority | What to do |
|----|-------|----------|------------|
| 11 | Extraction non-determinism (Ang, Jensen, Lami) | High | All three pinned by regression fixtures (Sessions 20-22). Underlying non-determinism unaddressed; mitigation is still run 3x and diff, verify against source quotes. See Session 26 priority 1 for reduction options. |
| 28 | Docker route never executed end to end | High | Hardware-blocked (no Docker on dev machine). |
| 19 | macOS launchers untested on macOS | Medium | Hardware-blocked. |
| 2  | WeasyPrint not installed; PDF report falls back to HTML | Medium | |
| 15 | RoB 2.0 ignores `study_overrides.yaml` | Low | |
| 3  | Anthropic geo-restricted from dev machine | Low | VPN or skip. |

---

## Session 25 Summary

Three commits, two of them code. 523 -> 526 tests. Every priority from
the Session 24 handoff addressed or explicitly deferred; two known
issues closed (#66, guide nit carryover). No new issues opened.

- **Priority 1 verification (no commit).** Confirmed CI green on
  `1458834` (Session 24's last code commit) via check-runs API:
  `test (3.11)` completed, conclusion success. Render
  `/_stcore/health` returns `HTTP 200 / ok`. `7791f43` (the S24
  handoff doc commit) also green. Neither hash needed a follow-up
  code fix; state rolled into this handoff.

- **#66 closed (19a583e).** Extracted the Stage-4 summary block from
  `main()` in `SOURCE_CODE/pipelines/sr/main.py` into a module-level
  `_log_stage4_summary(meta_audit, er, effect_measure)` helper.
  Introduced a uniform `n_extracted` denominator (any of mean/sd/n per
  arm, hedges_g, or one of the three tripwire warning fields set) for
  the four tripwire "clean" branches. Guarded the `[OUTCOME/TIMEPOINT]`
  provenance block so fully-empty rows no longer emit `? ():` lines.
  Pinned by `tests/test_stage4_summary.py` (3 cases): zero-extraction
  prints `0 of 0` and does NOT print the "every extracted value was
  bound" sentence; one clean study still prints the positive sentence
  and `0 of 1`; a mixed skipped+extracted meta_audit reports
  `n_extracted` not `len(meta_audit)`. `[SD/SE CHECK]` kept its
  partial `_n_checkable` denominator — vision-path studies are "not
  checkable", not "clean" (Known Issue #9). `[PLAUSIBILITY]` for MD
  still prints "check skipped (scale-dependent)". Refactor was
  +272/-83 lines in `main.py` (the helper carries its own rationale
  comments) plus +126 lines of test.

- **Guide nit closed (64a043d).** `REVIEWER_GUIDE.md` §2.2 branch 2
  and §6 both listed "decimal separator differences" as a limitation
  of the number-in-quote matcher. Verified against
  `SOURCE_CODE/pipelines/sr/src/extraction/data_extractor.py` line
  1022: `_number_in_text` does
  `re.escape(candidate).replace("\\.", "[.,]")` before matching, so
  `1.5` matches `1,5`. The real remaining gaps are unicode-vs-ASCII
  minus signs and thousands separators; those stay documented. Same
  lesson as #12 in S24: verify the current source before treating a
  documented claim as work.

- **Handoff-vs-artifact catch (this session).** The Session 24 handoff
  said #66 was in "the four Stage-4 summary lines in `main.py`". The
  repo has two `main.py` files: the top-level CLI dispatcher
  (`SOURCE_CODE/main.py`) and the SR sub-pipeline
  (`SOURCE_CODE/pipelines/sr/main.py`). A grep of the top-level file
  for `SOURCE QUOTE CHECK` returned nothing; the Stage-4 code was in
  the latter. Added to durable lessons.

- **Priorities 3 and 4 not touched.** Priority 3 (#11 mitigation)
  awaits a judgment call on whether reviewer time on the manual
  run-3x-and-diff step is the bottleneck. Priority 4 (decoder
  `!`-for-space gap) is an investigation task; no corpus PDF exercises
  the code path today, and Session 24 already documented that the
  decoded text keeps `!` where spaces were.

## Next Session Priorities (Session 26)

1. **#11 mitigation, if worth the effort.** Unchanged from S24/S25.
   Cheapest first: `temperature=0`/`seed` on the Qwen vision call
   (vision models often ignore seed, may not help). Expensive:
   internal N=3 agreement with `nondet_flag` (machine-enforces the
   manual run-3x step). Skip if reviewer time on the manual step is
   not the bottleneck.

2. **Decoder `!`-for-space gap, low.** `_shift_text` shifts letters
   only, so a +1-shifted PDF's spaces (arriving as `!`) stay as `!`
   after decode. Fine for the LLM screener; may matter if the
   extractor's text-fallback ever receives decoded text. Check whether
   it does before deciding it matters — no corpus PDF exercises this
   path today.

3. **Housekeeping carryovers** from S24 (still open per current
   `git status` on any dev machine): add `run_*.log` to `.gitignore`,
   delete `input/s24_mccrae/` when done with it, verify
   `.venv\Scripts\` Python is the one resolving, delete stale
   `%TEMP%\ai_km_run_*.bat` files on any machine that ran the
   pre-v2.4.7 UI launcher.

## Housekeeping (low priority, carry until done)

- Add `run_*.log` to `.gitignore` (two untracked from Session 24) and
  delete `input\s24_mccrae\` when done with it.
- Confirm `.venv\Scripts\` Python is the one resolving (a system Python
  was once seen behind a `(.venv)` prompt).
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
  paper extracts reliably". Lami and Jensen still need the
  run-3x-and-diff reviewer step; the fixtures only guarantee that a
  known good shape won't be falsely rejected and a known bad shape
  will still be caught. #11's underlying non-determinism is unchanged.

---

Handoff prepared: 2026-08-29, Session 25.
