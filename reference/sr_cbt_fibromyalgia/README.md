# Example review: CBT for pain in fibromyalgia

Worked example of the SR pipeline (Session 38). It is not used by the app;
nothing here is read unless you copy it into input/sr.

## Files
- prisma_criteria.yaml: the review criteria used for run 20261111_190839
  (PICO: adults with fibromyalgia; CBT; placebo, active comparator or
  waiting list (subgroup); pain intensity at post intervention; SMD).
  This is the old comparator wording. Since 2026-11-12 the launcher
  default is "Usual care, attention placebo or waiting list (pooled)"
  (Readme/readme_sr_pipeline.txt section 1).
- pico_sample.json: the RCT search output that produced the PICO (not a
  PICO file made in the launcher).
- study_overrides.yaml: values the reviewer checked in the PDFs.
- input/: the 5 papers (PDF; local only, not in Git because of copyright).
  The text cache (input/sr/paper_text) is rebuilt on the first run.
- reports/: saved pipeline runs (local only, not in Git):
  - 20261111_190839: the reference run; matches study_overrides.yaml
    (log: "Loaded 4 study override(s)").
  - 20261111_175754: before Ang was excluded (4 studies pooled).
  - 20261112_161648: run WITHOUT study_overrides.yaml (0 overrides);
    shows what the AI alone gives (Ang + Karlsson pooled, SMD 0.030).

## Papers
- Ang DC, Chakr R, Mazzuca S, France CR, Steiner J, Stump T.
  Cognitive-behavioral therapy attenuates nociceptive responding in
  patients with fibromyalgia: a pilot study. Arthritis Care Res.
  2010;62:618-623. doi:10.1002/acr.20119
  (file: Arthritis Care Research - 2010 - Ang ...pdf)
- Jensen KB, Kosek E, Wicksell R, Kemani M, Olsson G, Merle JV,
  Kadetoff D, Ingvar M. Cognitive Behavioral Therapy increases
  pain-evoked activation of the prefrontal cortex in patients with
  fibromyalgeia [sic]. Pain. 2012;153:1495-1503.
  doi:10.1016/j.pain.2012.04.010
  (file: Cognitive Behavioral Therapy increases ...pdf)
- Karlsson B, Burell G, Anderberg UM, Svärdsudd K. Cognitive behaviour
  therapy in women with fibromyalgia: a randomized clinical trial.
  Scand J Pain. 2015;9:11-21.
  (file: 1-s2.0-S1877886015000567-main.pdf)
- Lami MJ, Martínez MP, Miró E, Sánchez AI, Prados G, Cáliz R,
  Vlaeyen JWS. Efficacy of combined cognitive-behavioral therapy for
  insomnia and pain in patients with fibromyalgia: a randomized
  controlled trial. Cogn Ther Res. 2018;42:63-79 (online 19 Oct 2017).
  doi:10.1007/s10608-017-9875-4  (file: s10608-017-9875-4.pdf)
- McCrae CS, Williams J, Roditi D, Anderson R, Mundt JM, Miller MB,
  Curtis AF, Waxenberg LB, Staud R, Berry RB, Robinson ME. Cognitive
  behavioral treatments for insomnia and pain in adults with comorbid
  chronic insomnia and fibromyalgia: clinical outcomes from the SPIN
  randomized controlled trial. Sleep. 2019;42(3):zsy234.
  doi:10.1093/sleep/zsy234  (file: zsy234.pdf)

## What the reviewer did
- Karlsson, Lami, McCrae: means, SDs and Ns checked in the PDFs and entered
  in study_overrides.yaml (source table and page in each note).
- Ang: excluded from the meta-analysis (exclude_from_meta). Table 2 values
  are the NFR pain rating, not pain intensity; FIQ pain is given only as
  Week 6 change scores.
- Jensen: not pooled automatically (repeated AI readings disagreed; values
  not entered by the reviewer).

## Expected result (run 20261111_190839)
POOLED: 3 of 5 studies - Karlsson g=0.226 [-0.332, 0.785], Lami g=-0.029
[-0.517, 0.459], McCrae g=-0.227 [-0.677, 0.222].
Pooled SMD = -0.042 [-0.327, 0.242], I2 = 0.0% (k=3).
Not pooled: Ang (Reviewer), Jensen (Automatic).

## To rerun
1. Copy input/*.pdf (the 5 papers) and study_overrides.yaml into input/sr.
   The log must say "Loaded 4 study override(s)"; 0 means the overrides
   file was not copied (see run 20261112_161648).
2. Run with this prisma_criteria.yaml: enter the same PICO in the launcher,
   or run the SR pipeline with --config pointing to this file.
3. Afterwards restore the repo: git restore input/sr/study_overrides.yaml
   SOURCE_CODE/pipelines/sr/config/prisma_criteria.yaml (the launcher
   rewrites that sample file), and move the PDFs out of input/sr.
