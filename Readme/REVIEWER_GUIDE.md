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
evidence of correctness.** The only way to know whether a number is right is for
a human to open the paper and look.

Automated extraction here is a **first pass that reduces reading time**. It is
not a substitute for reading.

---

## 2. Two documented failure modes

These are real cases from this repository, kept as regression fixtures.

### 2.1 Loud failure — study drops out

`s10608-017-9875-4.pdf` (Lami 2018)

Vision extraction failed on all four page-selection strategies. Text fallback
succeeded on some runs and not others. On one run it returned
`mean = 7.32, SD = 1.80` where the source table says `7.35 / 2.08`, and omitted
the intervention N entirely, so the study was skipped with
`insufficient mean/SD/N to derive effect size`.

**Why this one is survivable:** the study disappeared from the forest plot. A
reviewer counting studies notices.

### 2.2 Silent failure — wrong number, no warning

`zsy234.pdf` (McCrae 2019, *SLEEP*)

The pipeline extracted:

```
n_intervention     76        mean_intervention  47.14   sd_intervention  2.36
n_control          37        mean_control       52.67   sd_control       2.27
                   -> Hedges g = -2.356 [-2.853, -1.859]
```

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

The paper reports **no** significant effect of treatment on pain. The pipeline
reported g = −2.36, one of the largest effects in the psychotherapy literature.

**Nothing in the pipeline flagged this.** It was found only by decoding the PDF
text layer and reading the results section.

---

## 3. Mandatory checks before reporting any result

Do all of these. None is optional if the output will be read by anyone else.

### 3.1 Per-study source verification

For **every** included study, open the PDF and confirm:

- [ ] **Both groups exist.** The two means come from two different arms at the
      same timepoint — not one arm at two timepoints, not a pooled sample.
- [ ] **Dispersion measure.** The table header or text says SD, not SE / SEM /
      CI / IQR. If SE: convert with `SD = SE x sqrt(n)` and record the conversion.
- [ ] **The Ns are the analysed Ns** for that timepoint — not baseline Ns, not
      randomised Ns, not the sum of several arms.
- [ ] **The outcome matches the PICO.** Same construct, same instrument, same
      timepoint. "Pain" in a sleep trial's secondary outcomes is not the same as
      "pain intensity at post-intervention" as a primary endpoint.
- [ ] **The direction is right.** Lower = better, or higher = better? A sign
      error silently reverses a study's contribution.
- [ ] **The paper's own conclusion is consistent** with the extracted effect. If
      the abstract says "no significant difference" and your g is −2.4, stop.

### 3.2 Cross-study sanity checks

- [ ] **Any |g| > 1.5 from a behavioural/psychotherapy trial is suspect.**
      Verify against source before accepting.
- [ ] **If I² > 75%, identify which study drives it.** Remove it and re-run. If
      the conclusion flips, that study needs verification before anything is
      reported.
- [ ] **Any study whose CI excludes every other study's point estimate**
      warrants source verification regardless of I².
- [ ] **Run the pipeline at least 3 times on the same inputs** and diff
      `meta_analysis_results.csv`. Extraction is non-deterministic; values that
      move between runs are not trustworthy until pinned.

### 3.3 Provenance review

At the end of Stage 3 the log prints a **DATA PROVENANCE SUMMARY**. Read it.

- Studies listed under `MANUAL OVERRIDES` used reviewer-entered values.
- Studies listed under `metadata auto-derived from the PDF (VERIFY)` had author
  or year inferred heuristically and may be wrong.

Both must be described in the review's data-collection methods.

---

## 4. Include / exclude decisions at extraction

Screening (Stage 2) decides topic relevance. This section covers the *second*
gate: whether a topically-eligible RCT yields a usable effect estimate.

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
which is "the" comparator. Do not let the extractor choose, and do not sum arms
to inflate N. If two arms are both eligible, either pick one *a priori* or split
the comparator N per Cochrane Handbook 23.3.4.

**Multiple timepoints.** The protocol timepoint wins. If the extractor returns
follow-up data when the protocol specifies post-intervention, that is an error,
not an alternative.

**Change-from-baseline vs final values.** Do not mix them in one meta-analysis
without a stated rationale.

**Imputed SDs.** Permitted (Cochrane Handbook 6.5.2) but must be declared, and
a sensitivity analysis without imputed studies should be reported.

---

## 5. Using `study_overrides.yaml`

`input/sr/study_overrides.yaml` records reviewer-verified values keyed by
filename.

```yaml
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
```

**Behaviour:** metadata fields fill only when extraction left them blank;
numeric fields **replace** whatever extraction produced. Extraction still runs
in full, so the log reports `field(7.32->7.35)` when an override corrected a
value and `field(confirmed 7.35)` when extraction independently agreed. The
`confirmed` case is a genuine cross-check — do not disable extraction to save
time, or you lose it.

**Scope:** overrides affect extraction and meta-analysis only. Screening and
RoB 2.0 assessment re-read the PDF independently and are unaffected.

### 5.1 Rules for reviewers

1. **Read the source table first.** Never enter a value inferred from what the
   pooled estimate "should" look like.
2. **Always fill `note`** with table number, page, and date. A value without
   provenance is unusable in a published review.
3. **Verify symmetrically.** If you verify studies whose results surprise you
   but not those that match expectations, you have introduced selection bias
   through the back door.
4. **Never edit this file after looking at the forest plot.** If you find
   yourself doing so, discard the session and re-extract from source.
5. **Overrides are data, not code.** They belong in version control with a
   commit message explaining the verification.

---

## 6. Known limitations

| Limitation | Impact | Mitigation |
|---|---|---|
| Extraction is non-deterministic | Same PDF yields different values across runs | Run 3x and diff; pin verified studies via overrides |
| Several corpus PDFs have broken font CMaps | Text layer appears garbled; pipeline falls back to OCR unnecessarily, losing fidelity | Decode with a fixed character offset before OCR fallback |
| Outcome tables may be embedded images | Values cannot be cross-checked against the text layer | Manual verification is the only check |
| Author/year heuristics fail on unusual name formats | Wrong study labels | Flagged as `pdf_auto (verify)`; override as needed |
| No SD/SE disambiguation | Silent 8x error in dispersion (see 2.2) | Manual check, item 3.1 |
| No within- vs between-group detection | Silent invalid effect size (see 2.2) | Manual check, item 3.1 |
| RoB 2.0 runs independently of overrides | RoB assessment may use OCR text of a study whose data was hand-entered | Review RoB judgements separately |

---

## 7. Minimum reporting statement

Any review using this pipeline should state, in the data-collection methods,
something equivalent to:

> Records were screened and data extracted using an automated LLM-assisted
> pipeline (provider and model version), followed by manual verification of all
> extracted outcome data against the source publications by [N] reviewer(s).
> Where automated extraction was incorrect or incomplete, values were entered
> manually from the source tables and recorded with their provenance; [N] of [N]
> included studies required manual correction. Studies excluded at the
> data-extraction stage, with reasons, are listed in [Supplementary Table X].

Do not describe the extraction as automated without stating the verification
step. Do not report a pooled estimate from unverified extraction.

---

## 8. One-line summary

**The pipeline finds candidate numbers. You are responsible for every number
that reaches a forest plot.**
