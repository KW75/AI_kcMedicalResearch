AI kcMedicalResearch - Session 14 Handoff (merge into HANDOFF.md)
Version 2.4.12 (suggested) - run_cli Refactor, OCR Truncation Root-Cause, Audit
Provenance, Screening Drop Guard, Source-Quote Verification (#48 REAL-RUN VERIFIED)

Date: 2026-08-26 (Session 14, following Session 13)
Repository: https://github.com/KW75/AI_kcMedicalResearch
Tests: 423 passing at session start; expected ~431 after this session's test
changes (+7 routing, +1 undispatched-mode, -1 impossible-path SR test, and the
new-scenario tests listed under NEXT SESSION PRIORITIES are NOT yet written) -
NOT re-run against the real project venv this session; every fix was verified
via stubbed harnesses in the working sandbox plus SIX real pipeline runs.
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
#28 temp-file/key rotation (STILL OUTSTANDING since Session 9), #36 CI BOM
wiring, CI/Render not re-verified since Session 10.

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
1   Run the full suite in the real venv (expected ~431; #54's
    screening-CSV schema change may require test updates), then port this
    session's harness scenarios into committed tests: source-quote check
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
6   Push Sessions 11-14 commits (suggested v2.4.12); re-verify CI and
    Render - NEITHER has been re-run since Session 10. Suggested commit
    split: (a) outer main.py + tests, (b) screener+rob2 (pipeline-behavior
    change, own revert point), (c) sr_main+audit_logger+__init__+extractor
    (#48 + provenance), (d) launcher.
7   ROTATE API KEYS (outstanding since Session 9), delete %TEMP% files, set
    spend limits.
8   Docker end-to-end (#19/HANDOFF, unchanged since Session 10); macOS
    launchers (#27/#39).
9   #18 CMap decode - now confirmed on all five papers and still the likely
    root of #17; a fixed +1 offset decode before the OCR fallback would give
    every stage a clean text layer and likely stabilize extraction.

Handoff prepared: 2026-08-26 - Session 14 - merge into HANDOFF.md as the
single source of truth for Session 15.
