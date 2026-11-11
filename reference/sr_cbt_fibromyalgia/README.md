# Example review: CBT for pain in fibromyalgia

Worked example of the SR pipeline (Session 38). It is not used by the app;
nothing here is read unless you copy it into input/sr.

## Files
- prisma_criteria.yaml: the review criteria (PICO: adults with fibromyalgia;
  CBT; placebo, active comparator or waiting list (subgroup); pain intensity
  at post intervention; SMD).
- pico_sample.json: the RCT search output that produced the PICO.
- study_overrides.yaml: values the reviewer checked in the PDFs.
- input/: the 5 papers (PDF; local only, not in Git because of copyright).
  The text cache (input/sr/paper_text) is rebuilt on the first run.
- reports/, output/: saved pipeline runs for comparison (local only).
  Run 20261111_190839 is the one that matches study_overrides.yaml;
  20261111_175754 predates Ang's exclusion.

## Papers (add full journal citations from the PDFs)
- Ang 2010: Cognitive behavioral therapy attenuates nociceptive responding in
  patients with fibromyalgia (Arthritis Care Research - 2010 - Ang ...pdf)
- Jensen 2012: Cognitive Behavioral Therapy increases pain-evoked activation of
  the prefrontal cortex in patients with fibromyalgia (Cognitive Behavioral Therapy increases ...pdf)
- Karlsson 2015: Cognitive behaviour therapy in women with fibromyalgia: a
  randomized clinical trial (1-s2.0-S1877886015000567-main.pdf)
- Lami 2018 (s10608-017-9875-4.pdf)
- McCrae 2019 (zsy234.pdf)

## What the reviewer did
- Karlsson, Lami, McCrae: means, SDs and Ns checked in the PDFs and entered
  in study_overrides.yaml (source table and page in each note).
- Ang: excluded from the meta-analysis (exclude_from_meta). Table 2 values
  are the NFR pain rating, not pain intensity; FIQ pain is given only as
  Week 6 change scores.
- Jensen: not pooled automatically (repeated AI readings disagreed; values
  not entered by the reviewer).

## Expected result (run 20261111_190839)
POOLED: 3 of 5 studies (Karlsson g=0.226, Lami g=-0.029, McCrae g=-0.227);
not pooled: Ang (Reviewer), Jensen (Automatic).

## To rerun
1. Copy input/*.pdf (the 5 papers) and study_overrides.yaml into input/sr.
2. Run with this prisma_criteria.yaml: enter the same PICO in the launcher,
   or run the SR pipeline with --config pointing to this file.
3. Afterwards, restore input/sr to the empty template.
