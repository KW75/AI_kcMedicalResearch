# Resolved Issues

One line per issue, so numbers cited in commit messages stay resolvable.
Full detail: `HANDOFF_archive_pre_S19.md` and `git log`. Do not reopen
without reading the closing notes there.

| #  | Issue | Resolved |
|----|-------|----------|
| 1  | Lami extraction failed (Table 4, pp. 12-13) | v2.4.6 - text fallback + `study_overrides.yaml`; instability tracked as #11 |
| 4  | Hard-coded `qwen3.7-plus` overrode `QWEN_MODEL` | v2.4.5 |
| 5  | SR launcher defaulted Qwen to text-only model | v2.4.5 - `QWEN_VISION_MODEL` |
| 6  | Spurious `[ollama] Auto-detected` line on Qwen runs | v2.4.9 (via #17) |
| 7  | Inner `sr/main.py` `--model` default hardcoded | v2.4.9 - verified None |
| 8  | Test referenced nonexistent `prompts/coding/*.txt` layout | v2.4.9 |
| 9  | No SD/SE disambiguation | MITIGATED v2.4.10/v2.4.12 - `sd_se_warning` + source-quote check. Manual check still required (`REVIEWER_GUIDE.md` 3.1). |
| 11 | Extraction non-deterministic (Ang, Jensen, Lami) | Session 26 (b847c55, bb48040) - MACHINE-FLAGGED. Measured first (`Readme/evidence/s26_issue11/`, 5 PDFs x 3 runs): qwen-vl-plus ignores `seed` and is not deterministic at `temperature=0` - quotes differed run-to-run on 4/5 papers, Ang returned three different tables, one a column shift that passed SOURCE QUOTE CHECK. Sampling controls cannot fix it (kept only so vision and text paths share one setting; vision had been at 0.1). Fix: every vision extraction runs N=3 (`--n-agreement`, `SR_EXTRACT_N_AGREEMENT`), majority-votes mean/sd/n per arm and both group labels, and always writes `nondet_flag` (unanimous / field:majority / field:no_majority / table_shift / single_run / not_checked); source quote carried from a run matching the chosen numbers. Stage 4 `[AGREEMENT]` line uses a voted-only denominator. Acceptance run flagged Ang 2/2, passed the four stable papers. Not a determinism fix: three runs can agree on the same wrong cell; only source quotes catch that. Reopen if a `unanimous` row is found carrying a wrong number. Ang's correct reading is Open Issue #67. `Readme/S26_issue11_closeout.md` has the full evidence. |
| 10 | No within- vs between-group detection | MITIGATED v2.4.10/v2.4.13 - `group_timepoint_warning` + tabular multi-timepoint flag. Manual check still required (`REVIEWER_GUIDE.md` 2.2). |
| 12 | CMap offset-decode fallback landed v2.4.13; unconfirmed on a real shifted PDF | v2.4.13 code, closed Session 24 (c6ac1fd) - decoder only runs on the "nearly space-free" failure mode and skips `(cid:` cases by design; all corpus PDFs are either `(cid:` cases or have clean text layers, so the branch cannot be exercised by the current corpus. Pinned by `tests/test_cmap_offset_decode.py` (16 cases). Decoded text keeps `!` where spaces were - fine for the LLM screener, may matter for the extractor's text-fallback if it ever receives decoded text (no corpus PDF exercises this today). |
| 13 | No effect-size plausibility bound | v2.4.9 - `plausibility_flag`, flag only |
| 14 | PICO file discovery differed UI vs CLI | v2.4.9 |
| 15 | RoB 2.0 ignores `study_overrides.yaml` | Session 25 - not a bug: RoB is an intentional independent second read (`REVIEWER_GUIDE.md` §5, §6). Verified no override references in `rob2_tool.py` or its tests. |
| 16 | Streamlit UI kept API keys in `st.session_state` | v2.4.9 - per-session only; "Clear stored keys" button |
| 17 | `providers.py` probed Ollama at import | v2.4.9 - lazy on first use |
| 18 | SR heavy imports pulled in for every mode | v2.4.9 |
| 20 | Pre-v2.4.7 launcher wrote API keys to `%TEMP%` `.bat` | Session 15 - keys rotated |
| 21 | `--provider ollama` could fall back to a cloud provider | v2.4.8 - `LOCAL_ONLY_PROVIDERS` |
| 22 | UTF-8 BOMs in 23 source files | v2.4.8 - stripped; `check_no_bom.py` guards |
| 23 | Install failed on Python 3.14 | v2.4.8 - version gate |
| 24 | OCR packages installed but unusable | v2.4.8 - `requirements-ocr.txt` |
| 25 | Auth errors mentioning "connection" were retried | v2.4.9 - status-code check |
| 26 | No test that Ollama never reaches cloud | v2.4.9 - `tests/test_provider_fallback.py` |
| 27 | Windows/macOS launchers used different mechanisms | v2.4.8 - both venv |
| 29 | Test exercised an impossible `main(mode='sr')` path | v2.4.12 - `run_cli(args)` |
| 30 | Ctrl+C during startup raised raw traceback | v2.4.9 |
| 31 | Provider-select box misaligned on CJK terminals | v2.4.9 |
| 32 | No wait notice before slow provider call | v2.4.9 |
| 33 | Hardcoded Windows Tesseract path | v2.4.10 |
| 34 | `RoB2Assessor` default model not in registry | v2.4.10 |
| 35 | Hardcoded arm names in group/timepoint inference | v2.4.10 |
| 36 | `write_results()` silently dropped tripwire columns | v2.4.11 |
| 37 | Local `.env` pointed at decommissioned DashScope endpoint | v2.4.11 - config, not code |
| 38 | Group-label check validated names, not numbers | v2.4.12 - verbatim per-arm source quotes, `source_quote_warning` |
| 39 | No test for group-label follow-up | v2.4.12 |
| 40 | Screening OCR budget saturated at 6414 chars | v2.4.12 - shared 6000-char budget |
| 41 | RoB2 OCR chunk cap | v2.4.12 |
| 42 | Launcher printed artifact paths unconditionally | v2.4.12 |
| 43 | Launcher banner hardcoded version/test count | v2.4.12 - parsed live |
| 44 | `pico_*` columns empty in every `screening_log.csv` | v2.4.12 - SCHEMA CHANGE |
| 45 | Audit CSVs carried no `run_id` | v2.4.12 |
| 46 | Transient screening error silently dropped a paper | v2.4.12 - retries + `[SCREENING]` block |
| 47 | Group-label follow-up returned literal `'null'` | v2.4.12 - `_clean_group_label()` |
| 48 | runpy RuntimeWarning on every SR run | v2.4.12 - lazy PEP 562 re-export |
| 49 | `check_no_bom.py` scanned only `SOURCE_CODE/` | Session 16/18 - repo-wide, in CI, tested |
| 50 | Anthropic SR path skips SD/SE text-line tripwire | Session 23 - documented as permanent limitation in REVIEWER_GUIDE.md §6. The Anthropic path receives structured JSON with no raw text to scan; the text-line SD/SE check requires raw text and cannot run there. The source-quote SE-marker branch (§2.2 item 3) still runs on Anthropic and catches most of what would have fired. Group/timepoint check runs on Anthropic via _coerce_extraction_result (previously misdescribed in the handoff as also skipped — the source has always run it since #38/v2.4.12). Not a bug; documented and closed. |
| 51 | `outcome_selected` / `timepoint_selected` not recorded or surfaced | v2.4.13 - recorded (Session 17), surfaced in Stage 4 `[OUTCOME/TIMEPOINT]` block (Session 19) |
| 52 | Tabular multi-timepoint rows escaped the source-quote check | v2.4.13 |
| 61 | Anthropic path bypassed source-quote check | v2.4.13 - ported; SD/SE + group/timepoint remain as #50 |
| 66 | Stage-4 summary asserted "every extracted value was bound" on an all-empty run | Session 25 (19a583e) - `_log_stage4_summary` with uniform `n_extracted` denominator; zero-extraction prints `0 of 0` and no positive assertion. `tests/test_stage4_summary.py`. |
| 62 | Suspected `49.0` vs `49` quote-matching bug | Session 21 - not reproducible; `_number_in_text` already tries the integer form. Pinned by test. |

Regression fixtures for Ang's non-deterministic value sets
(`tests/test_extraction_regression_fixtures.py`, Session 20) pin failure
shapes, not the failure rate; they remain in place alongside the Session 26
`nondet_flag` vote and are not a separate issue.
