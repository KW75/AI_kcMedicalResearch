# Session 26 — #11 close-out

## Evidence (probe, 2026-08-29, qwen-vl-plus, 5 corpus PDFs, 3 runs each)

| config | PDFs with any disagreement | numeric-field disagreement | quote disagreement |
|---|---|---|---|
| baseline `t=0.1`, no seed | 4/5 | 1-s2.0 paper (sd_i, mean_c, sd_c) | 4/5 |
| `t=0`, `seed=42` | 4/5 | **Ang: 3 runs, 3 different tables** (column shift; change scores; correct) | 4/5 |

Conclusions the data supports:
- `seed` is ignored by qwen-vl-plus and `temperature=0` is not deterministic — identical calls returned different source quotes on 4/5 papers.
- Sampling controls cannot fix #11. They stay in (vision and text paths can no longer drift apart) but the handoff must not describe them as a mitigation.
- Ang's run-1 column shift passed `SOURCE QUOTE CHECK`. Only run-2's change scores tripped it. Silent wrong answers reproduce on demand.
- The Lami `MANUAL OVERRIDE` hides raw drift (13.79 vs 13.68 mean, 4.22 vs 4.61 SD). "Stable" for Lami means "overridden".
- The tripwire fires non-deterministically (zsy234 #64 warning on 1 of 3 runs) because the quote varies while the number holds.

Raw JSON: `output/nondet/nondet_baseline_20260829_111509.json`, `output/nondet/nondet_t0seed42_20260829_111835.json`. Move to `Readme/evidence/` or similar before cleanup.

## What changed (data_extractor.py, +~230/−~20)

- `DataExtractor(n_agreement=None)` → env `SR_EXTRACT_N_AGREEMENT`, default **3**. `1` disables.
- `_extract_vision_with_agreement()` calls the vision API N times per page-image set, coerces each, drops unusable runs, votes via `_vote_runs()`.
- Voted fields: `mean/sd/n × intervention/control` (float/int-coerced) and `intervention_group`/`control_group` (`_normalize_label`-coerced). Source quotes are **not** voted — the quote is carried from a run whose mean+SD match the chosen values for that arm, so `SOURCE QUOTE CHECK` still tests a number against its own quote.
- Result keys, always written on the vision path:
  - `nondet_flag`: `[]` = all N unanimous on every voted field. Else entries `field:majority` (≥2 of 3 agreed, majority used) or `field:no_majority` (all differed; run-1 value kept and flagged), plus `usable_runs:k/N` if any run was unusable. Text fallback writes `["single_run"]` (not checked).
  - `table_shift` is appended when all four mean/SD fields disagree, or when one run's (mean, SD) for an arm equals the chosen pair of the other arm — the runs read different table cells, not different digits. 3-of-4 jitter alone does not tag. **Treat like `no_majority`.**
  - `nondet_detail`: `{field: {values:[per run], chosen, kind}}` for the reviewer.
  - `nondet_runs`, `nondet_usable_runs`.
- `[AGREEMENT]` log lines: info for the summary, warning per non-unanimous field with all values.
- Cost: 3× Stage-4 vision calls (~+20 s/paper at observed ~9 s/call). Group-label follow-up is still a single call.

Tests: `tests/test_extractor_sampling.py`, now 21 (7 sampling + 14 agreement). `test_agreement_no_majority_flags_and_keeps_first` pins the S26 Ang signature. Test count for README: 526 + 21 = **547 passed** (verify with `--collect-only`).

## Acceptance run (`--runs 2 --agreement 3`, 2026-08-29 11:32)

- Ang: `nondet_flag` non-empty in both runs (all four mean/SD `majority`, → `table_shift` after the follow-up patch). Across all 12 Ang calls today the two competing readings were drawn 5 and 6 times — a true coin flip. The chosen reading is **not verified**; a reviewer must read Table 2 of Ang 2010 and record which reading is right in `study_overrides` or the guide.
- Jensen, 1-s2.0, Lami, zsy234: `[]` in both runs. Quotes still vary (expected, not voted); zsy234's #64 warning fired on 1 of 2 runs (expected, documented above).
- `outcome_selected` wording varied on Ang ("FIQ pain rating" vs "FIQ pain score"); not voted, cosmetic.
- Raw JSON: `output/nondet/nondet_agree3_20260829_113202.json`.

## Still to do to fully surface the flag (needs `SOURCE_CODE/pipelines/sr/main.py` + the CSV writer)

1. **Audit CSV**: add `nondet_flag` (join list with `|`) and `nondet_runs` columns. Never drop the column when empty — an empty cell must mean "checked, unanimous".
2. **Stage-4 summary** in `_log_stage4_summary`: add a `[AGREEMENT]` line following the #66 denominator pattern — `k of n_extracted studies unanimous across N runs; m flagged (list)`. A `single_run`-only corpus prints `not checked (N=1)`, not `0 flagged`.
3. **`--n-agreement` CLI flag** on the SR sub-command, mapped to `DataExtractor(n_agreement=...)`, help text stating the default and the cost. (Lesson: the help text is a claim.)
4. **REVIEWER_GUIDE**: replace "run 3x and diff" with "read `nondet_flag`; `no_majority` or `table_shift` = mandatory source check; lone `majority` entries = recommended check". Note Lami's override masks drift.
5. Re-run `nondet_probe.py --runs 2 --agreement 3` on the corpus once wired, and record whether Ang gets flagged in both runs. That is the acceptance test for closing #11 in `RESOLVED_ISSUES.md`.

## What #11 becomes

The underlying non-determinism is a property of the model and is not fixable client-side. After steps 1–5 the issue is **closed** as "machine-flagged": non-determinism can no longer produce a clean-looking row silently. Reopen only if a flagged-clean row is later found to carry a wrong number, which would mean the vote agreed on the same wrong value three times (the harness cannot detect that; only source quotes can).

Move #11 from Open Issues to `RESOLVED_ISSUES.md` with the wording above; add to Durable Lessons: *"Sampling controls are not a determinism fix on vision models — measure before claiming; `seed` was silently ignored for as long as it was suggested."*
