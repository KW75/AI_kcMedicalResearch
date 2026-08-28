# Reviewer Guide — SR Extraction Pipeline

**Read this before using any output from this pipeline in a systematic review.**

This document explains what the pipeline can and cannot verify, what a reviewer
must check by hand, and how to decide whether an RCT belongs in the
meta-analysis.

---

## 1. The core warning

**This pipeline produces confident, well-formatted, precisely-quantified output
regardless of whether it has understood the source paper.**

It cannot tell the difference between:

- a between-group treatment effect and a within-subject change over time
- a standard deviation and a standard error
- an outcome that matches your PICO and one that merely shares a keyword
- a number it read correctly and a number it misread

Every effect size it emits will have a plausible magnitude, a symmetric
confidence interval, and a clean row in the results CSV. **Plausibility is not
evidence of correctness.** The only way to know whether a number is right is
for a human to open the paper and look.

Automated extraction here is a **first pass that reduces reading time.** It is
not a substitute for reading.

---

## 2. Two documented failure modes

These are real cases from this repository, kept as regression fixtures.

### 2.1 Loud failure — study drops out

`s10608-017-9875-4.pdf` (Lami 2018)

Vision extraction failed on all four page-selection strategies. Text fallback
succeeded on some runs and not others. On one run it returned
`mean = 7.32, SD = 1.80` where the source table says `7.35 / 2.08`, and
omitted the intervention N entirely, so the study was skipped with
`insufficient mean/SD/N to derive effect size`.

**Why this one is survivable:** the study disappeared from the forest plot. A
reviewer counting studies notices.

### 2.2 Silent failure — wrong number, no warning

`zsy234.pdf` (McCrae 2019, *SLEEP*)

The pipeline extracted:

    n_intervention     76        mean_intervention  47.14   sd_intervention  2.36
    n_control          37        mean_control       52.67   sd_control       2.27
                       → Hedges g = -2.356 [-2.853, -1.859]

This passed every stage without a warning and dominated the pooled estimate
(pooled SMD −0.514, I² = 93.9%).

The source text reads:

> "There were no significant group by time interactions for the morning and
> evening pain ratings. However, there was a main effect of time for morning
> pain. **Regardless of treatment condition,** participants reported less
> morning pain at posttreatment (M = 47.14, **SE** = 2.36) relative to baseline
> (M = 52.67, **SE** = 2.27, p = .004)."

Three independent errors:

| # | Error | Consequence |
|---|-------|-------------|
| 1 | SE read as SD | Dispersion understated ~8×; effect size massively inflated |
| 2 | Within-subject time contrast read as between-group contrast | 47.14 is *post-treatment for all arms*; 52.67 is *baseline for all arms*. There is no CBT-vs-control comparison in these numbers. |
| 3 | Group Ns fabricated from arm sums | 76 = CBT-I (39) + CBT-P (37); the trial has three arms, not two |

The paper reports **no** significant effect of treatment on pain. The
pipeline reported g = −2.36, one of the largest effects in the psychotherapy
literature. **Nothing in the pipeline flagged this** in the run that produced
the extract above. It was found only by decoding the PDF text layer and
reading the results section.

**What v2.4.12 changes (partial mitigation).** The extractor now emits
`source_quote_intervention` and `source_quote_control` fields alongside each
numeric extraction, plus a `source_quote_warning` column that fires on four
patterns:

1. The label `SE` or `SEM` appears in a quote used for an SD field.
2. The quote mentions two or more distinct timepoints, or contains
   within-subject phrases (`regardless of condition`, `main effect of time`,
   `pre-post`, `baseline to`, etc.).
3. The extracted number does not appear in its own quote, under a
   character-level string match. The match is not fully format-tolerant —
   an integer extracted as `49.0` will not match a quote reading `49 ± 19`,
   even though the underlying value is the same (see §6). Treat this
   specific shape as a review prompt, not evidence of a wrong number.
4. The quote is missing entirely.

On `zsy234.pdf` the flag now fires four times per re-extraction — SE-as-SD
on both arms plus multi-timepoint on both arms — making that specific
failure loud rather than silent.

**This does not remove the reviewer's responsibility.** The check is a
tripwire on the extractor's own quote, not a semantic verification against
the paper. If the extractor produces a clean quote from a hallucinated
passage, or misattributes a real quote from a different section, the flag
will not fire. `source_quote_warning = None` is not evidence of correctness;
it is evidence that the four specific patterns above did not trip. Item 3.1
remains mandatory.

**Disposition for this corpus (v2.4.12, run 20260826_113816).** All four
`source_quote_warning` flags fired on `zsy234.pdf` as documented above, plus
`plausibility_flag` on |g|=2.36. The extracted values were then manually
confirmed against the PDF as within-subject baseline vs posttreatment on a
single arm, not intervention vs control. Because the paper itself reports
no significant group-by-time interaction on the pain outcomes, there is no
usable between-group effect estimate to enter — Option B (reviewer override
with corrected between-group values) is not available for this paper.

`zsy234.pdf` is therefore **excluded at the data-extraction stage** with the
PRISMA reason:

> Outcome data not reported in a usable format for between-group comparison
> (McCrae 2019 reports within-subject pre/post values only; authors report
> no significant group-by-time interaction on pain outcomes).

This follows §4.2's row "Only within-subject change reported → No
between-group contrast available." The pipeline flags are recorded in the
audit trail; the exclusion is a reviewer decision documented here.

---

## 3. Mandatory checks before reporting any result

Do all of these. None is optional if the output will be read by anyone else.

### 3.1 Per-study source verification

For **every** included study, open the PDF and confirm:

- [ ] **Both groups exist.** The two means come from two different arms at the
      same timepoint — not one arm at two timepoints, not a pooled sample.
- [ ] **Dispersion measure.** The table header or text says SD, not SE / SEM /
      CI / IQR. If SE: convert with `SD = SE × √n` and record the conversion.
- [ ] **The Ns are the analysed Ns** for that timepoint — not baseline Ns, not
      randomised Ns, not the sum of several arms.
- [ ] **The outcome matches the PICO.** Same construct, same instrument, same
      timepoint. "Pain" in a sleep trial's secondary outcomes is not the same
      as "pain intensity at post-intervention" as a primary endpoint.
- [ ] **The direction is right.** Lower = better, or higher = better? A sign
      error silently reverses a study's contribution.
- [ ] **The paper's own conclusion is consistent** with the extracted effect.
      If the abstract says "no significant difference" and your g is −2.4,
      stop.

### 3.2 Cross-study sanity checks

- [ ] **Any |g| > 1.5 from a behavioural/psychotherapy trial is suspect.**
      Verify against source before accepting.
- [ ] **If I² > 75%, identify which study drives it.** Remove it and re-run.
      If the conclusion flips, that study needs verification before anything
      is reported.
- [ ] **Any study whose CI excludes every other study's point estimate**
      warrants source verification regardless of I².
- [ ] **Run the pipeline at least 3 times on the same inputs** and diff
      `meta_analysis_results.csv`. Extraction is non-deterministic; values
      that move between runs are not trustworthy until pinned.

### 3.3 Provenance review

At the end of Stage 3 the log prints a **DATA PROVENANCE SUMMARY**. Read it.

- Studies listed under `MANUAL OVERRIDES` used reviewer-entered values.
- Studies listed under `metadata auto-derived from the PDF (VERIFY)` had
  author or year inferred heuristically and may be wrong.

At the end of Stage 4 the log prints an **[OUTCOME/TIMEPOINT]** block naming
which outcome and which timepoint each study's numbers were drawn from. Two
runs that pick different outcomes or timepoints for the same paper produce
different effect sizes; this block is how a reviewer sees that difference
without opening `extracted_data.csv`.

Both must be described in the review's data-collection methods.

### 3.4 Correlating audit files via `run_id`

Every pipeline invocation stamps a `run_id` (timestamp of the form
`YYYYMMDD_HHMMSS`) on every row of every audit file it writes. To trace a
single study through the pipeline:

    screening_audit.csv          run_id, filename, decision, reason, error
    extracted_data.csv           run_id, filename, source_quote_warning, ...
    rob2_audit.csv               run_id, filename, domain_1..5, overall
    meta_analysis_results.csv    run_id, study, hedges_g, ...

Filter each file on the same `run_id` and join on `filename`. This is the
only reliable way to reconstruct *why* a specific effect estimate looks the
way it does — screening reason, extraction warning, and RoB judgement live
in different files but describe the same PDF read in the same session.

**Do not compare rows across `run_id` values.** Extraction is
non-deterministic (§6); a study's row in `extracted_data.csv` from run A
cannot be paired with its RoB judgement from run B, because the two reads
may disagree on which arms, timepoints, or numbers are present. If you need
to combine information across runs, first re-verify against source.

---

## 4. Include / exclude decisions at extraction

Screening (Stage 2) decides topic relevance. This section covers the
*second* gate: whether a topically-eligible RCT yields a usable effect
estimate.

### 4.1 Include

Include a trial in the meta-analysis when **all** hold:

1. Randomised controlled design with a comparator arm matching the PICO.
2. The review outcome is reported **by group** at the review timepoint.
3. Mean and SD (or convertible SE/CI) are available for **both** arms.
4. Analysed N per arm is reported or derivable for that timepoint.
5. The comparison is between-group, not within-group.

### 4.2 Exclude — and the reason to record

| Situation | PRISMA exclusion reason |
|---|---|
| Outcome reported only pooled across arms | No between-group effect estimate for the review outcome |
| Only p-values / F / χ² reported, no means or SDs | Insufficient data to compute effect size |
| Outcome measured but at a different timepoint | Outcome timepoint does not match review protocol |
| Different construct or instrument | Outcome does not match review protocol |
| Only within-subject change reported | No between-group contrast available |
| Multi-arm trial with no PICO-matching comparator | No eligible comparator arm |

Record the reason **verbatim with a page reference**, not just "excluded".

### 4.3 Judgement calls to make explicitly

**Multi-arm trials.** Decide in advance which arm is "the" intervention and
which is "the" comparator. Do not let the extractor choose, and do not sum
arms to inflate N. If two arms are both eligible, either pick one *a priori*
or split the comparator N per Cochrane Handbook 23.3.4.

**Multiple timepoints.** The protocol timepoint wins. If the extractor
returns follow-up data when the protocol specifies post-intervention, that
is an error, not an alternative.

**Change-from-baseline vs final values.** Do not mix them in one
meta-analysis without a stated rationale.

**Imputed SDs.** Permitted (Cochrane Handbook 6.5.2) but must be declared,
and a sensitivity analysis without imputed studies should be reported.

### 4.4 Reading the `[SCREENING]` accounting block

At the end of Stage 2 the console prints a partition of the screening batch:

    [SCREENING] 120 records processed
      INCLUDE    : 34
      EXCLUDE    : 71
      UNCERTAIN  : 12
      ERROR      :  3

- **INCLUDE / EXCLUDE / UNCERTAIN** are model decisions on PDFs the screener
  could read.
- **ERROR** rows are PDFs the screener could not read at all — corrupt file,
  API 5xx after retries exhausted, OCR budget saturated before any usable
  text was recovered, or an unhandled exception. **These are not exclusion
  decisions.** They are pipeline failures.

For PRISMA reporting, ERROR rows must be resolved manually before the flow
diagram is drawn. Counting them as EXCLUDE inflates your "excluded at
screening" number with studies that were never actually screened, and hides
records that a human should decide on.

The audit CSV distinguishes them via the `error` column: populated on ERROR
rows, blank on real decisions. If the console line was missed or the run was
resumed across sessions, filter `screening_audit.csv` on that column to
recover the true partition:

    records with error != ""    → pipeline failures, resolve manually
    records with error == ""    → real INCLUDE / EXCLUDE / UNCERTAIN decisions

The four totals in the console line should equal the row count of
`screening_audit.csv` filtered to the current `run_id`. If they do not, a
worker crashed silently and the run is incomplete.

---

## 5. Using `study_overrides.yaml`

`input/sr/study_overrides.yaml` records reviewer-verified values keyed by
filename.

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

**Behaviour:** metadata fields fill only when extraction left them blank;
numeric fields **replace** whatever extraction produced. Extraction still
runs in full, so the log reports `field(7.32→7.35)` when an override
corrected a value and `field(confirmed 7.35)` when extraction independently
agreed. The `confirmed` case is a genuine cross-check — do not disable
extraction to save time, or you lose it.

**Scope:** overrides affect extraction and meta-analysis only. Screening
and RoB 2.0 assessment re-read the PDF independently and are unaffected.

### 5.1 Rules for reviewers

1. **Read the source table first.** Never enter a value inferred from what
   the pooled estimate "should" look like.
2. **Always fill `note`** with table number, page, and date. A value without
   provenance is unusable in a published review.
3. **Verify symmetrically.** If you verify studies whose results surprise
   you but not those that match expectations, you have introduced selection
   bias through the back door.
4. **Never edit this file after looking at the forest plot.** If you find
   yourself doing so, discard the session and re-extract from source.
5. **Overrides are data, not code.** They belong in version control with a
   commit message explaining the verification.

---

## 6. Known limitations

| Limitation | Impact | Mitigation |
|---|---|---|
| Extraction is non-deterministic | Same PDF yields different values across runs | Run 3× and diff; pin verified studies via overrides |
| Several corpus PDFs have broken font CMaps | Text layer appears garbled; pipeline falls back to OCR unnecessarily, losing fidelity | Decode with a fixed character offset before OCR fallback |
| Outcome tables may be embedded images | Values cannot be cross-checked against the text layer | Manual verification is the only check |
| Author/year heuristics fail on unusual name formats | Wrong study labels | Flagged as `pdf_auto (verify)`; override as needed |
| No semantic SD/SE disambiguation | Silent 8× error in dispersion (see §2.2) | v2.4.12 `source_quote_warning` flags SE/SEM label in an SD quote; manual check (item 3.1) still required |
| SD/SE label check does not run on the Anthropic provider path | An Anthropic-path extraction that misreads SE as SD will not be flagged by the SE-label tripwire, though the source-quote and group/timepoint checks still run | Reviewer verification (item 3.1) is the only safeguard on Anthropic-path runs; prefer qwen for corpora where SE/SD confusion is likely |
| No semantic within- vs between-group detection | Silent invalid effect size (see §2.2) | v2.4.12 `source_quote_warning` flags multi-timepoint and within-subject phrasing in a quote; manual check (item 3.1) still required |
| Extractor quote check is a tripwire, not a verifier | A clean quote from a hallucinated or misattributed passage will not flag; only four specific patterns are detected | `source_quote_warning = None` means "four patterns did not trip", not "correct". Item 3.1 remains mandatory |
| Quote-check number matching is character-level, not numeric | An integer extracted as `49.0` does not match a quote reading `49 ± 19`; the warning fires even though the underlying value is the same | Treat this specific shape (extracted value ends `.0`, quote has the same digits without the decimal) as a review prompt, not evidence of a wrong number. Verify the digits match in the source table and move on |
| Retry, OCR-budget, and quote-check behaviour verified on the `qwen` provider path only | Anthropic provider path may fail or silently succeed differently under the same conditions | Reviewer verification required on any run whose provider is Anthropic; do not assume qwen-path test coverage transfers |
| RoB 2.0 runs independently of overrides | RoB assessment may use OCR text of a study whose data was hand-entered | Review RoB judgements separately |

---

## 7. Minimum reporting statement

Any review using this pipeline should state, in the data-collection methods,
something equivalent to:

> Records were screened and data extracted using an automated LLM-assisted
> pipeline (provider and model version), followed by manual verification of
> all extracted outcome data against the source publications by [N]
> reviewer(s). Where automated extraction was incorrect or incomplete,
> values were entered manually from the source tables and recorded with
> their provenance; [N] of [N] included studies required manual correction.
> Studies excluded at the data-extraction stage, with reasons, are listed
> in [Supplementary Table X].

Do not describe the extraction as automated without stating the
verification step. Do not report a pooled estimate from unverified
extraction.

---

## 8. One-line summary

**The pipeline finds candidate numbers. You are responsible for every
number that reaches a forest plot.**
