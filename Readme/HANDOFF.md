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
| 68 | Source-quote tripwire false-positives on Unicode minus/dash. `_number_in_text` compares ASCII `-` (U+002D) against Unicode `−` (U+2212) etc. and fails. Ang's run today fires the tripwire on both arms despite the numbers being present in the quotes. Fix: normalise U+2212, U+2013, U+2014, U+FE63, U+FF0D to `-` on both value and haystack before comparing. | Medium |
| 69 | Text-fallback path doesn't recover n_intervention / n_control. Lami's Ns come only from study_overrides.yaml; removing the override leaves both cells empty and Lami silently drops from any pooled estimate. Any future paper routed to text-fallback has the same failure mode. Fix: either a second text-fallback pass targeted at Ns, or a MANDATORY tripwire when text_fallback yields empty Ns. | Medium |



---

## Session 26 Summary

Three commits: `b847c55` (extractor + probe + evidence), `bb48040`
(CSV / Stage-4 / CLI wiring), `fb69d50` (docs). All three CI green.
526 -> 565 tests. #11 closed as machine-flagged; #66 migrated to
RESOLVED_ISSUES (S25 doc lag); #67 opened. Every other priority from
the S25 handoff explicitly deferred (unchanged from S25).

- **#11 cheap branch measured and rejected.** Before touching sampling,
  grepped the call site: `_call_vision_api` was at `temperature=0.1`
  while both text paths were at `0`, and no call sent `seed`. Built
  `SOURCE_CODE/pipelines/sr/scripts/nondet_probe.py` (N runs per PDF,
  per-field agreement table, JSON out) and ran 5 corpus PDFs x 3 runs
  at the old setting and at `t=0, seed=42`. Both: 4/5 PDFs disagreed.
  Source-quote hashes differed run-to-run under identical config, which
  is impossible if seed were honoured — qwen-vl-plus ignores it and
  `t=0` is not deterministic. Ang at `t=0` returned three different
  tables in three runs; run 1 was a column shift that passed SOURCE
  QUOTE CHECK. Evidence: `Readme/evidence/s26_issue11/*.json`.
  Sampling controls kept (`SR_EXTRACT_TEMPERATURE`, `SR_EXTRACT_SEED`,
  default 0/42) only so the vision and text paths can't drift again;
  `tests/test_extractor_sampling.py` pins that all three call sites
  share them.

- **#11 closed by N=3 agreement (b847c55, bb48040).**
  `DataExtractor(n_agreement=3)` / `SR_EXTRACT_N_AGREEMENT` /
  `--n-agreement`. `_extract_vision_with_agreement` calls the vision API
  N times on the same page images, `_vote_runs` majority-votes
  mean/sd/n per arm (float/int-coerced) and both group labels
  (`_normalize_label`-coerced). Source quotes are NOT voted: the quote
  is carried from a run whose (mean, SD) match the chosen values for
  that arm, so the quote tripwire still tests a number against its own
  quote. `nondet_flag` is always written: `[]` unanimous;
  `field:majority`; `field:no_majority` (run-1 value kept);
  `table_shift` (all four mean/SD disagree, or one arm's pair equals
  the other arm's chosen pair; guarded for genuinely identical arms);
  `usable_runs:k/N`; `["single_run"]` for N=1 and the text fallback.
  `audit_logger.nondet_flag_to_cell` renders it for
  `meta_analysis_results.csv` (`unanimous` / `not_checked` / joined);
  `nondet_flag` and `nondet_runs` added to `write_results` fieldnames.
  `_log_stage4_summary` prints `[AGREEMENT] k of n voted studies` with
  a voted-only denominator — an N=1 run prints "not checked", never
  "0 flagged" — and tags `no_majority`/`table_shift` rows MANDATORY.
  Cost: ~+20 s and 2 extra vision calls per study.

- **Acceptance run** (`nondet_probe.py --runs 2 --agreement 3`, 5 PDFs):
  Ang flagged in both runs (all four mean/SD `majority`, `table_shift`
  after the follow-up); Jensen, 1-s2.0, Lami, zsy234 came out `[]` in
  both. Tallying every Ang call of the day, the two competing readings
  were drawn 5 and 6 times of 12 — a coin flip, hence #67.

- **Three findings recorded in the guide, not fixed:** the source-quote
  tripwire fires non-deterministically (zsy234 #64 warning on 1 of 3
  runs) because the quote varies while the number holds; Lami's
  `MANUAL OVERRIDE` masks raw drift (13.79 vs 13.68 mean, 4.22 vs 4.61
  SD); `outcome_selected` wording varies on Ang ("FIQ pain rating" vs
  "FIQ pain score"), cosmetic, not voted.

- **Housekeeping hit in passing.** The probe's error line showed
  `C:\Users\...\Python311\python.exe` resolving behind a `(.venv)`
  prompt — the item below is real, not historical. Not fixed.

## Next Session Priorities (Session 27)

1. **Render health on fb69d50.** CI is confirmed green on all three
   S26 commits; the health endpoint was not hit. One request.

2. **#67 — Ang Table 2.** Human task, ten minutes, blocks every pooled
   estimate that includes Ang. Record the reading in
   `study_overrides.yaml` with page/table in `note:`, then re-run the
   corpus once and confirm the Ang row shows the override applied and
   `table_shift` still fires (the override corrects the value; it does
   not, and should not, silence the flag).

3. **Decide on voting `outcome_selected` / `timepoint_selected`.**
   Today they are recorded, not voted. Ang's wording varied
   cosmetically; a run that picks a different *timepoint* would not be
   flagged by the vote unless the numbers also moved. Probably worth a
   normalised-label vote like the group labels. Low effort.

4. **Decoder `!`-for-space gap, low.** Unchanged from S25.

5. **Housekeeping carryovers**, unchanged — and the `.venv` item is now
   confirmed live (see S26 summary).

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


---

Handoff prepared: 2026-08-29, Session 26.
