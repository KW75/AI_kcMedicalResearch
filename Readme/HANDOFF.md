# HANDOFF

Single source of truth for the next session. Read this, then work.
Session-by-session history (1-21) is in `Readme/HANDOFF_archive_pre_S19.md`
and git log; consult it only before reopening a closed issue.

Repository: https://github.com/KW75/AI_kcMedicalResearch
Live app:   https://ai-kcmedicalresearch.onrender.com
Health:     https://ai-kcmedicalresearch.onrender.com/_stcore/health

---

## Current State (Session 21, v2.4.13, 2026-08-28)

| Component      | Status |
|----------------|--------|
| Tests          | 486 passed, 3 skipped, 11 deselected (`python -m pytest -m "not live" --tb=short -q`) |
| CI             | green (8193231) |
| Render deploy  | green |
| SR pipeline    | working; extraction is non-deterministic (#11), verify every number |
| Providers      | DeepSeek (default) / Qwen (SR) / OpenAI / Anthropic / Groq / Ollama (local, never falls back) |

Issue numbers below match `README.md` > Known Issues. That is the only
numbering scheme in use; older archive entries used a different one.

---

## Open Issues

| #  | Issue | Priority | What to do |
|----|-------|----------|------------|
| 11 | Extraction non-determinism (Ang, Jensen, Lami) | High | Ang pinned by fixtures (Session 20). Jensen and Lami fixtures still to write - see Priorities 1-2. |
| 12 | CMap offset-decode (v2.4.13) needs real-run confirmation | High | Hardware-required. Run McCrae or Jensen, grep fallback log for `decoded with offset`. |
| 28 | Docker route never executed end to end | High | Hardware-blocked (no Docker on dev machine). |
| 19 | macOS launchers untested on macOS | Medium | Hardware-blocked. |
| 50 | Anthropic SR path skips SD/SE and group/timepoint tripwires | Medium | Decide: port a text pass, or document the gap in `REVIEWER_GUIDE.md` and close. Recommend the latter. |
| 2  | WeasyPrint not installed; PDF report falls back to HTML | Medium | |
| 15 | RoB 2.0 ignores `study_overrides.yaml` | Low | |
| 3  | Anthropic geo-restricted from dev machine | Low | VPN or skip. |

---

## Next Session Priorities (Session 22)

1. **Lami fixture (#11).** Add `test_lami_*` to
   `tests/test_extraction_regression_fixtures.py`. Reviewer-verified:
   n=28/36, m=7.35/7.4, sd=2.08/1.29; `text_fallback` path with a
   `study_overrides.yaml` entry. Straightforward.

2. **Jensen fixture (#11).** Reviewer-verified: n=25/18, sd=19.0/26.0,
   means 49.0-49.1 / 59.0-59.2 across runs. Pin n and sd strictly; pin
   means loosely or as per-run value sets (as Ang does). Note the
   `49.0`-vs-`49` quote-matching concern was checked in Session 21 and is
   NOT a bug: `_number_in_text` already tries an integer candidate.

3. **#12 real-run confirmation** (needs a working provider key).

4. **#50 scope decision** - see table above.

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

---

Handoff prepared: 2026-08-28, Session 21.
