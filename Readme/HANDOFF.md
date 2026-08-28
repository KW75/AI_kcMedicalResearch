# HANDOFF

Single source of truth for the next session. Historical detail for
Sessions 1-18 is in `Readme/HANDOFF_archive_pre_S19.md`; consult it
before repeating work or reopening a closed issue.

Repository: https://github.com/KW75/AI_kcMedicalResearch
Live app:   https://ai-kcmedicalresearch.onrender.com
Health:     https://ai-kcmedicalresearch.onrender.com/_stcore/health

---

## Current Status (as of Session 19, v2.4.13)

| Component            | Status                                              |
|----------------------|-----------------------------------------------------|
| Local tests          | 482 passed, 3 skipped, 11 deselected (`-m "not live"`) |
| GitHub Actions CI    | green as of Session 18                              |
| Render deploy        | green as of Session 18                              |
| SR pipeline          | working with caveats (see Open Issues #11, #12)     |
| Providers            | DeepSeek / Qwen / OpenAI / Anthropic / Groq / Ollama |
| Confidentiality      | `--provider ollama` never falls back (Session 10)   |

---

## Session 19 - 2026-08-28 - v2.4.13

**Commits:**

- 10174b2
  provenance summary (#22). New `[OUTCOME/TIMEPOINT]` block in
  `SOURCE_CODE/pipelines/sr/main.py`, +41 lines.
- de5fd1e
  `tests/test_outcome_timepoint_surfacing.py`, 5 tests. Count 477 -> 482.

**Correction to prior handoff prose (#23 grounding).** Session 14
introduced the claim that Ang was bimodal between g=+0.075 and g=-0.248,
carried unchallenged through Sessions 15-18. Session 19 pulled Ang's row
from all 8 preserved run CSVs (`reports/sr/*/data/extracted/extracted_data.csv`,
20260818_130309 through 20260827_143901). Findings:

- The +0.075 / -0.248 effect sizes exist only in HANDOFF prose. No CSV
  ever contained them.
- The real bimodality is at mean/SD level. **6 of 8 runs**: mean_i=-20.2,
  sd_i=23.9, mean_c=-14.9, sd_c=16.4, with source quote
  `"Pain, mean plus/minus SD / CBT / -20.2 plus/minus 23.9"` - matches the
  paper's Pain outcome table. **2 of 8 runs** (_095744, _104447):
  mean_i=-8.9, mean_c=-10.8 with an empty source quote - silent
  mis-extraction from before #48 (Session 14) landed.
- `outcome_match=True` on all 8 rows, including the mis-extractions.
  Flag is unreliable on pre-#48 runs; `source_quote_intervention` is
  the only column that discriminates correct from incorrect.
- `outcome_selected` / `timepoint_selected` are empty in every historical
  run - the fields only entered the schema in Session 17 (commit
  3b4c0ca). Session 19's surfacing block will populate them going
  forward.

**#50 scope clarification.** Session 18's handoff implied full SD/SE
+ group/timepoint porting to `_extract_anthropic`. Confirmed this
session: group/timepoint check already runs on the Anthropic path via
`_coerce_extraction_result` (verified by inspecting the tail of the
method). SD/SE text-scan is not portable without a separate text pass,
because `_extract_anthropic` uploads the PDF and receives structured
JSON with no raw text to scan. Only source-quote and group/timepoint
checks are portable; SD/SE requires a separate scope decision.

---

## Session 18 - 2026-08-27 - v2.4.13 (summary)

- Resolved #49 (`check_no_bom.py` scan-root and CI-wiring). Underlying
  code fix was already in Session 16; Session 18 closed the doc drift
  and added regression tests (`tests/test_check_no_bom.py`, 6 tests).
- Test count 471 -> 477.
- Lesson: "verify the artifact, not the summary" - fourth documented
  instance at that time.

## Session 17 - 2026-08-27 - v2.4.13 (summary)

- #61 full: Anthropic path now runs the source-quote tripwire.
- #12 mitigated: CMap offset-decode fallback before OCR
  (needs real-run confirmation on a known-shifted PDF).
- #51: added `outcome_selected` / `timepoint_selected` schema fields.
- #52: tabular multi-timepoint quote rows now flagged.
- README reorganised (Known Issues grouped by status); bumped to
  v2.4.13.

Full detail for Sessions 1-18 is in `Readme/HANDOFF_archive_pre_S19.md`.

---

## Open Known Issues

| #  | Issue                                                                       | Priority | Notes |
|----|-----------------------------------------------------------------------------|----------|-------|
| 2  | WeasyPrint not installed; PDF falls back to HTML                            | Medium   | |
| 3  | Anthropic geo-restricted                                                    | Low      | Use VPN or skip |
| 11 | Extraction non-determinism (Ang, Jensen, Lami)                              | High     | #23's fixtures will pin the correct signature; #48 should prevent the silent bad-extraction mode |
| 12 | CMap offset-decode landed Session 17; needs real-run confirmation           | High     | Look for "decoded with offset X" line in fallback log on McCrae or Jensen |
| 19 | macOS launchers untested on macOS                                           | Medium   | Hardware-blocked |
| 22 | `outcome_selected` / `timepoint_selected` provenance                        | Medium   | **Resolved Session 19** - kept here until pushed |
| 23 | Regression fixtures for Ang's value sets                                    | Medium   | Grounding data now factual (see Session 19); fixtures not yet written |
| 28 | Docker end-to-end unverified                                                | High     | Hardware-blocked (no Docker on dev machine) |
| 50 | Anthropic path bypasses SD/SE text-scan                                     | Medium   | Source-quote and group/timepoint already run; SD/SE not portable without a separate text pass |

Resolved issues #1-#59 are in `HANDOFF_archive_pre_S19.md` and in git
history; do not reopen without reading the closing session's notes.

---

## AI Providers

| Provider   | Flag                | Env Var             | Default Model                   | Vision |
|------------|---------------------|---------------------|---------------------------------|--------|
| DeepSeek   | `--provider deepseek`  | `DEEPSEEK_API_KEY`    | `deepseek-v4-flash`               | No     |
| Qwen text  | `--provider qwen`      | `DASHSCOPE_API_KEY`   | `qwen-plus-latest`                | No     |
| Qwen vision| `--provider qwen`      | `DASHSCOPE_API_KEY`   | `qwen-vl-max` (SR)              | Yes    |
| OpenAI     | `--provider openai`    | `OPENAI_API_KEY`      | `gpt-4o-mini`                     | Yes    |
| Anthropic  | `--provider anthropic` | `ANTHROPIC_API_KEY`   | `claude-sonnet-5`                 | Yes    |
| Groq       | `--provider groq`      | `GROQ_API_KEY`        | `llama-3.3-70b-versatile`         | Yes    |
| Ollama     | `--provider ollama`    | `OLLAMA_HOST`         | auto-detected on first use      | No     |

Fallback: transient errors trigger next provider; auth errors (401/403)
raise immediately. `--provider ollama` never falls back
(confidentiality, Session 10). SR pipeline blocks non-vision providers
for extraction.

---

## SR Pipeline

Run directly for interactive PICO:

    python SOURCE_CODE/main.py --mode sr --provider qwen

Defaults to `qwen-vl-max` via `QWEN_VISION_MODEL`. No `--model` flag
needed.

Per-run outputs (timestamped, audit-friendly):

    reports/sr/<run_id>/
      uploads/
      data/screened/
      data/extracted/
      data/results/
      output/figures/forest_plot.png
      output/reports/systematic_review.docx / .html

Mirror of latest run: `output/sr/figures/`, `output/sr/reports/`.

### Study Overrides

`input/sr/study_overrides.yaml`, keyed by PDF filename:

    "some_paper.pdf":
      first_author: Nguyen
      year: 2021
      n_intervention: 42
      n_control: 40
      mean_intervention: 4.10
      sd_intervention: 1.85
      note: "Table 2, 12-week endpoint. Verified from PDF p.7."

Allowed fields: `first_author, year, doi, study, study_id,
n_intervention, n_control, mean_intervention, sd_intervention,
mean_control, sd_control, note`. Metadata fills only when blank;
numeric fields replace extraction output; extraction still runs so
the log can report `field(7.32->7.35)` vs `field(confirmed 7.35)`.
Overrides do not affect screening or RoB 2.0.

---

## Immediate Actions Outstanding

1. Verify the venv resolves under `.venv\Scripts\` (Session 10 sighting
   of a system Python while the prompt showed `(.venv)` may recur).
2. Test macOS launchers on real hardware (#19, #27, #39 all
   hardware-blocked).
3. Verify Docker end-to-end (#28, hardware-blocked).
4. Delete stale `%TEMP%\ai_km_run_*.bat` on any machine that ran the
   pre-v2.4.7 UI launcher (keys are already rotated - this is
   housekeeping).

---

## Next Session Priorities (Session 20)

1. **#23 fixtures** - pin Ang's mean_i=-20.2 / mean_c=-14.9 as the
   reviewer-verified reference (with the "Pain, mean plus/minus SD"
   source quote); assert that a run producing the -8.9 / -10.8 pair
   with an empty `source_quote_intervention` is flagged. Grounding
   data is in Session 19's correction paragraph.
2. **#12 confirmation** - real-run test on McCrae or Jensen; verify
   the "decoded with offset X" line in the fallback log.
3. **#50 scope decision** - either write a separate text pass for
   Anthropic to enable SD/SE checking, or document the gap in
   `REVIEWER_GUIDE.md` and close #50 as "text-scan out of scope".

---

## Durable Lessons

These are the ones that keep recurring - read before starting work.

- **Verify the artifact, not the summary.** Five documented instances
  (Sessions 8, 14, 15, 18, 19). Before treating any Known Issue as
  work-to-do, read the current source of the affected file rather than
  the previous session's description. Before citing a number from a
  prior handoff, check that it appears in an audit CSV.

- **A silent wrong answer is worse than a crash.** zsy234 (g=-2.36)
  and the -8.9 mis-extraction of Ang both produced clean-looking CSV
  rows. Plausibility is not evidence of correctness. Bind verification
  to the numbers (source quotes), not the labels.

- **Identical byte counts across different inputs are a saturated cap.**
  6414 = 8*800+7*2 and 18022 = 12*1500+11*2 named their own bugs in
  Session 14.

- **A fallback chain that ignores WHY a provider was chosen will
  eventually violate the reason it was chosen.** Ollama was picked for
  confidentiality; the chain treated it as first in a list. Fixed in
  Session 10; do not undo.

- **Displayed claims that nothing re-verifies decay silently.** Banner
  versions, test counts, "supported" doc paths. Parse from source at
  display time, or do not display.

- **A tripwire that only writes its key on failure makes "checked and
  clean" indistinguishable from "never ran"** in every dynamically-built
  artifact. Always set the key; print the zero.

---

Handoff prepared: 2026-08-28 - Session 19. Sessions 1-18 archived in
`HANDOFF_archive_pre_S19.md`.
