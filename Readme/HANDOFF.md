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
2. **Closed-issue citation grep.** Take the issue numbers from the table
   rows of `Readme/RESOLVED_ISSUES.md` (pattern `^\|\s*(\d+)\s*\|`; print
   the count so "clean" cannot mean "never ran"). The pattern `#(\d+)`
   finds only numbers cited in passing. Grep `README.md` and this file's
   Current State / Open Issues / Next work sections for `(#N)`. Any hit
   is a stale citation; replace it with a positive description or a
   REVIEWER_GUIDE section reference. Hits inside session logs are history.
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

## Current State (Session 38, v2.6.0 on main, 2026-11-11)

| Component      | Status |
|----------------|--------|
| Tests | 1265 passed, 10 deselected on v2.10-sr-screening (Session 39); main 1064 (ef66b9f) (python -m pytest -m "not live" --tb=short -q) |
| Branch         | main = ef66b9f (PR #7 merged 2026-11-10: F7 truth fixture sr_truth.yaml + scripts/sr_score_run.py). Work on v2.10-sr-screening, PR #8 open: shared paper text (b3d804c), prisma_criteria write-if-changed (afd90a3), RoB2 overall rule (3e3785e), RoB2 Methods/Results text (908f889, 306d838), registration lines to RoB2 (Session 38); Session 38: Karlsson/Ang overrides (cf75209), RoB2 Domain 4 self-report rule (46fbd9b), Domain 4 High outright (e4e97b8), Ang excluded by reviewer + not-pooled report section (a56dc55), plain report reasons + POOLED line (0bf59dc), fibromyalgia set moved to reference/ (7h, b32f4c4), REVIEWER_GUIDE rewrite + readme_sr_pipeline.txt (docs, this commit). Branches v2.6-ocr-editor, v2.5-major-updates, v2.7-sr-fixes, v2.8-sr-review-gate, v2.9-sr-fixture deleted |
| CI | green on PR #8 at 776b3d9 (1265 passed, 10 deselected, 57 warnings). Last confirmed on main: bcd42d9 (2026-11-09, 1027, both jobs). Runs only on push to main and PRs to main (ci.yml lines 4-7) |
| SR docs        | Readme/readme_sr_pipeline.txt = for users: how the SR pipeline works and how to use it. docs/sr/REVIEWER_GUIDE.md = for reviewers: what to check by hand, documented failures, limitations, methods statement (rewritten Session 38; section numbers 2.2, 3.1, 3.5, 5, 6 are cited by code/tests/README, keep them). README.md = the app. Update the SR docs when SR behaviour changes |
| Deploy         | None: CLI only, local first. Render service deleted 2026-10-27; Streamlit UI and Render files removed in Session 33. UptimeRobot monitor for the old Render URL: not yet confirmed paused/deleted (user, outside the repo) |
| Writing mode   | one-pass (write + edit + review in one call); tracks Topic 800 / Article 3,500 / Report 500 / Synopsis 1,500; on main since fa4edb9; tested on gemma4:e4b; terminal menus only |
| OCR mode       | `--mode ocr`, launcher menu 8. Reads PDF / image / .txt / .docx; .doc refused with a message. Records in `reports/ocr/<header>/`, SUMMARY / SYNOPSIS in `output/ocr/`. Ollama by default; Qwen / OpenAI only behind the cloud gate; groq / deepseek / anthropic refused. Broken-font PDFs: text layer with [?], AI fills symbols only, document-wide vote per font code. [?] left varies run to run (Ang 2010, gemma4:e4b: 19 in s36_check, 7 in s36_vote; vote fills checked against Table 2) |
| SR pipeline    | working via CLI with Qwen; Ang 2010 verified against PDF (NFR week 6, unanimous N=3); text-fallback drops surface in Stage 4 `[SKIP]` block. Hard-coded `qwen-vl-plus` (404 on the current key) still in the SR extractors (see Next work) |
| Providers      | Ollama (default, local, never falls back to cloud; model = OLLAMA_MODEL in .env, else gemma4:e4b) / DeepSeek / Qwen (SR) / OpenAI / Anthropic / Groq. Anthropic and Gemini are geo-restricted on the dev machine; the planned Anthropic -> Gemini switch is on hold |


Issue numbers below match `README.md` > Known Issues.

---

## Open Issues

| #  | Issue | Priority | What to do |
|----|-------|----------|------------|
| 2  | WeasyPrint not installed; PDF report falls back to HTML | Medium | |
| 3  | Anthropic and Gemini geo-restricted from dev machine | Low | VPN or skip. Blocks the planned Anthropic -> Gemini switch. |

---

## Next work (start here)

Updated at Session 38 close (2026-11-11). Done items are removed; the
Session 38 log keeps the evidence. This list is the only place to tick
items off. Old item IDs (7i, 7n, ...) in brackets for tracing.

SR - review content
1. DONE (2026-11-12): criteria in the PICO step (old 7i). _create_pico /
   _modify_pico ask inclusion/exclusion after the Outcome (';'-separated;
   defaults RCT; Adult participants / Non-RCT; Animal studies; Enter keeps),
   saved in pico_<timestamp>.json, written to prisma_criteria.yaml via
   _criteria_from_pico (hard-coded lists removed). Comparator default
   "Usual care, attention placebo or waiting list (pooled)"; typing
   Exclude_WaitList saves "Usual care or attention placebo" (create and
   modify). tests/test_sr_pico_criteria.py (12). Docs: readme sections 1
   and 3, REVIEWER_GUIDE 4.1.
2. DONE (2026-11-12): 7h leftovers. Run 20261111_190839 had been copied
   into a misspelt folder "referemces/" (this was the "ouput" mix-up; the
   output folder name was already correct); moved to
   reference/sr_cbt_fibromyalgia/reports/20261111_190839 (complete: console,
   score, CSVs, report; "Loaded 4 study override(s)", pooled SMD -0.042
   [-0.327, 0.242], I2 0%, k=3). Duplicate top-level output/ deleted. Also
   kept locally: 20261111_175754 (before Ang excluded) and 20261112_161648
   (no overrides: Ang + Karlsson pooled, SMD 0.030). Reference README: full
   citations (Lami = 2018;42:63-79, online 2017), three runs described,
   old comparator wording noted, restore steps. pico_sample.json name kept
   (README says it is search output; renaming touches .gitignore/tests).
2a. DONE (2026-11-12, 4095e1f): launcher writes the run criteria to
    input/sr/prisma_criteria.yaml (git-ignored) and passes --config and
    --run-id; the tracked sample in pipelines/sr/config is never written.
    A saved PICO is prefilled in the normal P/I/C/O questions (no "Modify
    this PICO? [y/N]"); new pico_<timestamp>.json only if changed. P/I/O
    required; empty P/I/O also stop a direct run (placeholder_fields).
    PICO JSON copied to reports/sr/<run_id>/ after a successful run.
    tests/test_sr_launcher_config.py (11). Reference README removed; its
    content is in Readme/readme_sr_pipeline.txt section 1 (old version:
    git show b274d24:reference/sr_cbt_fibromyalgia/README.md).
    Verified by launcher run 20261112_210735 (new comparator default, 4
    overrides): same result as 20261111_190839 (Karlsson 0.226, Lami
    -0.029, McCrae -0.227; SMD -0.042 [-0.327, 0.242], I2 0%, k=3). Open
    cosmetic: the [OUTCOME/TIMEPOINT] log block prints twice.
3. DONE (2026-11-12): Jensen override in
   reference/sr_cbt_fibromyalgia/study_overrides.yaml (Table 3 p7, weekly
   FM pain VAS 0-100 posttreatment, 49 (19) CBT vs 59 (26) waiting list;
   brackets confirmed SD; N = completed treatment 19/15 (Fig 1 p3; 25/18
   randomised)). Test test_reference_override_jensen_values. Commit
   e7b7b85. Run 20261112_222233 (launcher, saved PICO reused, "Loaded 5
   study override(s)"): Jensen g=-0.437 [-1.106, 0.232]; pooled SMD
   -0.103 [-0.365, 0.159], I2 0%, k=4; Ang excluded. New reference run
   (local only: reference/sr_cbt_fibromyalgia/reports/20261112_222233; no
   console.txt). DONE (Session 39): truth Jensen N 19/15 (inferred), matches the
   override; pinned by tests/test_sr_truth_override_sync.py.
4. DONE (Session 39): report cosmetics (old 7n, 7f+) a-e; see Session 39 log.
5. SR LaTeX check: DONE (Session 39), no code change - no stray $...$ in
   run 20261112_222233 outputs. Console not checked (no log saved).
   PDF: WeasyPrint not installed (HTML-only, by decision); summary now says why.
6. Run-to-run variation (old 7l): DONE (Session 39), no code change -
   1 of 30 RoB2 cells varied over 4 runs, overall never; no vote.
   RoB2 dropout numbers can be wrong (flow-diagram arm order lost):
   reviewer checks them (see Session 39 log). Stale log text: DONE (6a).
7. Screening 6000 chars: DONE (Session 39), no code change - 20 of 20
   INCLUDE over 4 runs; kept for cost (see Session 39 log).

SR - extraction checks
8. F8: N check DONE (Session 39) - arm N must appear in its quote when the
   quote has candidate Ns. Open: arm-label check (needs full arm list; with
   item 10).
9. F6: NOT BUILT (Session 39) - whole-paper number check caught 1 of 22
   wrong values, 2 false alarms; quote-vs-paper check moved to item 10.
10. Wire paper_text into extraction: DONE (Session 39, option A) - images
    stay the extraction input; paper_text goes to the quote check only
    (branch 5). See Session 39 log.

SR - report
11. Control-type subgroups: 11a (subgroups by control type) and 11b
    (estimate excluding waiting-list trials) DONE (Session 39, see log).
    11d REVIEWER_GUIDE section 5.2 DONE. Open: 11c forest plot grouped
    by control type; 11e check the
    [SUBGROUP] lines and report section on the next real run.

SR - local-first (after 1-11)
12. Ollama vision for SR (Session 35 TODO SR item 3):
    a. Launcher: remove ollama from BLOCKED_FOR_SR (scripts/launcher.py
       line 198, checked at 487 and 532); allow only when
       ollama_models.model_capabilities lists "vision" (as OCR does).
    b. data_extractor.py: add ollama to vision_providers (lines 219-228)
       via OLLAMA_URL/v1 after checking image parts work there, or use
       call_ollama_provider(images=...). rob2_tool.py reads OLLAMA_URL,
       the rest of the app OLLAMA_HOST: settle one name.
    c. providers.py line 77: ollama vision=False for the whole provider;
       decide per model.
    d. OLLAMA_CONTEXT (default 32768) must fit 5 page images per call.
    e. No local vision model: offer cloud only after a typed "y";
       DeepSeek stays blocked.
    f. Verify only: hard-coded qwen-vl-plus was removed in Session 37.
       Grep SOURCE_CODE and scripts for 'qwen-vl-plus'; expect tests and
       comments only.
    g. Test: gemma4:e4b on the reference set, N=3, field by field vs
       qwen3-vl-plus and the PDFs (sr_score_run.py "AI alone" lines).

SR - carried
13. Baseline SR run on qwen3-vl-plus checked against the PDFs; rerun the
    nondet probe before REVIEWER_GUIDE section 6 claims anything about it.
14. Corrected paper text: paper_text.py caches input/sr/paper_text/<name>.txt
    and reruns reuse it. Still open: a PDF hash so a replaced PDF with the
    same name does not reuse stale text; "[?] left: N" per paper; run-1 vs
    run-2 comparison. Check Tesseract-missing behaviour in
    relevance_screener.py. HybridTableExtractor (built only by tests): wire
    in or remove. Text-based screening/RoB2 for CBT-women and zsy234
    UNVERIFIED until checked.
15. Session 28 priorities: vote outcome_selected / timepoint_selected;
    Ang outcome change S26 -> S27 (Readme/evidence/s26_issue11/); decoder
    !-for-space gap (low).

OCR
16. One-file run without SUMMARY (Session 37 decision; single-vote fills:
    see Session 37 log); Tesseract as second reader for [?] left (Session
    36 log); leftovers: "decrease of -10.2" double negative, nested bullets
    in SUMMARY .docx, "AI answers for refused lines" message, LaTeX in fill
    answers before _accept.

Writing
17. Read input through the OCR reader so .docx tables reach the AI; a read
    error must be a [SKIP] message; `--report` path (main.py ~985-998) and
    `list_input_names` still skip .doc silently.

Other
18. Menu 7 Data Analysis: design questions first.
19. Outside the repo: confirm the UptimeRobot monitor for the old Render
    URL is paused or deleted (user).

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
  CLOSED (Session 35): test_providers.py::test_ollama_404_tells_user_to_pull_model
  and tests/test_ollama_missing_model.py.

Verified by code review only: confirmed coding pipeline honours OLLAMA_MODEL
(coding.py uses an injected call_llm_fn, no hard-coded model); confirmed
Ollama never falls back to cloud (LOCAL_ONLY_PROVIDERS in providers.py);
confirmed DASHSCOPE_ANTHROPIC_URL / DASHSCOPE_OPENAI_URL are dead config
(unused in providers.py, main.py, streaming.py). NOT yet verified on real
hardware: a 14B pull and a demo run converging. Do before rollout.


## Session 28 priorities (history; the open ones are listed in "Next work")

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


Durable Lessons last added: Session 29 (2026-10-22).
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
  Not fully pinned: packaging/pygments floated (Session 34).
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
    Superseded (Session 33 commit 4): model = OLLAMA_MODEL in .env, else
    gemma4:e4b; no auto-detection.
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
2. **#3 Writing mode**: RESOLVED in Session 32 (branch v2.6-ocr-editor): one-pass flow, four tracks, files question. See the Session 32 log.
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

### Task B: Editor mode -> DONE in Session 32 (kept the name "Writing mode")
B1 name kept (`--mode writing`); B2 one AI pass; B3 tracks: Topic, Article,
plus new Report and Synopsis; B4 document and review as two files.
Details, commits and follow-ups: see "Session 32" at the end of this file.


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

## Session 32 - 2026-10-27 - branch v2.6-ocr-editor

- Task B (Editor mode) DONE. Name kept as "Writing mode" (`--mode writing`);
  the user does not need to see an "editor" label. main and Render unchanged
  (main = origin/main = 2a37319); all work is on branch v2.6-ocr-editor.
- Decisions:
  - One AI pass per job: writer, editor and reviewer in one prompt
    (`run_one_pass`, `run_synopsis` in pipelines/writing/writing.py).
  - Two output files: document (`.docx` + `.md`) and a separate `_REVIEW.md`,
    all in output/writing/. Nothing is written to reports/writing/.
  - Four tracks: 1 Topic (editorial / opinion, 800 words), 2 Article (medical
    research article, 3,500), 3 Report (abstract / report, 500), 4 Synopsis
    (one document summarising ALL files in input/writing/, 1,500). Word limit
    is always asked; Enter keeps the default.
  - Files question: files in input/writing/ are listed, then
    "Use these files? [Y/n]". "n" ignores them for this run only; files are
    never moved or deleted. Empty folder: a new document is written
    (Synopsis stops: "Synopsis needs files in input/writing/").
  - Cloud warning applies to the whole Writing mode (confirm_data_destinations
    runs before any AI call), because users may type confidential text.
  - Synopsis on Ollama stops before the AI call above 80,000 characters
    (`SYNOPSIS_LOCAL_MAX_CHARS`; num_ctx 32768 minus ~8192 for the answer):
    "Remove some files from input/writing/ or change to a cloud provider."
    The file list shows characters per file, the total and the limit;
    unreadable files are marked "(unreadable - will be skipped)".
- writing.py details:
  - The answer is split at a line `=== REVIEW ===` (`_split_document_and_review`).
    Fallback: split at a "Stage 3" / "QA Report" heading; if neither is found
    the document keeps all text and the review says "Review missing: ...".
  - The prompt no longer contains `## Stage N` headings. gemma4:e4b copied
    them and wrote the report twice (1,335 words); after the fix the Report
    track gave 478 words against a 500 target.
  - `_unreadable_reason` skips placeholder/empty files with `[SKIP] <file>`.
- Real runs on Ollama gemma4:e4b, all OK: Topic (655/800 words), Article,
  Report from a 37,395-character PDF, Synopsis from 3 PDFs.
- Commits: 6d7e666, 49cff65, 6dde284, cef5a8a, fa6f7b2, 8bb2be8, 9750db0,
  ffc0708, 9e8c9e7, 06f0031, bfefcc7, 6c73d08, 166f038, c303726, 99be9e2
  (docs), 1f8df30 (HANDOFF tables), plus this log.
- Tests: 743 -> 816 passed, 3 skipped, 11 deselected. New files:
  tests/test_writing_one_pass.py, tests/test_writing_menu.py.
- Follow-ups:
  - Reviewer is lenient ("FAIL items: None"); consider a stricter QA prompt.
  - LaTeX such as `$\rightarrow$` appears in output and in Word.
  - project-brief.md is loaded twice by `_load_guidelines` (harmless).
  - `_strip_boilerplate` cuts at fixed headings; review whether still needed.
  - Remove legacy run_writer / run_editor / run_qa and their tests in
    tests/test_writing.py (still exported by pipelines/writing/__init__.py).
  - `--mode writing --report` not checked against the new flow.
  - Render cannot answer terminal menus; hosted Writing mode needs a UI path.
  - Deferred: pick Synopsis files by number; size check for tracks 1-3.
- Lessons:
  - Check syntax after editing main.py:
    `python -c "import ast; ast.parse(open('SOURCE_CODE/main.py', encoding='utf-8').read()); print('syntax OK')"`
  - When replacing an import block, delete the old `try:` too (one stray
    `try:` broke collection of 5 test files).
  - PowerShell: put `Get-Content ... -Raw` in brackets before `-split`; use
    single quotes for regex patterns containing double quotes; paste long
    commands once (a double paste gave `-WrapGet-ChildItem`).
  - For multi-part edits, compare `git diff --stat` with the expected size
    before committing: 1f8df30 (+13/-43) was missing this whole log.

## Session 33 handoff: "UI startup" (written end of Session 32)

- State at end of Session 32: main = origin/main = fa4edb9 (PR #3 merged:
  Writing mode one-pass, four tracks). v2.6-ocr-editor = fa4edb9 + HANDOFF
  commits (not yet on main; they go with the next PR). Tests: 816 passed,
  3 skipped, 11 deselected (local and CI on PR #3). Version stays 2.5.0;
  bump to 2.6.0 after OCR is merged.
- Not yet confirmed: Render "Deploy live" hash (expected fa4edb9; the user saw
  the live app's API working); CI run on main for fa4edb9 (expected 816).
- JOB (user's words): Rename this pipeline to "UI startup". It provides users
  who have difficulty to locate where to put their input files and find the
  output files, set up API's. The work button will bring users to the
  corresponding CLI pipelines. This applies to all the pipelines in the UI
  with minimal coding.
- Meaning: the Streamlit UI is a front door, not a place where pipelines run.
  It handles (1) input: upload or locate files in input/<mode>/, (2) output:
  the output browser for output/<mode>/, (3) API keys: sidebar, kept in
  st.session_state, passed to the CLI via env= (never written to disk).
  Run opens the matching CLI pipeline in a terminal, where all menus are
  answered. No per-mode UI controls and no new CLI flags: the Session 32 idea
  of --track / --word-limit / --instructions / --no-files is DROPPED.
- DECISION 1 (ask the user first): Render has no terminal. _run_cli_cloud
  uses stdin=subprocess.DEVNULL (ui/app.py line 638), so menu modes stop at
  their first input() (Writing: "Select track [0-4]" main.py line 1943;
  also Appraisal and Search). Options: (a) on Render, UI startup shows
  guidance + output browser only and Run explains the pipelines run locally;
  (b) allow hosted Run only for modes that ask no questions; (c) flags later.
- DECISION 2 (DECIDED by the user, end of Session 32): launcher menu becomes
  7 Data Analysis (new), 8 OCR (new), 9 Dry Run (was 7), 10 Startup UI
  (was 8 "Pipeline UI", renamed). Dry Run and the UI are KEPT, not replaced;
  this supersedes the older plan (#4 Data Analysis replaces Dry Run, #5 OCR
  replaces option 8). Name: user said "UI startup" first, then "Startup UI";
  use "Startup UI" unless the user says otherwise (confirm once).
- Menu work order: (1) renumber 9 Dry Run and 10 Startup UI, and add
  placeholders for 7 and 8 that print "coming soon" and return to the menu.
  Test-first: pin the new numbers and labels in launcher tests, and update
  any existing tests that expect 7 = Dry Run or 8 = Pipeline UI. (2) Startup
  UI job (above). (3) OCR as option 8 (Task A). (4) Data Analysis as
  option 7 (#4: data file -> Python/R/Excel statistics -> Ollama model
  explains/checks/reports; needs its own design questions first).
- Places a new menu number touches: scripts/launcher.py MODES / menu
  numbers / _MODE_INPUT_MAP / show_help(); README launcher table;
  Readme/flashcard-help.html; the four launchers (.bat etc.) if they print
  the menu. First read-only check:
  `Select-String -Path scripts\launcher.py -Pattern 'Dry Run|Pipeline UI|"7"|"8"|def show_help|def main_menu|MODES' -Encoding utf8 | Select-Object LineNumber, Line`
- Known facts (Session 32, ui/app.py): "in the terminal" help text at lines
  89, 113, 130, 147, 149; launch messages at 1207-1208 ("session launched in
  a new terminal window"); _build_cli_cmd 484 (passes --sub at 496);
  RENDER* detection 475-477 and _RENDER_VARS 534; _launch_terminal 598;
  _run_cli_cloud 607; _launch_terminal_local 666; file_uploader on home
  page 936, SR page 1071, mode page 1122; hosted-upload note 1172.
- First read-only commands:
  `Select-String -Path SOURCE_CODE\ui\app.py, scripts\launcher.py, README.md, Readme\flashcard-help.html -Pattern 'Pipeline UI|Streamlit|page_title|--ui|option 8' -Encoding utf8 | Select-Object Filename, LineNumber, Line`
  Rename places expected: app.py page title/header (_render_header ~387),
  launcher menu label + show_help(), README, flashcard-help.html, HANDOFF.
- Working rules unchanged: read-only first, failing test (fails for the
  right reason), code, full suite, check_no_bom.py, docs, commit/push.
  CI runs only on PRs to main (ci.yml lines 4-7). Merging to main deploys
  to Render. Check syntax after editing main.py/app.py with ast.parse.
- After UI startup: Task A OCR (search HANDOFF for "Task A").
- Rule for every new mode: decide its UI startup entry (input folder,
  output folder, Run -> CLI) and its Render behaviour.

## Session 33 - 2026-10-27 - branch v2.6-ocr-editor

Decisions (these replace the "Session 33 handoff" plan above: DECISION 1 and
the Startup UI job are dropped):
- Streamlit UI removed completely (replaces the Session 29 decision to keep it).
  Without Run, uploads or keys it added nothing the launcher and Help don't.
- Render service deleted. It held no API keys, only `DEFAUL_PROVIDER`
  (misspelt, so never read) and `PYTHON_VERSION`. Steps: auto-deploy off,
  suspend (health 503), check no local Streamlit (port 8501 free), delete
  (health 404).
- Launcher menu: 7 Data Analysis (coming soon), 8 OCR (coming soon),
  9 Dry Run, 10 Setup.
- Setup sub-menu: 1 API keys (getpass, written to .env, only that line
  changed, .env.example copied if no .env, UTF-8 no BOM); 2 Local AI
  (check Ollama installed/running, choose default model, pull a new model);
  3 Open Help (Readme/flashcard-help.html, path relative to the launcher).
  All .env reading/writing goes in a new stdlib-only SOURCE_CODE/env_file.py.
- Model list: live facts only. MODEL_RANKS and "Not pulled yet" hints are
  dropped. A model is selectable only if /api/show lists `completion`
  (embedding models are excluded by capability, not by name).
- Default model: OLLAMA_MODEL from Setup, else gemma4:e4b
  (OLLAMA_DEFAULT_MODEL, the only model name left in code). `--model` or a
  job-time pick applies to that job only. The .env.example OLLAMA_MODEL line
  gets commented out so an unset value means "built-in default".
- If the default model isn't pulled: the launcher offers "pull it now" or
  "choose a pulled model for this job only". With no TTY, the job stops:
  "Run `ollama pull <model>` or choose another in Setup". No silent switch
  to the largest model (replaces choose_default's fallback).
- Pulling: Setup runs `ollama pull <name>` (name checked against a pattern,
  no shell, [y/N] size warning, Ctrl+C cancels, then "make it default?").
  It also offers to pull the embedding model (EMBEDDING_MODEL or
  nomic-embed-text). Setup points users to ollama.com/download and never
  installs Ollama itself.

Commit 0 (this commit): path_utils.py no longer creates data/ or docker/,
and docker_dir, data_dir, get_docker_path() and get_docker_file() are
removed. Nothing else used them. PATH_MANAGER = PathManager() runs
_ensure_directories() on import, which is why deleting the empty folders
by hand never stuck. Verified: after importing utils.path_utils,
Test-Path data, docker -> False, False. tests/test_path_utils_dirs.py (3;
2 failed with AssertionError before the fix). Suite: 816 -> 819 passed.

Order of work: 1 menu renumber + Setup/Open Help; 2 env_file.py + API keys;
3 ollama_models.py cleanup (ranks out, capability filter, default rule);
4 Setup -> Local AI; 5 remove Streamlit and Render; 6 update flashcard-help.html.

Commit 5 list (remove together): ui/app.py, tests/test_ui.py and the other
UI tests (test_ui_cloud_gate, test_ui_model_picker, test_ui_time_limit,
AppTest renders), --ui in main.py and the launcher, streamlit in the
requirements files, .streamlit/ (config.toml, secrets.toml.example) and
.gitignore line `.streamlit/secrets.toml`, render.yaml,
requirements-render.txt, tests/test_render_without_chromadb.py, the whole
assets/ folder, and in path_utils.py the ui_dir and assets_dir mkdir entries
plus get_assets_path()/get_assets(). Keep: streaming.py (not Streamlit),
the pyarrow==12.0.1 pin (chromadb needs it), `.gitattributes` `*.ico binary`.
Expect a large test-count drop; record before/after.

Notes:
- assets/icon_AI_kcMedicalResearch.ico was used only by the user's desktop
  shortcut; copied outside the repo before commit 5. No script uses it.
- The two untracked PNGs (icon_Data_Analysis, logo_OCR) were deleted;
  made for the dropped UI.
- Forest plot path disagrees: flashcard-help.html line 273 says
  output/figures/, README line 226 says output/sr/figures/. Check
  mirror_figures (main.py ~1569) in commit 6.
- Still stale (from the session-open read): #19 is RESOLVED but still in the
  Open Issues table; Providers row lists Ollama twice; Session 28 "[APPLY +
  add test pinning the 404->pull-message mapping]" not confirmed; Session 28
  priority "vote outcome_selected/timepoint_selected" never closed; the
  2026-09-02 notes still say llama3.2. Fix in a docs commit.

### Commit 1 - launcher menu
- Menu: 1-6 pipelines, 7 Data Analysis (coming soon), 8 OCR (coming soon), 9 Dry Run, 10 Setup; C Custom flags (was 9), H Help, X Exit.
- Setup sub-menu: 1 API keys (coming soon - commit 2), 2 Local AI (coming soon - commit 4), 3 Open Help, 0 Back.
- run_ui() and the --ui launch removed from the launcher; show_help() replaced by open_help() using HELP_FILE = Readme/flashcard-help.html.
- Banner: Render "Deploy" line replaced by "Runs  local first / cloud API"; Modes line 2 is now `rct_search  sr  data_analysis  ocr` (ui and dry-run dropped).
- tests/test_launcher_menu.py (20 tests) incl. a banner width guard, proven to fail when the padding is off by 2.
- Desktop shortcut checked: targets scripts/windows/AI_kcMedicalResearch_CLI.bat, icon C:\icon_AI_kcMedicalResearch.ico (outside repo) - unaffected by commit 5.
- Added to the commit 5 list: scripts/windows/AI_kcMedicalResearch_UI.bat, scripts/macos/Mac_kcMedicalResearch_UI.sh, assets/ (via git rm -r, plus assets_dir/get_assets* in path_utils.py), README lines 92/140 (web UI text), README line 186 (keep, reword).

### Commit 2 - Setup -> API keys
- New SOURCE_CODE/env_file.py (stdlib only): read_values, set_value, mask. set_value changes only the target key's active lines (all duplicates), appends a missing key, leaves comments/blank lines/order alone, keeps CRLF or LF, writes UTF-8 without BOM, copies .env.example if .env is missing, saves via temp file + os.replace (temp name .env.<random>.tmp is covered by .gitignore '.env.*'). Rejects bad key names and values with spaces, quotes or line breaks; error messages never include the value.
- Launcher Setup item 1 is live: api_keys_menu() lists Qwen (DASHSCOPE_API_KEY), Groq, DeepSeek, OpenAI, Anthropic with masked values (****abcd / (not set)); key typed hidden via getpass; Enter keeps the current key; Ctrl+C cancels; "Saved" message reads the value back from .env and shows only the mask; warns if the same name is also a system environment variable (load_dotenv does not override those).
- No "clear key" option yet (edit .env by hand). Ollama has no key; its model setting is Setup item 2 (commit 4).
- Checked 2026-10-28: no *_API_KEY / DEFAULT_PROVIDER / OLLAMA_MODEL system environment variables on this machine; user's .env is CRLF and lacks GROQ/OPENAI/ANTHROPIC key lines (appended on first save).
- Tests: tests/test_env_file.py (26), tests/test_launcher_api_keys.py (10, temp .env only - real .env never touched); test_setup_items_1_and_2_are_placeholders narrowed to item 2.
- Commit 3 note: .env.example is stale - v2.4.6 header (line 3), "ranked best" text (67-69), "let the app pick ... largest model" (76-77, contradicts no-silent-switch), Docker note (85-86).

### Commit 3 - remove Streamlit UI and Render deploy
- Commit order changed: 3 = Streamlit/Render removal (was 5), 4 = ollama_models tidy + default-model rule + .env.example (was 3), 5 = Setup -> Local AI (was 4), 6 = flashcard-help.html + forest-plot path. Reason: ui/app.py and test_ui_model_picker.py used RANKS_SOURCE/choose_default, so removing them first avoids editing code that is about to be deleted.
- git rm (22 files): SOURCE_CODE/ui/, .streamlit/, assets/, render.yaml, requirements-render.txt, scripts/windows/AI_kcMedicalResearch_UI.bat, scripts/macos/Mac_kcMedicalResearch_UI.sh, SOURCE_CODE/pipelines/sr/run_sr_ui.bat (dead: launched sr/src/ui/app.py, removed in Session 4), tests/test_ui.py, test_ui_cloud_gate.py, test_ui_model_picker.py, test_ui_time_limit.py, test_render_without_chromadb.py (84 tests).
- main.py: --ui flag and Streamlit launch block removed; Search-mode cloud detection (RENDER / STREAMLIT_* -> default Topic Search) removed, so Search always asks or uses --sub.
- path_utils.py: ui_dir, assets_dir, get_assets_path, get_assets removed; import no longer creates assets/.
- streamlit removed from requirements-base.txt, requirements-local.txt, SOURCE_CODE/pipelines/sr/requirements.txt; Render notes removed from requirements*.txt and rag.py comment; .gitignore .streamlit line removed. pyarrow==12.0.1 pin KEPT (chromadb). streaming.py kept.
- README: Render links, hosted-app line, web-UI sentences and Deployment (Render) section removed; pre-v2.4.7 key-rotation note kept and reworded.
- Guard: tests/test_no_streamlit.py (9 tests: files gone, no --ui/streamlit/is_cloud in main.py, no ui/assets in PathManager, no streamlit in requirements, pyarrow pin kept, .gitignore, README).
- Left for commit 4: README lines on model ranks and "ollama pull" hints, ollama_models.py docstring mentioning ui/app.py.

### Commit 4 - Ollama default-model rule, no rankings
- Rule: model = OLLAMA_MODEL in .env, else OLLAMA_DEFAULT_MODEL (gemma4:e4b). No auto-detection and no silent switching. A model that is not pulled fails with the plain-language 404 message ("ollama pull <model>").
- providers.py: _resolve_ollama_model() = OLLAMA_MODEL or default (no network call, no cache). Deleted _ollama_detect_best_model and _OLLAMA_MODEL_RESOLVED. get_default_model("ollama") returns the real model; the startup probe uses the same rule.
- ollama_models.py: deleted MODEL_RANKS, RANKS_SOURCE, rank_label, missing_ranked, choose_default, _norm, _SKIP_PATTERNS. list_ollama_models lists every model; describe() has no rank text.
- launcher.py pick_ollama_model: default read from .env each time the picker opens; lists only models with the 'completion' capability (embedding models hidden); Ollama unreachable or no chat model -> returns ''. Default not pulled -> warning, still the Enter choice. No ranks, no pull hints.
- main.py: new _sr_default_model(provider). The SR route (--mode sr --provider ollama) used raw OLLAMA_MODEL and sent an empty model name when unset; fixed. README "Noted, not fixed" line removed.
- sr/main.py: docstring only (resolve_model now never stops for Ollama).
- .env.example: removed v2.4.6 header, ranking text and Docker note; OLLAMA_MODEL comment explains the rule. README Step 3/5 and the v2.5 note rewritten.
- Tests: test_providers TestOllamaModelRule; test_streaming 3 tests; test_sr_cli_model_resolution (placeholder test replaced by 2); test_launcher_model_picker rewritten (10 picker tests, autouse temp .env); test_ollama_models (9 rank/choose_default tests deleted, TestNoRankings added); new tests/test_sr_default_model.py (4). Suite 799 -> 802.
- Note: tests/test_main.py::TestMainProviderCalls::test_call_ai_fallback_to_ollama is a live test (real DeepSeek call, got 400 on 2026-10-28). Always run test_main.py with -m "not live".
- Deferred to commit 5 (Setup -> Local AI): pull offer [y/N], 404 message to mention Setup, plain-language 404 in streaming.py (currently raw "Ollama streaming error 404").

### Commit 5 - Setup -> Local AI (Ollama)

- Setup item 2 now opens `local_ai_menu()` in scripts/launcher.py (was "coming soon").
- Status line: Ollama version (new `ollama_version()` in ollama_models.py, GET /api/version)
  and the default model (`OLLAMA_MODEL` in .env, else gemma4:e4b), marked pulled / NOT pulled yet.
- Not installed (`_ollama_exe()`: PATH, then %LOCALAPPDATA%\Programs\Ollama\ollama.exe):
  shows https://ollama.com/download and no menu. Installed but not running: says so, no menu.
- 1 Change default model: lists pulled models whose /api/show capabilities include
  `completion` (embedding models hidden), saves `OLLAMA_MODEL` via env_file.set_value.
  Enter cancels. Warns if a Windows/system `OLLAMA_MODEL` variable would override .env.
- 2 Pull a new model: name checked against `^[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}$`
  (no spaces, cannot start with `-`), size warning, `Download <name>? [y/N]` (Enter = no),
  runs `[ollama, "pull", name]` as a list (no shell). Ctrl+C stops; non-zero exit = "failed".
  Only after a successful pull: `Make <name> the default model? [y/N]`.
- Tests: tests/test_launcher_local_ai.py (15, nothing touches real Ollama or .env),
  TestVersion in tests/test_ollama_models.py (2); deleted the item-2 placeholder test
  in tests/test_launcher_menu.py. Full suite 818 passed, 3 skipped, 10 deselected (2026-10-28).
- Still open: streaming.py `_stream_ollama` shows a raw HTTP 404 when the model is not
  pulled; providers.py already says "ollama pull <model>". Next commit.

### Commit 6 - same "model not pulled" message when streaming

- New `ollama_model_missing_message(model)` in providers.py: "The local AI model '<model>'
  is not installed yet", the `ollama pull <model>` command, and the launcher route
  (10 Setup -> 2 Local AI -> 2 Pull a new model).
- Used by the Ollama call in providers.py and by streaming._stream_ollama on HTTP 404.
  Before this, streaming showed the raw "Ollama streaming error 404". Other HTTP codes unchanged.
- Tests: tests/test_ollama_missing_model.py (3, urlopen patched). Full suite 821 passed,
  3 skipped, 10 deselected (2026-10-28).
- Closes the "Still open" item in Commit 5.

## Session 33 handoff - for the next chat (2026-10-28)

Repo D:\AI_kcMedicalResearch, branch `v2.6-ocr-editor`, Windows PowerShell, `.venv`.
`main` is still at fa4edb9 (PR #3, 816 tests). The branch has 8 commits (7 code + this
handoff), all pushed, **not merged yet** (no PR opened).

### Session 33 commits

| Commit | What |
|---|---|
| e4d57cd | path_utils stops creating `data/` and `docker/` |
| c297396 | Launcher menu: 7 Data Analysis, 8 OCR, 9 Dry Run, 10 Setup |
| 982c46b | Setup -> API keys saved to `.env` (new `SOURCE_CODE/env_file.py`) |
| 1264d0c | Removed Streamlit UI and Render deploy (local-first CLI only) |
| 7fff199 | Ollama: `OLLAMA_MODEL` else gemma4:e4b, no rankings or auto-detect |
| 189491a | Setup -> Local AI: Ollama status, change default model, pull models |
| b67873e | Same "model not pulled" message when streaming |

Tests: **821 passed, 3 skipped, 10 deselected** (`python -m pytest -m "not live" --tb=short -q`).

### Where things stand

- **CLI only.** The Streamlit UI, `--ui`, `SOURCE_CODE/ui/`, `assets/`, `.streamlit/`, `render.yaml`,
  `requirements-render.txt`, `*_UI.bat`/`*_UI.sh` and `run_sr_ui.bat` are gone. The Render service
  was deleted (the health URL returns 404). README line ~179 still mentions the old Streamlit
  interface on purpose (it's the API-key rotation note).
- **Launcher menu** (`scripts/launcher.py`): 1 Coding, 2 Writing, 3 Appraisal, 4 Search,
  5 RCT Search, 6 SR Pipeline, 7 Data Analysis (coming soon), 8 OCR (coming soon), 9 Dry Run,
  10 Setup, C Custom flags, H Help (`Readme/flashcard-help.html`), X Exit.
- **Setup (10):**
  - 1 API keys: 5 keys typed hidden (getpass), saved by `env_file.set_value`, shown masked.
    Warns if a system environment variable would override `.env`.
  - 2 Local AI: `local_ai_menu()` shows the Ollama version and the default model.
    1 Change default (chat models only), 2 Pull a model (name checked, `[y/N]`, no shell).
    If Ollama is not installed it shows https://ollama.com/download; if not running it says so.
  - 3 Open Help.
- **Ollama model rule:** `OLLAMA_MODEL` from `.env`, else `OLLAMA_DEFAULT_MODEL = "gemma4:e4b"`
  (`ollama_models.py`). No auto-detection and no silent switching. A model that isn't pulled
  gives `ollama_model_missing_message()` (providers.py), used by both the normal and the streaming call.
- **`ollama_models.py`** (stdlib only): `list_ollama_models` (/api/tags),
  `model_capabilities` (/api/show), `ollama_version` (/api/version), `describe`.
  "Chat model" = capabilities include `completion`.
- **Safety rules kept:** Ollama never falls back to a cloud provider (`LOCAL_ONLY_PROVIDERS`).
  The SR pipeline blocks ollama and deepseek (no image input).
- **`env_file.py`** keeps `.env` CRLF/LF line endings, never writes a BOM, and saves through a temp
  file + `os.replace` (`.env.*.tmp` is gitignored).

### Working rules (same as before)

- Test-first, one step at a time: write a failing test, run it, then edit the code, then run the full suite.
- Edit bottom-up so line numbers stay valid. Save as UTF-8 without BOM; run
  `python scripts/check_no_bom.py` after every edit.
- Always use `-m "not live"`. `test_main.py::test_call_ai_fallback_to_ollama` makes a real
  DeepSeek call (it returned 400 on 2026-10-28).
- Use `git --no-pager ...`. In `git grep`, put patterns that start with `-` after `-e`.
- Commit with `git commit -F D:\commit_msg.txt`, and **check its first line first**
  (`Get-Content D:\commit_msg.txt -TotalCount 1`). f1dbc36 went out with a stale message and
  had to be amended and force-pushed (now c297396).
- On split imports inside `( ... )`, check that each line ends in a comma, not a full stop.
- The launcher tests load `scripts/launcher.py` by path with colorama mocked. The Local AI tests count
  `safe_input` calls, so don't add "Press Enter" prompts after actions there.
- CRLF->LF warnings on `git add` for new test files are harmless.
- Line viewer helper (define it once per PowerShell window):
  `function Show($f, $a, $b) { "--- $f ($a-$b)"; $i = 0; Get-Content $f -Encoding utf8 | ForEach-Object { $i++; if ($i -ge $a -and $i -le $b) { "${i}: $_" } } }`

### Next options (user to choose)

1. **Open a PR `v2.6-ocr-editor` -> `main`.** After the merge, update the Tests row
   ("816 on main") to 821.
2. **8 OCR.** gemma4:e4b can read images, but the app doesn't send images to Ollama yet:
   `call_ollama` and `_stream_ollama` are text-only. `.env` has TESSERACT_PATH and POPPLER_PATH;
   `utils/document_reader.py` already accepts image extensions. Start with read-only checks.
3. **7 Data Analysis** (placeholder).

Outside the repo (user): pause or delete the UptimeRobot monitor for the deleted Render URL.
The desktop shortcut icon now lives at `C:\icon_AI_kcMedicalResearch.ico`, so it wasn't affected
when `assets/` was removed.

### First commands for the next session (read-only)

```powershell
git status -sb
git --no-pager log --oneline -9
python scripts/check_no_bom.py
python -m pytest -m "not live" --tb=line -q
```
Expected: a clean tree in sync with origin, the top commit is this handoff, and 821 passed,
3 skipped, 10 deselected.

## Session 34 - 2026-11-06 - branch v2.6-ocr-editor

- Dev machine: every console script in .venv\Scripts failed with "Fatal error
  in launcher". The venv was created at D:\ai-automation-tool and the folder
  was later renamed; pip's .exe stubs store the absolute interpreter path.
  `python` and `python -m ...` kept working (pyvenv.cfg `home` is what Python
  uses), which is why nothing in the handoff commands noticed.
  Fixed in place: `pip freeze --exclude-editable` to D:\frozen.txt, then
  `python -m pip install --force-reinstall --no-deps -r D:\frozen.txt`
  (129 packages, same versions, from cache). Scan for the old path: 31 stale
  stubs before, 0 after. Suite unchanged (821).
- pyvenv.cfg `command` line still named D:\ai-automation-tool after the
  reinstall (pip never rewrites it). Edited by hand to
  D:\AI_kcMedicalResearch\.venv; Python does not read that line.
- Launchers (Windows .bat and macOS .sh):
  A. pip is called as `python -m pip`, never through the pip stub.
  B. New moved-folder check: reads the `command` line in .venv\pyvenv.cfg; if
     it does not name this folder's .venv, prints "This app folder was moved
     since setup" and asks "Rebuild the app environment now? [Y/n]". Yes
     renames .venv to .venv.old, rebuilds from requirements-local.txt, and
     deletes .venv.old only after a successful install; any failure restores
     .venv.old. An existing .venv.old stops the launcher with an explanation.
  Tests: tests/test_launcher_venv_move.py (12; 10 failed before the change).
  Suite: 821 -> 833 passed, 3 skipped, 10 deselected.
  Checked by hand on Windows: real folder -> no box, straight to the menu;
  copy at D:\kc_move_test -> box shown, rebuild ran, new `command` names the
  copy, .venv.old removed, no stub points at the old folder,
  pyarrow 12.0.1 / chromadb 0.5.23 installed, no streamlit.
  macOS script: `bash -n` syntax check only; not run on a Mac.
- FOUND, NOT FIXED (next commit): a fresh install from requirements-local.txt
  breaks every OpenAI-compatible and Anthropic call. It pins openai==1.43.0
    and anthropic==0.34.2 but not httpx; pip installs httpx 0.28.1, which
  removed `proxies`, and the old SDKs crash with
  "Client.__init__() got an unexpected keyword argument 'proxies'".
  89 errors/failures in the copy's test run. Ollama unaffected (urllib).
  Fix to test: pin httpx<0.28 in requirements-local.txt, then rerun in the copy.
- requirements-local.txt is NOT fully pinned (the 2026-09-02 note says it is):
  packages it does not name float to the newest version (the copy got
  packaging 26.3, pygments 2.21.0).
- Dev venv drift: this machine's venv has pyarrow 24.0.0, chromadb 1.5.9,
  openai 2.41.1, anthropic 0.120.0 and still has streamlit 1.60.0. Colleagues
  get the pinned versions above, so local test runs do not represent them.
  Consider rebuilding the dev venv from requirements-local.txt plus pytest.
- Other failures in the copy, not colleague-facing: test_gitignore_input.py
  (4) needs a .git folder; test_main.py::TestMainValidation::
  test_validate_api_keys_qwen_with_key failed without .env (check whether it
  depends on the developer's real .env).
- Follow-up C (not done): the launcher only runs setup when .venv\Scripts\
  python.exe is missing, so a setup interrupted halfway is never retried.
  Needs a success marker and a rule for existing venvs without one.
- To delete when done: D:\kc_move_test (copy, about 1 GB plus rebuilt venv),
  D:\frozen.txt.
- Lesson: a pip reinstall regenerates the stubs but not pyvenv.cfg. Any check
  that reads pyvenv.cfg sees the original creation path until it is edited
  or the venv is rebuilt.

### Session 34 commit 2 - httpx pin for colleagues' installs
- Launcher commit 2c7c57f pushed (821 -> 833).
- requirements-local.txt: added httpx==0.27.2 (fixes the FOUND item above).
  Checked in D:\kc_move_test: 89 `proxies` errors -> 0; 828 passed, 5 failed
  (the 4 .git + 1 .env failures, as expected); pyarrow/chromadb unchanged.
  Tests: tests/test_requirements_local_pins.py (2; both failed before).
  Suite: 833 -> 835 passed, 3 skipped, 10 deselected.
- Why CI missed it: CI installs requirements-ci.txt -> requirements-base.txt
  (newest SDKs); dev uses requirements.txt -> base too. Nothing installs
  requirements-local.txt, the file colleagues get. Follow-up: a CI job that
  installs requirements-local.txt and runs the suite.
- Follow-up: SR requirements.txt wants anthropic>=0.40.0; requirements-local
  pins 0.34.2. Raising it needs its own test in the copy.
- Push 403 (fixed): git uses `store --file=C:/Users/user/.git-credentials-github`
  for github.com (one token for every repo). On 31 Oct a fine-grained token
  for another KW75 repo replaced it. Fix: added AI_kcMedicalResearch to that
  token (Contents: Read and write). Lesson: a token made for one repo
  must list every repo pushed from this machine.
- Still to delete: D:\kc_move_test, D:\frozen.txt, D:\commit_msg.txt.


### Session 34 close
- Cleanup done: D:\kc_move_test, D:\frozen.txt, D:\commit_msg.txt deleted.
- Dev venv: activate.bat and activate (bash) also had the old path; fixed by
  hand (local only, .venv is untracked). PowerShell Activate.ps1 was fine.
  pip.exe runs from this folder. Housekeeping item "confirm .venv\Scripts\
  Python is the one resolving" is confirmed: cmd and PowerShell both
  resolve .venv\Scripts\python.exe first.
- This machine also has Python 3.14; rebuild the dev venv with py -3.11.
- Follow-ups (not urgent, suggested order):
  1. CI job that installs requirements-local.txt (+ pytest) and runs the
     suite; today nothing tests the file colleagues install.
  2. macOS launcher moved-folder check verified by `bash -n` only; run it
     on a Mac.
  3. SR requirements.txt wants anthropic>=0.40.0; requirements-local pins
     0.34.2. Raise it only after a fresh-copy test.
  4. requirements-local.txt is not fully pinned (unnamed packages float).
  5. Some tests write real files to output/writing/ and reports/rct_search/
     instead of tmp_path; check .gitignore covers output/ and reports/.
  6. Launcher follow-up C: retry a setup that failed halfway.
  7. Dev venv drift: newer pyarrow/chromadb/SDKs and still streamlit.
  8. test_validate_api_keys_qwen_with_key may depend on the developer's .env.

## Session 34 (cont.) - 2026-11-06 - folders for planned OCR / data_analysis
- The app now creates input\, output\ and reports\ ocr and data_analysis
  folders itself. path_utils.py has future_mode_subdirs = ['ocr',
  'data_analysis'] (input/output/reports only, no docs/). Git ignores
  input/*, output/ and reports/, so a fresh clone gets them on first run.
- Tests: test_path_utils_dirs.py +2 (folders created; no docs/ folder yet).
  Suite: 835 -> 837 passed, 3 skipped, 10 deselected.
- Found: the 10 .gitkeep files in output\ and reports\ exist only on this
  machine. .gitignore lines 13-14 ignore them, so they do nothing.
- main.py lines 187-202 is a second, partial folder list (sr missing from
  reports). Left unchanged because path_utils runs at every start.
- When OCR or data_analysis code is written: move the name into
  mode_subdirs, add it to the main.py --mode choices and _MODE_EXTENSIONS,
  and add it to the mode list in test_e2e.py line 269.

## Session 34 (cont.) - 2026-11-06 - test cleanup, Gemini checked
- Checked tests for leftovers from the removed Streamlit UI: none are
  redundant. The UI matches in test_launcher_menu.py, test_ollama_models.py
  and test_no_streamlit.py are guards that stop the UI coming back; keep
  them. Other matches ("render") are about report output, not UI.
- Deleted 3 placeholder tests from test_main.py (TestMainProviderCalls):
  two Ollama, one OpenAI. Each was @pytest.mark.skip with body `pass`;
  real calls are covered by test_live_providers.py.
  Suite: 837 passed, 3 skipped -> 837 passed, 0 skipped, 10 deselected.
- Found, not fixed: test_call_openai_provider_missing_key is marked
  @pytest.mark.live but makes no network call, so it never runs. Its patch
  target SOURCE_CODE.main.OPENAI_API_KEY may also be wrong (the Anthropic
  test below patches the provider module). Remove the mark and fix the
  patch target, test-first.
- Gemini API is not available in our region (checked 2026-11-06), so the
  planned Anthropic -> Gemini move was stopped. Anthropic kept (needs VPN).
  No-VPN options: DeepSeek (text only), Qwen (has a vision model), Ollama.

## Session 35 - 2026-11-06 - branch v2.6-ocr-editor

- Session-opening checklist, all four items run:
  1. Test count: 837/847 collected (10 deselected) = README line 7.
  2. Closed-issue citations: 55 RESOLVED_ISSUES rows, no `(#N)` in README.md
     or HANDOFF.md. Note: the pattern `#(\d+)` only finds numbers cited in
     passing (5 of them), not the table rows. Use `^\|\s*(\d+)\s*\|` and
     print the count, so "clean" cannot mean "never ran".
  3. Open Issues tables matched (#19, #2, #3). #19 was RESOLVED but still
     listed: moved to RESOLVED_ISSUES.md and removed from both tables.
  4. Spot check found the #61 warning (below).
- Gaps in issue numbers (53-60, 63-65) are not lost rows. The archive
  renumbering table maps old 53/54/60 to new 43/44/49; #63/#64 were working
  numbers for #51/#52.
- Current State table updated to Session 34 (no Render; 15 branch commits not
  through CI; providers). Anthropic AND Gemini are geo-restricted on the dev
  machine (#3); the Anthropic -> Gemini switch is on hold.
- Session 28 "[APPLY + add test pinning the 404->pull message]" CLOSED (Session 35): test_providers.py::test_ollama_404_tells_user_to_pull_model and tests/test_ollama_missing_model.py.
- Session 28 priorities still open: 1 vote outcome_selected /
  timepoint_selected; 2 Ang outcome change S26 -> S27; 3 decoder `!` (low).
- Corrections to the 2026-09-02 notes (left as history): the Ollama model is
  OLLAMA_MODEL in .env, else gemma4:e4b (no llama3.2, no auto-detect);
  requirements-local.txt is NOT fully pinned (unnamed packages float; httpx
  pinned in Session 34).
- Forest plot: primary copy reports/sr/<RUN_ID>/output/figures/, mirror shown
  to the user output/sr/figures/ (project_layout.py; main.py mirror_figures).
  README is right; flashcard-help.html "output/figures/" is wrong. Fix in the
  flashcard commit.
- Found, fixed next commit: main.py SR Anthropic warning (~line 2351) says the
  Anthropic path runs without the source-quote, SD/SE and group-timepoint
  tripwires, and cites resolved #61. In the code, _extract_anthropic calls
  _flag_suspect_source_quotes and (per #50) group/timepoint runs; only the
  text-line SD/SE check cannot run (REVIEWER_GUIDE §6). This is the same
  claim the S23 lesson called false, still printed to users.
- SR Anthropic warning corrected. New main.sr_provider_warning(mode, provider);
  run_cli prints it. It now says only two checks cannot run on
  --provider anthropic (verbatim quote-in-source, text-line SD/SE) and that the
  rest still run, and points to docs/sr/REVIEWER_GUIDE.md section 6 instead of
  closed #61. tests/test_sr_anthropic_warning.py (5); seen failing first
  (4 AttributeError + 1 on "Known Issue #61"). Suite: 837 -> 842.
- Noted, not fixed: REVIEWER_GUIDE section 6 "Quote-check number matching" row
  says unicode-vs-ASCII minus signs can still miss; #68 (Session 27) fixed that
  in _number_in_text. Thousands-separator claim not yet checked. Separate docs
  commit after grepping _number_in_text.
- Draft PR #4 opened (v2.6-ocr-editor -> main); CI green, 842 passed,
  10 deselected, 44 warnings (same unpinned-version warnings as Session 29).
- New CI job test-local-pins: installs requirements-local.txt exactly as both
  launchers do (pip upgrade, then -r requirements-local.txt; no build-essential),
  runs pip check, logs pip freeze, then the not-live suite. No pysqlite3-binary
  (colleagues never get it). tests/test_ci_matches_launchers.py (3; 2 failed
  first) pins that a CI job installs the launchers' file. Suite: 842 -> 845.
- CI on d7f11f1 (PR #4): both jobs green, 845 passed. test-local-pins shows
  57 warnings vs 44 (older pinned versions; not failing, look when convenient).
- REVIEWER_GUIDE section 6 "Quote-check number matching" row corrected:
  unicode minus/dash signs now match (#68, _number_in_text lines 1144-1145);
  thousands separators still miss (1234 vs 1,234 or 1 234), since [.,] is only
  allowed when the value has a decimal point (line 1156). Docs only.
  
### OCR design (agreed Session 35, not built yet)
- `--mode ocr`, launcher menu 8. Both functions use the same flow:
  OCR -> record (summary of the file at the top + full OCR text below) in
  output/ocr/records/ -> summary output in output/ocr/.
  1 Single file: choose one file from input/ocr/. Record saved to
    output/ocr/records/; that file's summary saved to output/ocr/.
  2 Document set: every file in input/ocr/ (any stack of documents, e.g.
    patient records or lecture notes). One record per file in
    output/ocr/records/; then one synopsis built from the per-file summaries
    (not the full texts, so more files fit locally) saved to output/ocr/.
    Each synopsis point names its source file. Records are kept if the
    synopsis fails.
- Records: one heading per page ("Page 3") in the full-text part.
  All outputs are .docx + .md.
- Names: the user types a short name (e.g. PT0123, Cardio_lectures); the app
  adds the date: records <name>_<YYYY-MM-DD>_<original>.docx; output
  <name>_<date>_SUMMARY.docx (function 1) or <name>_<date>_SYNOPSIS.docx
  (function 2). Enter = OCR_<date>_<time>. Advise against real patient names
  in file names.
- Input from input/ocr/: .pdf, .jpg, .jpeg, .png, .tif, .tiff, .bmp, .gif,
  .webp (.docx also read as text in a set). Images are converted to PNG before
  sending to the model. PDF pages with a text layer are read directly (no AI);
  only pages without text go to the model. pymupdf renders pages, pillow reads
  images (both in requirements-local.txt). Input files are never moved.
  Later option: .heic (needs pillow-heif, a new package).
- Providers: same routine as other pipelines. Ollama default; cloud only per
  job behind the consent warning. Like SR: only the chosen provider (no
  FALLBACK_PROVIDERS chain), DeepSeek blocked (no image input).
- Models: any pulled Ollama model whose /api/show capabilities include
  `vision` (gemma4:e4b confirmed: completion, vision, audio, tools, thinking).
  No fixed model list, so larger vision models on newer hardware work with no
  code change. The list shows sizes. No vision model -> stop before the job,
  point to Setup -> Local AI -> Pull a new model. qwen3:8b and
  qwen2.5:14b-instruct are text-only.
- Synopsis size limit on Ollama: decide when building (app sends
  num_ctx 32768; gemma4:e4b supports 131072).
- Later: amend the SR pipeline to use the same vision-capability check for
  Ollama instead of blocking all Ollama models.
- OCR step 1 done: providers.call_ollama_provider takes optional
  images=[png_bytes, ...], sent base64 in the "images" field of /api/generate.
  Text-only calls send no "images" key (request unchanged).
  tests/test_ollama_images.py (3; 2 failed first with "unexpected keyword
  argument 'images'"). Suite: 845 -> 848. Not yet: streaming.py image input
  (OCR will use the non-streaming call).
- OCR step 2 done: new SOURCE_CODE/pipelines/ocr/ (__init__.py, reader.py).
  list_inputs(folder): supported files, name order, any-case extension.
  read_input(path): pages {"page", "text", "png"}, exactly one set. PDF page
  with >= 20 characters of text is read directly; otherwise rendered to PNG
  at 200 dpi. Images (.jpg .jpeg .png .tif .tiff .bmp .gif .webp) converted
  to PNG; multi-page TIFF gives one page per frame. Unsupported -> ValueError.
  tests/test_ocr_reader.py (13; failed first with "No module named
  'pipelines.ocr'"). Suite: 848 -> 861. Not yet: .docx in a set.
- OCR step 3: pipelines/ocr/output.py writes records and the SUMMARY /
  SYNOPSIS as .docx + .md. Header = typed name + date (blank ->
  OCR_<date>_<time>). Record names keep the extension
  (<header>_<file>_<ext>) so scan01.pdf and scan01.png never clash. OCR text
  is written verbatim (no markdown-to-Word conversion); every file ends with
  an AI note naming the model. tests/test_ocr_output.py (9; failed first with
  "cannot import name 'output'"). Suite: 861 -> 870.
- OCR design update: inputs also include .txt, .doc and .docx. They are read
  as text (no AI reading), then summarised like any other file. .doc reading
  uses pywin32 (Windows only), so check the Mac behaviour. Not built yet.
- OCR step 4: pipelines/ocr/engine.py. run_single (function 1) and run_set
  (function 2) share _process_file: text-layer pages are kept as they are,
  PNG pages go to the vision model (TRANSCRIBE_PROMPT: "do not summarise"),
  then the file is summarised and the record is written. One bad file does
  not stop a set; no SYNOPSIS if every file fails. Default AI is the local
  Ollama model; tests use a fake. tests/test_ocr_engine.py (8; failed first
  with "cannot import name 'engine'"). Suite: 870 -> 878.
  Not yet: real Ollama run, --mode ocr / menu 8. A long set may go over
  num_ctx 32768 when summarised.
- OCR step 5a: --mode ocr in main.py; prompts in pipelines/ocr/cli.py
  (function 1/2 -> file -> name -> vision model). Only models reporting
  'vision' are listed; default OLLAMA_MODEL if it has vision, else
  gemma4:e4b. Checks that need no typing run first (no input files, no
  vision model -> "ollama pull gemma4:e4b"). data_destinations: ocr lists
  only the chosen provider, like sr. Cloud OCR refused for now
  (ocr_provider_error). tests/test_ocr_cli.py (16). Suite: 878 -> 894.
  Not yet: launcher menu 8 (5b), cloud OCR with consent, real-scan test.
- OCR prompts simplified (user request): input/ocr/ decides the function -
  one file -> record + SUMMARY, several -> records + SYNOPSIS. The "Choose
  1 or 2" and "File number" questions were removed. Questions left: "Scan
  title/name" (header; spaces -> _, capitals kept) and model.
  tests/test_ocr_cli.py rewritten (still 16). Next: .txt/.docx in a set.
- OCR records folder (user request): engine takes records_root; records go
  to <records_root>/<header>/ (CLI will pass reports/ocr). A header already
  used (records folder or SUMMARY/SYNOPSIS exists) gets _2, _3 ... (typed
  name or blank default OCR_<date>_<time>), so a repeat scan never
  overwrites. output.write_record takes rec_dir. tests/test_ocr_engine.py
  +3 (failed first on 'records_root'). Suite: 894 -> 897.
  Not yet: cli.py passes reports/ocr (prompts still use output/ocr/records).
- OCR CLI: cli.py passes records_root=reports/ocr, so --mode ocr writes
  records to reports/ocr/<header>/ and the SUMMARY/SYNOPSIS to output/ocr/.
  "Done" line shows the records folder. tests/test_ocr_cli.py +2 (failed
  first, records_root was None). Suite: 897 -> 899.
- OCR real-file test (Session 35): --mode ocr --provider ollama with
  gemma4:e4b works for one file (record + SUMMARY) and several files
  (records + SYNOPSIS). Records in reports/ocr/<header>/, repeat header
  gets _2. Still to check: a photo/scan page (AI read path) on real input.
  Next: .txt/.docx/.doc in a set, then launcher menu 8 (5b).
- OCR text inputs: reader.py reads .txt (UTF-8 with/without BOM, else
  cp1252) and .docx (paragraphs + tables in document order, row ->
  "cell | cell", merged cell once) as one text page, no AI. A file with no
  text raises ValueError, so it is listed as failed. .doc is refused with
  "save it as .docx". Correction to the earlier note: the app has NO
  pywin32 .doc reader; utils/document_reader.py tries textract (not in any
  requirements file) and silently falls back to _extract_with_alternative.
  main._read_docx not reused: it hides errors as text and skips tables.
  tests/test_ocr_reader_text.py (8); test_ocr_reader.py examples changed
  from .txt/.docx to .xyz/.xlsx. Suite: 899 -> 907.
  Next: launcher menu 8 (5b). Later: .doc support.
- OCR real-file test, text inputs (Session 35): a set of PDF + .txt +
  .docx (with table) works; text files go straight to summarising (no AI
  reading), records and SYNOPSIS written as expected.
- OCR .doc real test: refused with "save it as .docx", nothing crashed.
  Fixed two output issues it showed: the file name was printed twice
  (reader messages no longer include the name) and "Done: 0 record(s) in
  <folder>" named a folder that was never created (now "No records
  written."). +2 tests. Suite: 907 -> 909. Next: launcher menu 8 (5b).
- Cloud OCR step 1: call_openai_provider and call_qwen_provider accept
  images (shared _user_content: one image_url part per page as
  data:image/png;base64, then the prompt; same format as SR's
  _call_vision_api). No images -> request unchanged. Qwen with images and
  no --model uses QWEN_VISION_MODEL (qwen-vl-max). tests/test_cloud_images.py
  (7; 4 failed first on 'images'). Suite: 909 -> 916.
  Agreed design (user): no local vision model / Ollama not running ->
  offer pull or cloud (Qwen default, OpenAI); [CLOUD] confidentiality
  banner + typed "y" / --confirm-cloud; chosen provider only, no fallback;
  DeepSeek blocked. Groq/Anthropic later (Groq default model likely
  text-only; Anthropic uses a different image format, geo-restricted).
  Notes for later: PROVIDER_CAPABILITIES marks ollama vision False
  (outdated, per-model); SR uses qwen-vl-plus vs providers default
  qwen-vl-max.
  Next: OCR offers cloud when no local vision model, then menu 8 (5b).
- Cloud OCR step 2 (main.py): ocr_provider_error allows ollama, qwen and
  openai (OCR_PROVIDERS); other providers refused ("cannot be used to read
  page images"). The [CLOUD] banner adds "For OCR this means page images of
  your documents." Suite: 916 -> 917. Not yet: cli.py still runs Ollama only,
  so --provider qwen/openai shows the cloud banner but reads locally. Next:
  cli.py offers qwen/openai when no local vision model, after typed "y".
- Cloud OCR step 3: cli.run takes provider + confirm. --provider qwen/openai
  sends page images to that provider (run_cli already showed [CLOUD] and got
  "y"); Ollama is not asked. --provider ollama with no local vision model
  offers qwen/openai (only those with an API key set); runs only after the
  [CLOUD] banner and typed "y", Enter cancels. engine.cloud_call(provider,
  model) wraps call_qwen_provider/call_openai_provider. The AI note names
  e.g. "qwen-vl-max (qwen, cloud)". tests/test_ocr_cli_cloud.py (7; all
  failed first). Suite: 917 -> 924. Not yet: real cloud OCR run; menu 8 (5b).
- Cloud OCR real test works: --provider qwen, one photo (.jpeg) -> record
  (Page 1 AI read) + SUMMARY, AI note "qwen3-vl-plus (qwen, cloud)".
- Qwen vision model fix: qwen-vl-max and qwen-vl-plus return 404 "Model not
  exist" on our key (dashscope-intl); qwen2.5-vl-* and *-latest return 403.
  Only qwen3-vl-plus and qwen-vl-ocr work (probe 2026-11-07, /models list).
  providers.py line 41 default QWEN_VISION_MODEL -> qwen3-vl-plus. An env
  QWEN_VISION_MODEL still overrides it (a leftover session variable caused
  one false 404 during testing).
- TODO SR (next chat, do in this order):
  1. Qwen defaults: main._sr_default_model("qwen") already uses
     providers.QWEN_VISION_MODEL (qwen3-vl-plus). Leftover hard-coded
     qwen-vl-plus (404 model_not_found on this key): data_extractor.py 199,
     table_extractor.py 14 and 279, scripts/nondet_probe.py 145 -> use the
     constant. Verified SR results (e.g. Ang 2010, unanimous N=3) came from
     an older Qwen vision model: re-check the next real SR run vs the PDFs.
  2. Broken PDF text layers (has_broken_symbols over input/sr): all 5 SR
     papers flagged. Ang 2010 lost signs (OCR fill + vote handles this);
     CBT-prefrontal lost degree/(R)/(C); s10608 p4 lost ligatures ti/tt/ft;
     CBT-women (S1877886015) and zsy234 are gibberish in fitz, pdfplumber
     and pypdf alike (font encoding, not a library bug; not a clean shift).
     SR text paths read this silently: relevance_screener.py 127,
     rob2_tool.py 142, extraction/pdf_parser.extract_text, extractor text
     fallback. Fix: has_broken_symbols()/gibberish check -> page image path
     or WARNING. Until then, text-based screening and RoB2 for CBT-women
     and zsy234 are UNVERIFIED. Extraction uses images (likely fine).
  3. Local LLM for SR (as in OCR): SR is cloud-only today. Blocks:
     scripts/launcher.py BLOCKED_FOR_SR = {ollama, deepseek} (198, checked
     487 and 532); data_extractor.py vision_providers = qwen/openai/
     anthropic/groq (219-228); providers.py PROVIDER_CAPABILITIES ollama
     vision=False (77); main.py sr_provider_warning in run_cli. Plan: allow
     ollama when the picked model has 'vision' (ollama_models.
     model_capabilities, as OCR does); vision per model, not per provider;
     data_extractor reaches Ollama via _openai_compat_creds -> OLLAMA_URL/v1
     (check image_url parts work there, or use call_ollama_provider
     images=); check OLLAMA_CONTEXT fits 5 page images per call; no local
     vision model -> offer cloud after typed y (same as OCR); deepseek
     stays blocked (no vision). Test: gemma4:e4b on Ang, N=3 agreement,
     compare field by field with qwen3-vl-plus and the PDF.
- TODO OCR banner: in cloud mode the summary/synopsis is also written by the
  cloud model, so text (.txt, .docx, PDF text layers) leaves the machine too,
  not only page images. Fix the "For OCR this means page images..." line.
- DONE Writing .doc check: Writing never reads .doc. writing._load_input_files
  (all Writing roles) and the --report path in main.py filter by extension,
  and .doc is not listed, so it was skipped silently. _load_input_files now
  prints "[SKIP] <name>: old Word .doc files cannot be read - open it in Word
  and save it as .docx". tests/test_writing_doc_skip.py: 3 tests (2 failed
  first). Suite: 934 -> 937.
  DocumentReader's .doc -> textract -> Latin-1 binary fallback is unreachable:
  no pipeline under SOURCE_CODE calls DocumentReader.extract_text or
  batch_extract (grep 2026-11-07; scripts/ and tests/ not checked).
- TODO Writing: --report path (main.py ~985-998) still skips .doc silently;
  the Writing menu's list_input_names leaves .doc out with no message.
- TODO Writing: _load_input_files reads .docx paragraphs only, so tables
  (e.g. lab values) never reach the AI. On a read error it sends
  "[Could not read <name>]" to the AI as if it were the document text
  (main._read_docx does the same). The OCR reader already handles tables.
- DONE OCR banner TODO: [CLOUD] banner (main.py) and the no-local-model
  cloud offer (cli.py) now say page images AND the text of your documents
  leave the machine (the cloud AI also writes the summary).
  tests/test_ocr_cli.py: one assert added (failed first). Suite still 924.
- OCR step 5b: launcher menu 8 runs --mode ocr (7 Data Analysis still a
  placeholder). pick_provider for OCR: ollama/qwen/openai "+ vision";
  groq/deepseek/anthropic "x no vision" and refused (OCR_PROVIDERS,
  BLOCKED_FOR_OCR). Ollama skips the launcher's model list, because cli.py
  lists only vision models (plus the cloud offer when there are none).
  Model-list note no longer says "OCR mode is planned". Applied with a
  one-off patch script, not committed. test_launcher_menu.py: menu 8 now
  expects "--mode ocr", 8 removed from the placeholder test.
  test_launcher_model_picker.py: TestPickProviderOcr (7; 5 failed first).
  Suite: 924 -> 930. Not yet: real run from menu 8.
- OCR Word-writer fix: output._clean strips characters XML/Word cannot hold
  (control chars, NULL, lone surrogates; tab/newline/CR kept) from page text,
  summary and SUMMARY/SYNOPSIS before writing .docx/.md. Cause: Ang 2010 PDF
  text layer ("All strings must be XML compatible" from lxml). Menu 8 re-run
  on Ang PDF with gemma4:e4b: record + SUMMARY written, text reads normally.
  tests/test_ocr_output.py: 1 test added (failed first). Suite: 930 -> 931.
- DONE OCR context: SUMMARY/SYNOPSIS no longer risk silent truncation.
  call_ollama_provider already sends num_ctx = OLLAMA_CONTEXT (default 32768;
  not Ollama's small default). engine._summarise: text budget =
  (OLLAMA_CONTEXT - 8192 answer - 1000 prompt) x 3 chars/token (~70,000 chars
  at 32k). Fits -> one call, prompt unchanged. Too long -> split at paragraph
  breaks, notes per part (PART_PROMPT keeps numbers/units exactly), then
  combined (COMBINE_PROMPT); log "long text: summarised in N parts". Max 3
  rounds, then the file fails with a clear error. SYNOPSIS uses the same guard
  (built from per-file summaries, so only very large sets split). Cloud uses
  the same cautious budget. tests/test_ocr_engine.py: 3 tests added (failed
  first). Suite: 931 -> 934. OLLAMA_CONTEXT default left at 32768 (shared by
  all pipelines; bigger window = more GPU memory).
- DONE OCR parts test (2026-11-08, OLLAMA_CONTEXT=12000, Ang 2010): record
  written; parts summary dropped NFR pain and FIQ results that the one-call
  summary kept. Summary failure now keeps the record (commit 4acdb91).
- INTERIM OCR broken symbols: Ang 2010 text layer gives "\x02" for ± and
  "\x01" for = (font-specific, cannot be mapped). reader.has_broken_symbols()
  now sends such PDF pages to the vision model. Signs are back, but
  gemma4:e4b added silent errors elsewhere: FIQ PI ">= 2" lost the 2,
  "-65 to -5 msec" became "<= 65 to <= 5", "week 6" became "week 0",
  Table 1 anticonvulsants UC 33 became 40, last sentence words dropped,
  reference names misspelled.
- DONE OCR hybrid safety (2026-11-08): broken PDF pages keep the text layer
  with [?] per lost symbol; the model may only fill [?]; fill_symbols()
  refuses any other change. Ang 2010 run (hybrid_test): all 5 pages refused
  (139 [?] left) - but no wrong letters or digits (33, week 6, ">= 2" kept).
- DONE OCR per-line fill (Ang, gemma4:e4b, second_test_2026-11-08): 64 of
  139 [?] filled, 75 left (p1 21/23, p2 2/6, p3 11/30, p4 41/77, p5 0/3).
  No letter or digit changed. BUT wrong symbols pass the check: ± filled as
  "=" (p1 "mean = SD"; p4 Table 2 "mean = SD mA", "32.5 = 15", "37.6 = 10",
  "56.3 = 30.5"; "0.0 = 4.1"); "ES <= 0.6" likely "=". ASCII "+/-", ">=",
  "<=" accepted as fills.
- FOUND in FILL_DEBUG: most refusals are answers on the wrong line number
  (drift up to 10 lines on p4 with 15 lines per call; some lines missing).
  Model drops minus signs ("[?]65 to [?]5" -> "65 to 5") and reads
  "mean ± SD" as "mean = SD" - refusing those was correct.
- DONE OCR (A) content matching + LINES_PER_CALL 5 (match_test_2026-11-08):
  84 of 139 [?] filled, 55 left (p1 18/23, p2 3/6, p3 6/30, p4 28/77,
  p5 0/3). Table 2 header and baselines "+/-" now right. Still wrong: p1
  "(mean =" for ±; NEW sign error p1 "±10.8" (minus filled as ±); p3
  footnote "P < 0.01" vs p4 body "P = 0.01" - check PDF. Record mixes
  "+/-", "+-", "±" and hyphen for minus.
- TODO OCR next (do first): (B) reader keeps (font, code) of each [?];
  per-line rule: same code -> same fill, different codes of the same font
  -> different fills (refuses "±10.8 ± 24.1", "mean = SD 4.4 ± 13.7");
  then per-code vote over the document (>=2 votes, >=80%); normalise
  +/- +- >= <= and hyphen-minus first; conflict keeps [?] + WARNING;
  never guess minus. Font codes in Ang: 8 (font, code) pairs, 139 total.
- DONE OCR per-code check B1 (codes_test_2026-11-08): reader keeps font:code
  per [?]; on one line same code = same symbol, different codes from one
  font = different symbols; +/-, +-, >=, <=, hyphen normalised to ± ≥ ≤ −.
  56 of 139 [?] left (p1 18, p2 2, p3 8, p4 28, p5 0). Fixed: "versus
  ±10.8" -> "−10.8"; Table 2 all ± and −. Still wrong: p1 "(mean =" (one
  [?] on the line, should be ±). Check vs PDF: p3 "¶ P < 0.01", p4
  "adjusted P > 0.8", "P < 0.3". B2 (document-wide vote) is next.
- DONE OCR document vote B2 (vote_test_2026-11-09): fills compared per
  font:code over the whole document (>=2 votes, >=80% agree): majority sign
  fills every [?] of that code and corrects others; no majority -> back to
  [?]; two codes of one font with one sign trusted by neither. 19 of 139
  [?] left (p1 17, p2 0, p3 0, p4 2, p5 0; was 56). Fixed: p3 "P = 0.01",
  p4 "adjusted P = 0.8", "P = 0.3" (were < > <); p1 "(mean =" back to [?].
  Checked vs PDF page images: all of these, p3 Table 1 "Education >12"
  (earlier runs had ≥12, wrong) and p5 "FIQ pain = 0.2, FIQ PI = 0.5,
  FIQ total = 0.6" (3 vote corrections) are correct.
- TODO OCR: single-vote codes are kept unchecked (Education >12 was right
  by luck); p1 abstract font still 17 [?] (model answers wrong lines);
  summary still LaTeX ($\pm$) and says "Week 6 to Week 12" for the
  week-12 change from baseline. Copying text from such PDFs loses the
  sign too - check signs on the page image.
- TODO OCR option: broken-font pages to a stronger vision model
  (qwen3-vl-plus, cloud, with confidentiality prompt) if many [?] remain.
- TODO OCR summary: strip LaTeX in code after the model; prompt must copy
  [?] exactly (summary dropped [?] before numbers: -0.3 shown as 0.3);
  week-12 change still labelled "Week 6 to Week 12".
- TODO OCR output: lines starting "- " or "* " (Table 2 minus, footnote
  marks) become Word bullets.
- TODO next chat: Writing .docx tables (reuse OCR reader); --report path
  .doc skip message; SR re-check on qwen3-vl-plus against the PDFs.


## Session 36 - 2026-11-09 - branch v2.6-ocr-editor

- Session-opening checklist, all four items run: 1 test count 988 = README
  line 7. 2 56 RESOLVED_ISSUES rows (pattern `^\|\s*(\d+)\s*\|`), no `(#N)`
  in README.md; `#(\d+)` had found only 5, so checklist item 2 now names
  the row pattern. 3 Open Issues = README Known Issues (#2 Medium, #3 Low).
  4 LaTeX claim confirmed: only the prompts asked for plain symbols, there
  was no cleanup in code (SYNOPSIS_PROMPT did not ask at all).
- CI on draft PR #4: both jobs 988 passed (44 / 57 warnings).
- 911cb5e: HANDOFF tidy: Current State to Session 36 with an OCR row,
  new "Next work" list, checklist item 2 pattern.
- Next work item 1 DONE: `strip_latex()` in `pipelines/ocr/output.py`.
  Known commands become Unicode (\pm ±, \geq ≥, \rightarrow →, ^\circ °,
  \% %, Greek letters ...). A command is matched as a whole name, so \le
  never matches inside \leq. `$...$` is removed only when everything
  inside converts. Money ("$5"), [?] and unknown commands are not changed.
  Used on the AI summary in `write_summary` and `write_record`; OCR page
  text is not touched (it is the checked copy of the source).
  Tests: 17 in tests/test_ocr_output.py, failed before the fix
  (AttributeError; `$` still in the SUMMARY .md). Suite: 988 -> 1005
  passed, 10 deselected.
- Not yet checked: a real menu-8 run on Ang to look at the SUMMARY.
- Lesson: the first tidy paste overwrote the Session 35 "TODO SR" block,
  and the second paste duplicated Next work. Both were caught before
  commit by the diff stat (+67/-34 against about +50/-15 expected) and by
  counting the anchors. Check both after any large paste.
- Next work item 2 DONE in code: `KEEP_RULES` in engine.py (copy every
  [?] exactly; keep each change value with the reference point the text
  gives; never make up a time span), added to SUMMARY_PROMPT,
  SYNOPSIS_PROMPT and PART_PROMPT. SYNOPSIS_PROMPT now has PLAIN_SYMBOLS
  too. Evidence (vote_test_2026-11-09, run before the fix): the SUMMARY put
  7.3 ± 9.2 vs −5.4 ± 13.5 under "Week 6 to Week 12". The record's Table 2
  row is "Week 12 change‡" with footnote "‡ Change in reference to
  baseline measurement", so it is baseline to week 12. That SUMMARY kept
  every sign, because the body text repeats the numbers with signs filled.
  The abstract's [?] (e.g. `versus [?]10.2`) has no such backup, so the
  rule stays. Tests: tests/test_ocr_prompts.py (7; all failed before the
  fix with AssertionError; they check keywords, not exact wording).
  Suite: 1005 -> 1012 passed, 10 deselected.
- Seen in the same SUMMARY, not fixed: `strip_latex` leaves `$P = 0.8$`
  and `$P = 0.005$` as written (no backslash inside, so it is treated
  like money); "decrease of −10.2" is a double negative.
- `$P = 0.8$` FIXED: `strip_latex` now removes the dollar signs when the
  text between them is one letter, then = < > ≤ or ≥, then a number
  (`$P = 0.8$` becomes `P = 0.8`, `$n = 15$` becomes `n = 15`). Money is
  unchanged (`$5 and $10`, `from $5 < $10`, `$5 = $5`): the text after the
  first $ starts with a digit, so it can't match. Tests: 8 in
  tests/test_ocr_output.py (the 5 statistic cases failed before the fix
  with AssertionError; the 3 money cases passed before and after). Suite:
  1012 -> 1020 passed, 10 deselected. CI on 2f4cbd3: both jobs 1012 passed.
  Still open from that SUMMARY: "decrease of −10.2" (double negative).
- Real run `s36_check` (menu 8, ollama gemma4:e4b, Ang 2010) confirmed
  all three Session 36 fixes: SUMMARY has `±` and `(P = 0.8)`, no `$`;
  `[?]20.2`, `[?]14.9` and `[?]8.9` copied exactly; heading is "Baseline
  to Week 12". Every summary number checked against page 4 / Table 2.
  19 [?] left (page 1: 17), same as Session 35.
- Page 1 looked one line shifted in FILL_DEBUG, but that is not a bug:
  `refused` stores the answer given under each line's number, while
  `fill_lines` matches answers by content (engine.py docstring, lines
  306-311). Lines are refused because the model drops signs (`5.4` for
  `[?]5.4`); `+/-`, `>=` etc. are already normalised (`_SAME_SIGN`).
  A wrong sign (`>` for `=`) on a one-[?] line passes `_accept`; only
  the document vote catches it.
- Why the vote left page 1's [?] is not identified: FILL_DEBUG (68
  lines) holds only refused answers, and the run window was closed.
  Possible causes: under VOTE_MIN votes, under VOTE_SHARE agreement, or
  two codes of one font with the same sign. TODO: write the vote log
  lines to FILL_DEBUG too.
- TODO: the warning in `_vote_pages` says "AI changed other text on
  those lines", but a [?] can also be left by a dropped sign or a vote
  send-back. Reword to "could not be confirmed - check against the PDF".
- Next work item 3 confirmed in this run: footnotes `* Values are...`
  (Table 1) and `* NFR = ...` (Table 2) become list items in the record
  .docx. New, cosmetic: the SUMMARY .docx shows nested bullets as
  `- *   CBT: ...`.
- Next work item 3 re-checked on `s36_check`: the record .docx page text
  was already right. All `* ` / `- ` lines, including the footnotes
  `* Values are...` and `* NFR = ...`, are `Normal` paragraphs, word for
  word. They only look like bullets in the record .md viewer, and that
  file's text is also correct.
- The real problem was the AI summary: `write_summary` and the Summary
  section of `write_record` wrote its Markdown as literal text
  (`*   **Title:** ...`). FIXED: `_add_markdown()` in output.py turns
  # headings, * / - / + bullets (2 levels: `List Bullet`,
  `List Bullet 2`) and **bold** into Word formatting. Record summary
  headings start at level 4, below "Summary" (2) and the page headings
  (3). Page text never goes through it. The .md files are unchanged.
  Tests: 2 new in tests/test_ocr_output.py; suite 1020 -> 1022 passed,
  10 deselected.
- Open choice (not done): wrap each page's text in the record .md in a
  code fence so Markdown viewers show it word for word.
- `[?]`-left warning reworded (engine.py `_vote_pages`): "(AI changed
  other text on those lines)" -> "(could not be confirmed) - check
  against the PDF". A [?] can also be left by a dropped sign or a vote
  send-back, so the old text blamed the wrong cause. Test:
  tests/test_ocr_warnings.py (new); suite 1022 -> 1023 passed, 10
  deselected. CI green on 4039254 (1022 both jobs).
- FILL_DEBUG now also saves the document-vote and [?]-left lines
  (engine.py `_process_file`): `_vote_pages` gets a wrapper that still
  logs to screen and keeps a copy; the file ends with a
  "--- Document vote and warnings ---" section. The file is written when
  there are refused lines or vote lines (before: refused lines only).
  Next real run shows why each [?] was left without rerunning.
  Cosmetic, not changed: the screen line "AI answers for refused lines:
  <file>" also prints when the file holds only vote lines.
  Test: tests/test_ocr_warnings.py (+1); suite 1023 -> 1024 passed,
  10 deselected. CI green on aa668ae (1023 both jobs).
- Real run `s36_vote` (menu 8, ollama gemma4:e4b, Ang 2010), first run
  with vote lines in FILL_DEBUG: 7 [?] left (s36_check: 19; same PDF and
  model, so the count varies run to run with the model's answers).
  Per page: p1 23 [?], vote filled 14, 5 left (abstract minus signs
  before 10.2, 5.4, 20.2, 14.9, 8.9); p2 6, 2 filled, 1 sent back, 1
  left (`FIQ pain score [?]3`); p3 30, 1 filled + 1 corrected, 1 sent
  back, 1 left (`Education [?]12 years`); p4 77, 32 filled, 0 left;
  p5 3, 0 left. Vote fills checked against Table 2 / page 4 were right.
- Page 1 cause identified (too few votes): in the abstract only `−10.8`
  passed `_accept`, so its font code had 1 vote (< VOTE_MIN 2). It is
  kept unchecked, not copied. A live example of Next work item 4.
- FIXED: `strip_latex` left `($\text{mean} ± \text{SD } -0.3 ± 2.2$ ...)`
  in the summary. `_LATEX_TEXT` now unwraps \text, \textrm, \textit,
  \textbf, \mathrm, \mathit, \mathbf, \operatorname inside $...$ and
  squeezes double spaces; a span with an unknown command still stays.
  Test: tests/test_ocr_output.py (+1); suite 1024 -> 1025 passed,
  10 deselected. CI green on 0e09d81 (1024 both jobs).
- Not fixable in code: the "Week 6 to Week 12" heading came back despite
  KEEP_RULES (the prompt lowers the risk, the small model does not always
  follow it). User caveat: check summary time spans against the tables.
- Idea, not done: fill answers also contain LaTeX (`$\pm$` despite
  LINES_PROMPT), and `_FILL` refuses `$` and `\`. Converting LaTeX in the
  answers before `_accept` would be safe (`codes_agree` still applies).
- Next work item 4 DONE in code (option 3, chosen by the user): a fill
  whose font code has a single vote (in `keep`, not in `agreed`) stays,
  but `_vote_pages` logs "page N: K fill(s) confirmed only once (−10.8)
  - check against the PDF". Each fill is shown with up to 8 characters
  of the text after it, so the user can find it in the PDF. The line goes
  to screen and FILL_DEBUG (via the vote wrapper). Not yet in the record
  .docx/.md: decide separately. Options 1 (keep silently) and 2 (send
  back to [?]) were rejected: 1 hides the risk, 2 loses correct fills
  such as `−10.8` in s36_vote.
  Tests: tests/test_ocr_warnings.py (+2); suite 1025 -> 1027 passed,
  10 deselected. CI green on d224006 (1025 both jobs).
- Tesseract test (post-merge experiment, nothing in code yet).
  Tesseract 5.5.0 is installed at C:\Program Files\Tesseract-OCR but not
  on PATH (pytesseract raised TesseractNotFoundError until tesseract_cmd
  was set). Mac: `brew install tesseract` -> /opt/homebrew/bin (Apple
  Silicon) or /usr/local/bin (Intel). Lookup order to build:
  TESSERACT_CMD in .env -> PATH -> usual install folders -> clear
  message, skip, keep [?].
  Ang pages at 300 dpi, the 7 [?] left in s36_vote: abstract minus signs
  before 10.2, 5.4, 20.2, 14.9, 8.9 read as `—` (all right); `pain score
  [?]3` and `Education [?]12` read as `>` (right: the user checked the
  PDF at 400%; the AI's fill was wrong and safely refused). But `±` was
  read as `+` everywhere, and real `≥` (p2 "score ≥2", p3 "score ≥10",
  p4 "score ≥10") as `=`.
  Design: trust a Tesseract fill alone only for minus (`—`/`–`/`-` ->
  `−`; add `—` to `_SAME_SIGN`). `=`, `>`, `<`, `+` count only when the
  AI fill or the document vote agrees. Fill per [?], not per line, so a
  `+` in a `±` spot never comes in. Expected on s36_vote: 7 left -> 2.
- Check (SR TODO): `relevance_screener.py` imports pytesseract, but
  tesseract.exe is not on PATH on the dev machine. Find out whether that
  path fails or is silently skipped.
- Version set to 2.6.0 for the PR #4 merge (user's choice): README.md
  line 6, main.py VERSION (line 146), pipelines/__init__.py __version__
  (was stale at 2.3.0), CLI .bat lines 4/160, Mac .sh lines 4/19. No
  test checks the version; suite still 1027 passed, 10 deselected.
  Mac launcher exists (scripts/macos/Mac_kcMedicalResearch_CLI.sh), so
  Mac is supported. Post-merge items collected as Next work item 9.
  After merge: update the branch row (main = new merge commit).
- PR #4 merged 2026-11-09 as merge commit bcd42d9 (user chose "Create a
  merge commit" so the branch commit IDs cited in this log stay valid).
  Local main fast-forwarded fa4edb9..bcd42d9 (63 commits, Sessions 33-36).
  Suite on main: 1027 passed, 10 deselected. CI on main green, both jobs:
  test 1027 passed (44 warnings), test-local-pins 1027 passed (57 warnings).
  Current State rows Tests / Branch / CI updated to bcd42d9; OCR mode row
  no longer says "branch only". v2.6-ocr-editor (106c9ef) is fully merged
  and kept for now.
- Branches deleted 2026-11-09 (user's choice), after `git branch -a --merged
  main` listed both and `git log main..v2.6-ocr-editor` was empty:
  v2.6-ocr-editor (106c9ef) and the older v2.5-major-updates (1de797a),
  local (`git branch -d`) and GitHub (`git push origin --delete`), then
  `git fetch --prune`. Only main is left. All commits stay in main's
  history, so the commit IDs in this log are still valid. Branch row updated.

## Session 37 - 2026-11-09 - branch v2.7-sr-fixes

- Docs: Next work rebuilt (Session 36 items closed); OCR row [?] count
  marked run-dependent; corrections added to the 2026-09-02 and Session 28
  notes; Durable Lessons footer fixed.
- Decided: one-file OCR run writes no SUMMARY; output is the filled text
  reproduction only (Next work item 1). Single-vote fills: option A (stay
  [?]) or B (fill + yellow) still to choose. Agreed: Tesseract as second
  reader (item 2), SR reads through the OCR reader after the
  QWEN_VISION_MODEL baseline (items 4-6), Writing reads through the OCR
  reader (item 8).
- Order changed at session open: SR first. Next work item 4
  (QWEN_VISION_MODEL in place of hard-coded qwen-vl-plus) and the baseline
  SR run on this branch; then Writing reader swap -> one-file TEXT output ->
  Tesseract -> SR reader swap (items 5-6).
- main = 82eba10 at session open (two docs-only commits after the bcd42d9
  merge). v2.7-ocr-text was planned last chat but never created.
- SR model rule (Next work item 4): providers.sr_default_model is now the
  only SR model table. Found while checking: a normal launcher SR run was
  never affected (main.py always passes --model), but a direct run of
  `python -m SOURCE_CODE.pipelines.sr.main --provider qwen` without --model
  used get_default_model -> QWEN_MODEL (text) and sent page images to it;
  two tests in test_sr_cli_model_resolution.py pinned that. The probe's
  --model defaulted to qwen-vl-plus (404 on the current key). Local .env
  has no QWEN_VISION_MODEL line, so runs use the code default qwen3-vl-plus.
  Tests: test_qwen_vision_model.py (9), test_sr_cli_model_resolution.py
  rewritten (+2), test_sr_default_model.py (+1). Suite 1027 -> 1039.
- SR baseline on qwen3-vl-plus (run 20261110_120707, override OFF, then restored).
  Papers: Ang 2010, Jensen 2012 (CBT-prefrontal), Karlsson 2015 (CBT-women),
  Lami 2018 (s10608-017-9875-4), McCrae 2019 (zsy234). All 5 screened INCLUDE 0.95.
  Values hand-checked against the PDF text layer (pymupdf):
  - Jensen: pooled 45.6/20.1 vs 57.8/21.9, N 19/15. 45.6 = mean AGE (p2); 57.8,
    20.1, 21.9 not in the PDF. True: Table 3 p7, Posttreat weekly pain VAS
    49 +/- 19 (CBT) vs 59 +/- 26 (controls), means and SDs per footnote.
    N randomised 25/18 (p1, Fig 1 p3); 40 in fMRI analysis (p5); per-arm N behind
    Table 3 not in text layer - provisional. Comparator = waiting list; PICO says
    placebo or active - screener included anyway (outcome False). Question for user.
  - Lami: pooled 4.8/2.1 vs 6.2/2.3, N 38/41; runs gave 4.8 / 3.2 / 4.2. 6.2 not in
    the PDF; quote does not match the PDF. True (Table 4 p12, = override): CBT-P vs
    UMC 7.35 (2.08) vs 7.40 (1.29), N 28/36. Pooled g = -0.63 was the only
    significant study; true values give an effect near zero.
  - Ang: means/SDs match Table 2; N 17/15 extracted, week-6 row says 15/13.
  - Karlsson: values plausible (post-treatment column); year/DOI/source blank.
  - McCrae: correctly excluded (within-subject means with SE).
  Old vs new (20260901_164801_without override vs 20261110_120707): old model got
  Ang N 15/13, Jensen 49.0(19.0) vs 59.0(26.0) N 25/18, Lami 7.35(2.08) vs
  7.4(1.29) right (Lami old flag single_run, N blank); qwen3-vl-plus got all wrong.
  Old model not recorded (likely qwen-vl-max via launcher); it now returns 404 on
  our key (Session 35), so no rollback. Cause = model regression; pipeline gaps
  pre-existed and were masked.
  New run: every wrong pooled value carried a mandatory flag (Jensen: no_majority
  x4 + table_shift; Lami: no_majority on both means); unflagged Ang/Karlsson means
  were right. Stage 4 only LOGS [MANDATORY] (_log_stage4_summary); the pooling
  decision is the try block in the effect-size loop (sr/main.py ~634-726), which
  never reads nondet_flag.
  Findings (no code yet):
  F1 source-quote warning does not stop pooling (Jensen).
  F2 quote check tests numbers against the model's own quote, never the PDF (Lami).
  F3 N can come from another row/timepoint than the means, unflagged (Ang).
  F4 mandatory nondet flag (no_majority/table_shift) still pools (Lami, Jensen).
     DONE on v2.8-sr-review-gate (decided Session 37: BOTH estimates).
     audit_logger.review_skip_reason(cell, override_fields): None = pool;
     str = "needs review: runs disagree (<flags>)". Passes only if every flagged
     field was overridden in study_overrides.yaml (apply() records
     override_fields; table_shift needs all four means/SDs). sr/main.py: gate
     before try; gated studies still get an effect size (included_in_meta False,
     skip_reason set) and go to review_rows; _log_review_sensitivity pools
     rows + review_rows as [SENSITIVITY] "for comparison only", right after
     _log_stage4_summary (before the < 2 studies abort). Primary estimate
     excludes them. Gated + missing N is reported as needs review, not missing N.
     Tests: tests/test_sr_review_gate.py (16). Not yet: sensitivity estimate in
     the Word/HTML report and forest plot; group-label no_majority cannot be
     cleared by an override (not overridable) - stays gated.
  F5 metadata fields blank (Karlsson).
  F6 each extracted number must appear in the PDF text; catches unflagged wrong N
     (Ang) and single_run rows. Needs the OCR reader (item 5): [?] -> "unverifiable".
  F7 regression fixture from hand-checked values (Lami, Jensen, Ang N).
  Order after PR #5: F4 gate DONE (v2.8-sr-review-gate, both estimates); next F7
     (regression fixture), then F6, then [SENSITIVITY] in the report, then local-first SR.
- F4 gate real run 20261110_174457 (qwen3-vl-plus, override ON): Lami runs
  disagreed (no_majority x2 + table_shift) but all six fields overridden ->
  pooled with reviewer values, g -0.03 (gate override path confirmed). Jensen:
  all 3 runs empty -> skipped "insufficient mean/SD/N"; flag reads "unanimous"
  (agreement on nothing - misleading); quotes are Table 1 baseline. Ang N 17/15
  again, own quote says 15/13 (F3). McCrae now INCLUDED g +0.01 but control quote
  is the CBT-P row while control_group = WLC: CBT-I vs CBT-P, wrong comparison;
  only majority flags, gate does not apply. [SENSITIVITY]: nothing to compare.
  F8 (new): quote-vs-field checks, no PDF needed - control/intervention quote arm
  label must match the group label; Ns in the quote must match extracted N.
  Question for user: waiting-list comparator (Jensen, Karlsson, McCrae) vs PICO
  "placebo or active".
- Decided Session 37 (user): waiting-list comparator INCLUDED, reported as a
  subgroup: waiting list (Jensen, Karlsson, McCrae) vs active/placebo (Ang, Lami).
  Needs: PICO comparator wording in prisma_criteria.yaml, comparator type per
  study (screener rationale or study_overrides field), subgroup estimate in
  Stage 4 and the report; warn when a subgroup has < 3 studies.
- OCR tools vs SR accuracy (Session 37 analysis): OCR reader fixes screening/RoB2
  on broken-font papers (Karlsson, McCrae - currently UNVERIFIED) and gives F6 a
  trustworthy text layer ([?] -> "unverifiable"). It does NOT fix the baseline
  extraction errors (Jensen wrong table, Lami invented, Ang N wrong row, McCrae
  wrong arm): those text layers held the right numbers; the model chose wrongly.
  Order: F7 fixture -> OCR reader in SR (item 5, with manual [?] rerun) -> F6 + F8
  -> waiting-list subgroup -> local-first SR.
- F7 DONE on v2.9-sr-fixture: tests/fixtures/sr_truth.yaml (hand-checked Ang,
  Jensen, Lami; Karlsson, McCrae checked: false) + scripts/sr_score_run.py
  <run id or folder> (scores meta_analysis_results.csv = pooled values after
  overrides; tolerance 0.1; exit 1 if a checked study is POOLED wrong/missing;
  notes manual overrides). Tests: tests/test_sr_score_run.py (9). Suite 1064.
  First scores: 1 Sep old model 2/3 fully correct, 0 pooled wrong (exit 0);
  baseline 20261110_120707 0/3, 3 pooled wrong (exit 1); gated run
  20261110_174457 1/3 (Lami via override), Ang N 17/15 pooled wrong (exit 1).
  Old model's Jensen N 25/18 supports the truth N. 1 Sep run POOLED McCrae with
  SDs 2.36/2.27 on a 0-100 scale (likely SE) - unscored; hand-check McCrae next.
- Comparator wording (decided Session 37, user): placebo, active comparator, or
  waiting list; waiting-list trials INCLUDED and reported as a subgroup.
  Updated on v2.10-sr-screening: SOURCE_CODE/pipelines/sr/config/prisma_criteria.yaml
  (comparator, nested under a section) and input/sr/pico_sample.json (comparator +
  formulator_output, 3 places). The old "Placebo or active comparator" could make
  the screener exclude Jensen, Karlsson, McCrae. Guarded by
  tests/test_sr_comparator_criteria.py (3 tests). New reviews: comparator is what
  the doctor types (main.py ~line 1600); a waiting-list hint there is still TODO.
- Screening/RoB2 plan (Session 37, agreed): screening reads OCR text with [?]
  filled -> rule checks first (RCT, comparator type: placebo/active/waiting list)
  -> 3-run AI vote, Ollama first, cloud only behind the warning gate -> split vote
  or low confidence = NEEDS REVIEW, never exclude -> exclusion reason quote checked
  against the OCR text -> reviewer-confirmed decisions saved in
  input/sr/screening_decisions.yaml; reruns reuse them and show what changed.
  RoB2: same pattern per domain (signalling answers with quotes, 3-run vote,
  rob2_decisions.yaml; tool proposes, doctor confirms). Then extraction on OCR
  text with number-in-text and arm-label checks (F6 + F8). NOTE: .gitignore
  ignores input/sr/* - decision files need a !-exception if they are to be tracked.
- Shared paper text (Session 37, v2.10-sr-screening): new
  SOURCE_CODE/pipelines/sr/src/utils/paper_text.py, get_paper_text(pdf, cache_dir)
  built on pipelines/ocr/reader.py. Text-layer page -> text; few lost symbols ->
  [?] kept and counted; broken-font page (ratio >= 0.05 AND >= 20 [?]) ->
  Tesseract; scanned page -> Tesseract; Tesseract missing -> warning, marks kept.
  Saved as <cache_dir>/<stem>.txt, no BOM; reruns reuse it (manual [?] fixes
  respected). tests/test_sr_paper_text.py (12 tests). NOT yet wired into
  screening/RoB2/extraction; no AI fill or Tesseract counter-check of [?] yet.
  Real-paper trial (no AI, PDF_RENDER_DPI 200): Ang 139 [?], Jensen 46 (mostly
  copyright signs), Lami 21 (lost "ti" ligature); Karlsson 8670 -> 0 (11 pages
  Tesseract, 25 s), McCrae 10378 -> 0 (15 pages, 30 s). Broken ratio per page:
  Ang/Jensen/Lami <= 0.013, Karlsson/McCrae 0.101-0.138 on every page.
  Finding: the old screener's _try_cmap_offset_decode (#18) "succeeds" on these
  two (offset +1) but leaves spaces lost and digits WRONG ("Submitted: 15 March,
  2018" -> "904M]rch+1/07"; Karlsson shift not uniform). Old screener therefore
  fed wrong numbers to the AI for Karlsson/McCrae; RoB2 had no decode at all.
  Tesseract got "Submitted: 15. March, 2018" right. Caution for F6/F8: Tesseract
  adds stray dots ("15. March", "approximately. 4 million") - check before
  extraction trusts numbers next to dots.
  Also: screening and RoB2 prompts take only the first 6000 chars
  (MAX_SCREEN_CHARS, MAX_ROB2_CHARS) - RoB2 likely never sees most of Methods;
  later step: send Methods/Results sections from the saved text.
- McCrae 2019 hand-checked (Session 37, user decided option C): multi-arm trial
  (CBT-I, CBT-P, WLC). CBT-I + CBT-P combined vs WLC (Cochrane Handbook 23.3.4):
  46.86 (24.06) n 57 vs 52.38 (24.04) n 28; morning pain VAS 0-100,
  post-treatment, Table 3 p9; N = completed post-treatment (Figure 1); evening
  pain not used; g about -0.23 (calculated). Both earlier runs were wrong (1 Sep:
  whole-sample SEs 47.14/52.67; 20261110_174457: CBT-I vs CBT-P, allocated N
  39/37). Entry in input/sr/study_overrides.yaml; sr_truth.yaml McCrae
  checked: true (scorer now 4 checked). Commit 58c02d9.
- Reviewer-entered data in the report (Session 37, user: "mentioned in the
  report"): report_generator.py (Word, under Methods) and html_report.py (under
  Data Extraction) list every study with override_fields / override_note, note
  in full (McCrae arms combined; Lami). Before this it was only in the log and
  extracted_data.csv. tests/test_sr_report_overrides.py (5 tests).
- Shared text in screening + RoB2 (Session 37, commit b3d804c): Stage 2 of
  sr/main.py calls get_paper_text once per PDF, saves input/sr/paper_text/
  <stem>.txt (git-ignored, hand corrections kept), screener and RoB2 get
  paper_text= and no longer reopen the PDF. First run 20261110_234448:
  Karlsson 24 s, McCrae 32 s (Tesseract, all pages broken font). Rerun
  20261111_001942: all 5 "reused saved text", [?] 139/46/0/21/0, files
  untouched, 5 INCLUDE. Scorer identical in both runs (no drift on scored
  fields).
- Launcher criteria write (commit afd90a3): SOURCE_CODE/main.py Step 3 now
  calls pipelines/sr/src/utils/criteria_file.write_criteria_if_changed -
  writes prisma_criteria.yaml only if the parsed content differs, no line
  wrapping (old yaml.dump wrapped the comparator at 80 chars and left the
  tree modified after every run). Verified: launcher printed "unchanged
  (same PICO)", file time and git status unchanged. tests/
  test_sr_criteria_write.py (7). OPEN: launcher still hard-codes
  inclusion_criteria [RCT, Adult participants] and exclusion_criteria
  [Non-RCT, Animal studies]; hand edits to those in the yaml would be
  overwritten on the next run.
- RoB2 overall rule (Session 37): rob2_tool.apply_rob2_overall on both
  paths - any High domain -> High; all 5 Low -> Low; all 5 assessed
  otherwise -> Some concerns; domains missing and none High -> Not
  assessed. Model answer kept in new column overall_model. Failed
  assessment is "Not assessed" (was "High"); html_report shows it in grey,
  not as a red High badge. Found because Ang had Missing data = High but
  overall "Some concerns" in runs 20261110_234448 and 20261111_001942.
  tests/test_sr_rob2_overall.py (9).
- Findings from runs 20261110_234448 / 20261111_001942 (still open):
  Ang N 17/15 (truth 15/13) in BOTH runs - consistent extraction error, not
  drift; quote in the same row says 15 and 13 -> F8. Jensen quotes Table 1
  baseline (60.5 +/- 4.0), means empty, skipped; flag says unanimous.
  Lami quote looks invented; McCrae control labelled WLC but quote is the
  CBT-P row (F8). RoB2 still sees only the first 6000 chars (MAX_ROB2_CHARS):
  justifications say "in the abstract/excerpt"; McCrae missing data "not
  reported" though Figure 1 has 27/30/28; McCrae randomisation Low on weak
  grounds (near-equal groups, registered).
- Running: desktop start.bat -> launcher -> SR runs
  "python -m SOURCE_CODE.pipelines.sr.main --pdf-dir input\sr --provider
  qwen --model qwen3-vl-plus --effect-measure SMD". Plain
  "python SOURCE_CODE\main.py" starts the CODING pipeline (--mode default).
  Console capture: Ctrl+A, Enter in the window, paste to
  reports\sr_run_console.txt (no log file is written to the run folder).
- NEXT (in order): (1) RoB2 gets Methods/Results sections of the shared
  text instead of the first 6000 chars (test first); (2) F8 quote-vs-field
  checks (arm label vs group label, Ns in quote vs extracted N); (3) F6;
  (4) [SENSITIVITY] and waiting-list subgroup in the report; (5) local-first
  SR.

## Session 38 - 2026-11-11 - branch v2.10-sr-screening (PR #8)

- RoB2 reads Methods + Results of the shared paper text instead of the first
  6000 chars (Session 37 NEXT item 1). New stdlib-only
  pipelines/sr/src/utils/paper_sections.py: rob2_text(text, limit,
  fallback_chars) -> (text, note). Sends the start of the paper (title +
  abstract, up to 1500 chars) + Methods + Results, within
  MAX_ROB2_SECTION_CHARS = 20000. Each section gets half; space one section
  does not need goes to the other. A heading is a line on its own (METHODS,
  2. Methods, Methods., Materials/Patients and methods); a structured-abstract
  label "Methods: ..." is not. Methods found more than once -> longest span
  wins. No Methods heading -> first MAX_ROB2_CHARS (6000) as before, never a
  failure. rob2_tool.py logs "[ROB2 TEXT] <file>: <note>" per paper.
- MAX_ROB2_CHARS = 6000 kept as the page-reading budget (lines 192/251,
  test_rob2_ocr_stops_when_budget_met). Prompt unchanged: it never said
  "excerpt" or "abstract"; those words in Session 37 justifications came from
  the cut text. Screener cut (relevance_screener.py, MAX_SCREEN_CHARS) unchanged.
- Tests: tests/test_sr_paper_sections.py (23; 21 errored on the missing module
  and 2 failed on the 6000 cut before the code). Suite: 1106 -> 1129 passed.
- Committed as 908f889; CI green on PR #8 (1129, both jobs).
- Real saved texts (input/sr/paper_text/, all 5 papers) checked with a
  read-only script. Jensen (fMRI) heading "2. Methods and material" was not
  recognised (fell back to 6000); METHODS_RE now also accepts
  "Methods and material(s)/patients/subjects/participants". At 20000 the half
  split dropped every 'drop' mention (McCrae 8/8) and the intention-to-treat
  text (Karlsson, Lami, McCrae): MAX_ROB2_SECTION_CHARS and the rob2_text
  default raised to 50000. All 5 papers now send whole Methods + Results
  (Ang 15236, Jensen 30545, Karlsson 27753, Lami 28670, McCrae 48005 chars;
  McCrae ~12k tokens). Words still not sent are outside Methods/Results and
  not RoB2 facts (withdrawal reflex, cited titles, pain behaviour), except
  Lami line 1897 (Discussion, intention-to-treat): no Limitations section
  added; checked by hand at the rerun (Next work 7a).
- Tests: +4 (3 reversed heading variants, default limit >= 48000; 4 failed
  before the code). Suite: 1129 -> 1133 passed.
- Not yet verified: RoB2 rerun on the real papers (Next work 7a).
- 306d838 pushed: "Methods and material(s)" headings, limit 50000; PR #8 CI
  green, 1133 passed, both jobs.
- Rerun 20261111_081840 (console.txt in the run folder): [ROB2 TEXT] counts
  match the read-only check (Ang 15236, Jensen 30545, Karlsson 27753,
  Lami 28670, McCrae 48005). All overall stay Some concerns. Methods-based
  answers improved (Karlsson randomisation Low: ranuni + sealed opaque
  envelopes; Jensen outcome Low: blinded assessor). Weak spots in 7a/7c.
- Registration IDs did not reach RoB2: Ang NCT00965601 (abstract, past the
  1500-char start), Karlsson NCTO1004458 (letter O) + end matter. rob2_text now
  adds lines matching NCT/ISRCTN/clinicaltrials.gov if not already sent
  (max 500 chars). A bare "registered" does not match. Added: Ang 1,
  Karlsson 3, McCrae 1; Jensen and Lami have none. +4 tests, 1137 passed.
- de15a59 pushed: registration lines sent to RoB2. PR #8 CI green, 1137
  passed, both jobs.
- Scorer saves its report: scripts/sr_score_run.py also writes
  <run folder>/score.txt (same text as the screen, UTF-8 no BOM, LF; replaced
  on rerun; nothing written when the folder is not a run). The screen ends
  with "[SCORE] saved <path>" (not in the file). +3 tests in
  tests/test_sr_score_run.py. 20261111_081840 scored: Ang n 17/15 vs truth
  15/13 (WRONG, POOLED), Jensen not pooled (mean/SD missing), Lami and McCrae
  ALL MATCH via study_overrides, Karlsson not hand-checked.
- assets/ is back on purpose: desktop shortcut icons (icon_AI_kcMedicalResearch,
  icon_input, icon_output, icon_reports; .ico for Windows, .png for Mac).
  tests/test_no_streamlit.py no longer lists icon_AI_kcMedicalResearch.ico
  as deleted; logo_AI_kcMedicalResearch.png stays on the list. 1140 passed.
  Icons committed in 222e779: ico rebuilt from the png (16-256 px), ~0.9 MB
  instead of 15 MB.
- c6b188f (score.txt) and 222e779 (icons) pushed; PR #8 CI green at 222e779,
  1140 passed, both jobs.
- Rerun 20261111_114651 (console.txt and score.txt in the run folder):
  [ROB2 TEXT] Ang 15297 (+1 registration line), Jensen 30545, Karlsson 27919
  (+3), Lami 28670, McCrae 48125 (+1). All 25 domain labels and 5 overall
  the same as 20261111_081840 (all Some concerns). Score unchanged. The model
  ignores sent registration and ITT lines -> 7c (prompt).
- 75915e0 pushed (HANDOFF rerun findings).
- Correction: RoB2 never saw more than 6000 chars. _call_with_text cut every
  text with [6000, 3000] (only the empty-answer retry needs a shorter text).
  The [ROB2 TEXT] "sent N" counts were what rob2_text built, not what the
  model got; the wiring tests captured text before the cut, so they passed.
  Runs 20261111_081840 and 20261111_114651 therefore saw abstract + about the
  first 4500 chars of Methods only. Fixed: first try sends the whole text,
  the retry after an empty answer is cut to MAX_ROB2_CHARS; new log line
  [ROB2 SEND] attempt n: X of Y chars. tests/test_sr_rob2_send.py (4) checks
  the text at client.chat.completions.create. Comment at rob2_tool.py top
  updated. 1144 passed.
- 5907fae pushed; PR #8 CI green, 1144 passed, both jobs. Rerun
  30545 / 27919 / 28670 / 48125 chars, no retry. 7 domain labels changed vs
  20261111_114651: Ang and Jensen deviations + reported_result -> Low;
  Karlsson missing_data + outcome_measurement -> Low; Lami missing_data ->
  High (Methods line 501: per-protocol analysis; completed 34/38/41 of 42),
  so Lami overall High by the domain rule (model said Some concerns).
  Registration IDs cited, McCrae ITT seen, label now "Ang 2010". Score:
  Ang n WRONG as before; Jensen n WRONG 19/15 vs 25/18; Karlsson not pooled
  (table_shift), so 3 studies pooled instead of 4 -> 7e.
  superseded: Methods line 501 says per-protocol.
- Overrides vs validity: the review result stays valid (reviewer-checked, values
  traced in override_note); the AI accuracy check was circular for Lami/McCrae
  -> 7f. test_extraction_regression_fixtures.py comment "Lami means stable,
  only Ns drift" is outdated (121950: means no_majority 3.8/none/3.2).
- 7k: Ang excluded by the reviewer (exclude_from_meta), reason shown in the
  report; run 20261111_190839 pools 3. CI green at e4e97b8 (1157). 1164 passed.
- 7n(e) + 7m: report Reason cell reworded (plain_skip_reason, statistical
  reasons verbatim); score report prints "POOLED: n of N studies". CI green
  at a56dc55 (1164). 1177 passed.
- 7h: fibromyalgia set moved to reference/sr_cbt_fibromyalgia/; sample config
  with <...> placeholders stops a direct run; empty overrides template. 1193 passed.
- 7f done: sr_score_run.py scores the AI's own values for overridden studies
  (_ai_overrides reads override_fields). Run 20261111_121950: AI alone 4
  checked, 0 fully correct. Lami AI N 38/41 vs 28/36, means 3.8/5.2 vs
  7.35/7.4 (sd_intervention 2.1 within tolerance of 2.08); McCrae AI N 37/37
  vs 57/28, means 47.14/52.67 vs 46.86/52.38, both SDs missing. Pooled
  SUMMARY and exit code unchanged. +5 tests, 1149 passed.
- b0b4ab9 pushed; PR #8 CI green, 1149 passed, both jobs. 7e: Ang (Ns only)
  and Karlsson overrides added; Karlsson hand-checked in the PDF (crude mean
  (SD), adjusted means have no SD; tertiary outcome) and set checked: true in
  sr_truth.yaml. Two tests relied on Karlsson unchecked:
  test_unchecked_and_unknown_studies_are_not_scored now marks a copy
  unchecked; baseline test now 5 checked, 1 fully correct. Count test renamed
  to five. Run 20261111_161320: 4 pooled; SUMMARY 5 checked, 4 fully correct,
  0 wrong AND POOLED; AI alone 5 checked, 1 fully correct (Karlsson). Lami AI
  means 4.2/5.8 this run (3.8/5.2 in 121950), truth 7.35/7.4.
- 7c prompt fix: Domain 4 rule + PICO outcome to RoB2; 7 tests, 1156 passed.
  Run 20261111_171313: outcome_measurement off Low for all five, Jensen
  overall High by the domain rule (model said Some concerns). Lami AI means
  3.2/4.1 (3.8/5.2 in 121950, 4.2/5.8 in 161320; truth 7.35/7.4).
- 46fbd9b pushed; PR #8 CI green, 1156 passed, both jobs. 7j High outright:
  1 test, 1157 passed. Run 20261111_175754: Domain 4 and overall High for
  all five, no other domain changed vs 171313; Ang not pooled -> 7m.
- PR #8 CI green at b32f4c4: 1193 passed, both jobs.
- Docs (Session 38 close): Readme/readme_sr_pipeline.txt added (user guide:
  how the SR pipeline works and how to use it). docs/sr/REVIEWER_GUIDE.md
  rewritten for reviewers (kept, not deleted: cited by 2 tests, 5 console
  messages, 6 README lines and flashcard-help.html). Section numbers 2.2,
  3.1, 3.5, 5, 6 kept; 2.2 still numbers 5 branches (doc-sync test passes).
  Updated: McCrae pooled from reviewer values (Table 3 p9, arms combined),
  Tesseract instead of the offset decoder, qwen3-vl-plus, review gate,
  exclude_from_meta, RoB2 checks (new 3.6), change vs final values, new
  2.3 (errors seen in the worked example).
- Checked against code at close: screening cuts at MAX_SCREEN_CHARS = 6000
  (relevance_screener.py 222); RoB2 sends Methods + Results up to 50,000
  chars (MAX_ROB2_SECTION_CHARS), first 6000 if no Methods heading, retry
  cut to 6000 - readme section 5 corrected to say so; sr_score_run.py
  writes score.txt itself (line 242-243, UTF-8 no BOM) -> old 7b done.
- 7g superseded by 7k (Ang excluded, so change-vs-final mixing does not
  arise). Next work renumbered 1-19 in plan order.
- Suite unchanged: 1193 passed, 10 deselected (docs only).

## Session 39 - 2026-11-12 - branch v2.10-sr-screening
- Jensen N in the truth fixture: sr_truth.yaml had 25/18 (randomised,
  n_status: provisional) while the reference override had 19/15
  (completed treatment, Fig 1 p3 = the N behind posttreatment Table 3),
  so sr_score_run.py marked a correct override WRONG. Truth now 19/15,
  n_status: inferred (Table 3 N is not stated in the text). Rule in the
  yaml header: N = N analysed at the reported timepoint, not randomised N.
  New tests/test_sr_truth_override_sync.py: for every checked study in
  both files, truth N must equal override N; prints the denominator
  (8 N fields, 4 studies; Ang unchecked). Failed before the fix on Jensen
  only. test_empty_cell_is_missing now expects MATCH for Jensen N (WRONG
  path still covered by the Ang 17/15 test). Regression fixture comments
  no longer call 25/18 "reviewer-verified". The scorer never reads
  n_status (it compares FIELDS only). Suite: 1215 -> 1217 passed.
- Item 4 (b)(c)(e): override_fields entries have three shapes
  (study_overrides.py): field(old->v) / field(absent->v) = changed,
  field(confirmed v) = reviewer agreed with the AI, bare names
  (first_author, year, exclude_from_meta) = no value. Only a changed
  value now counts as reviewer-entered data.
  Scorer (sr_score_run.py): parse_override_fields(); exclude-only (Ang)
  no longer prints "values from study_overrides.yaml"; confirmed fields
  are the AI's own values, so a confirm-only study gets "AI alone" lines
  and "reviewer confirmed the AI's values". Real run 20261112_222233:
  only Ang's line changed.
  Reports: new pipelines/sr/src/reporting/override_summary.py used by
  html_report.py and report_generator.py (same rule, counts cannot
  differ). Run 20261112_222233 would have said 5 of 5; now 4 of 5.
  Confirm-only studies named separately. Tests +8 (test_sr_score_run.py
  4, test_sr_report_overrides.py 4); Word tests confirmed failing on the
  old report_generator.py (git stash). Suite 1217 -> 1225. Commit 434e771.
- CI on 13a3a86: green, 1217 passed, both jobs; 57 warnings (44 before;
  unpinned versions, not investigated).
- Item 4 (d): not a bug. "[SENSITIVITY] no needs-review studies" was
  correct: Jensen passes the F4 gate because its override covers every
  flagged field ([AGREEMENT]), so it is pooled, not held back. Now
  [SENSITIVITY] names such studies: "Runs disagreed on Jensen (2012), but
  a reviewer overrode every flagged field, so it is not held back".
  main.py: resolved_by_override list, resolved= parameter. Tests +3
  (tests/test_sr_review_gate.py). Suite 1225 -> 1228.
- CI on 083539e: green, 1225 passed, both jobs, 57 warnings.
- Item 4 (a): Word report (report_generator.py) now has "Studies included
  in the review but not in the meta-analysis" after the Meta-Analysis
  paragraph: "N of M studies pooled", one bullet per left-out study with
  the plain reason (plain_skip_reason from html_report.py) and
  [Reviewer]/[Automatic]. main.py passes meta_audit to ReportGenerator.
  Tests +3 (tests/test_sr_report_overrides.py). Suite 1228 -> 1231.
  Item 4 is complete.
- CI on 8d5a44f: <paste result>.
- Item 5 (SR LaTeX check): DONE, no code change. Run 20261112_222233:
  no stray $...$ in pipeline outputs (5 CSV, 1 HTML, 2 TXT, 1 JSON,
  docx paragraphs + tables); pattern \$[^$\s][^$]{0,80}\$ confirmed on
  a positive example. The only hits were in uploads/zsy234.pdf (McCrae
  source paper): its text layer is a broken font, every character
  shifted down by one ("o]hmqdctbshnmr" = "painreductions", "$" = "%").
  Not LaTeX, but any text-layer read of McCrae gets garbage.
  Not checked: console (no log saved). Open question: no pipeline-made
  PDF report in the run folder although main.py calls
  PDFReportGenerator().generate( - where does it write, or did it fail?
- CI on ccc6e86: green, 1231 passed, 10 deselected, both jobs, 57 warnings.
- PDF report (open question from item 5): run 20261112_222233 had no PDF
  because WeasyPrint is not installed in .venv (ModuleNotFoundError),
  although pipelines/sr/requirements.txt lists weasyprint>=62.0.
  PDFReportGenerator fell back to HTML-only mode; the run summary printed
  only "PDF -> None" and the warning was lost (no log saved). Fix:
  result["pdf_error"] for both failure paths, pdf_summary_line() in
  pdf_report.py; main.py summary now warns "PDF -> NOT WRITTEN (<reason>)".
  Reviewer decision: no real PDF needed (HTML + DOCX), WeasyPrint stays
  uninstalled. tests/test_sr_pdf_report_status.py (4). Suite 1231->1235.
- CI on 858273e: green, 1235 passed, 10 deselected, both jobs, 57 warnings.
- Item 6a (stale RoB2 log text): DONE. rob2_tool.py OCR log no longer says
  "(prompt uses first 6000)" - stale since Session 38 (prompt = Methods +
  Results via rob2_text, up to 50000; [ROB2 TEXT] logs what is sent).
  tests/test_sr_rob2_log_text.py (2). Suite 1235->1237.
- CI on 9cd6dfc: green, 1237 passed, 10 deselected, both jobs, 57 warnings.
- Item 6 b/c/d (RoB2 run-to-run): DONE, no code change. 4 runs
  (20261111_175754, 20261111_190839, 20261112_161648, 20261112_222233),
  5 studies x 6 cells: 1 of 30 differed (Lami missing_data Some concerns in
  161648, High in the others); overall High for all 5 in every run
  (outcome_measurement High everywhere). The 11 Nov runs predate the
  Session 38 RoB2 text change. Decision: no N-run vote (N x RoB2 cost for
  one cell, overall unchanged).
  6b: the flow-diagram lines ARE in the text sent to RoB2 (checked with
  rob2_text on input/sr/paper_text). McCrae: sent "Completed post-treatment
  (n=27/30/28)", but the model quoted "Did not receive intervention
  (n=9/7/0)" and gave WLC 5. Lami: 5 and 11 put in the wrong arms
  (analysed 28/27/36 imply 6/11/5). Flattened flow-diagram columns lose
  the arm order; this is a model reading error, not a text-selection bug.
  A reviewer must check dropout numbers in RoB2 justifications.
  6d (Jensen 45.6 no_majority, Lami mean drift): extraction; already kept
  out by the F4 gate and fixed by overrides; no further action.
- CI on d39817e: green, 1237 passed, 10 deselected, both jobs, 57 warnings.
- Item 7 (screening reads first 6000 chars): DONE, no code change.
  Screening uses the shared paper_text (relevance_screener.py 122-123),
  then cuts to MAX_SCREEN_CHARS = 6000 (221-222). In the 5 paper_text
  files "random" is inside the cut for all 5; first "method" is after it
  for Jensen (7172) and Lami (8887). 4 runs: 20 of 20 INCLUDE.
  pico_outcome False for Jensen in all 4 runs (pain results in Table 3
  p7, beyond the cut) - only the flag, not the decision (prompt leans to
  INCLUDE). Decision: keep 6000 (screening runs on every uploaded paper;
  Methods + Results up to 50000 = ~8x tokens per paper). Revisit if a
  relevant paper is ever excluded on outcome. Minor: prompt label at
  line 225 says "first 8 pages" although shared text is cut by characters.
- CI on 263fc4c: green, 1237 passed, 10 deselected, both jobs, 57 warnings.
- Screening note: run 20261112_222233 left Ang pico_outcome empty (not
  True/False; rationale says no standard pain measure). Decision INCLUDE
  unchanged; Ang is excluded from pooling by reviewer anyway. No action.
- Item 8 (F8 N check): DONE. Branch 2 (number_not_in_quote) of
  _flag_suspect_source_quotes now also checks each arm's N: if the quote has
  candidate Ns (whole numbers 2-1500; not decimals, %, mean (SD) cells,
  m +/- sd, ranges, SF-36-style, numbers after Week/Month), the extracted N
  must be one of them. Ang 17/15 vs quote 15/13 now warns (it had no
  warning). Branch count stays 5; REVIEWER_GUIDE 2.2 branch 2 extended.
  source_quote_warning only logs, does not gate pooling.
  Not done: arm-label check (McCrae control quote = CBT-P row) - needs the
  paper's full arm list (only 2 labels known); revisit with item 10.
  tests/test_sr_quote_n_check.py (6). Suite 1237->1243.
- CI on 13af67d: green, 1243 passed, 10 deselected, both jobs, 57 warnings.
- Item 9 (F6, number must appear in paper text): NOT BUILT, by measurement.
  Offline trial on run 20261112_222233: AI values (old side of override
  field(old->new)) checked with _number_in_text against input/sr/paper_text.
  22 wrong AI values, 1 caught (Lami mean_control 5.1); the rest exist
  elsewhere in the paper (Jensen 45.6 = mean age; Lami 38/41 = baseline Ns;
  Karlsson other row/column; McCrae pooled time effect). 2 false alarms:
  Ang -20.2 / -14.9 are correct (Table 2) but not found in paper_text
  (cause not checked; minus-sign rendering suspected). Whole-paper presence
  is too weak; binding a number to its own quote (branch 2, F8) is what
  catches errors. Moved to item 10: with paper_text wired into extraction,
  branch 5 (verbatim_mismatch) can check quotes against the paper (today
  source_text=None, data_extractor.py ~2137).
- Item 10 (paper_text into the quote check, option A): extract_batch passes
  r["paper_text"] to extract_by_pdf_path and _extract_anthropic; branch 5
  (verbatim_mismatch) now runs on image runs with source_text = paper_text
  (was None, so never checked). New _quote_in_source(): tolerant token match
  (ignores case, punctuation, whitespace, [?], stray dots), plus numseq for
  table rows only (>= 4 numbers and numbers >= words; numbers in order within
  40 tokens, for tables stored out of order, e.g. Ang Table 2). Sentences
  never use numseq: a paraphrase that keeps the numbers still warns.
  Run 20261112_222233: warns Lami x2 (made-up "mean = 4.2 (SD = 2.1)"
  quotes) and Jensen control (override covers it); no false alarms (exact
  matching had flagged Ang x2, McCrae x2). Branch count stays 5. Extraction
  input (images vs text) not changed; options B/C need paid live runs.
  tests/test_sr_quote_vs_paper.py (5 tests). Suite 1248.
- CI on 3355f73: green, 1243 passed, 10 deselected, both jobs, 57 warnings.
- Item 11 (control-type subgroups, option C): new src/analysis/subgroups.py.
  Control type = reviewer's comparator_type in study_overrides.yaml
  (waiting_list / usual_care / attention_placebo; now in ALLOWED_FIELDS,
  bare name in override_fields so it is not counted as reviewer-entered
  data), else the extracted control_group label (WL/WLC/wait-list ->
  waiting list; UC/UMC/usual/TAU -> usual care; attention/placebo/sham).
  Unknown label or unrecognised reviewer value -> unclassified: listed by
  name, never pooled. Pooled rows only (Ang is excluded by the reviewer, so
  it is not in any subgroup). k = 1 -> "1 study - not pooled"; k = 2 ->
  pooled with "< 3" caution; pooling errors are reported, not raised.
  Plus an estimate excluding waiting-list trials. main.py logs [SUBGROUP]
  lines (not [SENSITIVITY]); Word and HTML reports get "Subgroups by
  control type" from the shared subgroup_report_lines(). Expected on run
  20261112_222233 data: waiting list k=3 (Jensen, Karlsson, McCrae)
  pooled; usual care k=1 (Lami) and excluding-WL k=1 not pooled; all
  classified from label. NOT yet seen in a real run (needs a paid run).
  Tests: test_sr_subgroup_comparator.py (8), test_sr_subgroup_wiring.py
  (4), test_sr_subgroup_reports.py (5). Suite 1265.
- CI on f9551e7: green, 1248 passed, 10 deselected, both jobs, 57 warnings.
- Item 11d: docs/sr/REVIEWER_GUIDE.md new section 5.2 (comparator_type:
  allowed values, unclassified, bare name, exploratory, not [SENSITIVITY]).
  Docs only; suite unchanged at 1265.
- CI on 776b3d9: green, 1265 passed, 10 deselected, both jobs, 57 warnings.
