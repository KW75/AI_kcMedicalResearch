# HANDOFF

Single source of truth for the next session. Read this, then work.
Session-by-session history (1-23) is in `Readme/HANDOFF_archive_pre_S19.md`
and git log; consult it only before reopening a closed issue.

Repository: https://github.com/KW75/AI_kcMedicalResearch
Live app:   https://ai-kcmedicalresearch.onrender.com
Health:     https://ai-kcmedicalresearch.onrender.com/_stcore/health

---

## Current State (Session 24, v2.4.13, 2026-08-29)

| Component      | Status |
|----------------|--------|
| Tests          | 523 passed, 3 skipped, 11 deselected (`python -m pytest -m "not live" --tb=short -q`) |
| CI             | green (c6ac1fd); 1458834 pending at handoff time — confirm |
| Render deploy  | redeploys on 1458834 (CLI-only change, no UI impact) — confirm health URL |
| SR pipeline    | working via CLI with Qwen for the first time (#65 fixed); extraction non-deterministic (#11), verify every number |
| Providers      | DeepSeek (default) / Qwen (SR) / OpenAI / Anthropic / Groq / Ollama (local, never falls back) |

Issue numbers below match `README.md` > Known Issues.

---

## Open Issues

| #  | Issue | Priority | What to do |
|----|-------|----------|------------|
| 11 | Extraction non-determinism (Ang, Jensen, Lami) | High | All three pinned by regression fixtures (Sessions 20-22). Underlying non-determinism unaddressed; mitigation is still run 3x and diff, verify against source quotes. See Session 24 priority 2 for reduction options. |
| 28 | Docker route never executed end to end | High | Hardware-blocked (no Docker on dev machine). |
| 19 | macOS launchers untested on macOS | Medium | Hardware-blocked. |
| 2  | WeasyPrint not installed; PDF report falls back to HTML | Medium | |
| 15 | RoB 2.0 ignores `study_overrides.yaml` | Low | |
| 3  | Anthropic geo-restricted from dev machine | Low | VPN or skip. |
| 66 | Stage-4 summary lines assert positives on empty runs | Low | `[SOURCE QUOTE CHECK] 0 of 1 studies flagged - every extracted value was bound to a verbatim source quote` printed when zero values were extracted; `[OUTCOME/TIMEPOINT] ? ()` prints an empty label. Add an "n extracted" denominator so "0 flagged of 0 extracted" is distinguishable from "0 flagged of 1 extracted". Same lesson as the always-print-the-zero tripwire rule. |

---

## Session 24 Summary

Four commits, two of them code. 501 -> 523 tests. Every item below was
found by checking a handoff claim against the artifact.

- **Doc sync (5d286d2, 4c1018a).** HANDOFF.md said the source-quote
  tripwire fires on six branches; the Session 23 summary in the same
  file said five. Source says five (`_flag_suspect_source_quotes`; branch
  4 is an `if/elif/else` of three sub-checks, the #64 tabular check was
  being miscounted as a sixth). Added `SOURCE_QUOTE_WARNING_BRANCHES` and
  `tests/test_source_quote_doc_sync.py`, which asserts both docs agree
  with the tuple length. Dropped the carried "stray `CI |`" cosmetic
  item (not present).
- **#12 closed (c6ac1fd).** The v2.4.13 CMap offset decoder had no unit
  test and no live test case. The handoff's grep string `decoded with
  offset` does not exist in the code (actual line: `CMap offset decode
  succeeded for ... (offset=+N)`). More importantly, the decoder only
  runs on the "nearly space-free" failure mode and skips `(cid:` cases
  by design; all four broken-CMap corpus PDFs are `(cid:` cases and the
  fifth has a clean text layer. "Run McCrae or Jensen" could never have
  confirmed it. Added `tests/test_cmap_offset_decode.py` (16 cases: all
  four offsets, the space-to-`!` failure shape, false-positive guards).
  Documented, not fixed: decoded text keeps `!` where spaces were.
- **#65 found and fixed (1458834).** The first live Qwen CLI run failed
  on screening with `you must provide a model parameter`. `--model`
  defaults to None and `main.py` passed it straight to every stage;
  `providers.get_default_model` existed but only the Streamlit UI called
  it. No Qwen run had ever completed via the CLI. Added `resolve_model()`
  at parse time, failing loudly when no default is configured (including
  the Ollama placeholder string, which would otherwise have been sent as
  a model name). Verified live: McCrae ran screening/extraction/RoB2 with
  5x HTTP 200.
- **McCrae re-extraction returned no data** on every strategy, and the
  run aborted cleanly. Run 20260826_113816 produced g=-2.36 from the
  same PDF. This is the better outcome (paper is excluded per
  REVIEWER_GUIDE §2.2 regardless); #11 cuts both ways.
- Guide nit noted, not fixed: §2.2 branch 2 says decimal-separator
  differences can miss; they cannot (`_number_in_text` rewrites `\.`
  to `[.,]`).

## Next Session Priorities (Session 25)

1. **Confirm CI green on 1458834 and Render health**, then update the
   Current State rows. Doc-only commit is fine for the hash.

2. **#66, cheap.** Add an extracted-count denominator to the four
   Stage-4 summary lines in `main.py`. Pin with a test that a
   zero-extraction run prints `0 of 0`, not a sentence asserting every
   value was bound to a quote.

3. **#11 mitigation, if worth the effort.** Unchanged from Session 23:
   `temperature=0`/`seed` on the Qwen vision call (cheap, may not help),
   or internal N=3 agreement with `nondet_flag` (expensive, machine-
   enforces the manual step). Skip if reviewer time on the manual step
   is not the bottleneck.

4. **Decoder `!`-for-space gap, low.** `_shift_text` shifts letters only,
   so a +1-shifted PDF's spaces (arriving as `!`) stay as `!` after
   decode. Fine for the LLM screener; may matter if the extractor's
   text-fallback ever receives decoded text. Check whether it does
   before deciding it matters — no corpus PDF exercises this path today.

5. **Guide nit** from Session 24 summary, fold into the next doc commit.

## Housekeeping (low priority, carry until done)

- Add `run_*.log` to `.gitignore` (two untracked from Session 24) and
  delete `input\s24_mccrae\` when done with it.
- Confirm `.venv\Scripts\` Python is the one resolving (a system Python
  was once seen behind a `(.venv)` prompt).
- Delete stale `%TEMP%\ai_km_run_*.bat` on any machine that ran the
  pre-v2.4.7 UI launcher (keys already rotated).
- Commit-message files: write them from an editor (UTF-8, no BOM).
  PowerShell `Out-File` adds a BOM to the subject line.

---

## Durable Lessons

- **Verify the artifact, not the summary.** Eleven documented instances now
  (Session 24 added three in one file: a CI hash one commit stale, a
  cosmetic glitch that no longer existed, and a grep string that never
  existed — plus the branch count itself). Previously eight
  (Session 23 had added the phantom "Anthropic skips group/timepoint" claim
  that had been restated across at least two handoffs without being
  checked against `_coerce_extraction_result`). Before treating a Known
  Issue as work, read the current source of the affected file. Before
  citing a number from a prior handoff, confirm it appears in an audit
  CSV. This applies to your own outputs mid-session too.

- **A silent wrong answer is worse than a crash.** Clean-looking CSV rows
  have carried wrong numbers (zsy234 g=-2.36; Ang -8.9). Plausibility is
  not evidence. Bind verification to the numbers (source quotes), not the
  labels.

- **Identical byte counts across different inputs mean a saturated cap.**

- **A fallback chain that ignores WHY a provider was chosen will violate
  the reason it was chosen.** Ollama is local-only for confidentiality;
  `LOCAL_ONLY_PROVIDERS` must never fall back. Do not undo.

- **Displayed claims that nothing re-verifies decay silently.** Parse
  version/test counts from source at display time, or do not display them.
  This applies to prose too: `REVIEWER_GUIDE.md` §2.2 described the
  source-quote tripwire as four branches when the extractor actually fires
  on five (branch 4 carrying three mutually exclusive sub-checks), because
  branches were added after the doc was last touched and nothing forced
  the doc to stay in sync. If a doc claims a specific count or list,
  either derive it from source or accept that it will rot. (Session 24:
  this very entry said "six" while the Session 23 summary above said
  "five" — the same document contradicted itself one screen apart.)

- **A "confirm it works" item must name a test case that can reach the
  code.** #12 sat as High for three sessions with an instruction (run
  McCrae) that could not exercise the branch, and a grep string that did
  not exist. Before carrying a confirmation item, check: which input
  reaches this code path, and what exact line does it emit?

- **The help text is a claim too.** `--model` promised "provider's
  configured model" for as long as the flag existed; nothing delivered
  it. Handoffs said Qwen was the SR provider; the CLI had never completed
  a Qwen run.

- **A tripwire that only writes its key on failure makes "checked and
  clean" indistinguishable from "never ran".** Always set the key; print
  the zero.

- **Pin the property a test exists to protect (sign, presence, ordering),
  not a specific number** - unless that number is itself the
  reviewer-verified artifact.

- **A regression fixture pins a known failure signature, not the failure
  rate.** Do not conflate "the shape is pinned" with "the paper extracts
  reliably". Lami and Jensen still need the run-3x-and-diff reviewer
  step; the fixtures only guarantee that a known good shape won't be
  falsely rejected and a known bad shape will still be caught. #11's
  underlying non-determinism is unchanged.

---

Handoff prepared: 2026-08-29, Session 24.
