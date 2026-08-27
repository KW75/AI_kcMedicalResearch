## Session 17 - 2026-08-27 - v2.4.13

**Status:** 7 commits pushed, CI green (pending final confirmation), Render green.
**Tests:** 471 passed, 3 skipped, 11 deselected (up from 470 at session start).
**Baseline:** v2.4.13 (commit 2faec37), CI green.

### Commits this session

- `9cf0bbf` - Route Anthropic extraction through source-quote tripwire (#61 full).
  `_extract_anthropic` now coerces the API response, restructures flat fields into
  nested `primary_outcome` / `participants` dictionaries, sets
  `extraction_method = "anthropic_file"`, and calls `_flag_suspect_source_quotes`
  with `source_text=None`. Closes the #50 gap for source-quote checks on the
  Anthropic path (SD/SE and group/timepoint flags still text-fallback only).

- `316bc76` - Add CMap offset-decode fallback before OCR (#12).
  Added module-level helpers to `relevance_screener.py`: `_CMAP_STOPWORDS`,
  `_cmap_score`, `_shift_text`, `_try_cmap_offset_decode`. When the text layer
  triggers a non-CID fallback reason, tries offsets (+1, -1, +2, -2) and adopts
  the best decode if it beats baseline by >=15 stopword hits. Reduces
  unnecessary OCR on shift-broken CMaps; McCrae/Jensen-style within-subject
  offsets are the target case. Note: commit message says #18, README's stable
  numbering has this as #12 (broken font CMaps) - same issue, README wins.

- `3b4c0ca` - Add outcome_selected/timepoint_selected schema fields (#51).
  Extended `EXTRACTION_PROMPT_TEMPLATE`, both flat-key lists in
  `extract_by_pdf_path` and `_extract_anthropic`, and `_text_extraction_prompt`
  to carry `outcome_selected` and `timepoint_selected`. Targets Ang's bimodal
  outcome flip (pain-change g=-0.248 vs NFR g=+0.075, #11) and Lami's
  timepoint-picking; the fields record WHICH outcome and WHICH timepoint the
  model chose, so the flip becomes visible in extracted_data.csv rather than
  silent. Not yet surfaced in Stage 4 provenance summary. Commit message
  cites #63 (working number during the session); README canonical is #51.

- `ed7c43a` - Flag tabular multi-timepoint quote rows (#52).
  Extended `_flag_suspect_source_quotes` with an `else` branch after the
  timepoint-vocab / within-subject check: three or more
  `\d+\.?\d*\s*\(\s*\d+\.?\d*\s*\)` cells in one quote now trigger a
  "multiple mean(SD) cells" warning even without timepoint keywords. Added
  regression test `test_tabular_multi_timepoint_row_is_flagged` (Lami
  "CBT-P 7.58 (1.75) 7.35 (2.08) 7.21 (1.79)" pattern). Test count
  470 -> 471. Commit message cites #64; README canonical is #52.

- `8875df4` - Clean up README: fix cross-references, group Known Issues by
  status, bump to v2.4.13. 353 insertions, 269 deletions. Reorganized the
  flat Known Issues table into four groups (Open / Mitigated / Resolved /
  Interim). Fixed drifted cross-references (Docker note now points to #28
  not #19; Startup Time clarifies #17=Ollama probe vs #18=sr.main import).
  Added #51, #52 and Interim #61.

- `8ca7160` - Bump VERSION to 2.4.13. One-line edit to `SOURCE_CODE/main.py`
  line 146; startup banner and code now agree.

### Resolved this session

- **#61 full** - Anthropic path now runs the source-quote tripwire.
  Remaining #50 sub-scope: SD/SE and group/timepoint checks on Anthropic path.
- **#12** - MITIGATED. CMap offset-decode before OCR fallback (implementation
  landed; needs a real-run confirmation on a known-shifted PDF to fully close).
- **#51** - `outcome_selected` / `timepoint_selected` schema fields added.
- **#52** - Tabular multi-timepoint quote rows now flagged (with regression
  test).
- **Priority 1 verification** - Run `20260827_143901` confirmed #62 fix from
  Session 16: Ang/Karlsson/Lami `source_quote_warning` empty; only McCrae's
  expected multi-timepoint warning fires. Jensen-style false-positive
  eliminated.

### Still open

- **#11** - Extraction non-determinism (Ang bimodal, Jensen bimodal, Lami
  chaotic Ns). #51's new fields make the flip visible but do not fix it.
- **#12** - CMap fix landed but needs real-run confirmation on a
  known-shifted PDF; measure OCR-avoided count in the fallback log.
- **#19** - macOS launchers still untested on macOS (hardware-blocked).
- **#22 (equivalent)** - `outcome_selected` / `timepoint_selected` not yet
  consumed by any audit summary or reviewer report; currently
  reviewer-inspectable only.
- **#23 (equivalent)** - Regression fixtures pinning Ang's two exact bimodal
  value sets (g=+0.075 / g=-0.248) still not written; the v2.4.12 verbatim
  quotes identify which table each mode drew from and are ready to key
  fixtures on.
- **#28** - Docker end-to-end still unverified (hardware-blocked).
- **#49** - `check_no_bom.py` still scans only `SOURCE_CODE/`; needs widening
  to `tests/` and `scripts/`, then CI wiring.
- **#50 (partial)** - Anthropic path still bypasses SD/SE and
  group/timepoint tripwires (source-quote check resolved this session).

### Housekeeping notes carried forward

- Header shows "Version 2.4.12" in older run logs; only affects runs before
  commit `8ca7160`. Fresh runs will show 2.4.13.
- Lami's N values still appear as `28.0` (float) in CSV - cosmetic only.
- Log label for McCrae was corrected mid-session (now matches CSV entry
  McCrae 2019).

### Next session priorities

1. **#49** - widen `check_no_bom.py` scan to `tests/` and `scripts/` and add
   to CI (carried from Session 16, deferred twice now).
2. **#12 confirmation** - real-run test of CMap offset-decode on a
   known-shifted PDF (McCrae or Jensen); check the fallback log for the
   new "decoded with offset X" line.
3. **#23 regression fixtures** for Ang's bimodal value sets, keyed on the
   v2.4.12 verbatim source quotes.
4. **#50 completion** - port SD/SE and group/timepoint checks into
   `_extract_anthropic` (the source-quote scope is already done).
5. **#22 surfacing** - consume `outcome_selected` / `timepoint_selected` in
   the Stage 4 provenance summary so reviewers see the flip without
   opening the CSV.

### Instructions to close Session 17

Save this file, then:

    python scripts/check_no_bom.py
    git add Readme/HANDOFF.md
    git commit -m "Update HANDOFF.md with Session 17 summary"
    git push

Paste the push output to close Session 17.


## Version 2.4.13 (Session 16) — 2026-08-27

**Status:** 5 commits pushed, CI green, Render green. Tests: 470 passed, 3 skipped.

**Commits this session:**
| SHA | Description |
|-----|-------------|
| 32e0098 | Widen check_no_bom / strip_bom to repo root; strip 24 BOMs (#60) |
| 0ede7bd | Add BOM check step to CI workflow (#36) |
| d65fd1e | Fix numeric-matcher false-positive for integer-vs-float (#62) + regression test |
| 6a6bdf1 | Add startup warning for --provider anthropic --mode sr (#61 interim) |
| be98fb2 | Add zsy234 PRISMA exclusion entry to REVIEWER_GUIDE.md |

**Resolved:** #60, #36, #62, #19 (zsy234 excluded). **Interim:** #61 (warning only; full Anthropic-path tripwires deferred).

**Still open:** #17, #18, #2, #22, #23, #27, #39.

**Next session priorities:**
1. Verify #62 fix on a fresh pipeline run (Jensen no longer flagged).
2. Full Anthropic-path implementation for #61 (source-quote, SD/SE, group-timepoint checks in `_extract_anthropic`).
3. CMap decode offset-detection for #18 (helps McCrae within-subject flavor of #17).
4. Add `outcome_selected` and `timepoint_selected` schema fields (Ang outcome-selection, Lami timepoint-picking).
5. Tabular multi-timepoint detection in `_flag_suspect_source_quotes`.
6. Hardware-blocked: Docker end-to-end (#27), macOS launchers (#39).

Session 15's handoff follows below unchanged as the historical record.

---

Version 2.4.12 (Session 15) — Priority 1 Tests Committed, REVIEWER_GUIDE
Updated for v2.4.12, activate_venv.bat Version Drift Fixed, Session 14
Commits Pushed, CI/Render Verified Green
======================================
Date: 2026-08-26 (Session 15, following Session 14)
======================================
Repository: https://github.com/KW75/AI_kcMedicalResearch
Tests: 469 passed, 3 skipped, 11 deselected with `-m "not live"` (up from
430 at Session 14 end); 478 passed, 5 skipped without markers - both
verified in the real venv this session. The +39 delta is the Session 14
harness scenarios ported into a committed test suite (Priority 1 from
Session 14's next-session list).
Committed: five commits this session (26ebd7d, 1fcf87f, 80cb05f, 44c25fe,
b0d8b41), all pushed to origin/main. GitHub Actions green on every push.
Render auto-deploy green.
Current Status: all v2.4.12 priorities scoped for committed work are
closed except items 1 (Ang/Jensen quote analysis - needs CSV pull), 
2 (zsy234 disposition - reviewer judgement), and 
3 (check_no_bom.py scan root + CI wiring). API key rotation resolved out-of-band; see below.
No pipeline runs this session - all work was
tests, docs, and script hygiene against the code already committed in
Session 14.

CRITICAL READ FIRST (1): Session 10's confidentiality fix and Session 11's
regression tests - unchanged. Session 14's #48/#38 source-quote
verification remains MITIGATED+VERIFIED (real run 20260826_113816
evidence unchanged); Session 15 added committed pytest coverage but did
not re-run the pipeline.

CRITICAL READ FIRST (2): Session 14's "commits made locally, not pushed"
state is now historical. All five Session 14 commits (c5d222b..2527a0f)
plus all five Session 15 commits (26ebd7d..b0d8b41) are on origin/main.
CI green on the push, Render deploy green. The five-session gap since
Session 10's last CI verification is closed.

CRITICAL READ FIRST (3): The `source_quote_warning` mechanism is now
covered by committed regression tests bound to the exact zsy234 quote
signature (4 flags: SE-as-SD on both arms + multi-timepoint on both
arms). A future refactor that breaks the check on that specific quote
will fail CI. This does NOT extend the check's semantic scope - it is
still a tripwire on four specific patterns, not a semantic verifier
(see REVIEWER_GUIDE.md §2.2 and §6, updated this session).

======================================
SESSION 15 - 2026-08-26 - v2.4.12: DETAIL
======================================

    Priority 1 from Session 14 (RESOLVED) - Session 14's harness scenarios
    ported into a committed test suite. Two new files:

    tests/test_data_extractor_source_quotes.py (31 tests). Source-quote
    verification (#48/#38): the exact zsy234 verbatim quote fires SE+multi-
    timepoint flags (4 total, matching real run 20260826_113816);
    clean between-group quote stays silent; number-not-in-quote (7.45
    absent, 7.4 present matches 7.40); trailing-zero tolerance; missing-
    quote handling; source_quote_warning key always set (None when clean,
    per Session 14's always-set-key contract). Null-sentinel group labels
    (#57): every documented sentinel ("null", "None", "n/a", "NA",
    "not reported", "unknown", "-", "") normalizes to None at every read
    site; real arm names preserved; identical-label tripwire does not
    fire on sentinel-vs-sentinel; and specifically -
    test_null_sentinel_at_main_extraction_does_not_suppress_followup and
    test_real_arm_names_do_suppress_followup exercise
    _needs_group_labels directly (closes #39, the follow-up-mechanism
    regression-test gap Session 13 flagged).

    tests/test_screener_and_accounting.py (8 tests). Screener retry
    (#56): transient RemoteDisconnected retries once and succeeds;
    persistent failure gives exactly 3 attempts then honest error;
    HTTP 401/403 never retried (same principle as #34). Screening
    accounting partition: INCLUDE/EXCLUDE/UNCERTAIN separated from
    ERROR rows using the `error` column (blank vs populated), missing
    error keys handled gracefully. OCR budget early-stop (#50/#51):
    both RelevanceScreener and RoB2Assessor stop OCR when
    MAX_SCREEN_CHARS/MAX_ROB2_CHARS budget is met, verified by
    monkey-patching fitz/pytesseract/PIL and counting page calls
    (asserts doc.pixmap_calls <= 3 when 2 pages of 3000 chars saturate
    MAX_ROB2_CHARS=6000, well below MAX_ROB2_PAGES=12).

    Suite total 469/3/11 (was 430/3/11); +39 tests, +0 regressions.
    Full run 17.69s in isolation, 41.32s for the whole `-m "not live"`
    suite. Committed as 26ebd7d.

    Priority 10 from Session 14 (RESOLVED) - activate_venv.bat hardcoded
    "v2.4.6" in the banner and "v2.4.7" in the header comment, three
    versions behind the current v2.4.12. Same drift pattern as #43/#53
    (launcher banner), fixed in Session 14 commit a1a9e33 by parsing
    VERSION live from SOURCE_CODE/main.py. Applied the identical
    approach here: a PowerShell one-liner inside the -Command block
    does Select-String on main.py, extracts the VERSION value with a
    regex, falls back to "unknown" if the file is missing. Header
    comment now notes the version is parsed live rather than claiming
    a specific value. Verified: banner displays v2.4.12 on Windows
    PowerShell 5.1, Python 3.11.9. No macOS equivalent exists (the
    scripts/macos/ folder contains only Mac_kcMedicalResearch_CLI.sh
    and Mac_kcMedicalResearch_UI.sh, both venv-managing launchers
    without a separate activate step). Committed as 44c25fe.

    Priority 4 from Session 14 (RESOLVED) - REVIEWER_GUIDE.md updated
    for v2.4.12. Four changes: (a) §2.2 (zsy234 case) gains a
    "What v2.4.12 changes (partial mitigation)" block documenting the
    four source_quote_warning patterns, the 4-flag firing on zsy234
    specifically, and an explicit "tripwire not a verifier" caveat -
    `source_quote_warning = None` means "four patterns did not trip",
    not "correct"; item 3.1 remains mandatory. (b) New §3.4 covers
    run_id correlation across screening_audit.csv, extracted_data.csv,
    rob2_audit.csv, and meta_analysis_results.csv - filter each file
    on the same run_id, join on filename, and DO NOT compare rows
    across run_id values because #17's non-determinism makes such a
    join unsound. (c) New §4.4 documents the [SCREENING] accounting
    block partition (INCLUDE/EXCLUDE/UNCERTAIN/ERROR); ERROR rows are
    pipeline failures, not exclusion decisions; explains how to
    recover the true partition from the audit CSV's `error` column if
    the console line was missed. (d) §6 known limitations table: SD/SE
    and within/between rows updated to note v2.4.12 partial mitigation
    (was "manual check only"); two new rows added -
    "extractor quote check is a tripwire, not a verifier" and
    "retry/OCR-budget/quote-check verified on qwen provider path only"
    (the Anthropic-path gap, #61). Committed as b0d8b41.

    Priority 6 from Session 14 (RESOLVED) - Session 14's five commits
    (c5d222b..2527a0f) plus Session 15's five commits were pushed to
    origin/main across the session. GitHub Actions ran on every push
    and stayed green. Render auto-deploy triggered on every push and
    stayed green. Neither had been exercised since Session 10 (five
    sessions of local-only work); no divergence found. The Session 15
    tests exercise fitz/pytesseract via sys.modules injection, which
    was the highest CI-risk area - both Linux and Windows workers
    passed on first push.

    Session 14 handoff cleanup - Readme/HANDOFF_Session14.md was added
    as a merge source in commit 2527a0f (Session 14) and its contents
    merged into HANDOFF.md in commit 7d3fa5a (also Session 14). The
    standalone file was redundant from that point on; deleted as
    commit 1fcf87f. HANDOFF.md is the single source of truth from
    Session 15 onward.

    README.md test-count line - updated the top banner and the
    "Running Tests" section to reflect the actual test count
    (469/3/11 with `-m "not live"`, 478/5 without markers), the
    v2.4.12 baseline, and the commit reference (26ebd7d) that
    introduced the Priority 1 harness ports. Also flipped Known
    Issue #39 (group-label follow-up regression-test gap) from Open
    to RESOLVED (v2.4.12), citing the two specific tests that close
    it: test_null_sentinel_at_main_extraction_does_not_suppress_followup
    and test_real_arm_names_do_suppress_followup. Preserved the note
    that _fetch_group_labels_if_missing /
    _build_group_label_followup_prompt / _call_chat_api_with_prompt
    remain verified only via real pipeline runs - a full integration
    test would require API mocking, out of scope. Committed as 80cb05f.

======================================
KNOWN ISSUES - STATUS CHANGES (Session 15)
======================================
#39   follow-up regression test    Open -> RESOLVED (Session 15) - two
                                   tests in test_data_extractor_source_
                                   quotes.py exercise _needs_group_labels
                                   directly; the outer follow-up functions
                                   remain verified only via real pipeline
                                   runs (an integration test would need
                                   API mocking, deferred).

Carried unchanged (all Session 14 statuses preserved): #17 (Open,
characterized), #18 (Open, confirmed on all 5 papers), #19 (Open,
5 flags on zsy234, disposition decision still pending), #60 (Open,
check_no_bom scan root), #61 (Open, Anthropic-path tripwire gap),
#2, #22, #23, #27, #36. 

#28   API key rotation
Open -> RESOLVED (Session 15) - user confirmed all three provider keys
(Anthropic, DeepSeek, DashScope) rotated out-of-band after the
pre-v2.4.7 launcher leak. %TEMP% file cleanup remains as housekeeping
(leaked strings are no longer valid).

======================================
FILES DELIVERED THIS SESSION
======================================
tests/test_data_extractor_source_quotes.py  (new, 31 tests)
tests/test_screener_and_accounting.py       (new, 8 tests)
scripts/windows/activate_venv.bat           (banner parses VERSION live)
Readme/REVIEWER_GUIDE.md                    (4 edits per Priority 4 above)
README.md                                   (test count 469; #39 RESOLVED)
Readme/HANDOFF_Session14.md                 (DELETED - merged into
                                             HANDOFF.md in Session 14)
Readme/HANDOFF.md                           (this file - Session 15 head)

Commit trail: 26ebd7d (Priority 1 tests) -> 1fcf87f (HANDOFF_Session14.md
removal, amended from 43e7805) -> 80cb05f (README test count + #39) ->
44c25fe (activate_venv.bat VERSION parse) -> b0d8b41 (REVIEWER_GUIDE.md
v2.4.12 documentation).

======================================
LESSONS LEARNED (Session 15)
======================================
    Verify the artifact, not the intent. Commit 43e7805 was made with a
    message describing a README test-count update, but the actual diff
    was the deletion of Readme/HANDOFF_Session14.md - two operations
    mentally conflated before staging. Caught by `git show --stat HEAD`
    on review, then amended to 1fcf87f with a message matching the
    real diff, and the intended README update made as a separate commit
    (80cb05f). Same class of failure as Session 8's "verify a patch
    actually applied" and Session 14's "identical byte counts are a
    saturated cap, not a coincidence": in every case, the fix is to
    inspect the concrete artifact rather than trust the summary.
    Preventive check now standard: after any commit, run
    `git show --stat HEAD` before pushing, and confirm the file list
    matches the message.

    A first-time push after five sessions of local-only work is a risk
    concentration, not a routine event. The Session 15 push was green
    on the first try, but that outcome was not guaranteed: CI hadn't
    been exercised since Session 10, Render hadn't been deployed since
    Session 10, and the Priority 1 tests used sys.modules injection
    (fitz/pytesseract) that could plausibly break on Linux. Green on
    the first push is the good outcome; the lesson is not to defer
    pushes long enough to make it a coin flip. Push per-commit or
    per-session, not per-milestone.

    A hardcoded version string is a load-bearing lie unless it is
    parsed at runtime. activate_venv.bat's "v2.4.6" banner (three
    versions stale) was the third instance this project has fixed of
    the same pattern (#43 launcher argparse, #53 launcher banner,
    Session 15 activate_venv.bat) - and the merged HANDOFF.md itself
    picked up a UTF-8 BOM during the Session 14 paste-merge, which is
    the fourth. Any string that displays a fact should either be
    computed from the fact's source at display time, or not displayed.

    "The tests I wrote already work in a harness" and "the tests are
    committed to the suite" are different states with different
    guarantees. Session 14 verified all its tripwires via harness runs
    but explicitly noted the tests were not yet ported. Session 15
    ported them; the +39 tests now gate CI on the real-run signatures
    (zsy234 4-flag firing, 6414/18022 saturation numbers,
    401/403 no-retry). A future refactor that silently breaks those
    signatures now fails CI on push - a guarantee no harness can give.

======================================
NEXT SESSION PRIORITIES (Session 16)
======================================

1   Pull run 20260826_113816's extracted_data.csv (deferred from
    Session 14 Priority 2). Read primary_outcome.source_quote_* for
    Ang - which table/timepoint does each value set (+0.075 vs -0.248
    families) come from? - and Jensen (extraction returned rounded
    49.0/59.0 which its own quotes do not contain; almost certainly
    #17 caught in the act). Ang's answer resolves the bimodality
    story; Jensen's confirms whether the pipeline's rounding is
    model-side or a downstream cast. Both feed #23's corpus fixtures
    ground truth.

2   Decide zsy234's disposition (#19), unchanged from Session 14.
    Five flags across three mechanisms (source-quote SE x2,
    source-quote multi-timepoint x2, plausibility). Reviewer choice:
    exclude with a documented PRISMA reason, or enter reviewer-verified
    between-group values via study_overrides.yaml. Not a code task.

3   #60 check_no_bom.py scan root, then #36 CI wiring. Change the scan
    root from SOURCE_CODE/ to the repo root (with an explicit ignore
    list for .git, .venv, output/, reports/, and node_modules if
    ever added). Re-run against the current tree; expect zero BOMs
    (the three known BOMs in tests/ and scripts/ were stripped in
    Session 14). Then add a GitHub Actions step that runs
    check_no_bom.py before pytest. Small self-contained work, ~30 min.

4   #61 Anthropic-path tripwire gap. Either implement source-quote /
    SD-SE / group-timepoint checks on the _extract_anthropic /
    assess_by_file_id paths, or add a startup warning when
    --provider anthropic is selected for SR mode (and document the
    gap in REVIEWER_GUIDE.md - already noted in §6 this session).
    Implementation is preferred; documentation-only is acceptable as
    an interim step.

5   #17 root cause via #18 (broken font CMaps confirmed on all 5
    papers). A fixed +1 character-offset decode before the OCR
    fallback would give every stage a clean text layer and likely
    stabilize extraction - the highest-leverage unfixed defect in
    the repo per Session 14's assessment. Session 15 did nothing on
    this; it remains the correct large-scope item for Session 16.

6   Session 14 Priority 8 (Docker end-to-end, unverified since
    Session 10) and Priority 9 (macOS launchers untested, #27/#39) -
    both blocked on hardware access, both carried unchanged.

Housekeeping (not urgent, not a Session 16 priority): run
`Remove-Item "$env:TEMP\ai_km_run_*.bat" -ErrorAction SilentlyContinue`
on any Windows machine that ran the pre-v2.4.7 UI launcher. The keys
inside are invalidated by the out-of-band rotation, but the files are
noise on disk.

Handoff prepared: 2026-08-26 - Session 15 - prepended to HANDOFF.md; this
document remains the single source of truth for Session 16. Session 14's
handoff follows below unchanged as the historical record.

Version 2.4.12 - run_cli Refactor, OCR Truncation Root-Cause, Audit
Provenance, Screening Drop Guard, Source-Quote Verification (#48 REAL-RUN VERIFIED)
======================================
Date: 2026-08-26 (Session 14, following Session 13)
======================================
Repository: https://github.com/KW75/AI_kcMedicalResearch
Tests: 430 passed, 3 skipped, 11 deselected - VERIFIED in the real venv at
session end (423 at start; +7 routing, +1 undispatched-mode, -1 impossible-
path SR test; two clean-case tripwire assertions updated to the always-set
key contract). The new-scenario tests listed under NEXT SESSION PRIORITIES
are NOT yet written. Every fix was verified via stubbed harnesses plus SIX
real pipeline runs, then the full suite gated the commits.
Committed: five commits c5d222b..2527a0f on main (one concern each: run_cli
+ tests / OCR budgets + retry / #48 + provenance / launcher / docs) plus
this HANDOFF merge; NOT pushed at time of writing - see priority 6.
Current Status: SR pipeline run six times end-to-end against the real 5-paper
corpus during this session; the final run (20260826_113816) is the first run
in project history in which the documented zsy234.pdf failure was flagged by
its own targeted mechanism (source quotes) rather than only by the #13
plausibility bound.

CRITICAL READ FIRST (1): Session 10's confidentiality fix and Session 11's
regression tests - unchanged this session.

CRITICAL READ FIRST (2): #48/#38 (bind verification to the NUMBERS) is
IMPLEMENTED and REAL-RUN VERIFIED this session. The extraction schema now
requires a verbatim per-arm source quote on BOTH extraction paths; a
deterministic check flags missing quotes, numbers absent from their own
quote, SE labels in an SD's quote (this also closes #9's vision-path gap),
multiple-timepoint / within-subject phrasing in a quote, and (text path)
quotes not found verbatim in the source. In run 20260826_113816 the model
complied 5/5 with the new field and zsy234 fired FOUR quote flags (SE x2 +
multi-timepoint x2) on the vision path, plus #13's plausibility flag - the
exact configuration every prior real run sailed through with one flag.
Jensen ALSO fired (all four extracted values absent from their own quotes -
almost certainly #17's instability caught in the act; extraction returned
49.0/19.0/59.0/26.0 while earlier runs and probably the quotes carry
49.1/59.2). Treat the mechanism as MITIGATION VERIFIED, not as removing the
manual-verification requirement.

CRITICAL READ FIRST (3): A transient network error during screening in run
20260826_110915 SILENTLY REMOVED Karlsson from the entire review (error ->
UNCERTAIN -> not INCLUDE -> absent from extraction, RoB2, and the pooled
estimate, which swung -0.514 -> -0.777) with a single ERROR line mid-log and
no other trace. Fixed two ways: the screener now retries transient failures
(3 attempts, backoff; 401/403 never retried, same principle as #34), and
sr/main.py prints a [SCREENING] accounting block (INCLUDE/EXCLUDE/UNCERTAIN/
ERROR counts, error drops labelled "NOT a scientific judgment and NOT a valid
PRISMA exclusion") plus a reminder directly under the pooled estimate when
any paper was dropped non-scientifically.

======================================
SESSION 14 - 2026-08-26 - v2.4.12: DETAIL
======================================

    #43 (RESOLVED) - Extracted the entire mode-dispatch elif chain from
    main.py's `if __name__ == "__main__"` block into run_cli(args); the guard
    is now three lines and keeps the KeyboardInterrupt handler. Replaced
    test_main_sr_mode (which exercised main.main(mode='sr'), an impossible
    path) with TestCliRouting: SR routes to run_sr_launcher and never reaches
    choose_role, plus one routing test per mode - the dispatch chain
    previously had zero real coverage. The dead `else: main(...)` fallthrough
    (the exact mechanism that produced the SR KeyError path) now raises
    ValueError for undispatched modes; regression test added. All routing
    scenarios verified by executing the real extracted dispatch source with
    stubbed handlers.

    Version/encoding hygiene (RESOLVED) - VERSION "2.4.8" -> "2.4.11" (bump
    to 2.4.12 when committing); module docstring's hardcoded v2.2.0 replaced
    with a pointer to VERSION. Nine mojibake sites ('??' comments, '??????'
    print prefixes) replaced with ASCII ('--', '[!]', '[i]'). THREE UTF-8
    BOMs found OUTSIDE SOURCE_CODE/ (tests/test_main_coverage.py - which also
    had MIXED CRLF/LF endings - and scripts/launcher.py); stripped. See new
    issue #60: check_no_bom.py's scan root must cover tests/ and scripts/
    before it is wired into CI (#36).

    #50 (NEW, RESOLVED) - Screening OCR truncation. relevance_screener.py
    capped each OCR'd page at t[:800] over up to 8 pages; every >=8-page
    paper saturated at exactly 8*800 + 7*len("\n\n") = 6414 chars (the
    identical "OCR extracted 6414 chars" lines across four different PDFs in
    the Session 13 run log), and the 6000-char prompt cap then cut page 8
    anyway - screening decisions were made on 800-char snippets, less than
    most abstracts. Replaced with one shared MAX_SCREEN_CHARS=6000 budget
    filled front-to-back with EARLY STOP (consistent with the pdfplumber text
    path), reason-specific fallback logging (empty layer / CID markers /
    space-free - all five corpus papers turn out to be "CID markers in text
    layer", confirming #18's broken-CMap diagnosis on every paper), honest
    char/page accounting, fitz doc closed, and the qwen endpoint now honors
    DASHSCOPE_BASE_URL like every other stage (it hardcoded the intl URL - a
    dormant sibling of #37). Real-run effect: screening OCR ~15-19s -> ~3s
    per paper, Stage 2 ~2m31s -> ~1m13s; all 5 papers still screen INCLUDE.
    Old-code 6414 signature and new budget behavior both reproduced in a
    stubbed harness before deployment.

    #51 (NEW, RESOLVED) - RoB2 OCR truncation, same disease. rob2_tool.py
    capped OCR chunks at t[:1500] over up to 12 pages: every RoB2 OCR count
    in real logs is the saturated formula (12*1500+11*2=18022 for zsy234,
    9*1500+8*2=13516 Jensen, 6*1500+5*2=9010 Ang), of which the prompt kept
    only 6000 - ~70% of ~2m50s of OCR bought nothing. Same fix package
    (MAX_ROB2_PAGES=12 / MAX_ROB2_CHARS=6000 shared budget, early stop,
    reason logging, doc close); the confusing page selection
    list(range(3)) + list(range(3, n))[:9] (= first 12 pages in disguise)
    replaced with a straightforward loop; the pdfplumber text path's own
    t[:800]/20-page cap replaced with the same budget. Real-run effect:
    Stage 3.5 ~2m50s -> ~60-80s. BEHAVIOR NOTE: the garble detection now
    inspects only the budget window (first ~2-4 pages), so CID damage that
    starts later goes undetected there - observed benignly on Lami, whose
    clean front pages now legitimately take the text path in RoB2 (better
    input than OCR), but the narrowed window is a real scope change.

    #52 (NEW, RESOLVED) - Launcher advertised artifacts unconditionally.
    run_sr_launcher printed "[SR] PDF -> ...systematic_review.pdf" even when
    the pipeline itself reported "PDF -> None" (WeasyPrint absent, #2). Each
    artifact line now prints only if the file exists AND its mtime is at or
    after this run's start - the mirror dir persists across runs, so a bare
    exists() would advertise a STALE copy from an earlier run as this run's
    output. Verified in three real runs ("PDF -> not generated (see pipeline
    log above)").

    #53 (NEW, RESOLVED) - scripts/launcher.py banner claimed "Version 2.4.3 /
    Tests 400 passed - 3 skipped" - nine versions and ~30 tests stale, a
    displayed claim nothing re-verified (same failure shape as #52). The
    banner now parses VERSION and the MIN/MAX_PYTHON gate live from
    SOURCE_CODE/main.py with a regex (no import chain) and shows
    "Version 2.4.11 / Python 3.11 - 3.12" with computed padding; the
    unverifiable test count is deliberately not displayed. BOM stripped;
    stale version suffixes scrubbed from comments. Rendered against the real
    patched main.py with machine-verified box alignment.

    #54 (NEW, RESOLVED) - screening_log.csv's pico_* columns have been EMPTY
    IN EVERY FILE EVER WRITTEN: the screener returns a nested pico_match
    dict, write_screens' fixed fieldnames expected flat pico_* keys nothing
    ever wrote, and extrasaction="ignore" silently dropped pico_match,
    confidence, is_rct and exclusion_reasons too (same disease as #47, one
    function up the file). write_screens now flattens on a copy (input dicts
    are reused downstream and stay unmutated) and carries the real fields.
    SCHEMA CHANGE: any test asserting the old column set must be updated.

    #55 (NEW, RESOLVED) - Audit CSVs carried no run identifier; combined
    with #17 this makes cross-run conflation inevitable. INCIDENT: this
    session an extracted_data.csv from a Session 13 run folder was analyzed
    as the day's run, producing a (retracted) claim that the audit trail
    failed to reproduce the pooled input for Ang. Decisive tell: the CSV's
    Lami override audit read "n_intervention(absent->28)" while the day's
    console read "n_intervention(72->28)" - mutually exclusive within one
    run; pooled arithmetic corroborated (that CSV's Ang implies Session 13's
    -0.577, the day's Ang implies -0.514). Fix: sr/main.py stamps run_id
    (the timestamped folder name) into every row of all four audit CSVs;
    write_results' fixed fieldnames gained "run_id" (or the #47 trap would
    silently eat it).

    #56 (NEW, RESOLVED) - Silent screening drop (see CRITICAL (3) above).
    Retry + accounting + pooled-estimate reminder. Retry verified in harness
    (one RemoteDisconnected -> retried -> INCLUDE; persistent failure ->
    exactly 3 attempts -> honest error row; HTTP 403 -> no retry).
    Accounting verified in two real runs ("[SCREENING] 5 INCLUDE / 0 / 0 / 0
    of 5 papers").

    #57 (NEW, RESOLVED) - Sentinel group labels. In run 20260826_111938 the
    group-label follow-up returned the QUOTED STRING 'null' for both of
    Lami's fields; _value_present('null') is truthy so it was stored as a
    real label, and the identical-labels tripwire fired with a misleading
    within/between message (the first real firing of that tripwire ever -
    right alarm, wrong diagnosis). The old prompt actively invited this:
    the placeholder "...or null if you cannot find a real arm name" sat
    INSIDE a quoted string. Fixes: _clean_group_label() treats
    null/none/n/a/na/not reported/unknown/"-"/"" (case-insensitive) as
    declines at EVERY label read site (tripwire, _needs_group_labels - where
    a truthy sentinel would have SUPPRESSED the follow-up - and the
    follow-up assignment); the prompt now demands unquoted JSON null
    explicitly; filename is set before the follow-up's tripwire re-run so
    its warnings no longer log "?". Real-run result: the very next run,
    Lami's follow-up returned genuine arm names ('CBT' / 'Usual Medical
    Care') for the first time in project history.

    Silence-ambiguity fixes (RESOLVED) - All Stage 4 check summaries now
    print unconditionally with coverage: [PLAUSIBILITY] prints "0 of N" when
    clean and "check skipped (no bound for MD)" when inapplicable; [SD/SE
    CHECK] reports how many rows were checkable at all (text-fallback only)
    and how many vision rows were not; [GROUP/TIMEPOINT CHECK] states on
    every clean run that it validates labels only and points at the source-
    quote check. Both extraction tripwires now ALWAYS set their result key
    (None when clean) so the dynamically-built extracted_data.csv columns
    exist on clean runs - previously "checked and clean" and "never ran"
    were indistinguishable in both console and CSV. Vision rows now record
    extraction_method="vision_<strategy>" (text path already recorded
    text_fallback), which feeds the coverage counts and documents which
    page-selection strategy produced each row (useful for #17). The
    previously-silent model-reported-effect-estimate path in Stage 4 now
    logs explicitly (no run has ever taken it; it was an armed silent path).

    #48 / #38 (RESOLVED as designed; REAL-RUN VERIFIED) - Source-quote
    verification, the actual fix for the zsy234 failure class. Schema: both
    prompts require source_quote_intervention / source_quote_control in
    primary_outcome - VERBATIM sentence/table-row copies including any SD/SE
    label and timepoint words, paraphrase forbidden, null permitted. Quotes
    are preserved through _coerce_extraction_result and the restructure step
    (both key lists extended - restructure REBUILDS primary_outcome from a
    fixed list and would otherwise discard them, the same way raw_fragment
    was never preserved). _flag_suspect_source_quotes runs on BOTH paths,
    after restructure and BEFORE reviewer overrides (flags describe what was
    extracted). Checks: (1) values without a quote -> unauditable, flagged;
    (2) extracted mean/SD not present in its own quote (tolerant matcher:
    7.4 matches "7.40", refuses "7.45"/"176"/"76.3"); (3) SE/SEM label in an
    SD's quote -> #9 NOW COVERED ON THE VISION PATH (Session 13 Priority 4
    closed by the same schema change, as predicted); (4) >=2 distinct
    timepoint references or within-subject phrasing ("relative to baseline")
    -> the within/between failure; (5) text path: quote not found verbatim
    in source (whitespace-normalized) -> possible fabrication. Always sets
    source_quote_warning (None when clean); wired into audit_row,
    write_results fieldnames, an unconditional [SOURCE QUOTE CHECK] Stage 4
    block, and extracted_data.csv (nested quote columns appear
    automatically). Verified in harness against the exact documented zsy234
    sentence AND in real run 20260826_113816 (see CRITICAL (2)). The
    Anthropic path (_extract_anthropic) does NOT run this check - same
    limitation as every other tripwire there (new issue #61).

    #17 characterization (Open, materially advanced) - Six real runs this
    session establish: Ang is BIMODAL between two exact value sets
    (+0.075 [-0.647,0.796] vs -0.248 [-0.972,0.476], each reproduced to
    three decimals across runs; RoB2's own justification explains why: two
    outcomes x two timepoints to choose from), and the pooled estimate is
    essentially keyed to which set a run draws (-0.514 vs -0.576/-0.577).
    Jensen is bimodal (-0.443 / -0.447 families) and in the final run
    extraction returned ROUNDED values (49.0/59.0) that its own quotes do
    not contain - the first time #17 has been caught in the act by a
    tripwire. Lami's extracted Ns are chaotic (absent / 72,41 / absent
    across runs; the override caught every variant). McCrae and Karlsson are
    stable. The source quotes now identify WHICH table each run's numbers
    came from, turning the instability from a mystery into a documented
    outcome-selection problem and giving #23's corpus fixtures their ground
    truth.

    Real-run verification ledger (six runs): 20260826_095744 (baseline,
    pre-fix, produced the 6414/18022 evidence and phantom-PDF line);
    _104447 (screener/launcher/summaries/run_id fixes verified; RoB2 still
    old); _110915 (RoB2 fix verified; KARLSSON SILENTLY DROPPED by network
    error - the #56 incident); _111938 (retry+accounting verified clean;
    'null' sentinel incident #57; first real group-tripwire firing);
    _113816 (source quotes live: zsy234 flagged 4x by #48 + 1x by #13,
    Jensen flagged for quote/number mismatch, Lami got real arm names,
    runpy warning gone, 5/5 model compliance with the quote field).

======================================
KNOWN ISSUES - STATUS CHANGES (HANDOFF numbering)
======================================
15/#9   SD/SE confusion            CRITICAL -> MITIGATED+VERIFIED (S14): the
                                   source-quote SE check fired on zsy234's
                                   real quotes ON THE VISION PATH in run
                                   _113816 (2 flags). The text-path tripwire
                                   remains unexercised against zsy234 (the
                                   paper never takes that path) - now moot
                                   for this paper. Manual check still
                                   required.
16/#10  within/between confusion   CRITICAL -> MITIGATED+VERIFIED (S14) via
                                   #48's multi-timepoint quote check (2
                                   flags on zsy234 in _113816). Manual check
                                   still required.
17      extraction non-determinism Open - characterized (Ang/Jensen bimodal,
                                   Lami Ns chaotic); quotes now localize the
                                   source per run. Root cause still likely
                                   #18.
18      broken font CMaps          Open - now confirmed on ALL five corpus
                                   papers by the reason-specific logging
                                   ("CID markers in text layer" x5, every
                                   stage). Still the highest-leverage
                                   unfixed defect.
19      zsy234 disposition         Open - decision now well-evidenced: 5
                                   flags across 3 mechanisms. Exclude with a
                                   documented PRISMA reason, or enter
                                   corrected values via overrides.
38/48   verification bound to      RESOLVED (S14) - see CRITICAL (2).
        numbers
43      test_main_sr_mode          RESOLVED (S14) - run_cli + routing tests.
47      write_results fieldnames   (was RESOLVED S13) - pattern recurred
                                   twice more and is now fixed in
                                   write_screens (#54) and pre-empted for
                                   run_id (#55).
49      follow-up regression test  Open - plus the new-scenario tests listed
                                   below.
NEW 50  screening OCR 800/page cap RESOLVED (S14)
NEW 51  RoB2 OCR 1500/chunk cap    RESOLVED (S14)
NEW 52  phantom artifact lines     RESOLVED (S14)
NEW 53  stale launcher banner+BOM  RESOLVED (S14)
NEW 54  empty pico columns in      RESOLVED (S14) - schema change; update
        screening_log.csv          any dependent tests
NEW 55  no run_id in audit CSVs    RESOLVED (S14) - incident documented
NEW 56  silent screening drop      RESOLVED (S14) - retry + accounting
NEW 57  'null' sentinel labels     RESOLVED (S14)
NEW 58  runpy double-import warn   RESOLVED (S14) - lazy PEP 562 __init__;
                                   verified absent in _113816
NEW 59  screener ignored           RESOLVED (S14) - folded into #50
        DASHSCOPE_BASE_URL
NEW 60  check_no_bom scan root     Open - must cover tests/ and scripts/
        misses tests/ + scripts/   (three BOMs found there this session)
                                   before CI wiring (#36)
NEW 61  Anthropic path runs no     Open - _extract_anthropic /
        tripwires                  assess_by_file_id bypass quotes and all
                                   flags; document or implement before
                                   recommending the Anthropic provider for SR

Carried unchanged: #2 WeasyPrint, #19(README)/HANDOFF Docker unverified,
#22 RoB2 vs overrides, #23 corpus fixtures, #27/#39 macOS launchers,
#36 CI BOM wiring, CI/Render not re-verified since Session 10.

======================================
FILES DELIVERED THIS SESSION (place at these paths)
======================================
main.py                 -> SOURCE_CODE/main.py            (run_cli, VERSION,
                           mojibake, launcher artifact check, loud dead-else)
test_main_coverage.py   -> tests/test_main_coverage.py    (routing tests; BOM
                           stripped, endings normalized to LF)
relevance_screener.py   -> SOURCE_CODE/pipelines/sr/src/screening/
sr_main.py              -> SOURCE_CODE/pipelines/sr/main.py   (RENAME)
data_extractor.py       -> SOURCE_CODE/pipelines/sr/src/extraction/
rob2_tool.py            -> SOURCE_CODE/pipelines/sr/src/screening/
audit_logger.py         -> SOURCE_CODE/pipelines/sr/src/utils/
__init__.py             -> SOURCE_CODE/pipelines/sr/__init__.py
launcher.py             -> scripts/launcher.py
NOTE: two files shared the upload name "main.py"; sr_main.py is the SR
pipeline's, main.py is the outer CLI's. Place carefully.

======================================
LESSONS LEARNED (Session 14)
======================================
    Identical byte counts across different inputs are a saturated cap, not a
    coincidence. 6414 = 8*800+7*2 and 18022 = 12*1500+11*2 named their own
    bugs; the log had been printing the confession for weeks.
    An audit file without a run identifier will eventually be read as a
    different run's file - and with #17, "eventually" is immediately. This
    session's own analysis fell into it; the retraction is in the transcript.
    Verify "within a single run" before alleging an audit break. One
    override-audit string ("absent->28" vs "72->28") settled in seconds what
    effect-size arithmetic only made suspicious.
    A dropped API call is not a PRISMA exclusion. Retry logic and inclusion
    logic must never share a code path silently; when they do, a TCP reset
    becomes a scientific judgment.
    A tripwire that only writes its key on failure makes "checked and clean"
    indistinguishable from "never ran" in every dynamically-built artifact.
    Always set the key; print the zero.
    _value_present() is not consent semantics for model output. "null" the
    string is a decline, and a prompt placeholder inside quotation marks
    teaches the model to return it quoted.
    Bind verification to the artifact, not the summary. The model answers
    "what are the arms called" correctly for a paper whose numbers are a
    within-subject contrast; only the verbatim quote carries the SE label
    and the two timepoints that convict the numbers.
    Displayed claims nothing re-verifies (banner versions, test counts)
    decay silently. Parse them live from the source of truth or do not
    display them.
    When a fix cuts an input cap, re-check every downstream judgment stage:
    richer screening/RoB2 input is usually better input, but detection
    windows (garble checks) silently narrowed with the budget.

======================================
NEXT SESSION PRIORITIES
======================================
1   [PARTIALLY DONE at session end: suite run in the real venv - 430
    passed, 3 skipped, 11 deselected; the two clean-case tripwire
    assertions were updated to the always-set contract and committed.
    REMAINING:] port this session's harness scenarios into committed
    tests: source-quote check
    (zsy234 quote fires SE+timepoint; clean quote stays clean; number-not-
    in-quote; missing-quote), sentinel labels (3 cases incl. suppression),
    screener retry (3 cases incl. 403-no-retry), screening accounting
    partition, OCR budget early-stop for both tools. Also closes #49.
2   Pull run 20260826_113816's extracted_data.csv: read
    primary_outcome.source_quote_* for Ang (which table/timepoint does the
    -0.248 set come from? - resolves the bimodality) and Jensen (rounded
    values vs the quote's printed values). Use the quotes as ground truth
    for #23's corpus fixtures.
3   Decide zsy234's disposition (#19) - now backed by 5 flags: exclude with
    a documented PRISMA reason, or enter reviewer-verified between-group
    values via study_overrides.yaml.
4   REVIEWER_GUIDE.md: add source_quote_warning to the mandatory checklist;
    document run_id and the [SCREENING] accounting block; note the
    Anthropic-path tripwire gap (#61).
5   Fix check_no_bom.py's scan root (#60), run strip_bom across tests/ and
    scripts/, then wire into CI (#36).
6   [PARTIALLY DONE at session end: the five v2.4.12 commits are made
    locally, c5d222b..2527a0f, in exactly the suggested split.
    REMAINING:] git push, then WATCH GitHub Actions (expect 430 passed)
    and the Render deploy to completion - NEITHER has been exercised
    since Session 10; a divergence from local results is a finding.
7   ROTATE API KEYS (outstanding since Session 9), delete %TEMP% files, set
    spend limits.
8   Docker end-to-end (#19/HANDOFF, unchanged since Session 10); macOS
    launchers (#27/#39).
9   #18 CMap decode - now confirmed on all five papers and still the likely
    root of #17; a fixed +1 offset decode before the OCR fallback would give
    every stage a clean text layer and likely stabilize extraction.
10  The venv shell banner (activate script) hardcodes "v2.4.6" - a third
    baked-in version string, observed in Session 14's terminal logs after
    the launcher banner was fixed (#53). Apply the same parse-live pattern
    or drop the version from that banner. NOTE also: the merged HANDOFF.md
    itself picked up a UTF-8 BOM during the Session 14 paste-merge
    (stripped in the same commit) - the fourth BOM found outside
    SOURCE_CODE/ this session, reinforcing #60.

Handoff prepared: 2026-08-26 - Session 14 - merged into HANDOFF.md; this
document is the single source of truth for Session 15. Session 13's
handoff follows below unchanged as the historical record.


======================================
Version 2.4.11 — Real-Corpus Verification of Session 12's Tripwires, audit_logger.py Fix, Group-Label Follow-Up
======================================

Date: 2026-08-18 (Session 13, following Session 12) Repository: https://github.com/KW75/AI_kcMedicalResearch Live App: https://ai-kcmedicalresearch.onrender.com Health Check: https://ai-kcmedicalresearch.onrender.com/_stcore/health Uptime Monitor: UptimeRobot, 5-minute interval, keeps free-tier Render instance warm Tests: 423 passed, 3 skipped, 11 deselected (unchanged this session - no new tests were written or run against the real project venv; the new group-label follow-up mechanism has NO regression test, see #49) Coverage: ~53% (not re-measured this session) Current Status: local test suite green at 423 (not re-run this session, no changes to tested code paths); SR pipeline run successfully end-to-end against the real 5-paper corpus for the first time since Session 12's tripwires were added

CRITICAL READ FIRST (1): Session 10's confidentiality fix, Session 11's regression tests. Unchanged this session.

CRITICAL READ FIRST (2): Session 12 added three SR-pipeline tripwires (#13 plausibility, #9/#15 SD/SE, #10/#16 group/timepoint) but explicitly stated they had only been verified via unit tests and code tracing, never against a real pipeline run. Session 13 did that verification. READ THIS CAREFULLY: #13 (plausibility) is the ONLY one of the three that has actually caught the documented zsy234.pdf failure in a real run, twice. #9 (SD/SE) has not yet been exercised against that paper at all - it keeps succeeding via vision, never reaching the text-fallback path the tripwire is scoped to. #10 (group/timepoint) was extended this session with a group-label follow-up mechanism, which works exactly as built - but what it verifies turned out to be shallower than what actually matters: it confirms a trial's arm names, not whether the specific numbers already extracted belong to a between-group comparison of those arms. zsy234.pdf's follow-up returned genuinely correct arm names (CBT-I, WLC) while the underlying suspect numbers were completely unaffected. Do not treat #9/#10 as resolved, or their current mitigations as sufficient, based on this session's work. #13 is currently the only thing standing between this specific known failure mode and a silently-accepted pooled estimate.

======================================
1. PROJECT OVERVIEW
======================================
AI kcMedicalResearch is a local-first Python application providing six specialised AI pipeline modes for medical research workflows. It supports multiple LLM providers, local and cloud inference, multi-agent iteration loops, file-based input/output, Docker deployment, checkpoint/resume, streaming CLI output, and a Streamlit web UI.

Target Users: Medical students, clinical researchers, academic writers. Default Provider: DeepSeek, configurable via .env DEFAULT_PROVIDER. Fallback Chain: DeepSeek → Qwen → Groq, configurable via FALLBACK_PROVIDERS. Live UI: https://ai-kcmedicalresearch.onrender.com

======================================
2. SESSION HISTORY
======================================
Session 1 — 2026-08-10 — v2.3.0: SOURCE_CODE Restructure and Docker

    Complete project reorganisation into SOURCE_CODE/ structure.
    Cross-platform Docker support; Windows/macOS one-click setup scripts.
    Test suite expanded from 127 to ~243 tests. Coverage ~26% → ~50%.
    Render.com deployment configured.

Session 2 — 2026-08-11 — v2.3.1: Stability and Auto-Detection

    Recovered from destructive commit via hard reset 62e412c → 9aef3e6.
    Launcher fix: removed CREATE_NEW_PROCESS_GROUP.
    Ollama auto-detection; Qwen → qwen-plus-latest; LLM timeout 5 → 15 min.
    MAX_ITERATIONS 5 → 3. Default provider Ollama → DeepSeek.
    Tests: 275 passed, 6 skipped.

Session 3 — 2026-08-13 — v2.4.0 to v2.4.1: CI/CD, Fallback, Streaming, Monitoring

    GitHub Actions CI fixed (Python 3.11, build-essential, cmake, python3-dev).
    pysqlite3 monkey-patch; conditional pytesseract import; live tests marked.
    Provider fallback chain (DeepSeek → Qwen → Groq, transient errors only).
    Streaming default on; --no-stream flag. Render health check + UptimeRobot.
    Actions updated to checkout@v5 / setup-python@v6.
    Removed 12 debug scripts, a backup file, and orphan scripts/.venv.
    Tests: 362 passed, 3 skipped, 11 deselected. CI green.

Session 4 — 2026-08-14 — v2.4.2: Render Recovery and Dashboard Configuration Fix Render repeatedly failed with "Exited with status 1" while the live app kept serving the last successful deploy. Root causes: dashboard used manual settings not render.yaml; Build Command installed requirements.txt (Windows-only pywin32306); default Python 3.14.3; Start Command pointed to old src/ui/app.py; a partial Start Command began with $PORT. Final fixes: PYTHON_VERSION=3.11.9; Build Command uses requirements-render.txt with --only-binary=:all: plus separate docx2txt0.8; Start Command uses SOURCE_CODE/ui/app.py; health endpoint verified returning ok.

Session 5 — 2026-08-14 — v2.4.3: Test Suite Repair, Coverage, Cleanup

    Fixed 7 failing tests in test_main_coverage.py (blocked on input(); asserted on run_* functions main() never calls). Fixed by mocking input with task + KeyboardInterrupt, asserting on call_ai.
    Mocked utils.rag.index_uploads (removed ~113s of real PDF embedding); file runtime 121s → 8s.
    Added TestSessionManagement (16 tests) + interactive-loop tests for all six modes.
    main.py coverage 36% → 41%; suite 362 → 400; overall ~53%.
    Removed dead code cli.py, session.py; removed duplicate sr/src/ui files; resolved project_layout.py escape-sequence warning; removed scratch files + empty data/ folder.

Session 6 — 2026-08-14 — v2.4.4: SR Import Crash, Output Path, Cleanup

    Fixed SR pipeline ImportError (relative import with no parent package). Fixed by adding init.py across the package tree and switching Step-5 subprocess call in run_sr_launcher to python -m SOURCE_CODE.pipelines.sr.main with cwd=BASE_DIR.
    Fixed SR output landing under SOURCE_CODE/ (project_layout.py used five .parent hops; changed to six). Outputs now write to root reports/sr/<run_id>/ + mirror output/sr/.
    Routed rct_search output into reports/rct_search/; removed unused reports/systematic_review/ startup entry.
    Cleanup: removed stale SOURCE_CODE/docs/ (26 files), main.py.bak, leftover SOURCE_CODE/output and SOURCE_CODE/reports.
    Verified full SR run completes all 6 stages. Committed aa0f210, pushed, Render green.

Session 7 — 2026-08-15 — v2.4.5: Vision-Model Regression Fix, Prompt & Dead-Code Cleanup

    #9 (resolved) — Replaced hardcoded qwen3.7-plus in outer _DEFAULT_MODELS and wired model constants from providers.py (commit 3c2e51b).
    #3 (resolved) — Added -m invocation regression test guarding against the Session 6 import crash (commit 4b793ea).
    #11 (resolved) — Fixed stale pipelines/sr/outputs path in run_sr_launcher completion message; now points to real mirror paths output/sr/reports + output/sr/figures and adds HTML output line plus per-run audit-folder pointer (commit a83ec1c).
    Test hygiene (resolved) — test_sr_pipeline_dry_run no longer overwrites the real prisma_criteria.yaml; writes to pytest tmp_path (commit 5d6a8ca). Eliminates the recurring git restore step after full test runs.
    Vision regression (NEW issue, resolved) — After #9, the SR launcher resolved qwen to QWEN_MODEL = qwen-plus-latest, which is text-only, so all vision extraction returned empty (0/5 papers extracted, meta-analysis aborted with "< 2 studies"). Root cause: the qwen provider is marked vision-capable but its default model is not. Fixed by adding QWEN_VISION_MODEL (env QWEN_VISION_MODEL, default qwen-vl-max) in providers.py and pointing the SR launcher's _DEFAULT_MODELS["qwen"] + fallback default to it. Text modes keep QWEN_MODEL. Verified: 4/5 papers extract without a --model flag, pooled SMD ≈ −0.715 [−1.958, 0.528], I² ≈ 94.4%, forest plot + DOCX/HTML generated (commit 9c536e1).
    Prompt cleanup (resolved) — Investigated whether the top-level prompts/ folder was unused. Confirmed it is load-bearing: 14 of 15 files are referenced by the agent registry in main.py (AI_DIR / "*-prompt.md") and by rct_search.py. Deleting the folder would silently break every agent at runtime (not caught by tests). Removed only the one genuine orphan, prompts/sr-methodologist-prompt.md — referenced nowhere in code, tests, or the SR subtree (commit b1f4c48).
    Dead-code cleanup (resolved) — Removed the never-called get_prompt() / get_prompt_path() helpers from path_utils.py (agents load prompts via explicit AI_DIR paths, not this dynamic helper). Added sr_*.log to .gitignore (commit 1b6b9b0).
    Tests throughout: 401 passed, 3 skipped, 11 deselected. All commits pushed to main.


Session 8 — 2026-08-17 — v2.4.6: SR Extraction Provenance, Generic Overrides, Reviewer Guide

    #1 (resolved) — Lami extraction (s10608-017-9875-4.pdf). Text fallback now recovers Table 4 and the study is included. The metadata label was a separate bug: study_metadata was written nowhere in the codebase (only referenced in the prompt template at data_extractor.py:35), while corrections wrote top-level first_author. Reporting and Stage 4 read the nested block, so the forest plot showed "Hedges g for None". Fixed by mirroring resolved first_author/year into study_metadata before every return path of _apply_known_pdf_corrections.
    Dead code (resolved) — The except handler in extract_by_pdf_path spent 36 lines populating result["first_author"] etc., then returned a freshly-constructed dict that discarded all of it. Never had any effect. Removed.
    Hardcoding removed (resolved) — Lami-specific corrections had accumulated across three places in data_extractor.py, including numeric-signature matching (self._near(mi, 7.35) and self._near(sdi, 2.08) ...) that fired only when extraction was already correct and stayed silent exactly when it was wrong. On one run extraction returned 7.32/1.80, the signature missed, sample sizes were never set, and the study was dropped with "insufficient mean/SD/N". All of it replaced.
    New module (added) — SOURCE_CODE/pipelines/sr/src/extraction/study_overrides.py. Two mechanisms: resolve_pdf_metadata() derives first_author/year/doi from the PDF (PyMuPDF metadata, DOI regex, copyright-line year) for any paper; StudyOverrides applies reviewer-verified values from input/sr/study_overrides.yaml keyed by filename. Metadata fields fill only when blank; numeric outcome fields replace extraction output. Unknown YAML fields are rejected with a warning.
    Provenance (added) — Overrides that change numeric values log at WARNING. End of Stage 3 prints a DATA PROVENANCE SUMMARY listing every study that used overrides or auto-derived metadata. Per-field audit distinguishes field(7.32->7.35) (corrected), field(confirmed 7.35) (extraction independently agreed), and field(absent->7.35). Extraction still runs in full for overridden studies specifically to preserve the "confirmed" cross-check.
    McCrae invalid effect size (NEW issue, unresolved) — zsy234.pdf was contributing g = -2.356 [-2.853, -1.859] and driving the entire pooled estimate (SMD -0.514, I2 93.9%). Decoding the PDF text layer showed the source reads: "There were no significant group by time interactions for the morning and evening pain ratings ... Regardless of treatment condition, participants reported less morning pain at posttreatment (M = 47.14, SE = 2.36) relative to baseline (M = 52.67, SE = 2.27)". Three simultaneous errors: SE read as SD; a within-subject main effect of time read as a between-group contrast; group Ns fabricated by summing two arms (39+37=76) of a three-arm trial. The paper reports NO significant treatment effect on pain. Nothing in the pipeline flagged any of this.
    Broken font CMaps (NEW issue, unresolved) — All five test PDFs trigger "Garbled text detected - switching to OCR". The text layer is not garbled; it has a broken CMap with a fixed +1 character-code offset. "LbBq]d ds ]k-" decodes to "McCrae et al."; digits are shifted too, which is why searching for the literal "47.14" found nothing. The pipeline OCRs documents that have a clean recoverable text layer, likely the upstream cause of the extraction instability.
    Extraction non-determinism (NEW issue, unresolved) — Same PDF, same code, different values across consecutive runs. Lami returned 7.35/2.08/n=28 on one run and 7.32/1.80/n=absent on the next. Ang's CI moved between runs with no code change affecting it. 2 of 5 papers observed unstable; the other 3 are unverified rather than verified.
    Documentation (added) — Readme/REVIEWER_GUIDE.md: mandatory manual verification checklist, the two documented failure modes as worked examples, include/exclude decision rules at the extraction gate with PRISMA exclusion reasons, override file usage rules, and a minimum reporting statement for a methods section.
    Repo hygiene — .gitignore rewritten so input/ stays ignored but input/sr/study_overrides.yaml and input/sr/pico_sample.json are tracked (a bare negation does not work when the parent directory is excluded; git never descends into it). Test corpus PDFs removed from input/sr/ as copyrighted. Debug logs cleared.
    Tests: 401 passed, 3 skipped, 11 deselected throughout.


Session 9 — 2026-08-17 — v2.4.7: API Key Leak, Startup Performance, Launcher Repair

    SECURITY (resolved) — The Streamlit UI wrote every API key into a generated .bat as `set "KEY=value"` lines. cmd echoes each line, so all keys were printed on screen at every launch, and the file persisted in %TEMP% in plaintext. Popen was ALREADY passing env=env_vars, so the child inherited the keys regardless — the set lines were pure redundancy. Removed them, added @echo off, changed cmd /k to cmd /c (the script already ends with pause). The same redundant interpolation existed in the macOS and Linux launchers, where keys were additionally visible in ps output; removed there too. NOTE: keys exposed during this session must be rotated at the provider consoles — clearing .env does not invalidate them.
    Startup performance (resolved) — Startup was 15-20s. Profiled with `python -X importtime`: utils/__init__.py eagerly imported .rag (chromadb) and .document_reader (pymupdf, docx2txt), so `from utils.path_utils import ...` — three trivial path helpers — pulled the entire RAG and document stack, ~2.2s, on every run including every test. Converted to lazy loading via PEP 562 __getattr__. Public API unchanged; `from utils import DocumentReader` still works. Startup ~20s -> ~7s; test suite ~45s -> ~19s. Remaining chunks: providers ~2.2s (includes the module-scope Ollama probe, Issue #10) and pipelines.sr.main ~2.8s imported even for coding mode — same lazy treatment applies.
    Windows launchers (resolved) — UI launcher opened TWO browser tabs: --server.headless=false makes Streamlit open one itself, and the script also ran `start "" "http://localhost:8501"` after a fixed 3s ping wait — well before the ~7s startup, so that tab hit connection-refused. Removed the manual start. Both launchers now propagate the real exit code instead of always 0, check for the target script before venv setup, and upgrade pip before installing requirements.
    macOS launchers (resolved) — Three fixes. (1) OLLAMA_HOST was http://localhost:11434 while running inside Docker, where localhost is the container, not the Mac; Ollama was unreachable from all three scripts despite --add-host host.docker.internal:host-gateway. Now overridden per-container with -e OLLAMA_HOST=http://host.docker.internal:11434. (2) Mac_Setup.sh baked a private DashScope workspace endpoint (ws-uv5pi4kkqbrg1vpe...) into every colleague's generated .env; replaced with the generic intl endpoint. (3) QWEN_VISION_MODEL was absent from the generated .env, so any Mac user running SR would hit the Session 7 vision regression. Also: browser now polls /_stcore/health before opening instead of firing `open` immediately; `set -e` replaced with `set -uo pipefail` so the existing `if [ $? -ne 0 ]` handlers actually run (with set -e the script exited first, making them dead code); added Docker-daemon and port-in-use checks; switched `docker images | grep` to `docker image inspect` (grep matched substrings).
    .gitattributes (resolved) — Every rule still targeted the pre-v2.3.0 src/ tree and none covered *.sh. With core.autocrlf=true, shell scripts were being stored CRLF, which breaks the shebang on macOS ("bad interpreter: /bin/bash^M"). Rewritten for the SOURCE_CODE layout: LF forced on *.sh and source/config files, CRLF on *.bat/*.cmd/*.ps1, binaries marked binary. Applied repo-wide with git add --renormalize.
    .env.example (resolved) — Was 14 variables and stale. Missing the entire DashScope block, QWEN_VISION_MODEL, DEFAULT_PROVIDER, FALLBACK_PROVIDERS, SR_STUDY_OVERRIDES, and the Ollama tuning vars. Now 24 variables with comments on the vision-model requirement and the Docker localhost trap. Removed stale OLLAMA_MODEL=qwen2.5-coder:3b (the app auto-detects).
    Renamed scripts/windows/"PWD_activate virtual enviroment.bat" -> activate_venv.bat (space in filename, misspelling). Now fails clearly if .venv is absent, narrows -ExecutionPolicy Bypass to RemoteSigned, drops the dead pause (-NoExit already holds the window), and prints the resolved interpreter after activating — a direct diagnostic for the observed case where the prompt showed (.venv) while python resolved to C:\Users\user\...Python311.
    Tests: 401 passed, 3 skipped, 11 deselected throughout.
    Commit trail: 190ec9e (v2.4.6 docs + SR overrides) -> fb7b5ce (Windows launchers) -> ab77bb5 (lazy imports, key leak, macOS launchers, .gitattributes).


Session 10 — 2026-08-17 — v2.4.8: Confidentiality Fix, BOM Cleanup, Python Gate

    CONFIDENTIALITY (resolved, most serious defect found to date) — The app is intended to let clinicians process patient data locally via Ollama; every other provider transmits the prompt to an external API. But call_ai_with_fallback built its chain as `[provider] + [p for p in chain if p != provider]`, so an explicit --provider ollama became [ollama, deepseek, qwen, groq]. "timeout" and "connection" are both in _TRANSIENT_INDICATORS, and the project's own notes record that large Ollama models time out frequently on the coding and writing pipelines. So a routine local timeout sent patient data to DeepSeek, printed "[fallback] Succeeded with deepseek" among hundreds of log lines, and completed as though the run were normal. Fixed by introducing LOCAL_ONLY_PROVIDERS = {"ollama"}: requests to a local provider never fall back, and the resulting error states explicitly that nothing was sent to a cloud API. The "trying next..." log line is now conditional on a next provider existing. Verified by injecting a failing call_ai: ollama tried ['ollama'], deepseek tried ['deepseek','qwen','groq'].
    UTF-8 BOMs (resolved) — 23 files under SOURCE_CODE/ began with EF BB BF. Python tolerates a BOM on import so the code ran, but ast.parse() rejects it and, combined with an encoding mismatch, it renders as garbage characters. This is what earlier notes recorded as "corrupted Chinese comments" in sr/main.py and project_layout.py — not corruption, a BOM. Note some were self-inflicted: PowerShell 5 `Set-Content -Encoding UTF8` writes a BOM, and files generated that way during Sessions 8-9 acquired one. Added scripts/check_no_bom.py and scripts/strip_bom.py; check_no_bom.py should be wired into CI.
    Python version gate (resolved) — A clean install on Python 3.14 (now the python.org default) fails across pywin32 306, textract 1.6.5, pillow, opencv-python 4.8 and pymupdf, taking hours to diagnose from pip and import errors. main.py now checks the interpreter before any third-party import — critically, above `from dotenv import load_dotenv`, or the user hits ModuleNotFoundError first — and exits with the supported range, the detected version and path, a Python 3.12 download link, and the Docker alternative. Decision: support 3.11-3.12 rather than raise floors on numpy/scipy/pillow/pymupdf and gamble on chromadb wheels for an interpreter that cannot be tested here.
    Requirements split (resolved) — requirements-base.txt now holds the 18 shared runtime deps, referenced by requirements.txt and requirements-ci.txt via -r. requirements-render.txt deliberately left standalone and pinned: it had just recovered from a failed deploy and mixing floors with pins for marginal DRY benefit was not worth destabilising it. New requirements-ocr.txt holds the optional OCR stack. Key finding: the OCR packages were installed but could not work — the Dockerfile apt-gets only curl and wget, so no Tesseract, no Poppler, no libGL for cv2 — meaning ~2GB of PyTorch via easyocr bought nothing. Also resolved duplicate conflicting pins (python-docx >=1.0.0 vs ==1.1.0; pillow >=9.0.0 vs Pillow==10.1.0, where last-wins made the floors decorative) and dropped textract.
    Docker consolidation (resolved) — Nine files in docker/ reduced to two: Dockerfile and docker-compose.yml. The six deleted run scripts each carried their own copy of the docker run command, which is why the same bugs appeared six times over. Dockerfile now installs requirements-base.txt. Discovered in the process that Docker_setup.bat — the advertised one-click Windows setup — was non-functional: unescaped parentheses in echo text inside if-blocks (lines 110, 256, 288, 289) close the block early, so cmd exits with "was unexpected at this time" before any Docker command runs. mac_docker_setup.sh called goto_run_app, a leftover from batch translation that is not a bash construct and, under set -e, exited the script on the update path. Neither could ever have completed a setup.
    Docker still UNVERIFIED — Docker is not installed on the dev machine, which is why none of the above was ever caught. Nothing Docker-related has been executed: not the build, not either compose service, not the .env-exclusion check. This is the gate before pointing colleagues at that route (Issue #19).
    Windows/macOS launchers (resolved in Session 9, verified Session 10) — activate_venv.bat now prints the resolved interpreter after activating; confirmed D:\AI_kcMedicalResearch\.venv\Scripts\python.exe, 3.11.9. The earlier sighting of C:\Users\user\...Python311 was a non-activated shell, not a broken venv.
    Launcher parity (resolved) — Windows and macOS launchers shared filenames but not mechanisms: AI_kcMedicalResearch_CLI.bat ran the project virtualenv while Mac_kcMedicalResearch_CLI.sh ran `docker run`. Anyone comparing or documenting them together was describing two different things, and the setup instructions did exactly that. Both macOS launchers are now venv-based mirrors of their Windows counterparts: they create .venv from the first available Python 3.11/3.12, refuse with a `brew install python@3.12` hint plus the Docker alternative if neither is present, warn when .env is missing, run in the foreground so PICO prompts get a TTY, and return the real exit code. The UI launcher also checks port 8501 with lsof and lets Streamlit open the browser itself. Deleted Mac_Setup.sh, the macOS half of the Docker setup pair whose Windows half was already gone. Confirmed no setup script is needed at all: PATH_MANAGER creates input/, output/, reports/ and docs/ per mode via mkdir(parents=True, exist_ok=True) on import (path_utils.py:74-89), and everything else the scripts did is three documented commands.
    Documentation (resolved) — Setup_Instructions_for_Users.txt previously led with the hosted app as "the right choice for most people" with no confidentiality warning, in a tool intended for patient data. It now states plainly that the hosted app must not be used for confidential or patient-identifiable input, and the Providers section carries the Ollama local-only guarantee, the pre-v2.4.8 caveat, and the note that SR works on published papers so a cloud provider is appropriate there. Also documents the platform launchers, the version-gate message, and the BOM check.
    Commit trail: f0b678e (local-provider fallback) -> 1541b09 (requirements split, compose, docs) -> c851259 (delete broken setup scripts) -> 5439ede (BOM strip + guards) -> f64d84d (Python version gate) -> e332b3b (v2.4.8 docs) -> 8d2e110 (launcher parity, delete Mac_Setup.sh).

Session 11 — 2026-08-18 — v2.4.9: Startup Reliability, Provider Lazy-Init, PICO/UI Parity, SR Plausibility Flag

    Startup crash on Ctrl+C (resolved) — main.py's entry-point try/except KeyboardInterrupt only wrapped code inside `if __name__ == "__main__":`. The document_reader -> pytesseract -> pandas import chain runs at module load, before that block starts, so Ctrl+C during the ~7s cold start (a routine action per the on-screen tip "Press Ctrl+C ... to stop and return here") fell through to a raw traceback through pandas internals instead of the clean "Session stopped. Returning to menu..." message. Fixed by wrapping the import block in its own try/except KeyboardInterrupt with the same message.
    No wait notice during slow provider calls (resolved) — A user report showed the CLI appearing to hang for 15s+ after selecting Ollama, with real risk of an impatient Ctrl+C mid-generation. call_ai() now prints a visible notice ("Pulling LLM..." for Ollama, a lighter version for cloud providers) before dispatching, gated on sys.stdout.isatty() to stay silent in non-TTY/CI runs.
    #26 (RESOLVED) — pipelines.sr.main (~2.8s: scipy, matplotlib, pymupdf) was imported unconditionally at the top of main.py via `from pipelines.sr import run_sr`, alongside three sibling imports (run_coding, run_writing, run_search) — none of which were referenced anywhere else in the file. Every real handler (handle_coding_mode, handle_writing_mode, handle_search_mode, run_sr_launcher) already does its own local import from a different submodule path when it actually needs one. Deleted the four dead imports; every mode now only pays for the pipeline it actually uses.
    Provider-select box misalignment (resolved) — scripts/launcher.py's SR provider table used a Unicode checkmark (✓) for vision-capable providers and plain "x" for non-vision ones, padded with hand-counted trailing spaces. On a CJK-locale terminal, ✓ is an ambiguous-width character and renders as 2 columns instead of 1, so every checkmark row was a column wider than its character count implied — throwing the right-hand border out of alignment. Root-caused by testing the byte-length assumption directly rather than guessing at font metrics. Fixed by replacing ✓ with a plain-ASCII "+" and padding every badge variant to the same fixed width via ljust on the plain text before adding color codes.
    #10 / #25 (RESOLVED, same root cause) — providers.py auto-detected the best Ollama model at import time unconditionally, for every provider, every run: `if not OLLAMA_MODEL: OLLAMA_MODEL = _ollama_detect_best_model(OLLAMA_HOST)` at module scope. This did a live network probe (bounded by a 5s timeout, but still a latent hang per #25's own framing) and printed "[ollama] Auto-detected..." even on a pure Qwen SR run that never touches Ollama (#10's "cosmetic" framing undersold it — a network call during import is not merely cosmetic). Fixed by moving resolution into _resolve_ollama_model(), called lazily from call_ollama_provider() on first actual use. get_default_model("ollama") now returns "(auto-detected on first use)" instead of triggering the probe just to answer a status-display query.
    #34 (RESOLVED) — _is_transient_error matched the bare substring "connection" against the lowercased error message, so an auth error whose text happened to contain that word anywhere (e.g. a gateway saying "connection refused by auth proxy") would be misclassified as transient and incorrectly retried against a fallback provider — a mechanism that could have reopened the exact confidentiality hole #29 fixed in Session 10, since Ollama's own connection-failure messages contain that phrase. Fixed by parsing the actual HTTP status code when the message contains one (401/403 are never transient, full stop, regardless of wording) and falling back to a small set of specific phrases — the precise "connection error" (what this module's own URLError handlers actually produce), not the bare word "connection" — only when no status code is present.
    #35 (RESOLVED) — Added tests/test_provider_fallback.py: four regression tests covering (1) Ollama failure never reaching a cloud provider, (2) normal cloud-to-cloud fallback still working, (3) the #34 auth-error-mentions-"connection" edge case specifically, (4) import of providers.py doing no network I/O. Verified locally with a hand-rolled monkeypatch harness (no pytest available in the sandbox that authored the fix) before handoff; re-run and confirmed passing (4/4) in the real project venv.
    #13 (RESOLVED, verified not reproducible) — Checked SOURCE_CODE/pipelines/sr/main.py's --model argparse default directly: `default=None`, threaded through unchanged to every extractor/screener/assessor call (args.model appears 4 times, always passed straight through). No hardcoded qwen3.7-plus found anywhere in the file. Matches the documented QWEN_VISION_MODEL auto-resolution path from Session 7. Downgrading from "Open — verify" to RESOLVED.
    #14 (RESOLVED) — test_main_coverage.py hardcoded a nested prompts/<mode>/<role>.txt layout (e.g. 'prompts/coding/builder.txt') that has never existed on disk. Cross-checked against ALL_MODES in main.py, which builds every real prompt path as AI_DIR / "<role>-prompt.md" (flat, no mode subfolder) — e.g. Appraiser's file is "appraisal-prompt.md", not "appraiser-prompt.md" as the role name would suggest. All five reachable mode/role pairs corrected. Side finding, NOT yet fixed: ALL_MODES has no "sr" key at all — SR mode is dispatched straight to run_sr_launcher() at the entry point and never reaches choose_role(). test_main_sr_mode currently only "passes" because choose_role is fully mocked; with the mock removed it would raise KeyError on ALL_MODES['sr']. Tracked as new issue #43 — needs a decision (redesign the test to assert SR routes to run_sr_launcher, or drop it) rather than a code fix.
    #20 (RESOLVED) — Added an effect-size plausibility check to sr/main.py: |Hedges g / SMD| > 1.5 (the exact threshold this document's own #20 entry names) or OR/RR beyond 10x / below 0.1x. Does NOT auto-exclude the study — an unusual value might be genuine — it writes a plausibility_flag column into results_csv and prints a summary block at the end of Stage 4 listing every flagged study, feeding the manual-verification workflow #15/#16 already mandate. This is a tripwire for the zsy234-class failure (g=-2.356, would have been flagged), not a fix for #15/#16 themselves — those require actual SD-vs-SE and within/between-group detection logic, which is unimplemented.
    #21 (RESOLVED, description corrected) — This document's own entry read "Streamlit UI globs output/rct_search/, CLI globs input/sr/" — checked both files directly and that's not accurate. rct_search.py's CLI actually checks input/rct_search/pico_*.json first, falling back to output/rct_search/pico_*.json (never input/sr/ — that path is INPUT_SR, used only for a one-way opt-in copy-to-SR-input step, not read back for PICO discovery). app.py's UI checked output/rct_search/ only. The real gap: a PICO JSON existing solely in input/rct_search/ (e.g. manually placed) was invisible to the UI. Fixed app.py's _get_all_pico_files() to check both locations, merged and deduped, with input/rct_search/ winning on a filename collision to match the CLI's own precedence.
    #24 (RESOLVED, risk narrowed) — Verified the actual data flow before treating this as a straightforward fix: st.session_state is per-browser-session in Streamlit's execution model, not shared server-wide as this document's own framing implied ("i.e. into the server process"). _get_env_with_api_keys() does `os.environ.copy()` (never mutates the real os.environ) and the result is only ever passed via subprocess `env=`, never written to disk or echoed — confirmed the Session 9 .bat-file leak fix is durable and has an explicit guard comment against reintroducing it. The genuine remaining risk is narrower: an entered key sits in server-side session memory as plaintext for the whole session's lifetime with no way to clear it early. Added a "Clear stored keys" sidebar button; had to also reset each provider's text_input widget state (st.session_state.pop(f"api_{provider}")), not just the api_keys dict, since Streamlit repopulates api_keys from the still-filled widgets on the very next rerun otherwise.
    Local test suite: 405 passed, 3 skipped, 11 deselected (up from 401 — the four new tests in test_provider_fallback.py account for the difference). Commit trail (7 commits, one per file): 3bcecb4 (main.py: KeyboardInterrupt handler, wait notice, #26) -> d328b42 (launcher.py: box alignment) -> f032dc2 (providers.py: #10, #25, #34) -> 644365c (test_provider_fallback.py: #35) -> 43fc085 (test_main_coverage.py: #14) -> f40ee69 (app.py: #21, #24) -> c4aec59 (sr/main.py: #20).
    NOT done this session, still needs a human decision: whether to redesign test_main_sr_mode (#43), and everything in "IMMEDIATE ACTIONS BEFORE NEXT SESSION" below — none of it was touched this session (key rotation, temp-file deletion, spend limits, venv verification, macOS launcher testing).

Session 12 — 2026-08-18 — v2.4.10: SR Extraction Tripwires, Cross-Platform OCR Fix

    Cross-platform Tesseract path (RESOLVED) — relevance_screener.py and rob2_tool.py both hardcoded pytesseract.pytesseract.tesseract_cmd to a Windows-only absolute path (C:\Program Files\Tesseract-OCR\tesseract.exe), unconditionally, in both files. On macOS/Linux/Docker this silently broke the OCR fallback entirely regardless of whether Tesseract was actually installed and working there - not a "package installed but unusable" problem like #24 in this document's numbering, a straight-up wrong-path problem masking as one. Fixed in both files: only overrides tesseract_cmd on Windows, and only if that default path actually exists; otherwise defers to pytesseract's normal PATH-based discovery (the correct behavior on macOS/Linux where Tesseract is installed via apt-get/brew).
    RoB2Assessor stale model default (RESOLVED) — Constructor defaulted to model="qwen3.7-plus", which matches nothing in providers.py's model registry (QWEN_MODEL=qwen-plus-latest, QWEN_VISION_MODEL=qwen-vl-max). Currently unreachable via the documented pipeline since sr/main.py always passes model=args.model explicitly (even when that's None), but a landmine for any direct construction that omits model - would send a request to Qwen naming a model that doesn't exist. While fixing this, found assess_by_pdf_path() only ever calls _call_with_text() - _call_with_images() exists on this class but is never invoked from any code path, dead code. Confirms the text model, not a vision model, is the correct default here (my first attempt got this wrong, assumed vision was needed without checking which method actually gets called - corrected before committing). New default: qwen-plus-latest.
    #9/#15 SD/SE tripwire (MITIGATED, not resolved) — The only existing SE-vs-SD guidance lived in _text_extraction_prompt() (the fallback path); EXTRACTION_PROMPT_TEMPLATE (the primary vision path, run first on every paper) had no such instruction at all. Added the same warning to both prompts. More importantly, added a deterministic post-hoc check, _flag_possible_se_as_sd(): on the text-fallback path only (needs literal source text to check against - the vision path has no text), flags any value extracted into sd_intervention/sd_control that shares a source line with the literal word "SE"/"SEM"/"standard error". Tested directly against the documented zsy234 failure text ("M = 47.14, SE = 2.36") - fires correctly on both intervention and control values, stays silent on a clean SD-only negative control. Sets result["sd_se_warning"] (top-level, not nested in primary_outcome - the extraction restructuring step doesn't move this key, unlike the fields it does know about). Wired into sr/main.py: audit_row gets a new sd_se_warning column, results_csv carries it, console prints a [SD/SE CHECK] summary block at end of Stage 4, same pattern as the #13/#20 plausibility flag from Session 11. Does NOT catch every SE/SD confusion - only the specific same-line co-occurrence pattern, and only on the text-fallback path.
    #10/#16 group/timepoint tripwire (MITIGATED, not resolved) — No existing check anywhere validated that a "group" label represented an actual randomized arm rather than a mislabeled timepoint - the exact zsy234 failure (baseline/posttreatment extracted as if they were intervention/control). Added _flag_group_timepoint_confusion(): two checks, both narrow and low-false-positive by design. (1) intervention_group or control_group contains timepoint vocabulary (baseline, post-treatment, follow-up, week N, T1/T2/T3, etc.) - real arm names essentially never look like this. (2) intervention_group and control_group are literally the same value - structurally impossible for a genuine between-group contrast. Called from _coerce_extraction_result, so it runs on BOTH extraction paths (vision and text-fallback), unlike the SD/SE check - it only needs the group labels the model already extracted, not literal source text. Tested against 8 cases including the exact zsy234 pattern (flags), two genuine two-arm trials with different naming conventions (stays silent), and a deliberate trap ("Waitlist Control" containing the word "Control" but no timepoint word - correctly stays silent). Wired into sr/main.py the same way as the SD/SE flag: group_timepoint_warning column, [GROUP/TIMEPOINT CHECK] console summary. Scope limit stated explicitly in the docstring: only catches mislabeling visible in the group NAME itself - a model that invents a plausible-but-wrong arm name (rather than reusing an obvious timepoint word) is not caught.
    Hardcoded trial-specific group matching (RESOLVED) — _infer_group_timepoint_from_text hardcoded three literal arm names from one specific trial (CBT-IP, CBT-P, UMC) with NO generic fallback - for every other paper, group_name stayed None and the function returned (None, None) unconditionally. This gave the appearance of general group-inference machinery while only ever working for the one study it was written against. Fixed by adding _collect_candidate_group_names(), which derives candidate arm names from whatever the model already extracted for THIS specific paper (intervention_group/control_group fields, or group/arm/name/label values inside any groups_n_by_timepoint-style rows) instead of hardcoded literals. Verified both that the original trial still matches correctly (now driven by data, not string literals) and that a completely different trial's arm names - previously impossible to match at all - now work. Separately reviewed _sample_size_from_text_for_group, which ALSO hardcodes those same three literal names: left it alone and just documented why it's safe - its hardcoding only activates when group_norm exactly equals "cbtip"/"cbtp"/"umc" (guarded), with a working generic substring-match fallback (`else: matches_group = group_norm in normalized_line`) already in place for everything else, unlike _infer_group_timepoint_from_text which had no fallback at all.
    New regression tests (added) — tests/test_data_extractor_flags.py, 18 tests covering all of the above: the SD/SE tripwire (3 tests, including the exact zsy234 text), the group/timepoint tripwire (8 parametrized cases + 1 wiring-integration check confirming it actually runs as part of _coerce_extraction_result, not just callable in isolation), and the generalized group-name matching (4 tests, including confirming the original hardcoded trial's paper still works and a different trial's names now match too). Import path required correction: initially wrote `from data_extractor import DataExtractor`, which doesn't match this project's actual package layout - confirmed against tests/test_sr.py's own import (`from pipelines.sr.src.extraction import data_extractor`) and corrected to `from pipelines.sr.src.extraction.data_extractor import DataExtractor`. All 18 pass against the real project venv (not just simulated logic) - local suite now 423 passed (up from 405), 3 skipped, 11 deselected.
    Files touched this session: SOURCE_CODE/pipelines/sr/src/screening/relevance_screener.py, SOURCE_CODE/pipelines/sr/src/screening/rob2_tool.py, SOURCE_CODE/pipelines/sr/src/extraction/data_extractor.py, SOURCE_CODE/pipelines/sr/main.py, tests/test_data_extractor_flags.py (new).
    Verification limits, stated plainly: everything in this session was verified by (a) synthetic unit-level tests exercising the isolated logic, later confirmed passing against the real project venv, and (b) tracing the actual code paths and call sites by hand. NONE of it was verified against a real SR pipeline run on real PDFs - no live extraction, no live provider call, no confirmation that these tripwires actually fire (or stay silent) on the five-paper test corpus this document's earlier sessions used. That is the natural next verification step before treating #9/#15 and #10/#16 as meaningfully de-risked in practice, not just in unit tests.

Session 13 — 2026-08-18 — v2.4.11: Real-Corpus Verification, audit_logger.py Fix, Group-Label Follow-Up

    First real pipeline run since Session 12's tripwires were added (diagnostic) — Ran the SR pipeline against the real 5-paper corpus. Every extraction call failed with "Connection error" (openai SDK's own retry/exception, not a bug in Session 12's new code - confirmed by the absence of any Python traceback pointing at data_extractor.py) and every RoB2 call got HTTP 404 from https://ws-uv5pi4kkqbrg1vpe.ap-southeast-1.maas.aliyuncs.com. That exact URL is the private DashScope workspace endpoint documented in Session 9 and removed from .env.example's DASHSCOPE_ANTHROPIC_URL in Session 11 - but the user's real .env (gitignored, never touched by any session's code changes) still had DASHSCOPE_BASE_URL pointed at it, a pre-existing dormant misconfiguration from before this project's Session 9-11 work, only surfaced now because this was the first time the pipeline was actually run after those sessions. NOT a regression from Session 12. User corrected their local .env; pipeline then ran successfully end-to-end (5/5 papers extracted, pooled SMD=-0.577, I2=93.6%).
    #47 (RESOLVED) — meta_analysis_results.csv was missing the plausibility_flag/sd_se_warning/group_timepoint_warning columns entirely, not just empty values - the columns themselves absent. Root cause: audit_logger.py's write_results() passes a hardcoded fieldnames list to csv.DictWriter(..., extrasaction="ignore"), which silently drops any dict key not in that list. The three new fields existed in every audit_row (wired in Session 12) but were never in write_results()'s fixed list. Fixed by adding the three names to the list. Verified against real pipeline output (not just a synthetic test) - the second real run's meta_analysis_results.csv shows all three columns present, with McCrae/zsy234's plausibility_flag correctly populated and the other four rows correctly empty. write_extracts() (Stage 3's extracted_data.csv) did NOT have this bug - it already builds columns dynamically via pandas from whatever keys exist per row.
    #9/#15 real-world test result (informational, not a fix) — zsy234.pdf succeeded via vision on the FIRST strategy on both real runs, never reaching the text-fallback path _flag_possible_se_as_sd is scoped to. The tripwire has not yet been exercised against the paper it was built for. This is not a bug in the tripwire - it is a real gap in what "text-fallback only" actually covers in practice, now confirmed rather than theoretical.
    #10/#16 group-label follow-up (added, but read the finding below before treating this as progress) — Real-world test on the first successful run showed EVERY one of the 5 papers had zero group-label data: no intervention_group, no control_group, anywhere, for any paper, including Lami (the one paper that went through text-fallback, where the schema explicitly requests these fields - the model simply didn't answer that part of the prompt). Built _fetch_group_labels_if_missing(): after usable outcome data is found on either extraction path, if group labels are still missing, fires ONE additional focused API call (reusing the same page images for vision, or the same extracted text for text-fallback) with a narrow prompt asking ONLY for the two arm names - explicitly instructing the model not to answer with a role description ("intervention"/"control") and not to answer with a timepoint, and to return null rather than guess. Re-runs _flag_group_timepoint_confusion() itself after the follow-up, since _coerce_extraction_result already ran once before labels existed to check - confirmed via test that even a bad follow-up answer (still a timepoint) gets caught by this re-run, not bypassed. New helper _call_chat_api_with_prompt() for text-only follow-ups (guarded to skip the Anthropic provider entirely, different client API). Verified via standalone logic simulation (4 scenarios: real gap detected, good follow-up resolves cleanly, bad follow-up still caught by re-run, model-declines case stays honestly unresolved) before wiring in - no regression test committed (see #49).
    SECOND real pipeline run (verification, and the important finding) — The follow-up mechanism worked exactly as built: fired for all 5 papers, [GROUP LABELS] log lines confirm real, plausible arm names came back for 4 of them (Ang: CBT/UC; Jensen: "CBT treatment"/"Control"; Karlsson: "CBT intervention group"/"Wait-list group"; McCrae/zsy234: CBT-I/WLC) and a correct None/None decline for Lami. None of the genuine names false-triggered the timepoint-vocabulary check, including the tricky "Wait-list group" case (contains no timepoint word). BUT: McCrae/zsy234's mean/SD values were IDENTICAL to every previous run (47.14/2.36 vs 52.67/2.27, matching to full float precision) - the follow-up call only ever asks "what is this trial's design," a question the model can answer correctly and easily from the abstract, completely independent of whether the SPECIFIC numbers sitting in mean_intervention/mean_control actually came from a between-group table or a within-subject one. CBT-I and WLC are zsy234's genuine, correct arm names - and the group/timepoint tripwire correctly found nothing wrong with them, because there is nothing wrong with them. The paper's actual documented failure (a within-subject pre/post contrast extracted as if between-group) is about where the NUMBERS came from, not what the trial's arms are called - a category the follow-up mechanism, as built, cannot detect. Only #13's plausibility bound flagged this paper, in both real runs, unchanged by anything built this session. Tracked as new #38 (CRITICAL, Open) rather than quietly left as an unstated limitation - a clean run through #10 now looks MORE reassuring than before this session's work, which is worse than not running it if a reader takes that silence as evidence of correctness.
    Files touched this session: SOURCE_CODE/pipelines/sr/src/utils/audit_logger.py, SOURCE_CODE/pipelines/sr/src/extraction/data_extractor.py.
    NOT done this session: no regression test for the group-label follow-up (#49); no fix for the deeper #38 gap (needs the model to quote/cite the specific source text a number came from, and a check that the quote doesn't contain timepoint language - binding verification to the numbers, not just the labels); #9 remains unexercised against its target paper in any real run.

======================================
3. CURRENT STATUS
======================================
Component 	                      Status 	                Details
GitHub Actions CI 	              not re-verified 	      Local suite 423 tests passing (unchanged Session 13), Python 3.11.9; CI not re-run since Session 10
Render Build 	                      not re-verified 	      Unchanged from Session 10; not re-deployed this session
Render Deploy 	                      not re-verified 	      Unchanged from Session 10; not re-checked this session
Render Health Check 	              ACTIVE 	                /_stcore/health returns ok
UptimeRobot 	                      MONITORING 	        5-minute pings
Provider Fallback 	              ACTIVE 	                DeepSeek → Qwen → Groq on transient errors
Streaming CLI 	                      DEFAULT 	                --no-stream disables
All Pipelines 	                      WORKING 	                coding, writing, appraisal, search, rct_search, sr
SR Pipeline 	                      WORKING WITH CAVEATS 	5/5 papers extract; outputs to root reports/sr/<run_id>/ + mirror output/sr/. Extraction is non-deterministic and has no semantic validation - see Known Issues #15-#18. Output requires manual verification before use.
Docker Support 	                      COMPLETE 	                Windows and macOS one-click scripts
Documentation 	                      CURRENT 	                README.md, HANDOFF.md, REVIEWER_GUIDE.md, Setup Instructions

======================================
4. KNOWN ISSUES
======================================
# 	Issue 	                                                                               Priority 	       Status
1 	Lami extraction fails — paper s10608-017-9875-4.pdf, Table 4, pages 12-13
                                                                                               High 	               RESOLVED (Session 8) — text fallback + study_overrides.yaml; underlying instability tracked as #17
2 	WeasyPrint not installed; PDF falls back to HTML                                       Medium 	               Open
3 	Anthropic geo-restricted 	                                                       Low 	               Use VPN or skip
4 	DeprecationWarning: escape sequence in project_layout.py 	                       Low 	               RESOLVED (Session 5)
5 	Streamlit warning: theme.baseFontSize invalid config option 	                       Low 	               RESOLVED (Session 5)
6 	cli.py and session.py dead code 	                                               Low 	               RESOLVED (Session 5) — deleted
7 	SR pipeline relative-import crash (-m invocation) 	                               High 	               RESOLVED (Session 6)
8 	SR output written under SOURCE_CODE/ instead of repo root 	                       Medium 	               RESOLVED (Session 6)
9 	Hardcoded qwen3.7-plus in _DEFAULT_MODELS (outer main.py); should read model constants Low 	               RESOLVED (Session 7)
10 	Cosmetic [ollama] Auto-detected best model line fires even on Qwen SR runs; does not affect actual provider used
                                                                                               Low 	               RESOLVED (Session 11) — see #25, same root cause (module-scope probe made lazy)
11 	Launcher completion message in run_sr_launcher printed stale pipelines/sr/outputs path Low 	               RESOLVED (Session 7)
12 	Vision regression: SR launcher defaulted qwen to text-only qwen-plus-latest, breaking all extraction
                                                                                               High 	               RESOLVED (Session 7) — now defaults to qwen-vl-max via QWEN_VISION_MODEL
13 	Inner sr/main.py argparse default may still hardcode qwen3.7-plus (only the outer launcher was verified fixed this session)
                                                                                               Low 	               RESOLVED (Session 11) — verified: --model defaults to None, threaded through unchanged everywhere; no hardcoded override found
14 	test_main_coverage.py references a nested prompts/coding/*.txt layout (with .txt) that does not exist on disk; actual files are flat prompts/-prompt.md. Tests pass against mocked paths, not real files
                                                                                               Low 	               RESOLVED (Session 11) — corrected to flat prompts/<role>-prompt.md; side finding tracked as new #43
15 	No SD/SE disambiguation. A reported SE is read as an SD, understating dispersion by up to sqrt(n) and inflating the effect size. Observed 8x understatement in zsy234.pdf
                                                                                               CRITICAL 	        MITIGATED (Session 12), tested against real corpus (Session 13) — tripwire exists but zsy234.pdf succeeded via vision on 2/2 real runs, never reaching the text-fallback path this check is scoped to; not yet exercised against its target paper. Manual check still required
16 	No within- vs between-group detection. A within-subject pre/post contrast can be extracted as intervention-vs-control, producing a large invalid effect with no warning. Observed in zsy234.pdf
                                                                                               CRITICAL 	        MITIGATED (Session 12), tested against real corpus (Session 13) — group-label follow-up added and works correctly, but real testing on zsy234.pdf showed it validates trial-design facts (arm names), not whether the extracted NUMBERS belong to a between-group comparison - see #48. Manual check still required
17 	Extraction is non-deterministic. Same PDF yields different means/SDs/Ns on consecutive runs; observed in 2 of 5 test papers
                                                                                               High 	                Open — run 3x and diff before trusting output
18 	Broken font CMaps misdetected as garbled text. Affected PDFs have a clean text layer recoverable with a fixed +1 character offset, but the pipeline falls back to OCR
                                                                                               High 	                Open — likely upstream cause of #17
19 	zsy234.pdf still included in the test corpus results as a valid study despite reporting no between-group pain effect
                                                                                               High 	                Open — exclude with documented reason, or extract correct group-level values
20 	No effect-size plausibility bound. |g| > 1.5 from a psychotherapy trial passes unflagged
                                                                                               Medium 	                RESOLVED (Session 11) — flags |g/SMD|>1.5 or OR/RR beyond 10x/0.1x in results_csv + console; does not auto-exclude (tripwire only, not a fix for #15/#16)
21 	PICO discovery differs between interfaces: Streamlit UI globs output/rct_search/, CLI globs input/sr/. A PICO saved in one is invisible to the other
                                                                                               Low 	                RESOLVED (Session 11) — description was inaccurate: CLI actually checked input/rct_search/ then output/rct_search/ (never input/sr/); UI checked output/rct_search/ only. UI now merges both, matching CLI precedence
22 	RoB 2.0 runs independently of study_overrides.yaml and may assess OCR text for a study whose outcome data was hand-entered
                                                                                               Low 	                Open
23 	No regression fixtures for the five-paper test corpus. Ground truth exists only in REVIEWER_GUIDE.md prose
                                                                                               Medium 	                Open

24 	Streamlit UI override fields put API keys into st.session_state, i.e. into the server process. Safe locally; a shared/Render deployment would place user keys in a multi-user process 	Medium 	RESOLVED (Session 11, risk narrowed) — st.session_state is per-browser-session in Streamlit, not shared server-wide as originally framed; verified no os.environ mutation and no disk/echo leak (Session 9 fix confirmed durable). Added a "Clear stored keys" button to shorten the plaintext-in-memory exposure window
25 	providers.py probes Ollama at MODULE scope: the "[ollama] Auto-detected best model" line fires on import, on every run and every test, regardless of --provider. A network call during import is also a latent hang if Ollama is installed but unresponsive 	Medium 	RESOLVED (Session 11) — resolution moved to _resolve_ollama_model(), called lazily from call_ollama_provider() on first real use; also resolves #10
26 	pipelines.sr.main (~2.8s: scipy.stats, matplotlib, pymupdf) is imported even for coding mode 	Low 	RESOLVED (Session 11) — removed 4 dead top-level imports (run_coding, run_writing, run_search, run_sr) that were never referenced anywhere in main.py
27 	macOS launcher changes are untested on macOS. The curl /_stcore/health poll loop and the lsof port check need a real run 	Medium 	Open — verify before relying on them
28 	Old %TEMP%\ai_km_run_*.bat files from before the v2.4.7 fix still contain API keys in plaintext on any machine that ran the UI 	High 	Action required — delete them and rotate affected keys
29 	call_ai_with_fallback sent prompts to cloud providers even when --provider ollama was requested. Confidential input could reach a third party on a routine timeout 	CRITICAL 	RESOLVED (Session 10) — LOCAL_ONLY_PROVIDERS never falls back
30 	23 source files began with a UTF-8 BOM; previously misdiagnosed as corrupted comments 	Medium 	RESOLVED (Session 10) — stripped; check_no_bom.py guards
31 	Clean install on Python 3.14 fails across five packages 	High 	RESOLVED (Session 10) — main.py gates 3.11-3.12 with a download link
32 	OCR packages installed but unusable: no Tesseract/Poppler/libGL in the image, so ~2GB of PyTorch bought nothing 	Medium 	RESOLVED (Session 10) — moved to requirements-ocr.txt
33 	Docker_setup.bat and mac_docker_setup.sh were both non-functional and were the advertised one-click setup routes 	High 	RESOLVED (Session 10) — deleted; replaced by docker compose
34 	_is_transient_error matches substrings, so an auth error mentioning "connection" is treated as retryable and triggers fallback 	Low 	RESOLVED (Session 11) — checks HTTP status code explicitly (401/403 never transient); falls back only to the precise phrase "connection error", not the bare word "connection"
35 	No regression test asserting --provider ollama never reaches a cloud API. The fix for #29 is verified only by a manual check 	Medium 	RESOLVED (Session 11) — added tests/test_provider_fallback.py, 4 tests, verified passing in the real project venv (405 total)
36 	check_no_bom.py is not wired into CI, so BOMs can return silently 	Low 	Open
37 	Windows and macOS launchers used matching filenames but different mechanisms: the .bat files ran the virtualenv, the .sh files ran docker run 	Medium 	RESOLVED (Session 10) — both venv-based; Docker via docker compose only
38 	Setup instructions led with the hosted app and carried no confidentiality warning, in a tool intended for patient data 	High 	RESOLVED (Session 10) — explicit warning added to Option 1 and the Providers section
39 	macOS launchers are untested on macOS. Rewritten from Docker-based to venv-based in v2.4.8; the lsof port check and the Python 3.11/3.12 discovery loop need a real run 	Medium 	Open
40 	Ctrl+C during the startup import chain (pandas/pytesseract, ~7s cold start) raised a raw traceback through pandas internals instead of the clean "Session stopped. Returning to menu..." message - the entry-point's try/except KeyboardInterrupt only wrapped code inside if __name__ == "__main__", not the module-level imports above it 	Medium 	RESOLVED (Session 11) — imports wrapped in their own try/except KeyboardInterrupt
41 	Provider-select box in scripts/launcher.py misaligned on CJK-locale terminals: the Unicode checkmark (✓) is an ambiguous-width character and renders as 2 columns instead of 1, throwing every vision-capable provider row a column wider than its "x no vision" counterpart 	Low 	RESOLVED (Session 11) — replaced ✓ with ASCII "+", padded all badge variants to a fixed width before adding color codes
42 	No visible wait notice before a slow provider call (Ollama model load, or any cloud provider taking 15s+); looked indistinguishable from a hang, risking an impatient Ctrl+C mid-generation 	Low 	RESOLVED (Session 11) — call_ai() now prints a wait notice before dispatch, gated on sys.stdout.isatty()
43 	test_main_sr_mode (test_main_coverage.py) exercises main.main(mode='sr', ...), a code path that cannot occur for real: ALL_MODES has no "sr" key (SR mode is dispatched straight to run_sr_launcher() at the entry point, never reaches choose_role()). The test only passes because choose_role is fully mocked; with the mock removed it would raise KeyError on ALL_MODES['sr'] 	Low 	Open — needs a decision: redesign to assert SR routes to run_sr_launcher, or remove
44 	relevance_screener.py and rob2_tool.py both hardcoded a Windows-only absolute Tesseract path (C:\Program Files\Tesseract-OCR\tesseract.exe), unconditionally, in both files. Broke the OCR fallback entirely on macOS/Linux/Docker regardless of whether Tesseract was actually installed and working there - distinct from #32 (OCR packages installed but unusable due to missing system binaries), this was a straight wrong-path bug 	Medium 	RESOLVED (Session 12) — only overrides tesseract_cmd on Windows and only if that default path exists; otherwise defers to pytesseract's normal PATH-based discovery
45 	RoB2Assessor defaulted to model="qwen3.7-plus", matching nothing in providers.py's model registry. Unreachable via the documented pipeline (sr/main.py always passes model=args.model explicitly) but a landmine for direct construction that omits model 	Low 	RESOLVED (Session 12) — corrected to qwen-plus-latest, matching providers.py's QWEN_MODEL; also found _call_with_images() on this class is dead code, never actually invoked - assess_by_pdf_path() only ever calls _call_with_text()
46 	_infer_group_timepoint_from_text (data_extractor.py) hardcoded three literal arm names (CBT-IP, CBT-P, UMC) from one specific trial with NO generic fallback - silently returned (None, None) for every other paper's table, giving the appearance of general group-inference machinery while only ever working for one study 	Medium 	RESOLVED (Session 12) — generalized via _collect_candidate_group_names(), deriving candidate arm names from each paper's own extraction output instead of hardcoded literals; verified both the original trial and a different trial's names now match correctly
47 	audit_logger.py's write_results() passed a hardcoded fieldnames list to csv.DictWriter(extrasaction="ignore"), silently dropping plausibility_flag/sd_se_warning/group_timepoint_warning from meta_analysis_results.csv - the columns themselves absent, not just empty, even though the fields existed in every audit_row dict since Session 12 	Medium 	RESOLVED (Session 13) — added the three field names to the fixed list; verified against real pipeline output, not just a synthetic test
48 	The Session 13 group-label follow-up (added to give #10/#16 something to check) validates "what are this trial's treatment arms called," not "do the specific numbers already extracted actually belong to a between-group comparison of those arms." Real-world test on zsy234.pdf: follow-up correctly returned genuine, correct arm names (CBT-I, WLC) while the underlying suspect mean/SD values were completely unaffected and unchanged from prior runs - the tripwire went silent on exactly the paper it exists to catch, leaving only #13's plausibility bound to flag it 	CRITICAL 	Open — needs the model to quote/cite the specific source text a number came from, and a check that the quote doesn't contain timepoint language, binding verification to the numbers rather than only to the labels
49 	No regression test for the Session 13 group-label follow-up mechanism (_fetch_group_labels_if_missing, _needs_group_labels, _build_group_label_followup_prompt, _call_chat_api_with_prompt) - verified only via standalone logic simulation and two real pipeline runs, no committed pytest test 	Medium 	Open
======================================
5. AI PROVIDERS
======================================
Provider 	                      Flag 	                Env Var 	        Default Model 	                Vision 	Streaming
DeepSeek 	                      --provider deepseek 	DEEPSEEK_API_KEY 	deepseek-v4-flash 	        No 	Yes
Qwen (text) 	                      --provider qwen 	        DASHSCOPE_API_KEY 	qwen-plus-latest (QWEN_MODEL) 	No* 	Yes
Qwen (vision/SR) 	              --provider qwen 	        DASHSCOPE_API_KEY 	qwen-vl-max (QWEN_VISION_MODEL) Yes 	Yes
OpenAI 	                              --provider openai 	OPENAI_API_KEY 	        gpt-4o-mini 	                Yes 	Yes
Anthropic 	                      --provider anthropic 	ANTHROPIC_API_KEY 	claude-sonnet-5 	        Yes 	Yes
Groq 	                              --provider groq 	        GROQ_API_KEY 	        llama-3.3-70b-versatile 	Yes 	Yes
Ollama 	                              --provider ollama 	OLLAMA_HOST 	        Auto-detected 	                No 	Yes

*The qwen provider is registered as vision-capable in providers.py, but its default text model (qwen-plus-latest) is text-only. SR extraction now uses QWEN_VISION_MODEL (qwen-vl-max) so vision works without a --model flag.

Fallback: transient errors (timeout, 429, 502, 503) trigger next provider; auth errors (401, 403) raise immediately. SR pipeline blocks non-vision providers (DeepSeek/Ollama not usable for SR).

======================================
6. TEST COVERAGE (per-module % not re-measured this session; total test count did change)
======================================
Module 	Coverage
writing.py 	        89%
traice_integration.py 	98%
appraisal.py 	        86%
coding.py 	        78%
checkpoint.py 	        73%
path_utils.py 	        74%
search.py 	        72%
rct_search.py 	        63%
ui/app.py 	        58%
rag.py 	                57%
streaming.py 	        55%
providers.py 	        54%
main.py 	        41%
document_reader.py 	24%
SR pipeline (src/*) 	~10-53% (low)
TOTAL 	~53% (423 tests, not re-measured this session - up from 405)

======================================
	Wire check_no_bom.py into CI (#36) 	Still open, unchanged since Session 10. One step in the workflow.

8. LESSONS LEARNED
======================================
    Tests must mock utils.rag.index_uploads rather than doing real embedding (slow + non-deterministic).
    Use single-quoted here-strings when writing Python files from PowerShell to avoid $/quote/backtick escaping.
    main() runs an interactive input() loop and calls call_ai directly, NOT the run_* functions. Mock input with task + KeyboardInterrupt.
    Never use CREATE_NEW_PROCESS_GROUP for interactive CLI on Windows.
    Never hardcode model versions if *-latest aliases exist.
    Render dashboard settings can override render.yaml; always inspect Render logs.
    Render Linux must not install Windows-only packages (pywin32); use requirements-render.txt.
    docx2txt==0.8 has no wheel; install separately or allow from source.
    Streamlit app path is SOURCE_CODE/ui/app.py, not src/ui/app.py.
    Mark network tests @pytest.mark.live to avoid CI flakes.
    ChromaDB on Linux CI needs cmake, python3-dev, and pysqlite3.
    Raw-string (r""") docstrings when they contain backslashes to avoid escape-sequence warnings.
    (Session 6) Never launch a package's module by file path via subprocess; use python -m package.module with cwd= so relative imports resolve.
    (Session 6) Every directory in an import chain needs an init.py for -m module invocation.
    (Session 6) When computing a repo root from Path(file), count .parent hops carefully; prefer parents[N] for verifiability. sr/src/utils/project_layout.py needs six hops.
    (Session 6) SR nested input() prompts require a real interactive TTY; run python SOURCE_CODE/main.py --mode sr --provider qwen directly for PICO selection.
    (Session 6) Git does not track empty directories; use git rm -r for tracked folders so deletion is recorded.
    (Session 7) A provider being "vision-capable" is not the same as its default model being vision-capable. After centralising model constants (#9), the qwen provider stayed marked vision-capable while its default (qwen-plus-latest) is text-only — silently breaking all SR extraction with HTTP 200 + empty results. Keep a separate QWEN_VISION_MODEL for image work.
    (Session 7) A silent extraction failure looks like success: the pipeline completed all stages, wrote CSVs, and produced reports/forest plot while extracting zero data. Watch for meta-analysis "< 2 studies with usable data" as the real signal.
    (Session 7) Verify "unused" before deleting. The prompts/ folder looked deletable but 14/15 files are load-bearing agent persona files loaded via explicit AI_DIR paths that a naive grep for the folder can miss. Always cross-reference against the actual loader/registry, widen the search beyond one subtree, and remove individual orphans rather than whole folders. The test suite would NOT have caught deletion of the folder.
    *(Session 7) Diagnostic .log files clutter git status; gitignore them (sr_*.log) rather than committing.
    (Session 8) A silent wrong answer is worse than a crash. Lami failed loudly (dropped off the forest plot, immediately visible). zsy234 failed silently: confident magnitude, symmetric CI, clean CSV row, passed six stages and a DOCX report while being entirely invalid. Plausibility is not evidence of correctness.
    (Session 8) Never gate a correction on the value it is correcting. The numeric-signature match (self._near(mi, 7.35) ...) fired only when extraction was already right and went silent exactly when it was wrong — turning a wrong-number failure into a missing-study failure, and risking mislabelling any other study whose means landed nearby.
    (Session 8) Find the reader before patching the writer. Three patches wrote result["first_author"] while every consumer read result["study_metadata"]["first_author"], which nothing in the codebase ever wrote. Grep for the consumer first.
    (Session 8) Verify a patch actually applied. Two patch scripts printed success while writing nothing (one searched for "result = self._derive_missing_sample_sizes(result)"; the actual line has no assignment). Any patch script must assert its anchors before writing and abort loudly otherwise.
    (Session 8) Apply multi-edit patches bottom-up (highest line number first) so earlier line numbers stay valid.
    (Session 8) "Garbled text" may be a broken font CMap, not a scan. Check for a fixed character-code offset before falling back to OCR — decoding is lossless, OCR is not.
    (Session 8) A bare negation in .gitignore cannot re-include a file inside an excluded directory; git never descends into it. Use input/*, !input/sr/, input/sr/*, !input/sr/file.
    (Session 8) git check-ignore reports the matching rule whether it excludes or re-includes; a leading ! means the file is tracked. Use --no-index to test the rule rather than the index state.
    (Session 8) Do not paste Python at a PowerShell prompt. Use @' ... '@ | Set-Content file.py, then run the file.
    (Session 9) Popen's env= already passes variables to the child. Writing them into a generated script as well is redundant AND leaks them — cmd echoes every line, and the file persists on disk. Secrets belong in env=, never on a command line or in a script body (a command line is also visible in ps / Task Manager details).
    (Session 9) Clearing .env does not revoke a key. Anything that reached a screen, a screenshot, a temp file, or shell history must be rotated at the provider.
    (Session 9) An unescaped ( or ) in echo text inside a batch if ( ... ) block closes the block early. cmd parses the whole block before executing it, so "... was unexpected at this time" appears before the block would even run — and the parenthetical text can be far from where the error is reported. Escape as ^( / ^) or reword.
    (Session 9) A package __init__.py that eagerly imports heavy submodules makes every consumer pay for them. Importing three path helpers cost 2.2s of chromadb and pymupdf. PEP 562 __getattr__ gives lazy loading with no API change. Verify mock.patch targets still resolve — patch("utils.rag.X") works because patch imports the submodule; patch("utils.X") would not.
    (Session 9) Inside a container, localhost is the container. --add-host host.docker.internal:host-gateway only creates the route; the app still needs the host-facing URL. This silently broke Ollama on macOS.
    (Session 9) set -e makes subsequent `if [ $? -ne 0 ]` handlers dead code — the script exits before reaching them. Use set -uo pipefail when the script does its own error checking.
    (Session 9) .gitattributes must force LF on *.sh. With core.autocrlf=true, a Windows commit stores CRLF and the shebang breaks on macOS. Check with git check-attr text eol -- path, not by reading the warnings.
    (Session 9) git check-ignore reports a file as tracked (not ignored) once it is in the index; use --no-index to test the rule itself. And a bare ! negation cannot re-include a file inside an excluded directory — git never descends into it.
    (Session 10) Matching filenames across platforms imply matching behaviour. Mac_kcMedicalResearch_CLI.sh and AI_kcMedicalResearch_CLI.bat looked like a pair and were not - one ran the venv, the other ran Docker. Parity in naming without parity in mechanism is worse than obviously different names, because the documentation then describes both as one thing.
    (Session 10) Check what the default path in the documentation actually recommends. The setup instructions led with a third-party hosted app as "the right choice for most people" in a tool built so that patient data could stay local. Nobody had reread that sentence against the tool's purpose.
    (Session 10) A fallback chain that ignores WHY a provider was chosen will eventually violate the reason it was chosen. Ollama was selected for confidentiality; the chain treated it as merely first in a list. Any mechanism that substitutes one provider for another must know which properties of the original were load-bearing.
    (Session 10) A timeout is not consent. Retry logic that changes WHERE data goes is not the same as retry logic that changes WHEN it is sent.
    (Session 10) The most dangerous failures print a success message. "[fallback] Succeeded with deepseek" scrolled past in a 200-line log while patient data left the machine. Compare Session 8's zsy234: a confident g=-2.36 with a clean CI. Neither looked like an error.
    (Session 10) Code paths nobody executes do not work. Both advertised one-click setup scripts were broken, unnoticed, because Docker was never installed on the dev machine. Documentation asserting that an untested path works is worse than no documentation.
    (Session 10) PowerShell 5 `Set-Content -Encoding UTF8` writes a BOM. Use `-Encoding utf8NoBOM` (PS7), `Out-File -Encoding ascii`, or [System.IO.File]::WriteAllText with UTF8Encoding($false). Files generated during Sessions 8-9 acquired BOMs this way.
    (Session 10) Put a version gate above the first third-party import, not merely near the top. Below `from dotenv import load_dotenv` the user gets ModuleNotFoundError and never sees the message.
    (Session 10) When a dependency needs system binaries pip cannot install, installing the Python package alone is worse than not installing it: it looks supported, costs disk, and fails at runtime. The image carried ~2GB of PyTorch for OCR it could not perform.
    (Session 9) Profile before optimising. The 15-20s startup was assumed to be an Ollama network probe; importtime showed it was eager imports. Measured 3.2s of imports against 15-20s observed, so filesystem/AV cold cache accounts for the remainder — no code change fixes that part.
    (Session 11) An entry-point's try/except doesn't cover module-level code. Wrapping `if __name__ == "__main__":` in try/except KeyboardInterrupt looks complete but doesn't catch Ctrl+C during the imports that run before that block starts. If startup is slow enough to interrupt, the imports need their own handler.
    (Session 11) "Ambiguous width" Unicode characters are locale-dependent, not font-dependent in the way you'd assume. A checkmark that's 1 column in an English-locale terminal can render as 2 columns in a CJK-locale terminal (East Asian Width property), silently breaking any layout that counts characters instead of accounting for this. Prefer plain ASCII for anything alignment-critical.
    (Session 11) When a document names an exact number as a bug example ("|g| > 1.5"), use that number, not a substitute you consider more defensible. A plausibility bound of 2.0 felt more principled but would have silently failed to catch the document's own cited case at g=1.51-1.99.
    (Session 11) Verify a Known Issue's literal claim against the code before fixing it, not just its symptom. #21's description ("CLI globs input/sr/") was wrong — checking rct_search.py directly showed the real behavior (input/rct_search/ then output/rct_search/). Fixing the described-but-nonexistent bug would have left the real, narrower gap in place.
    (Session 11) A named risk mechanism doesn't always match the real one. #24 described API keys landing in "the server process" as if shared across users; st.session_state is per-browser-session in Streamlit by default. Trace the actual data flow (here: os.environ.copy(), never mutated; subprocess env= only) before implementing a fix for the risk as originally framed — the real, narrower risk (plaintext duration-of-exposure) still needed addressing, just not the way the description implied.
    (Session 11) Fixing a hardcoded test path can surface a design bug the test was hiding. Correcting test_main_sr_mode's mocked prompt path revealed that ALL_MODES has no "sr" key at all — the test exercises a code path that cannot happen outside its own mock. A mechanical path fix is not the same as validating the test still tests something real; flag the deeper finding rather than silently patch past it.

======================================
9. FINAL VERIFIED RENDER SETTINGS
======================================
Build Command: pip install --upgrade pip && pip install --no-cache-dir --only-binary=:all: -r requirements-render.txt && pip install --no-cache-dir --no-deps docx2txt==0.8

Start Command: streamlit run SOURCE_CODE/ui/app.py --server.address=0.0.0.0 --server.port=$PORT --server.enableCORS=false --server.enableXsrfProtection=false

Env: PYTHON_VERSION=3.11.9 Health: https://ai-kcmedicalresearch.onrender.com/_stcore/health → ok
10. SR PIPELINE — OUTPUT LOCATIONS & VISION MODEL

Run directly (not via menu launcher) for interactive PICO selection: python SOURCE_CODE/main.py --mode sr --provider qwen (defaults to vision model qwen-vl-max after the Session 7 fix — no --model flag needed).

Per-run output (timestamped, audit-friendly): reports/sr/<run_id>/ containing uploads/, data/screened/, data/extracted/, data/results/, output/figures/forest_plot.png, output/reports/systematic_review.docx and .html.

Mirror (always latest run): output/sr/figures/ and output/sr/reports/.

All paths are repo-root relative (no SOURCE_CODE/ prefix) after the Session 6 project_layout.py fix.

Vision model override: set env QWEN_VISION_MODEL to change the SR extraction model (default qwen-vl-max). Text-mode Qwen still uses QWEN_MODEL (qwen-plus-latest).

Commit trail Session 7: 3c2e51b (#9) → 4b793ea (#3) → a83ec1c (#11) → 5d6a8ca (test hygiene) → 9c536e1 (vision fix) → b1f4c48 (orphan prompt) → 1b6b9b0 (dead-code + gitignore).
11. SR STUDY METADATA AND MANUAL OVERRIDES (Session 8)

Metadata resolves in three stages, each overriding the last: (1) model output, (2) PDF-derived via resolve_pdf_metadata() and flagged metadata_source = "pdf_auto (verify)", (3) reviewer overrides from input/sr/study_overrides.yaml (env SR_STUDY_OVERRIDES).

Override file format, keyed by PDF filename:

"some_paper.pdf":
  first_author: Nguyen
  year: 2021
  n_intervention: 42
  n_control: 40
  mean_intervention: 4.10
  sd_intervention: 1.85
  note: "Table 2, 12-week endpoint. Verified from PDF p.7, 2026-08-17."

Allowed fields: first_author, year, doi, study, study_id, n_intervention, n_control, mean_intervention, sd_intervention, mean_control, sd_control, note. Unknown fields are ignored with a warning.

Metadata fields fill only when extraction left them blank. Numeric fields replace extraction output. Extraction still runs in full so the log can report field(7.32->7.35) versus field(confirmed 7.35) — do not add a fast path that skips extraction for overridden studies or the cross-check is lost.

Overrides affect extraction and meta-analysis only. Screening (Stage 2) and RoB 2.0 (Stage 3.5) re-read the PDF independently.

Reviewer rules (full version in Readme/REVIEWER_GUIDE.md): read the source table before entering a value; always fill note with table, page, and date; verify symmetrically rather than only checking studies whose results surprise you; never edit the override file after looking at the forest plot.

======================================
12. IMMEDIATE ACTIONS BEFORE NEXT SESSION
======================================

1. ROTATE API KEYS. (Still outstanding as of Session 10.) Anthropic, DeepSeek, and DashScope keys were displayed in
   plaintext by the pre-v2.4.7 UI launcher and appeared in screenshots.
   Clearing .env does not revoke them. Rotate at each provider console, then
   put the new keys in .env (which is gitignored).

2. Delete stale temp files: Remove-Item "$env:TEMP\ai_km_run_*.bat"

3. Set spend limits at each provider so a future leak is bounded.

4. Verify the venv: python -c "import sys; print(sys.executable)" should
   resolve under .venv\Scripts\. It was observed resolving to
   C:\Users\user\...Python311 while the prompt showed (.venv).

5. Test the macOS launchers on an actual Mac (Issue #27).

6. Decide on test_main_sr_mode (#43): redesign to assert SR mode routes to
   run_sr_launcher(), or remove it - it currently tests a code path
   (ALL_MODES['sr']) that only "passes" because choose_role is fully mocked.

7. Push Sessions 11-13's commits and re-verify CI (GitHub Actions) and the
   Render deployment - neither has been re-run since Session 10. Local
   suite is green (423 passed, 3 skipped, 11 deselected) but that is not
   the same guarantee as CI passing in a clean environment.

8. DONE this session, no longer an action item: ran the SR pipeline
   against the real 5-paper corpus twice. Results: #13 (plausibility)
   works correctly in practice; #9 (SD/SE) has not yet been exercised
   against its target paper (zsy234.pdf keeps succeeding via vision);
   #10 (group/timepoint) works as built but what it verifies turned out
   to be too shallow to catch zsy234's actual failure - see #38.

9. Implement #38's fix: bind #10's verification to the extracted NUMBERS
   (a source-text quote per value, checked for timepoint language), not
   just to the group labels. This is the actual next step for the
   zsy234-class failure - see NEXT SESSION PRIORITIES item 1.

10. Add a regression test for Session 13's group-label follow-up
    mechanism (#49) - built and verified via real pipeline runs, but has
    no committed pytest test.

Handoff prepared: 2026-08-18 · Version: v2.4.11 · Single source of truth for next session.

