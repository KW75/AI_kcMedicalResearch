# HANDOFF

Single source of truth for the next session. Read this, then work.
Session-by-session history (1-22) is in `Readme/HANDOFF_archive_pre_S19.md`
and git log; consult it only before reopening a closed issue.

Repository: https://github.com/KW75/AI_kcMedicalResearch
Live app:   https://ai-kcmedicalresearch.onrender.com
Health:     https://ai-kcmedicalresearch.onrender.com/_stcore/health

---

## Current State (Session 22, v2.4.13, 2026-08-28)

| Component      | Status |
|----------------|--------|
| Tests          | 501 passed, 3 skipped, 11 deselected (`python -m pytest -m "not live" --tb=short -q`) |
| CI             |  CI | green (244e43b) |
| Render deploy  | green (no code change since Session 21) |
| SR pipeline    | working; extraction is non-deterministic (#11), verify every number |
| Providers      | DeepSeek (default) / Qwen (SR) / OpenAI / Anthropic / Groq / Ollama (local, never falls back) |

Issue numbers below match `README.md` > Known Issues.

---

## Open Issues

| #  | Issue | Priority | What to do |
|----|-------|----------|------------|
| 11 | Extraction non-determinism (Ang, Jensen, Lami) | High | All three pinned by regression fixtures (Sessions 20-22). Underlying non-determinism unaddressed; mitigation is still run 3x and diff, verify against source quotes. See Session 23 priority 3 for reduction options. |
| 12 | CMap offset-decode (v2.4.13) needs real-run confirmation | High | Hardware-required. Run McCrae or Jensen, grep fallback log for `decoded with offset`. |
| 28 | Docker route never executed end to end | High | Hardware-blocked (no Docker on dev machine). |
| 19 | macOS launchers untested on macOS | Medium | Hardware-blocked. |
| 50 | Anthropic SR path skips SD/SE and group/timepoint tripwires | Medium | Decide: port a text pass, or document the gap in `REVIEWER_GUIDE.md` and close. Recommend the latter (see Session 23 priority 2). |
| 2  | WeasyPrint not installed; PDF report falls back to HTML | Medium | |
| 15 | RoB 2.0 ignores `study_overrides.yaml` | Low | |
| 3  | Anthropic geo-restricted from dev machine | Low | VPN or skip. |

---

## Session 22 Summary

Tests-only session. No production code changed.

- Added Lami fixtures to `tests/test_extraction_regression_fixtures.py`
  (2 tests): text_fallback path passes cleanly; Ns-drift signature
  (correct means/SDs, missing source quotes) is caught by the
  missing-quote branch. The latter is what keeps the override
  mechanism's `confirmed` log entry a real cross-check.
- Added Jensen fixtures (13 tests): 6 quote-check parametrizations
  over {49.0, 49.1} x {59.0, 59.1, 59.2}, 6 arm-order parametrizations
  (mean_i < mean_c, no outcome-direction assumption), and 1 pin of
  `_number_in_text`'s integer-fallback branch (the Session 21
  "49.0 vs '49'" investigation, now executable).
- 486 -> 501 tests. `scripts/check_no_bom.py` clean.

---

## Next Session Priorities (Session 23)

1. **#12 real-run confirmation.** Run McCrae or Jensen with a working
   provider key; grep the fallback log for `decoded with offset`.
   Hardware/key-dependent.

2. **#50 scope decision.** Recommend documenting the tripwire-coverage
   gap in `REVIEWER_GUIDE.md` and closing #50. Porting a text pass to
   the Anthropic path costs more than it protects while #3 (Anthropic
   geo-restricted from dev machine) is open.

3. **#11 mitigation, if worth the effort.** The fixtures pin known
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

- **Verify the artifact, not the summary.** Seven documented instances.
  Before treating a Known Issue as work, read the current source of the
  affected file, not the previous session's description. Before citing a
  number from a prior handoff, confirm it appears in an audit CSV. This
  applies to your own outputs mid-session too.

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

Handoff prepared: 2026-08-28, Session 22.
