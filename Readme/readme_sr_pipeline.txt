SR PIPELINE - HOW IT WORKS AND HOW IT GUARDS ACCURACY
(Systematic review of RCTs: screening -> extraction -> RoB 2 -> meta-analysis
-> report. Branch v2.10-sr-screening, Session 38, commit b32f4c4.)

Principle: the AI drafts, the program checks, the reviewer decides. Every
number that reaches the pooled result is either agreed by repeated AI
readings or entered by a reviewer from the PDF, and the report says which.

1. BEFORE A RUN
- Enter the PICO in the launcher. The launcher writes
  SOURCE_CODE/pipelines/sr/config/prisma_criteria.yaml from it (only if it
  changed). The default file is a sample with <...> placeholders; a direct
  run stops until they are replaced. Inclusion/exclusion criteria are still
  hard-coded in the launcher (RCT, adults / non-RCT, animal) - open item 7i.
- Put the trial PDFs in input/sr. Papers never go into Git.
- input/sr/study_overrides.yaml starts empty (comments only). See section 7.
- Worked example (CBT for fibromyalgia pain, 5 trials):
  reference/sr_cbt_fibromyalgia/README.md.

2. READING THE PAPERS (shared text, paper_text.py)
Each PDF is read once and saved as input/sr/paper_text/<name>.txt; reruns
reuse it, so hand corrections in that file are kept.
- Normal page: the PDF text layer is used.
- A few lost symbols (broken font codes, e.g. +/- or = in Ang 2010): each
  is marked [?] and counted, never guessed.
- Broken-font page ([?] ratio >= 0.05 and >= 20 [?] on the page) or a
  scanned page: re-read with Tesseract OCR from a page image. Karlsson 2015
  and McCrae 2019 are entirely broken-font (8670 and 10378 [?] -> 0).
- Tesseract missing: warning, [?] kept.
Why: the old decoder "repaired" broken fonts by shifting character codes
(data shift). It produced wrong digits ("15 March, 2018" -> "904M]rch+1/07")
that the AI then used. Tesseract reads the printed page instead. Caution:
Tesseract can add stray dots ("15. March"), so numbers next to dots need
checking.
The shared text feeds screening and RoB 2. Extraction still reads page
images itself (vision model), not this text (open item).
LaTeX: AI models sometimes answer in LaTeX ($\pm$, $P = 0.8$,
\text{...}). strip_latex() converts these to plain symbols in the OCR mode
summaries; the paper text itself is never altered. The SR pipeline does
not run strip_latex - check SR outputs for stray $...$ (open item).

3. SCREENING
The AI judges each paper against the PICO and inclusion criteria (RCT,
comparator: placebo, active comparator or waiting list as a subgroup).
Planned: rule checks first, 3-reading vote, split vote = NEEDS REVIEW
(never automatic exclusion), exclusion quote checked against the text.

4. EXTRACTION AND VOTING (data_extractor.py, --n-agreement, default 3)
The model reads each paper several times independently. Each field (Ns,
means, SDs per arm) is compared across readings:
- unanimous: all readings agree (caution: all-empty also reads unanimous).
- no_majority: readings disagree on a field.
- table_shift: one reading took the neighbouring table row or column
  (example: Karlsson, two readings took Pain severity 3.88 (1.05) vs
  3.67 (0.75), one took the next row, Interference).
Review gate (F4): a study with no_majority or table_shift is NOT pooled
unless the reviewer has entered every flagged field in
study_overrides.yaml. It is still calculated and shown in the
[SENSITIVITY] comparison, so the reviewer sees its effect.
Other checks before pooling: outcome must match the review outcome;
enough mean/SD/N for an effect size; Hedges g computed by the program
(an effect size reported by the model is labelled "verify against PDF").
Known AI errors in the example: Ns from randomised instead of completers
(Ang 17/15 vs 15/13), wrong table (Jensen), invented values (Lami),
wrong arm (McCrae). Agreement does not prove correctness - the votes can
agree on the wrong row. That is why reviewer checks remain essential.

5. RISK OF BIAS (RoB 2, rob2_tool.py)
- The model receives the paper text (since Session 38: Methods and Results,
  up to 50,000 characters, so randomisation, registration and ITT lines
  are not cut off; if no Methods heading is found, only the first 6000
  characters) and the PICO outcome, and judges the 5 domains for THAT outcome.
- Domain 4 rule: for self-reported outcomes (pain) the participant is the
  outcome assessor. A blinded researcher handing out questionnaires is not
  blinded assessment. Participants who knew their arm + subjective outcome
  = High (4.3 Yes, 4.4 Yes, 4.5 Probably yes).
- Overall is computed by the program, not taken from the model: any High
  -> High; all Low -> Low; otherwise Some concerns; missing domains ->
  Not assessed (grey). The model's own overall is kept in overall_model.
- Known issue: judgements outside Domain 4 vary between runs (7l).

6. META-ANALYSIS AND REPORT
Pooled: studies with agreed or reviewer-entered values (SMD, Hedges g).
The HTML/PDF report shows:
- "Reviewer-entered data": every override with its source note;
- "Studies included in the review but not in the meta-analysis": each
  study with the reason and who decided (Reviewer or Automatic);
- RoB 2 table and forest plot.
Technical skip reasons stay in meta_analysis_results.csv and console.txt.
Each run is saved in reports/sr/<run_id>/ (data, output, console, score).

7. STUDY_OVERRIDES.YAML - WHEN AND HOW
When to add an entry (always after checking the PDF):
- the report lists a study as not pooled because readings disagreed;
- a value is wrong (wrong row, timepoint, randomised vs completer N);
- arms must be combined (multi-arm trial: Cochrane Handbook 23.3.4);
- a study must be kept out of the meta-analysis (exclude_from_meta).
How:
- Key = the exact PDF file name in input/sr, in quotes.
- Fields: first_author, year, n_intervention, n_control,
  mean_intervention, sd_intervention, mean_control, sd_control, note,
  exclude_from_meta. Unknown fields are ignored with a warning.
- Enter only what you checked; partial entries are allowed. Numbers
  replace the AI values; author/year fill in only if missing.
- To clear the review gate, enter ALL flagged fields (table_shift needs
  all four means/SDs).
- note: table, page, row and timepoint, e.g. "Table 2 p6, MPI-1 Pain
  severity, post-treatment, crude mean (SD). Verified from the PDF."
- exclude_from_meta: "one-line reason" - shown in the report as Reviewer.
Example: reference/sr_cbt_fibromyalgia/study_overrides.yaml.

8. CHECKING ACCURACY (developers)
tests/fixtures/sr_truth.yaml holds hand-checked values;
python scripts/sr_score_run.py <run_id> scores a run (pooled values and
"AI alone"), saves score.txt and prints "POOLED: n of N studies".
Overrides make the pooled score correct by design - judge the AI by the
"AI alone" lines (Session 38: 1 of 4 fully correct).
All outputs require human verification before use.
