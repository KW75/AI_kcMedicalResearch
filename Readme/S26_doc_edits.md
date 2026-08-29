# S26 doc edits for closing #11 — copy-paste blocks

Apply these by hand (they touch files I have not seen, so I give the text,
not a patch). Run the session-closing checklist afterwards.

---

## 1. `Readme/RESOLVED_ISSUES.md` — add

### #11 — Extraction non-determinism (Ang, Jensen, Lami) — RESOLVED S26 (machine-flagged)

**What it was.** qwen-vl-plus returns different numbers for the same page
images across runs. Mitigation for 20+ sessions was a manual
run-3x-and-diff reviewer step.

**What S26 measured** (`Readme/evidence/s26_issue11/`, 5 corpus PDFs,
3 runs each): `seed` is ignored and `temperature=0` is not deterministic
— source quotes differed run-to-run on 4/5 papers at t=0/seed=42, same
as at the old t=0.1. Ang returned three different tables in three runs;
one (a column shift) passed SOURCE QUOTE CHECK. Sampling controls
therefore cannot fix this and are kept only so vision and text paths
share one setting.

**What closed it.** Every vision extraction now runs N=3
(`SR_EXTRACT_N_AGREEMENT`, `--n-agreement`), majority-votes mean/sd/n per
arm and both group labels, and writes `nondet_flag` on every row:
`unanimous`, `field:majority`, `field:no_majority`, `table_shift` (runs
read different table cells), `single_run` (N=1, not checked),
`not_checked` (error/Anthropic path). Source quote is carried from a run
whose numbers match the chosen values so the quote tripwire stays bound
to its number. Stage-4 prints `[AGREEMENT] k of n voted studies ...` with
the voted-only denominator. Acceptance run flagged Ang 2/2 and passed the
four stable papers.

**What it is not.** The model is still non-deterministic. Three runs can
agree on the same wrong cell; only source quotes catch that. Ang's true
reading (32.5/15.0 vs 37.6/10.0, or 37.6/10.0 vs 45.3/24.5) was NOT
decided by S26 — see Open Issue #67.

**Reopen if** a row with `nondet_flag=unanimous` is found carrying a
wrong number. That is the failure mode the vote cannot see.

---

## 2. `README.md` Known Issues + `Readme/HANDOFF.md` Open Issues — replace #11 row

Remove the #11 row. Add:

| 67 | Ang 2010 reading unverified: N=3 vote draws either of two table readings (~50/50); `table_shift` flags it but the correct cells must be confirmed by a human against Table 2 and recorded in `study_overrides` | High | One reviewer, one PDF, ten minutes. Blocks trusting any pooled estimate that includes Ang. |

(Keep both tables identical — checklist item 3.)

---

## 3. `REVIEWER_GUIDE.md` — replace the "run 3x and diff" instruction

### Non-determinism flag (`nondet_flag` column, meta_analysis_results.csv)

Each vision-extracted study is drawn N=3 times and voted. Read the cell:

| cell | meaning | action |
|---|---|---|
| `unanimous` | all 3 runs agreed on mean/SD/n per arm and group labels | normal source-quote check |
| `field:majority` (alone, one or two fields) | 2 of 3 agreed; majority used | recommended: open the PDF, confirm the field |
| any `no_majority` | all 3 differed; run-1 value kept | **mandatory** source check |
| `table_shift` | runs read different table cells (all four mean/SD disagree, or one arm's pair equals the other arm's chosen pair) | **mandatory** — a 2-of-3 majority here is a coin flip, not evidence (Ang S26) |
| `single_run` | N=1, nothing voted | treat as pre-S26: run-3x-and-diff manually, or re-run with `--n-agreement 3` |
| `not_checked` | extraction error or Anthropic path | n/a |

`nondet_runs` gives N. The per-run values are in `extracted.csv`
(`nondet_detail.*` columns) and in the `[AGREEMENT]` warning lines.

Limits: agreement measures stability, not correctness. Source quotes
vary between runs even when numbers agree, so a quote-tripwire warning
that appears in one run and not another is expected. Studies with a
`study_overrides` entry (Lami) show `unanimous` after the override even
when the raw extraction drifted — the override log line shows the raw
values.

---

## 4. `Readme/HANDOFF.md`

**Current State table** — Tests: 547 + wiring tests (verify with
`--collect-only`; expect +18: 14 audit_logger cases + 4 stage-4 cases).
SR pipeline row: replace "extraction non-deterministic (#11), verify
every number" with "extraction voted N=3, read `nondet_flag` (#11 closed
S26; #67 open for Ang)".

**Session 26 Summary** — three commits: `b847c55` (extractor + probe +
evidence), the wiring commit, the docs commit. Cheap branch of #11
(temp/seed) measured and rejected with data; N=3 agreement implemented
and accepted on corpus; #11 closed as machine-flagged; #67 opened.

**Durable Lessons — add:**

- **Measure a mitigation before carrying it.** "Try temperature=0/seed"
  sat in the handoff for three sessions as the cheap fix for #11. Thirty
  calls showed the seed was ignored and t=0 changed nothing. The vision
  call had also been at 0.1 the whole time — a fact that would have been
  found by grepping the call site (checklist item 4) in S24.

- **A majority is not evidence when the alternatives are structured.**
  Ang's two readings are the same numbers with arms shifted; a 2-of-3
  vote picks either depending on the draw. Tag the shape
  (`table_shift`), do not trust the count.

- **Overrides hide drift.** `MANUAL OVERRIDE` makes Lami look unanimous;
  the raw values in the override log line disagreed. When a study is
  overridden, its `nondet_flag` says nothing about the extractor.

**Next Session Priorities** — 1. #67 (human reads Ang Table 2, ten
minutes). 2. Decide whether `nondet_detail` should also vote
`outcome_selected`/`timepoint_selected` (Ang wording varied: "FIQ pain
rating" vs "FIQ pain score"; cosmetic today). 3. Decoder `!`-for-space,
unchanged. 4. Housekeeping, unchanged.

---

## 5. Test count line for README

Run `python -m pytest -m "not live" --collect-only -q | Select-Object -Last 1`
after copying the wiring files; write the number it gives, not the one
above.
