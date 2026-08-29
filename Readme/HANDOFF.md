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

## Current State (Session 26, v2.4.13, 2026-08-29)

| Component      | Status |
|----------------|--------|
| Tests          | 565 passed, 3 skipped, 11 deselected (`python -m pytest -m "not live" --tb=short -q`) |
| CI             | green (fb69d50; b847c55 and bb48040 also confirmed green) |
| Render deploy  | not re-checked after fb69d50; S26 commits touch the SR CLI, extractor, and docs only (no UI change). Confirm health returns `ok` at S27 open. |
| SR pipeline    | working via CLI with Qwen; vision extraction voted N=3, read `nondet_flag`; Ang's correct reading unverified (#67) |
| Providers      | DeepSeek (default) / Qwen (SR) / OpenAI / Anthropic / Groq / Ollama (local, never falls back) |

Issue numbers below match `README.md` > Known Issues.

---

## Open Issues

| #  | Issue | Priority | What to do |
|----|-------|----------|------------|
| 28 | Docker route never executed end to end | High | Hardware-blocked (no Docker on dev machine). |
| 19 | macOS launchers untested on macOS | Medium | Hardware-blocked. |
| 2  | WeasyPrint not installed; PDF report falls back to HTML | Medium | |
| 3  | Anthropic geo-restricted from dev machine | Low | VPN or skip. |




---

## Current State (Session 27, v2.4.13, 2026-08-29)

| Component      | Status |
|----------------|--------|
| Tests          | 569 passed, 3 skipped, 11 deselected (`python -m pytest -m "not live" --tb=short -q`) |
| CI             | green (28e616e; 3a9081b and 6813b12 also confirmed green) |
| Render deploy  | health returned `ok` on 28e616e (S27 close) |
| SR pipeline    | working via CLI with Qwen; Ang 2010 verified against PDF (NFR week 6, unanimous N=3); text-fallback drops now surface in Stage 4 `[SKIP]` block |
| Providers      | DeepSeek (default) / Qwen (SR) / OpenAI / Anthropic / Groq / Ollama (local, never falls back) |

Issue numbers below match `README.md` > Known Issues.

---

## Open Issues

| #  | Issue | Priority | What to do |
|----|-------|----------|------------|
| 28 | Docker route never executed end to end | High | Hardware-blocked (no Docker on dev machine). |
| 19 | macOS launchers untested on macOS | Medium | Hardware-blocked. |
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

  **A handoff describing a run's content is a snapshot, not an invariant.**
  S26 wrote "Ang shows table_shift on FIQ readings" as a standing property.
  By S27 the pipeline was extracting NFR-threshold, unanimous, no shift.
  One session's specific numbers and flags will not survive a code change.
  Describe behaviours the reviewer must verify, not outputs from a run
  they can't reproduce.

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

Handoff prepared: 2026-08-29, Session 27.

