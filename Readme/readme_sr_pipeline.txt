==============================================================================
 AI_kcMedicalResearch - Systematic Review (SR) pipeline
 How it works, and why it was built this way
==============================================================================

This file explains the logic of the SR pipeline: what happens to a paper from
the moment it is uploaded to the final pooled estimate, which method is used
at each step, and why that method was chosen. It is not a user guide (how to
start a run, menus, settings): see the Help page (Readme/flashcard-help.html).
What a reviewer must check by hand is in docs/sr/REVIEWER_GUIDE.md.

Contents
  1. The problem this pipeline solves
  2. Design principles
  3. The pipeline, step by step
       3.1 Protocol first: PICO and eligibility criteria
       3.2 Reading the papers once: the shared paper text
       3.3 Screening (selection decision)
       3.4 Data extraction
       3.5 Automatic checks on every extracted number
       3.6 The reviewer's role: study_overrides.yaml
       3.7 The pooling gate: which studies enter the estimate
       3.8 Effect sizes and meta-analysis
       3.9 Subgroups by control type
       3.10 Risk of bias (RoB 2)
       3.11 Reports and audit trail
  4. How accuracy is measured, and what the numbers show
  5. Compared with asking a general cloud chat to "do a systematic review"
  6. Honest limitations
  Appendix A. Worked example: CBT for fibromyalgia pain, 5 RCTs



------------------------------------------------------------------------------
1. The problem this pipeline solves
------------------------------------------------------------------------------

A language model can read a trial report and give you a mean and a standard
deviation in seconds. The danger is not that it sometimes fails. The danger is
that it fails silently: the wrong number looks exactly like a right one.

Real examples from this project's own test papers (CBT for fibromyalgia):

  - Jensen 2012: the model reported "45.6" as the pain score for both arms.
    45.6 is the participants' mean AGE (page 2). The real pain VAS is in
    Table 3, page 7: 49 (19) vs 59 (26).
  - Lami 2018: a model run quoted "mean = 4.2 (SD = 2.1)" as if copied from
    the paper. That sentence is not in the paper.
  - McCrae 2019: an earlier run took standard errors (2.36, 2.27 on a 0-100
    scale) as standard deviations. That single study gave Hedges g = -2.36
    and dominated the pooled estimate (I2 = 93.9%).

One wrong number like these changes the conclusion of a meta-analysis. So the
pipeline is built around one rule:

    A number enters the pooled estimate only if it is either confirmed by
    independent, repeated machine reading, or checked by a human against the
    PDF and recorded with its page and table. Everything else is shown, but
    kept out, with the reason written down.


------------------------------------------------------------------------------
2. Design principles
------------------------------------------------------------------------------

  P1. Never silent. Every study that is left out, every value a reviewer
      changed, and every warning is written to the log, the CSV files and the
      Word/HTML report. Nothing disappears without a recorded reason
      (PRISMA 2020 item 13a).

  P2. Repeat, then compare. Extraction is run several times on the same
      paper. Agreement is evidence; disagreement is a flag, never averaged
      away.

  P3. Deterministic checks around a non-deterministic model. The model does
      the reading; plain code (no AI) checks the result: does the number
      appear in the quote, does the quote appear in the paper, is an "SE"
      being used as an SD, is the N the N in the quote.

  P4. Rules decided in advance by code, not by the model. For example the
      RoB 2 overall judgement is computed from the five domain judgements by
      a fixed rule; the model's own overall answer is kept only for
      comparison.

  P5. The human is part of the method, and is recorded as such. Reviewer
      corrections are data (a version-controlled YAML file with a source
      note), not edits hidden in a spreadsheet. The report states which
      values were entered by a reviewer, so they can be reported as manually
      extracted.

  P6. Measured, not assumed. A hand-checked "truth" file and a scoring
      script measure how often the pipeline - and the model alone - is
      right on real papers.

  P7. Data stays where you put it unless you say otherwise. Before any cloud
      call, the pipeline lists every external destination and refuses to
      run without explicit confirmation. The SR run uses only the provider
      you chose; there is no hidden fallback to another company.


------------------------------------------------------------------------------
3. The pipeline, step by step
------------------------------------------------------------------------------

  PICO + criteria -> shared paper text -> screening -> extraction (repeated)
  -> automatic checks -> reviewer overrides -> pooling gate -> effect sizes
  -> meta-analysis + subgroups -> forest plots -> RoB 2 -> reports + audit

3.1 Protocol first: PICO and eligibility criteria
  What: before any paper is read, the review question is fixed as PICO
  (Population, Intervention, Comparator, Outcome) plus inclusion and
  exclusion criteria (for example: randomised controlled trial; adults).
  These are saved with the run.
  Why: a systematic review is defined by deciding the rules before seeing
  the results. Fixing them first, and saving them with each run, makes the
  selection reproducible and stops criteria from drifting to fit the data.
  Detail that matters: the comparator wording decides which trials qualify.
  "Placebo or active comparator" would wrongly exclude waiting-list trials
  (three of the five test papers); the wording therefore names waiting list
  explicitly when it is meant.

3.2 Reading the papers once: the shared paper text
  What: each PDF is converted to text once and saved as
  input/sr/paper_text/<paper>.txt. Screening, RoB 2 and the quote check all
  read this same file.
  Why: (a) every stage sees the same text, so their results can be compared;
  (b) a reviewer can open and correct the text; (c) the PDF is not re-read
  differently by each stage.
  Broken PDFs: some journal PDFs have a broken font layer - the visible page
  is fine, but the stored text is garbage (in McCrae 2019 every letter is
  shifted by one: "o]hmqdctbshnmr" = "painreductions"). The pipeline detects
  this and falls back to decoding or OCR of the page images. Characters OCR
  cannot read with confidence are marked [?], so they are never trusted as
  exact.

3.3 Screening (selection decision)
  What: for each paper the model receives the PICO, the criteria, and the
  start of the paper (title, abstract and opening text, up to 6000
  characters). It returns INCLUDE, EXCLUDE or UNCERTAIN, a confidence, a
  yes/no for each PICO element and for "is this an RCT", the exclusion
  reasons, and a written rationale.
  Why the start of the paper: eligibility (population, intervention,
  comparator, randomisation) is stated in the title and abstract - this is
  also how human reviewers screen. In the test set, the word "random"
  appears inside this window for all five papers.
  Why the bias toward INCLUDE: an excluded study is lost for good; a wrongly
  included study is caught later, at extraction and at the pooling gate.
  When in doubt, the screener includes.
  No silent drops: a paper that failed for a technical reason (API error) or
  was left UNCERTAIN is not treated as excluded. It is counted in a separate
  [SCREENING] block, and the pooled estimate carries a reminder that papers
  are missing for non-scientific reasons.
  Stability measured: 4 independent runs, 5 papers: 20 of 20 decisions
  identical (all INCLUDE).

3.4 Data extraction
  What: the model reads page images of the paper (not only the text layer)
  and returns, per arm: N, mean, SD, group label, outcome, timepoint, and a
  verbatim source quote for each arm's numbers.
  Why images: tables are where the numbers are, and text layers often
  scramble tables or are broken (3.2). A vision model sees the table as
  printed.
  Why repeated runs: the same model, asked the same question, can give
  different numbers. Extraction is therefore run several times (default 3)
  and each field is decided by majority. The disagreement itself is
  recorded as a flag:
    no_majority  - the runs gave different values for a field
    table_shift  - a run read the neighbouring row of a table (for example
                   "Interference" instead of "Pain severity")
    single_run   - only one usable answer, so no agreement was possible
  Why a verbatim quote: it binds each number to a place in the paper, so
  both code (3.5) and a reviewer can check where it came from.

3.5 Automatic checks on every extracted number
  Plain code, no AI. Each check produces a written warning, shown in the log
  and the report.
    1. Missing quote - a number without its source quote.
    2. Number not in its own quote - the mean, SD or N does not appear in the
       quote given for it. (Ang 2010: N 17/15 extracted, quote says 15/13.)
    3. SE label in an SD quote - the quote says SE / SEM / standard error
       but the value was stored as an SD (the McCrae error in section 1).
    4. Timepoint confusion - the quote describes another timepoint, a
       within-group change, or a table row with several mean(SD) cells.
    5. Verbatim mismatch - the quote is not in the paper text. Matching
       tolerates case, punctuation, spacing and OCR marks; a table row
       counts as found if its numbers appear in the same order nearby. A
       reworded sentence still warns. (Catches the invented Lami quotes.)
  Plus: possible SE-reported-as-SD detection from the size of the SD
  relative to N, and missing Ns derived from the text where possible.
  Why: these errors are the most common ways a correct-looking extraction
  is wrong, and all of them can be detected without trusting the model.

3.6 The reviewer's role: study_overrides.yaml
  What: when a value is flagged or wrong, the reviewer reads the PDF and
  enters the correct value in study_overrides.yaml, with a note giving the
  table, page, row and timepoint. Example (Jensen 2012):
    Table 3 p7, weekly pain VAS 0-100, posttreatment: CBT 49 (19) vs
    waiting list 59 (26); N = completed treatment 19/15 (Fig 1 p3).
  The pipeline records each entry as changed (AI value -> reviewer value),
  confirmed (reviewer agreed with the AI), or a decision without a value
  (for example "leave out of the meta-analysis" with the reason).
  Why: the reviewer's work becomes part of the run's data, is version
  controlled, and is reproducible. The reports list reviewer-entered values
  separately, so a published review can state honestly which numbers were
  extracted manually. Reviewer decisions follow the Cochrane Handbook, for
  example combining arms of a multi-arm trial (23.3.4: McCrae CBT-I + CBT-P
  vs waiting list) and not mixing change scores with final values (10.5.2:
  Ang 2010, reported narratively).

3.7 The pooling gate: which studies enter the estimate
  What: a study whose runs disagreed (no_majority, table_shift) is kept OUT
  of the primary pooled estimate, unless the reviewer has entered every
  flagged field. Such a study still gets its effect size calculated, and the
  log shows a second, comparison-only estimate that includes it
  ([SENSITIVITY]). Studies released by a reviewer's override are named.
  Why: this gate exists because of a real failure. Before it, run
  20261110_120707 pooled Jensen and Lami with numbers that do not appear in
  the PDFs. Both carried disagreement flags, but flags were only logged.
  Now a disagreement blocks pooling until a human resolves it.
  Every study left out appears in the report table "Studies included in the
  review but not in the meta-analysis", with its reason and whether the
  decision was automatic or the reviewer's.

3.8 Effect sizes and meta-analysis
  Per study: from the two arms' mean, SD and N the pipeline computes
  Hedges g (standardised mean difference with small-sample correction) when
  the outcome is measured on different scales across trials, or the mean
  difference (MD) when it is the same scale. Odds ratio and risk ratio are
  supported for binary outcomes. If an effect size could only be taken as
  reported by the paper (not recomputed), the log says so - it is the least
  verifiable kind of input. An implausibly large effect is flagged.
  Pooling: random-effects model (DerSimonian-Laird), because CBT trials
  differ in population, dose and comparator, so a single true effect is not
  assumed. Reported: pooled effect with 95% CI, z and p, between-study
  variance tau2, Cochran's Q with its p, and I2 (share of variation due to
  heterogeneity). Fewer than 2 usable studies: no pooled estimate.
  Forest plot: each study's effect and CI, square size = weight, diamond =
  pooled estimate.

3.9 Subgroups by control type
  What: studies are grouped by comparator - waiting list, usual care,
  attention placebo - and each group is pooled separately, plus an estimate
  excluding waiting-list trials. A second forest plot has two panels: top,
  all pooled studies with the overall estimate; bottom, the same studies with
  waiting-list trials taken off. A trial whose only control is a waiting list
  has no comparator left, so it is listed in grey with no effect (its control
  is never set to 0); the bottom estimate pools the rest.
  Why: waiting-list controls usually make a therapy look better than usual
  care does, so pooling them together can overstate the effect.
  How the control type is decided: the reviewer's entry (comparator_type)
  wins; otherwise the extracted control-group label ("WLC", "Wait-list
  group" -> waiting list; "UC", "Usual Medical Care" -> usual care). A label
  that matches nothing, or a misspelt reviewer value, is "unclassified":
  listed by name and never guessed into a group.
  Caution built in: a group with 1 study is not pooled; a group with 2 is
  pooled with a written caution. Subgroup results are labelled exploratory.

3.10 Risk of bias (RoB 2)
  What: the Cochrane RoB 2 tool, five domains: randomisation process,
  deviations from intended interventions, missing outcome data, measurement
  of the outcome, selection of the reported result. Each domain is judged
  Low / Some concerns / High, with a written justification.
  Text given to the model: the start of the paper (title, abstract) plus the
  Methods and Results sections, located by their headings (up to 50,000
  characters), plus any trial registration lines (NCT, ISRCTN). If no
  Methods heading is found, the first 6000 characters are used.
  Why sections, not the first pages: the information RoB 2 needs -
  allocation concealment, blinding, dropouts per arm, intention-to-treat -
  lives in Methods and Results. An earlier version cut the text at 6000
  characters and lost exactly this information.
  Overall judgement by fixed rule, in code (P4):
    any domain High            -> High
    all five Low               -> Low
    all five assessed, others  -> Some concerns
    domains missing, none High -> Not assessed
  A failed assessment is "Not assessed", never a default "High". The
  model's own overall answer is stored separately for comparison.
  Stability measured: 4 runs x 5 papers x 6 judgements = 30 cells; 1
  differed (Lami, missing data: Some concerns vs High). The overall
  judgement never changed. Known weakness: the model can misread dropout
  counts (for example swapping arms), so the reviewer checks the missing-
  data numbers against the flow diagram.

3.11 Reports and audit trail
  Each run gets its own folder with a run id, and every audit CSV carries
  that id so rows from different files can be matched. A run produces:
    - screening, extraction and RoB 2 tables (CSV)
    - meta-analysis results per study, with included / not included and the
      reason (CSV)
    - forest plot, and forest plot of all pooled studies vs excluding
      waiting-list trials (PNG)
    - Word and HTML reports: PICO and criteria, PRISMA counts, extraction
      table, reviewer-entered data, studies not pooled with reasons, pooled
      result, subgroups, risk of bias, forest plots
    - the run log with every [SCREENING], [SOURCE QUOTE CHECK], [MANDATORY],
      [SENSITIVITY] and [SUBGROUP] line
  If a report format cannot be produced (for example PDF without its
  library), the run summary states why instead of silently skipping it.


------------------------------------------------------------------------------
4. How accuracy is measured, and what the numbers show
------------------------------------------------------------------------------

  The truth file: every study's primary outcome values (N, mean, SD for
  both arms) were read by hand from the PDF and stored with their page and
  table (tests/fixtures/sr_truth.yaml).

  The scorer: scripts/sr_score_run.py compares a run's POOLED values with
  the truth file, and separately scores what the model alone extracted
  before any reviewer correction. It fails if any hand-checked study was
  pooled with a wrong or missing value.

  What it showed on the five test papers:
    - Before the pooling gate (run 20261110_120707): the hand-checked
      studies that were pooled were all wrong; values not in the PDFs
      entered the estimate. This is what a pipeline without checks does.
    - Current pipeline (run 20261112_222233): 4 studies checked, 4 fully
      correct, 0 pooled with a wrong value; 4 of 5 pooled (Ang left out by
      a recorded reviewer decision).
    - The model alone on the same run: 0 of 4 studies fully correct.

  How to read this: the model on its own was not reliable on these papers.
  The pipeline's value is that it found where the model was wrong, kept
  those numbers out, and made the human correction fast, documented and
  checkable. The correct final result comes from the method, not from
  trusting the model.


------------------------------------------------------------------------------
5. Compared with asking a general cloud chat to "do a systematic review"
------------------------------------------------------------------------------

                     General cloud chat            This pipeline
  ------------------ ----------------------------- ---------------------------
  Protocol           Question typed in a chat;     PICO and criteria fixed
                     criteria can drift between    before reading, saved per
                     messages                      run
  Screening          One answer per paper,         Fixed criteria, rationale
                     no record of why              and PICO flags per paper;
                                                   errors/uncertain counted,
                                                   never silently excluded
  Extraction         One reading; a wrong number   Repeated reading, majority
                     looks like a right one        vote, disagreement flagged
  Source of numbers  Usually not given, or a       Verbatim quote per arm,
                     paraphrase                    checked by code against
                                                   the paper text
  SE vs SD, wrong    Not checked                   Checked by code, warned
  timepoint, wrong N
  Human correction   Retyped in chat, lost         Recorded with page/table,
                                                   reported as manual
  What gets pooled   Whatever was extracted        Only agreed or reviewer-
                                                   verified values; the rest
                                                   listed with reasons
  Statistics         Often computed in prose;      Hedges g / MD / OR / RR,
                     method unclear                random effects, tau2, Q,
                                                   I2, computed by code
  Risk of bias       Free-text impression          RoB 2, five domains,
                                                   overall by fixed rule
  Reproducibility    Different answer next time    Run id, saved inputs,
                                                   audit CSVs, re-runnable
  Accuracy           Unknown                       Measured against hand-
                                                   checked truth
  Data destination   Paper sent to the chat's      Destinations listed and
                     provider                      confirmed before any call

  The same model can sit behind both. The difference is everything around
  it: the pipeline treats the model as a fast but fallible reader, not as
  the reviewer.


------------------------------------------------------------------------------
6. Honest limitations
------------------------------------------------------------------------------

  - Tested on one worked example (five RCTs, CBT for fibromyalgia, pain
    intensity after treatment). Accuracy on other topics is not yet
    measured.
  - A human reviewer is still required. On the test papers, the model alone
    got no study fully right; correct pooled values depended on reviewer
    checks that the pipeline asked for.
  - Extraction reads page images. Corrections made in the shared paper text
    do not change extraction; use study_overrides.yaml.
  - Screening reads the start of each paper only (up to 6000 characters).
  - Subgroup results with few studies are exploratory.
  - SR runs on a local Ollama vision model (default gemma4:e4b), or on qwen /
    openai after the cloud warning. Local accuracy is not yet checked against
    the reference set; check every value against the PDF.
  - PDF reports need an extra library; Word and HTML reports are always
    produced.

  For the full list of checks a reviewer must make before reporting any
  result, see docs/sr/REVIEWER_GUIDE.md, sections 3 and 6.
==============================================================================

------------------------------------------------------------------------------
Appendix A. Worked example: CBT for fibromyalgia pain, 5 RCTs
------------------------------------------------------------------------------

Question: in adults with fibromyalgia, does cognitive behavioural therapy
reduce pain intensity after treatment, compared with an inactive control
(usual care, attention placebo or waiting list)?
Trials: Ang 2010, Jensen 2012, Karlsson 2015, Lami 2018, McCrae 2019.
Files: reference/sr_cbt_fibromyalgia (prisma_criteria.yaml,
study_overrides.yaml, pico_sample.json). The PDFs and saved runs are local
only, not in Git. Full citations:
git show b274d24:reference/sr_cbt_fibromyalgia/README.md

What happened at each step (reference run 20261112_222233):

  Screening   5 of 5 INCLUDE; identical decisions in 4 separate runs.

  Extraction  The model alone got 0 of 4 hand-checked studies fully right.
              The errors were found by the checks in section 3.5 or by the
              pooling gate (3.7), and corrected by the reviewer from the PDF:
    Ang       NOT POOLED (reviewer decision). Table 2 is the NFR pain rating
              (pain from a laboratory stimulus), not pain intensity; FIQ pain
              is given only as week-6 change scores, which should not be
              mixed with final values (Cochrane Handbook 10.5.2). Described
              narratively.
    Jensen    The model's "45.6" for both arms was the mean age. Reviewer
              values: Table 3 p7, pain VAS 49 (19) vs 59 (26); N = completed
              treatment 19/15 (the N behind the posttreatment table), not
              randomised 25/18.
    Karlsson  Table 2 p6, MPI-1 pain severity, crude mean (SD). One of three
              readings took the next table row (table_shift).
    Lami      Table 4, post-intervention; N 28/36 (post-intervention, not
              baseline). The model's quotes "mean = 4.2 (SD = 2.1)" do not
              exist in the paper (now caught by check 5).
    McCrae    Three arms (CBT-I, CBT-P, waiting list). CBT-I and CBT-P were
              combined into one intervention arm (Cochrane Handbook 23.3.4).

  Result      4 of 5 pooled. Hedges g: Jensen -0.437, Karlsson 0.226,
              Lami -0.029, McCrae -0.227. Pooled SMD -0.103
              [-0.365, 0.159], I2 = 0.0%, k = 4. The 95% CI includes zero.

  The gate at work: the earlier run 20261111_190839, made before the
  reviewer had verified Jensen, pooled only 3 studies (SMD -0.042
  [-0.327, 0.242]). Jensen's readings disagreed, so it stayed out until a
  human entered values checked against the PDF.

  Accuracy    Scored against the hand-checked truth file (section 4):
              4 checked, 4 fully correct, 0 pooled with a wrong value.

  RoB 2       Overall High for all 5 trials, the same in 4 runs.

  Subgroups   Added after this run (Session 39), not yet seen in a run.
              Expected on these data: waiting list (Jensen, Karlsson,
              McCrae) k = 3, pooled; usual care (Lami) k = 1, not pooled;
              Ang in no group (not pooled).

How to rerun the example: see the Help page (Readme/flashcard-help.html).
