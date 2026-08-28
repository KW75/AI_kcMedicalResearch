# HANDOFF

Single source of truth for the next session. Historical detail for
Sessions 1-18 is in `Readme/HANDOFF_archive_pre_S19.md`; consult it
before repeating work or reopening a closed issue.

Repository: https://github.com/KW75/AI_kcMedicalResearch
Live app:   https://ai-kcmedicalresearch.onrender.com
Health:     https://ai-kcmedicalresearch.onrender.com/_stcore/health

---

## Current Status (as of Session 21, v2.4.13)


| Component            | Status                                              |
|----------------------|-----------------------------------------------------|
| Local tests          | 486 passed, 3 skipped, 11 deselected (`-m "not live"`) |
| GitHub Actions CI    | green as of Session 20 (8193231)                   |
| Render deploy        | green as of Session 18                              |
| SR pipeline          | working with caveats (see Open Issues #11, #12)     |
| Providers            | DeepSeek / Qwen / OpenAI / Anthropic / Groq / Ollama |
| Confidentiality      | `--provider ollama` never falls back (Session 10)   |

## Session 21 - 2026-08-28 - v2.4.13

**Commits:**

- 60ab5ae
  #62 closes as not-reproducible. Added
  `test_source_quote_check_tolerates_extracted_float_vs_integer_quote`
  to `tests/test_data_extractor_source_quotes.py` pinning that extracted
  `49.0` matches an integer-formatted source quote (`"Posttreat CBT:
  49 ± 19"`). Count 485 -> 486.

**#62 was a phantom.** Session 20's handoff described the Jensen post-#48
tripwire firing because extractor wrote `49.0` and the quote read `49`,
and framed this as a design question about tolerant number matching.
Session 21 wrote a one-line diagnostic test asserting the tripwire runs
clean on the exact Jensen inputs; it passed on first run. Trace of
`_number_in_text` shows why: when `value == int(value)`, the matcher
derives both `str(value)` and `str(int(value))` as candidates, so
`49.0` searches for both `49.0` and `49` in the quote text. The
integer-fallback candidate matched, the tripwire stayed silent, and
`source_quote_warning` was `None`.

**What actually fired on Jensen in run 20260826_113816 is now unknown.**
The other tripwire branches (SE-marker, timepoint vocab, within-subject
phrasing, tabular multi-timepoint, text-fallback verbatim) also do not
fire on `"Posttreat CBT: 49 ± 19"` under a code trace. Resolving which
requires reading `run_20260826_113816/extracted_data.csv`'s
`source_quote_warning` column directly - deferred; not blocking, since
the number-matching axis is confirmed clean either way.

**The diagnostic became a regression test.** The mirror-direction case
(extracted `7.4` vs quote `7.40`) was already pinned by
`test_source_quote_check_tolerates_trailing_zero_formatting`. The new
test pins the opposite direction (extracted `49.0` vs quote `49`). They
exercise different regex candidates within `_number_in_text` and both
are worth locking in.

**Session 20's own lesson applied to Session 20's own handoff.**
"Verify the artifact, not the summary" hit its seventh documented
instance. The existing durable-lessons entry already covers this class;
no new lesson needed. **Bonus procedural finding:** commit `8193231`'s
subject line is clean, confirming the editor-paste path (VS Code /
Notepad save-as UTF-8 without BOM) avoids the `Out-File`-default BOM
that landed in `346939f`. Use editor-paste, not `Out-File`, for future
commit-message files.

---

## Session 20 - 2026-08-28 - v2.4.13

**Commits:**

- 346939f
  #23 fixtures. New `tests/test_extraction_regression_fixtures.py`,
  3 tests pinning Ang (2010) against reviewer-verified numbers and
  the Session 19 silent-mis-extraction signature. Count 482 -> 485.

**#23 grounded to real CSV bytes.** Session 19's correction paragraph
gave the reviewer-verified Ang row (mean_i=-20.2, sd_i=23.9,
mean_c=-14.9, sd_c=16.4) as prose. Session 20 pulled the actual
`source_quote_intervention` / `source_quote_control` strings from run
20260826_113816's extracted_data.csv - the earliest run whose schema
carries source_quote_* to disk - and pinned them byte-for-byte:

    source_quote_intervention = "Pain, mean ± SD\nCBT\n-20.2 ± 23.9"
    source_quote_control      = "Pain, mean ± SD\nUC\n-14.9 ± 16.4"

The embedded newlines are real - the model rendered a three-line
table row as one string, and both post-#48 CSV runs ({113816, 143901})
recorded the identical bytes. The fixture keeps them as-is so the
tripwire is exercised on the extractor's real output shape.

**Two corrections to Session 19's correction paragraph.** These are
now in the test file's docstring so they cannot drift again:

1. Session 19 said "2 of 8 runs (_095744, _104447)". Session 20's
   CSV survey shows only one Ang-bearing run with the bad extraction:
   `20260826_104447`. If `_095744` exists in a location Session 20
   did not survey, verify before trusting this correction.

2. Session 19 said the bad runs had "empty source quote". The pre-#48
   CSVs are column-ABSENT for `source_quote_*`, not empty-valued.
   The tripwire's missing-quote branch fires identically on both, so
   the behavioural claim is unchanged; the artifact-level phrasing is.

**#23 closed.** A third bonus test pins the sign of Hedges g on the
verified numbers (must be negative - intervention reduced pain more
than control) using the closed-form calculation from `main.py`
lines ~285-292. Guards against a silent arm-swap regression. Pinned
the SIGN, not the magnitude, deliberately - see new durable lesson
below.

**Jensen edge case surfaced, not resolved.** Post-#48 run
20260826_113816 records Jensen's quote as `"Posttreat CBT: 49 ± 19"`
with extracted values `mean_intervention=49.0`, `sd_intervention=19.0`.
The tripwire fires because the extractor writes `49.0` but the quote
says `49` - i.e. the number-matching check does not treat `49.0` as
appearing in a quote that reads `49`. This is a real code question
(should `49.0` match `49`?) not a test-authoring question, and was
deferred to Session 21. See Next Session Priorities.

**BOM in commit message subject.** 346939f's subject line carries a
UTF-8 BOM (visible in `git log` output as an invisible character
before "test"). Cosmetic; CI unaffected (`check_no_bom.py` scans
source files, not commit messages). Cause: PowerShell 5.x
`Out-File -Encoding utf8` writes a BOM by default. Fix for future
commits: use `utf8NoBOM` (PS 7+) or `[IO.File]::WriteAllText` with
`UTF8Encoding.new($false)`. Not worth history-rewriting a pushed
commit for.

---

## Session 19 - 2026-08-28 - v2.4.13 (summary)

- Resolved #22: new `[OUTCOME/TIMEPOINT]` provenance block in
  `SOURCE_CODE/pipelines/sr/main.py` (10174b2, +41 lines).
- Added `tests/test_outcome_timepoint_surfacing.py`, 5 tests. Count
  477 -> 482 (de5fd1e).
- Correction to prior handoff prose (#23 grounding): the g=+0.075 /
  g=-0.248 numbers only ever existed in HANDOFF prose. Real bimodality
  is at mean/SD level; corrected grounding data is what Session 20's
  fixture pins. See `HANDOFF_archive_pre_S19.md` if the full Session 19
  entry is needed.
- #50 scope clarification: SD/SE text-scan is not portable to
  `_extract_anthropic` without a separate text pass, because that
  path uploads the PDF and receives structured JSON with no raw text
  to scan.

## Session 18 - 2026-08-27 - v2.4.13 (summary)

- Resolved #49 (`check_no_bom.py` scan-root and CI-wiring). Underlying
  code fix was already in Session 16; Session 18 closed the doc drift
  and added regression tests (`tests/test_check_no_bom.py`, 6 tests).
- Test count 471 -> 477.

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
| 11 | Extraction non-determinism (Ang, Jensen, Lami)                              | High     | Ang pinned by Session 20 fixtures. Jensen and Lami not yet - #62 (Jensen's presumed blocker) closed clean in Session 21, so both fixtures are unblocked. |
| 12 | CMap offset-decode landed Session 17; needs real-run confirmation           | High     | Look for "decoded with offset X" line in fallback log on McCrae or Jensen |
| 19 | macOS launchers untested on macOS                                           | Medium   | Hardware-blocked |
| 23 | Regression fixtures for Ang's value sets                                    | -        | **Resolved Session 20** - kept here until pushed |
| 28 | Docker end-to-end unverified                                                | High     | Hardware-blocked (no Docker on dev machine) |
| 50 | Anthropic path bypasses SD/SE text-scan                                     | Medium   | Source-quote and group/timepoint already run; SD/SE not portable without a separate text pass |
| 62 | `_flag_suspect_source_quotes` number-matching: `49.0` vs `49`               | -        | **Resolved Session 21** - did not reproduce. `_number_in_text` already derives an int-fallback candidate (`"49"`) when `value == int(value)`, so extracted `49.0` matches an integer-formatted quote. S20 handoff prose mis-characterised the branch that fired on Jensen. Pinned by `test_source_quote_check_tolerates_extracted_float_vs_integer_quote`. Kept in table until pushed. |


Resolved issues #1-#59 are in `HANDOFF_archive_pre_S19.md` and in git
history; do not reopen without reading the closing session's notes.

---

## AI Providers

(unchanged from Session 19 - see previous handoff)

---

## SR Pipeline

(unchanged from Session 19 - see previous handoff)

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

## Next Session Priorities (Session 22)

1. **Lami fixture** (#11). Add `test_lami_*` to
   `tests/test_extraction_regression_fixtures.py`. Reviewer-verified
   numbers from Session 20's CSV survey: n=28/36, m=7.35/7.4,
   sd=2.08/1.29, `text_fallback` extraction with a study_overrides.yaml
   entry pinning it. Clean-and-easy case.

2. **Jensen fixture** (#11). Now unblocked - #62 closed clean in
   Session 21. Add `test_jensen_*` alongside Lami. Reviewer-verified:
   n=25/18, m=49.1/59.2 or 49.0/59.0 across runs, sd=19.0/26.0. The
   m_i variability across runs (49.0 vs 49.1) is a separate
   non-determinism from the -20.2/-8.9 flip Ang has; pin what recurs
   (n, sd) strictly and the volatile means loosely, or pin per-run
   value sets like Ang.

3. **#12 real-run confirmation.** Hardware-required. Run McCrae or
   Jensen with a working provider key, grep the fallback log for
   `decoded with offset`. If you can share the log section, verify
   the line format matches what Session 17 landed.

4. **#50 scope decision.** Still deferred. Option (a) write a
   separate text pass for Anthropic to enable SD/SE checking, or
   (b) document the gap in `REVIEWER_GUIDE.md` and close #50 as
   "text-scan out of scope". Recommend (b) unless there's a real
   Anthropic-path SD/SE mis-extraction on record that source-quote
   and group/timepoint checks didn't catch.

5. **Session 20 handoff #62 forensics (optional).** If curious,
   pull `run_20260826_113816/extracted_data.csv`'s
   `source_quote_warning` column and identify which branch of
   `_flag_suspect_source_quotes` actually fired on Jensen. Not
   blocking anything; a code trace already ruled out every branch
   on the recorded quote, so the answer is "different quote,
   different field, or a since-fixed matcher version" - closes the
   audit trail if you want it closed.

---

## Durable Lessons

- **Verify the artifact, not the summary.** Six documented instances
  now (Sessions 8, 14, 15, 18, 19, 20). Before treating any Known Issue
  as work-to-do, read the current source of the affected file rather
  than the previous session's description. Before citing a number from
  a prior handoff, check that it appears in an audit CSV. **Session 20
  added: this applies to your own outputs during a session too - the
  346939f BOM was a case of trusting the file-write command's default
  encoding without inspecting the resulting bytes.**

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

- **When pinning a value from a prior session's prose, pin the
  property the test exists to protect (sign, presence, ordering) rather
  than the specific number, unless the specific number is itself the
  reviewer-verified artifact.** New Session 20. The Ang bonus test almost
  became a wrong test by pinning `g ≈ -0.248` (the retracted Session 14
  number). Pinning `g < 0` instead protects against the arm-swap the test
  actually exists to catch, while surviving future changes to the SMD
  formula variant (Hedges g vs Cohen's d vs bias correction on/off).

---

Handoff prepared: 2026-08-28 - Session 21. Sessions 1-18 archived in
`HANDOFF_archive_pre_S19.md`.

