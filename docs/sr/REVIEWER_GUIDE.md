# Reviewer Guide — SR Pipeline

<!-- Section numbers 2.2, 3.1, 3.5, 5 and 6 are cited by console messages,
tests and README.md. Keep them. tests/test_source_quote_doc_sync.py counts
the numbered bold items in 2.2; it must equal the extractor's branch count. -->

**Read this before using any output from this pipeline in a systematic review.**

How the pipeline works and how to run it: `Readme/readme_sr_pipeline.txt`.
This guide covers what the pipeline cannot verify, what a reviewer must check
by hand, and how to decide whether an RCT belongs in the meta-analysis.

Worked example: CBT for fibromyalgia pain, 5 RCTs,
`Readme/readme_sr_pipeline.txt` section 1.

---

## 1. The core warning

**This pipeline produces confident, well-formatted, precisely-quantified output
regardless of whether it has understood the source paper.**

It cannot tell the difference between:

- a between-group treatment effect and a within-subject change over time
- a standard deviation and a standard error
- an outcome that matches your PICO and one that merely shares a keyword
- a number it read correctly and a number it misread

Every effect size it emits has a plausible magnitude, a symmetric confidence
interval and a clean row in the results CSV. **Plausibility is not evidence
of correctness.** The only way to know whether a number is right is for a
human to open the paper and look.

Automated extraction is a **first pass that reduces reading time**, not a
substitute for reading.

---

## 2. Documented failures

Real cases from this repository, kept as regression fixtures. The values
shown come from the runs named; later runs on the same PDF can differ. Read
them as failure *shapes* to watch for, not as fixed outputs.

### 2.1 Loud failure — study drops out

`s10608-017-9875-4.pdf` (Lami 2018)

Vision extraction failed on all four page-selection strategies. Text fallback
succeeded on some runs and not others. On one run it returned
`mean = 7.32, SD = 1.80` where the source table says `7.35 / 2.08`, and
omitted the intervention N, so the study was skipped with
`insufficient mean/SD/N to derive effect size`.

**Why this one is survivable:** the study disappeared from the forest plot,
and the report's not-pooled section now names it. In the worked example Lami
is pooled from reviewer-entered values (§5).

### 2.2 Silent failure — wrong number, no warning

`zsy234.pdf` (McCrae 2019, *SLEEP*), v2.4.12-era run.

The pipeline extracted:

    n_intervention     76        mean_intervention  47.14   sd_intervention  2.36
    n_control          37        mean_control       52.67   sd_control       2.27
                       → Hedges g = -2.356 [-2.853, -1.859]

This passed every stage without a warning and dominated the pooled estimate
(pooled SMD −0.514, I² = 93.9%). The source text reads:

> "There were no significant group by time interactions for the morning and
> evening pain ratings. However, there was a main effect of time for morning
> pain. **Regardless of treatment condition,** participants reported less
> morning pain at posttreatment (M = 47.14, **SE** = 2.36) relative to baseline
> (M = 52.67, **SE** = 2.27, p = .004)."

| # | Error | Consequence |
|---|-------|-------------|
| 1 | SE read as SD | Dispersion understated ~8×; effect size massively inflated |
| 2 | Within-subject time contrast read as between-group contrast | 47.14 is post-treatment for all arms; 52.67 is baseline for all arms. No CBT-vs-control comparison |
| 3 | Group Ns built from arm sums | 76 = CBT-I (39) + CBT-P (37); the trial has three arms |

That extract was excluded at the time. The current pipeline re-reads McCrae
with Tesseract, and the worked example pools McCrae from reviewer-entered
values (Table 3 p9, morning pain VAS, CBT-I and CBT-P combined per Cochrane
Handbook 23.3.4; see reference/sr_cbt_fibromyalgia/study_overrides.yaml).
The case is kept because the failure shape can recur on any paper.

**The source-quote check (partial mitigation).** The extractor emits
`source_quote_intervention` and `source_quote_control` with each numeric
extraction, plus a `source_quote_warning` column that fires on the following
patterns, checked per arm:

1. **Missing quote.** A mean or SD was reported but no source quote was
   provided. A number with no supporting quote cannot be audited.
2. **Number not in own quote.** The extracted mean or SD does not appear in
   its own quote. Matching is character-level with three tolerances: an
   integer fallback (`49.0` matches `49`), a decimal-separator branch (`1.5`
   matches `1,5`), and Unicode minus/dash signs converted to ASCII `-`
   (`−20.2` matches `-20.2`); see `_number_in_text` in `data_extractor.py`.
   Thousands separators can still miss (`1234` vs `1,234`). Treat a mismatch
   as a review prompt, not proof of a wrong number.
   Since Session 39 (F8) the same branch also checks the arm's N: if the
   quote contains whole numbers that could be Ns (not decimals, ranges such
   as 0-100, mean (SD) cells, or numbers after Week/Month), the extracted N
   must be one of them. Example: Ang 2010, quote "Week 6 change 15 13 ...",
   extracted N 17/15 -> "intervention N (17) does not appear in its own
   source quote (quote has 13, 15)".
3. **SE label in an SD quote.** `SE`, `SEM` or `standard error` appears in a
   quote used for an SD field. This catches most of the McCrae signature on
   paths that don't run the separate text-line SD/SE tripwire (§6).
4. **Timepoint confusion in the quote.** One of three mutually exclusive
   checks fires, in this priority order:
   - the quote mentions two or more distinct timepoints (baseline /
     post-treatment / follow-up / week N / T1–T3 / etc.);
   - otherwise, the quote contains within-subject phrasing (`regardless of
     condition`, `main effect of time`, `pre-post`, `baseline to`,
     `compared to baseline`, etc.);
   - otherwise, the quote contains three or more `mean (SD)` cells on one
     row (e.g. `CBT-P 7.58 (1.75) 7.35 (2.08) 7.21 (1.79)`), which almost
     always means three timepoints. The extractor picked one cell; the
     reviewer needs to know a choice was made.
5. **Verbatim mismatch against the source text.** The quote could not be
   found verbatim (after whitespace and case normalisation) in the raw source
   text the extractor worked from. This runs only on paths that have raw text
   (the qwen text-fallback path), not on pure-vision or Anthropic paths. A
   missing branch-5 result means the check could not run, not that it passed.
  Since Session 39 (item 10) this check also runs on image extractions, against the shared paper text (input/sr/paper_text/). Matching ignores case, punctuation and OCR marks; a table row whose numbers appear in the same order nearby also counts as found. A reworded sentence still warns.

On the McCrae extract above the flag fired four times per re-extraction
(branch 3 and the multi-timepoint part of branch 4, on both arms).

**This does not remove the reviewer's responsibility.** The check is a
tripwire on the extractor's own quote, not a semantic check against the
paper. A clean quote from a hallucinated or misattributed passage does not
flag. `source_quote_warning = None` means the patterns did not trip, not
that the value is correct. Item 3.1 remains mandatory.

### 2.3 Other errors seen in the worked example (Session 38)

- **Randomised instead of analysed Ns** (Ang: 17/15 randomised vs 15/13
  analysed at Week 6).
- **Wrong number** (Jensen: readings returned 45.6, which is the mean age).
- **Invented or drifting values** (Lami: AI means varied between runs; the
  table says 7.35 vs 7.40).
- **Wrong arm** (McCrae: control quote taken from the CBT-P row).
- **Right numbers, wrong outcome** (Ang: Table 2 values are the NFR pain
  rating, a laboratory stimulus measure, not pain intensity; excluded from
  the SMD by the reviewer).
- **Wrong dropout numbers in RoB 2** (Lami, McCrae missing-data counts
  differed from the CONSORT flow).

The vote measures stability, not correctness: readings can agree on the
wrong row. On the worked example the AI alone was fully correct for 1 of 4
checked studies (readme_sr_pipeline.txt section 8).

---

## 3. Mandatory checks before reporting any result

None is optional if the output will be read by anyone else.

### 3.1 Per-study source verification

For **every** included study, open the PDF and confirm:

- [ ] **Both groups exist.** The two means come from two different arms at the
      same timepoint — not one arm at two timepoints, not a pooled sample.
- [ ] **Dispersion measure.** The header or text says SD, not SE / SEM / CI /
      IQR. If SE: convert with `SD = SE × √n` and record the conversion.
- [ ] **The Ns are the analysed Ns** for that timepoint — not baseline,
      randomised, or the sum of several arms.
- [ ] **The outcome matches the PICO.** Same construct, same instrument, same
      timepoint. A laboratory pain threshold is not pain intensity.
- [ ] **Final values vs change scores.** Note which one the study reports;
      do not mix them in one SMD (§4.3).
- [ ] **The direction is right.** Lower = better, or higher = better? A sign
      error silently reverses a study's contribution.
- [ ] **The paper's own conclusion is consistent** with the extracted effect.
      If the abstract says "no significant difference" and your g is −2.4,
      stop.

### 3.2 Cross-study sanity checks

- [ ] **Any |g| > 1.5 from a behavioural/psychotherapy trial is suspect.**
      Verify against source before accepting.
- [ ] **If I² > 75%, identify which study drives it.** Remove it and re-run.
      If the conclusion flips, that study needs verification first.
- [ ] **Any study whose CI excludes every other study's point estimate**
      needs source verification regardless of I².
- [ ] **Read `nondet_flag` for every study** (§3.5).
- [ ] **Read the not-pooled section** of the report: every study there needs
      a decision (enter checked values, or record an exclusion reason).

### 3.3 Provenance review

- End of Stage 3: the **DATA PROVENANCE SUMMARY** lists `MANUAL OVERRIDES`
  (reviewer-entered values) and `metadata auto-derived from the PDF (VERIFY)`
  (author/year guessed).
- End of Stage 4: the **[OUTCOME/TIMEPOINT]** block names the outcome and
  timepoint each study's numbers came from. Two runs that pick different
  outcomes or timepoints give different effect sizes.
- The report's "Reviewer-entered data" and not-pooled sections show the same
  information for readers.

All of these must be described in the review's data-collection methods.

### 3.4 Correlating audit files via `run_id`

Every run stamps a `run_id` (`YYYYMMDD_HHMMSS`) on every row of every audit
file:

    screening_audit.csv          run_id, filename, decision, reason, error
    extracted_data.csv           run_id, filename, source_quote_warning, ...
    rob2_audit.csv               run_id, filename, domain_1..5, overall
    meta_analysis_results.csv    run_id, study, hedges_g, ...

Filter each file on the same `run_id` and join on `filename`.

**Do not compare rows across `run_id` values.** Extraction is
non-deterministic (§6); a study's extraction from run A cannot be paired with
its RoB judgement from run B.

### 3.5 Reading `nondet_flag`

Each vision-extracted study is read N=3 times (`--n-agreement`, default 3) and
the numeric fields (mean, SD, N per arm) and both group labels are
majority-voted. The result is in `meta_analysis_results.csv` as `nondet_flag`
and `nondet_runs`; per-run values are in `extracted_data.csv`
(`nondet_detail.*`) and in the Stage 4 `[AGREEMENT]` lines.

| cell | meaning | action |
|---|---|---|
| `unanimous` | all runs agreed on every voted field (also true if all were empty) | normal item-3.1 check |
| `field:majority` | 2 of 3 agreed; the majority value is used | recommended: confirm that field in the PDF |
| any `field:no_majority` | all runs differed | **not pooled** until the reviewer enters the field (§5) |
| `table_shift` | runs read neighbouring cells (all four mean/SD fields disagree, or one arm's pair equals the other arm's). A 2-of-3 majority here is a coin flip | **not pooled** until the reviewer enters all four means/SDs |
| `single_run` | `--n-agreement 1`; nothing voted | re-run with the default |
| `not_checked` | extraction error, or Anthropic path | n/a |

Example of `table_shift`: Karlsson, two readings took Pain severity
3.88 (1.05) vs 3.67 (0.75), one took the next row (Interference).

The vote does not check correctness: three runs can agree on the same wrong
cell. Source quotes are not voted, so a `source_quote_warning` in one run and
not the next is expected. A study with an override shows `unanimous` after
the override even if the raw readings drifted; the `MANUAL OVERRIDE` log line
shows the raw values.

### 3.6 RoB 2 checks

- Check Domains 1–3 and 5 by hand: judgements outside Domain 4 vary between
  runs (randomisation, deviations, missing data).
- Check missing-data counts against the CONSORT flow diagram.
- Overall is the program's rule (readme_sr_pipeline.txt section 5), not the
  model's; `overall_model` shows where they differ.
- RoB 2 reads the paper text, not `study_overrides.yaml`; it is unaffected by
  reviewer-entered values.

---

## 4. Include / exclude decisions at extraction

Screening decides topic relevance. This section covers the second gate:
whether a topically eligible RCT yields a usable effect estimate.

### 4.1 Include

Include a trial in the meta-analysis when **all** hold:

1. Randomised controlled design with a comparator arm matching the PICO.
2. The review outcome is reported **by group** at the review timepoint.
3. Mean and SD (or convertible SE/CI) are available for **both** arms.
4. Analysed N per arm is reported or derivable for that timepoint.
5. The comparison is between-group, not within-group.

**Which comparator matches the PICO.** The launcher default pools usual
care, attention placebo and waiting list into one result. If the doctor
typed `Exclude_WaitList`, the PICO comparator is "Usual care or attention
placebo": a waiting-list-only trial then fails item 1. Check that the
screener did not let one through, and record "No eligible comparator arm".
A trial whose only control is an active treatment (e.g. exercise, drugs)
fails item 1 under either choice; that comparison needs a separate run.

### 4.2 Exclude — and the reason to record

| Situation | Reason to record |
|---|---|
| Outcome reported only pooled across arms | No between-group effect estimate for the review outcome |
| Only p-values / F / χ² reported, no means or SDs | Insufficient data to compute effect size |
| Outcome measured at a different timepoint | Outcome timepoint does not match review protocol |
| Different construct or instrument | Outcome does not match review protocol |
| Only within-subject change reported | No between-group contrast available |
| Multi-arm trial with no PICO-matching comparator | No eligible comparator arm |
| Only change scores while the other studies give final values | Change and final values not combined in the SMD |

Record the reason **with a page reference**, not just "excluded". To keep a
study in the review but out of the meta-analysis, use `exclude_from_meta`
(§5); the report then lists it as decided by the Reviewer.

### 4.3 Judgement calls to make explicitly

**Multi-arm trials.** Decide in advance which arm is the intervention and
which the comparator. Do not let the extractor choose, and do not sum arms.
If two arms are both eligible, pick one *a priori* or split the comparator N
(Cochrane Handbook 23.3.4).

**Multiple timepoints.** The protocol timepoint wins. Follow-up data when the
protocol says post-intervention is an error, not an alternative.

**Change-from-baseline vs final values.** Do not mix them in one SMD
(Cochrane Handbook 10.5.2). Use final values for all studies, or analyse
differently (MD, sensitivity analysis) with a stated rationale. In the worked
example Ang reports pain only as Week 6 change and is excluded from the SMD.

**Imputed SDs.** Permitted (Cochrane Handbook 6.5.2) but must be declared,
with a sensitivity analysis without imputed studies.

### 4.4 Reading the `[SCREENING]` accounting block

At the end of Stage 2 the console prints a partition:

    [SCREENING] 120 records processed
      INCLUDE    : 34
      EXCLUDE    : 71
      UNCERTAIN  : 12
      ERROR      :  3

- **INCLUDE / EXCLUDE / UNCERTAIN** are model decisions on PDFs the screener
  could read. UNCERTAIN papers do not proceed; adjudicate them manually.
- **ERROR** rows are PDFs that could not be screened (corrupt file, API
  failure after retries, unreadable text, unhandled exception). **They are
  not exclusion decisions.** Resolve them before drawing the PRISMA flow
  diagram.

`screening_audit.csv` separates them via the `error` column (filled on ERROR
rows, blank on real decisions). The four totals should equal the row count
for the current `run_id`; if not, a worker crashed and the run is incomplete.

---

## 5. Using `study_overrides.yaml`

When to add an entry, the field list and the format:
`Readme/readme_sr_pipeline.txt` section 7. Full example:
`reference/sr_cbt_fibromyalgia/study_overrides.yaml`. A short example:

    "s10608-017-9875-4.pdf":
      first_author: Lami
      year: 2018
      n_intervention: 28
      n_control: 36
      mean_intervention: 7.35
      sd_intervention: 2.08
      mean_control: 7.40
      sd_control: 1.29
      note: >-
        Table 4, post-intervention CBT-P vs UMC. Ns are post-intervention
        (28/36), not baseline (34/41). Verified from PDF pages 12-13.

**Behaviour:** numeric fields **replace** the AI values; author/year fill in
only if blank. To clear the review gate, enter **all** flagged fields
(`table_shift` needs all four means/SDs). `exclude_from_meta` keeps the study
out of the meta-analysis and the report lists it as decided by the Reviewer.
Extraction still runs in full, so the log shows `field(7.32→7.35)` when an
override corrected a value and `field(confirmed 7.35)` when the AI agreed.
The `confirmed` case is a real cross-check — do not disable extraction to
save time.

**Scope:** overrides affect extraction and meta-analysis only. Screening and
RoB 2 read the paper text independently.

### 5.1 Rules for reviewers

1. **Read the source table first.** Never enter a value inferred from what
   the pooled estimate "should" look like.
2. **Always fill `note`**: table, page, row, timepoint, and that it was
   checked in the PDF. A value without provenance is unusable in a review.
3. **Verify symmetrically.** Checking only studies whose results surprise you
   introduces selection bias.
4. **Decide from the PDF, not the forest plot.** Entering values for a study
   the review gate held back is expected. Changing a value because the pooled
   result looks wrong is not; if that happens, discard the session and
   re-extract from source.
5. **Overrides are data, not code.** Keep them under version control with a
   note explaining the verification.

---

### 5.2 Control type for subgroups (`comparator_type`, Session 39)

The report has a section "Subgroups by control type" (waiting list / usual
care / attention placebo) and an estimate excluding waiting-list trials. The
run log shows the same results as `[SUBGROUP]` lines. Each pooled study's
control type comes from your entry if you made one, otherwise from the
control-group label the model extracted (for example `WLC` or `Wait-list
group` becomes waiting list, and `UC` or `Usual Medical Care (UMC)` becomes
usual care). The log line for each study says which source was used
(`from reviewer` or `from label`).

To set it yourself, add one line inside the study's existing entry in
`study_overrides.yaml`, at the same indentation as `note`:

```yaml
    comparator_type: waiting_list
```

The allowed values are `waiting_list`, `usual_care` and `attention_placebo`.
Any other value (for example the typo `waitlist`) does not silently become a
guess: the study is listed as **unclassified**, with the message "not
recognised", and is left out of every subgroup. The same happens when you made
no entry and the label matches no known pattern. Set `comparator_type` for
every unclassified study before reporting subgroups. A misspelt key (for
example `comparator:`) is ignored, and the run log says "unknown fields".

`comparator_type` changes no numbers. Like `exclude_from_meta`, it is shown in
`override_fields` as a bare name and is not counted as reviewer-entered data.
Only pooled studies are grouped, so a study you excluded with
`exclude_from_meta` is in no subgroup. A group with 1 study is not pooled. A
group with 2 studies is pooled, with a caution note. Subgroup results are
exploratory, so report them as such. This is not the `[SENSITIVITY]` line,
which compares the estimate with and without needs-review studies.

## 6. Known limitations

| Limitation | Impact | Mitigation |
|---|---|---|
| Extraction is non-deterministic | Same PDF gives different values across runs. Measured in Session 26 on the earlier model (qwen-vl-plus ignored `seed`, not deterministic at `temperature=0`); not yet re-measured on qwen3-vl-plus | 3 readings + vote; review gate on `no_majority` / `table_shift` (§3.5); overrides for checked studies |
| Agreement is not correctness | Readings can agree on the wrong row, arm or outcome (§2.3) | Item 3.1 for every included study |
| Broken font codes in PDFs | Text layer garbled | Shared text re-reads those pages with Tesseract (readme_sr_pipeline.txt section 2). Tesseract may add stray dots; without Tesseract `[?]` stay |
| Extraction does not use the shared text | Corrections in `input/sr/paper_text/` do not reach extraction | Use `study_overrides.yaml` |
| Screening sees the first 6000 characters | Eligibility details later in the paper are not seen | Check UNCERTAIN and EXCLUDE decisions with the full paper |
| RoB 2 text depends on finding a Methods heading | Methods + Results (up to 50,000 characters) are sent; if no Methods heading is found, only the first 6000 characters. The retry after an empty answer is also cut to 6000 | Check the `[ROB2 SEND]` line in the console log; if it shows about 6000 characters, check the RoB 2 judgements against the full paper |
| Outcome tables may be embedded images | Values cannot be cross-checked against the text | Manual verification is the only check |
| Author/year heuristics fail on unusual name formats | Wrong study labels | Flagged `pdf_auto (verify)`; override as needed |
| No semantic SD/SE disambiguation | Silent ~8× error in dispersion (§2.2) | Source-quote branch 3; item 3.1 |
| Text-line SD/SE tripwire (`sd_se_warning`) and verbatim branch 5 do not run on the Anthropic path | That path receives structured JSON and never sees raw PDF text. Branch 3 still runs and catches an SE label quoted with the value; the uncovered case is an SE value reported as SD without the label in the quote. `group_timepoint_warning` runs on Anthropic. This is a permanent limitation of that path | Prefer `--provider qwen` where SE/SD confusion is likely (its text fallback adds a second SE check). Item 3.1 on every Anthropic run |
| No semantic within- vs between-group detection | Silent invalid effect size (§2.2) | Source-quote branch 4; item 3.1 |
| Quote check is a tripwire, not a verifier | Hallucinated or misattributed quotes do not flag | `source_quote_warning = None` is not "correct" |
| Quote matching is character-level | Thousands separators can miss (`1234` vs `1,234`) | Treat a mismatch as a prompt; check the digits in the table |
| Retry, OCR and quote-check behaviour tested on the qwen path only | Anthropic path may behave differently | Reviewer verification on any Anthropic run |
| RoB 2 judgements vary outside Domain 4 | Different runs give different domain judgements | §3.6 |
| RoB 2 runs independently of overrides | RoB may use text of a study whose data was hand-entered | Review RoB judgements separately |

---

## 7. Minimum reporting statement

State, in the data-collection methods, something equivalent to:

> Records were screened and data extracted using an automated LLM-assisted
> pipeline ([provider], [model version]), with each paper read three times and
> discordant readings withheld from pooling until verified. All extracted
> outcome data were verified against the source publications by [N]
> reviewer(s). Where automated extraction was incorrect or incomplete, values
> were entered manually from the source tables with their provenance; [N] of
> [N] included studies required manual correction. Studies included in the
> review but not in the meta-analysis are listed with reasons in
> [Table/Supplement X].
>
> Risk of bias was assessed with RoB 2 for the review outcome. For
> participant-reported outcomes in trials where participants knew their
> allocation, Domain 4 was judged High. The overall judgement followed the
> RoB 2 algorithm (any High -> High; all Low -> Low; otherwise Some concerns).

Do not describe the extraction as automated without stating the verification
step. Do not report a pooled estimate from unverified extraction.

---

## 8. One-line summary

**The pipeline finds candidate numbers. You are responsible for every
number that reaches a forest plot.**
