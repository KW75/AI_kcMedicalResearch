# HANDOFF

Single source of truth for the next session. Read this, then work.
Session-by-session history (1-23) is in `Readme/HANDOFF_archive_pre_S19.md`
and git log; consult it only before reopening a closed issue.

Repository: https://github.com/KW75/AI_kcMedicalResearch
Live app:   https://ai-kcmedicalresearch.onrender.com
Health:     https://ai-kcmedicalresearch.onrender.com/_stcore/health

---

## Current State (Session 23, v2.4.13, 2026-08-28)

| Component      | Status |
|----------------|--------|
| Tests          | 503 passed, 3 skipped, 11 deselected (`python -m pytest -m "not live" --tb=short -q`) |
| CI             | green (5d286d2) |
| Render deploy  | green (no code change since Session 21) |
| SR pipeline    | working; extraction is non-deterministic (#11), verify every number |
| Providers      | DeepSeek (default) / Qwen (SR) / OpenAI / Anthropic / Groq / Ollama (local, never falls back) |

Issue numbers below match `README.md` > Known Issues.

---

## Open Issues

| #  | Issue | Priority | What to do |
|----|-------|----------|------------|
| 11 | Extraction non-determinism (Ang, Jensen, Lami) | High | All three pinned by regression fixtures (Sessions 20-22). Underlying non-determinism unaddressed; mitigation is still run 3x and diff, verify against source quotes. See Session 24 priority 2 for reduction options. |
| 12 | CMap offset-decode (v2.4.13) needs real-run confirmation | High | Hardware-required. Run McCrae or Jensen, grep fallback log for `decoded with offset`. |
| 28 | Docker route never executed end to end | High | Hardware-blocked (no Docker on dev machine). |
| 19 | macOS launchers untested on macOS | Medium | Hardware-blocked. |
| 2  | WeasyPrint not installed; PDF report falls back to HTML | Medium | |
| 15 | RoB 2.0 ignores `study_overrides.yaml` | Low | |
| 3  | Anthropic geo-restricted from dev machine | Low | VPN or skip. |

---

## Session 23 Summary

Docs-only session. No production code, no tests changed.

- Closed #50. The Anthropic SR extraction path's SD/SE gap is documented
  as a permanent architectural limitation in `REVIEWER_GUIDE.md` §6 rather
  than fixed. The Anthropic path receives structured JSON from Claude's
  Files API and has no raw source text to scan; the text-line SD/SE
  tripwire requires raw text and cannot run there.
- Verified against source that the residual Anthropic coverage is
  stronger than the handoff had claimed. `source_quote_warning` runs on
  Anthropic (v2.4.13, #61), including the SE-marker-in-quote branch that
  catches most of what `sd_se_warning` would have caught.
  `group_timepoint_warning` also runs on Anthropic via
  `_coerce_extraction_result` (has since v2.4.10, #10 mitigation) —
  contra the previous handoff's phantom claim that it was skipped.
- Corrected `REVIEWER_GUIDE.md` §2.2. The section described the
  `source_quote_warning` tripwire as firing on four patterns; the
  extractor actually fires on five numbered branches (missing quote,
  number not in own quote, SE-label-in-SD-quote, timepoint confusion
  with three mutually exclusive sub-checks including the #64 tabular
  branch, and the verbatim-source-text branch that only runs when raw
  text is available). This was a documented claim that had decayed
  silently — the "displayed claims that nothing re-verifies decay
  silently" lesson applies to prose docs too, not just displayed
  version/test counts.
- Commit: `25efcd9`. Three files: `README.md` (-1), `RESOLVED_ISSUES.md`
  (+1), `REVIEWER_GUIDE.md` (+55/-23).

---

## Next Session Priorities (Session 24)

1. **#12 real-run confirmation.** Run McCrae or Jensen with a working
   provider key; grep the fallback log for `decoded with offset`.
   Hardware/key-dependent.

2. **#11 mitigation, if worth the effort.** The fixtures pin known
   failure signatures; they do not reduce the rate. Options, cheapest
   first:
   - Set `temperature=0` and a fixed `seed` on the Qwen vision call.
     Cheap; vision models often ignore seed, so may or may not help.
   - Run extraction N=3 internally per PDF; surface the row only if
     all three agree on n, mean (1dp), and sd (1dp), else write
     `nondet_flag`. Turns the manual "run 3x and diff" step into
     machine-enforced coverage. Expensive per PDF.
   - Skip both if reviewer time on the manual step is not the
     bottleneck - the tripwires + overrides + manual verification
     already close the correctness loop.

3. **Guide nit, fold into next doc commit.** `REVIEWER_GUIDE.md` §2.2
   branch 2 says decimal-separator differences "can still miss". They
   do not: `_number_in_text` rewrites `\.` to `[.,]`, so `47.14` matches
   `47,14`. Unicode minus and thousands separators still miss, as stated.

(Session 24 closed the branch-count question from source:
`_flag_suspect_source_quotes` has five top-level conditions, branch 4 an
`if/elif/else` chain of three. `SOURCE_QUOTE_WARNING_BRANCHES` in
`data_extractor.py` and `tests/test_source_quote_doc_sync.py` now pin the
count against both docs. Also dropped the carried "stray `CI |`" cosmetic
item — the glitch is not present in the table above.)

---

## Housekeeping (low priority, carry until done)

- Confirm `.venv\Scripts\` Python is the one resolving (a system Python
  was once seen behind a `(.venv)` prompt).
- Delete stale `%TEMP%\ai_km_run_*.bat` on any machine that ran the
  pre-v2.4.7 UI launcher (keys already rotated).
- Commit-message files: write them from an editor (UTF-8, no BOM).
  PowerShell `Out-File` adds a BOM to the subject line.

---

## Durable Lessons

- **Verify the artifact, not the summary.** Eight documented instances now
  (Session 23 added the phantom "Anthropic skips group/timepoint" claim
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

Handoff prepared: 2026-08-28, Session 23. Session 24 (2026-08-29): doc-sync test added, branch count verified from source.
