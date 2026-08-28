# SOURCE_CODE/pipelines/sr/main.py
import argparse, logging, sys
import pandas as pd
from pathlib import Path
import yaml

# Add the parent directories to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SOURCE_CODE_DIR = PROJECT_ROOT / "SOURCE_CODE"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SOURCE_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(SOURCE_CODE_DIR))

# Now use relative imports from the sr module
from .src.upload.file_manager import FileManager
from .src.screening.relevance_screener import RelevanceScreener
from .src.screening.rob2_tool import RoB2Assessor
from .src.extraction.data_extractor import DataExtractor
from .src.analysis.meta_analysis import MetaAnalyzer
from .src.visualization.forest_plot import ForestPlotGenerator
from .src.reporting.report_generator import ReportGenerator
from .src.reporting.pdf_report import PDFReportGenerator
from .src.utils.project_layout import SRProjectLayout
from .src.utils.audit_logger import (
    write_screens, write_extracts, write_rob2, write_results
)

def resolve_model(provider: str, model):
    """CLI > provider's configured default. Fail loudly if neither exists.

    The --model help text has always promised the provider default, but the
    CLI passed args.model (None) straight through to every stage, so Qwen
    rejected the very first call with "you must provide a model parameter"
    (Session 24, #65). The Streamlit UI resolves via get_default_model; the
    CLI now does the same so both entry points agree.
    """
    if model:
        return model
    from providers import get_default_model
    default = get_default_model(provider)
    if not default or default.startswith("("):
        raise SystemExit(
            f"--model not given and no default model is configured for "
            f"provider {provider!r}. Set {provider.upper()}_MODEL in .env "
            f"or pass --model.")
    return default


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s -- %(message)s")
logger = logging.getLogger("sr.main")

SR_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Effect-size plausibility bounds (Known Issue #13)
# ---------------------------------------------------------------------------
# These do NOT exclude a study from the meta-analysis automatically - an
# unusually large effect might be genuine (e.g. a dramatic drug response).
# They flag the study in the audit trail and console log so a human
# reviewer catches it during the manual verification already required by
# Known Issues #9 (SD/SE confusion) and #10 (within- vs between-group
# mixup) - both of which are the most common causes of an implausible
# effect size passing through unnoticed.
PLAUSIBILITY_BOUNDS = {
    "SMD": 1.5,    # matches the exact threshold cited in this project's own
                   # Known Issue #13 ("|g| > 1.5 from a psychotherapy trial")
    "MD":  None,   # scale-dependent (units vary by outcome) - no fixed
                   # bound is meaningful here without knowing the outcome
    "OR":  10.0,   # an odds/risk ratio this extreme (or its reciprocal) is
    "RR":  10.0,   # rare enough in real RCTs to warrant a second look
}


def _check_plausibility(effect_measure: str, est: float, author_label: str) -> str | None:
    """Return a warning string if `est` exceeds the plausibility bound for
    this effect measure, else None. Logs a warning as a side effect."""
    bound = PLAUSIBILITY_BOUNDS.get(effect_measure)
    if bound is None:
        return None
    if effect_measure in ("OR", "RR"):
        implausible = est > bound or (est > 0 and est < 1.0 / bound)
    else:
        implausible = abs(est) > bound
    if not implausible:
        return None
    msg = (
        f"|{effect_measure}|={est:.3f} exceeds plausibility bound ({bound}) "
        f"for {author_label} - verify against source PDF before trusting "
        f"this estimate (see Known Issues #9, #10, #13)."
    )
    logger.warning(f"[PLAUSIBILITY] {msg}")
    return msg

# Fields whose presence in a meta_audit row means the extractor produced
# usable per-arm data for that study. Used to compute n_extracted, the
# uniform denominator for the four Stage-4 tripwire summary lines and the
# [OUTCOME/TIMEPOINT] provenance block (#66).
#
# Rationale: on an all-empty-extraction run, len(meta_audit) is still >0
# (every included paper produces a row, even when every field is None),
# so the pre-#66 lines printed "0 of 1 studies flagged - every extracted
# value was bound to a verbatim source quote" while nothing had actually
# been extracted. "0 of 0" is the honest denominator; anything else lets
# a silent-empty run look like a clean run.
_EXTRACTED_VALUE_FIELDS = (
    "mean_intervention", "sd_intervention",
    "mean_control",      "sd_control",
    "n_intervention",    "n_control",
    "hedges_g",
)
_EXTRACTION_WARNING_FIELDS = (
    "sd_se_warning",
    "group_timepoint_warning",
    "source_quote_warning",
)


def _row_has_extracted_value(row: dict) -> bool:
    """True if a meta_audit row shows the extractor produced anything the
    tripwires could meaningfully check. See #66."""
    if any(row.get(k) is not None for k in _EXTRACTED_VALUE_FIELDS):
        return True
    # A warning implies the extractor saw a value and flagged it; count
    # it as "extracted" so a flagged-but-otherwise-empty study still
    # appears in the denominator.
    if any(row.get(k) for k in _EXTRACTION_WARNING_FIELDS):
        return True
    return False


def _log_stage4_summary(meta_audit: list[dict],
                        er: list[dict],
                        effect_measure: str) -> None:
    """Emit the four tripwire summary lines and the [OUTCOME/TIMEPOINT]
    provenance block. Extracted from main() for #66 so a zero-extraction
    run prints '0 of 0' (not '0 of N') and does not assert positives.

    Every branch always emits a line for its label (per the 'always set
    the key; print the zero' rule); the denominator now says whether the
    zero means 'checked and clean' or 'nothing was there to check'.
    """
    n_extracted = sum(1 for r in meta_audit if _row_has_extracted_value(r))

    # --- [PLAUSIBILITY] --------------------------------------------------
    _bound = PLAUSIBILITY_BOUNDS.get(effect_measure)
    flagged = [r for r in meta_audit if r.get("plausibility_flag")]
    if flagged:
        logger.warning(
            f"[PLAUSIBILITY] {len(flagged)} of {n_extracted} extracted "
            f"studies exceeded the effect-size plausibility bound and "
            f"need manual verification before this pooled estimate is "
            f"trusted:")
        for r in flagged:
            logger.warning(
                f"  - {r.get('first_author','?')} ({r.get('year','')}): "
                f"{r.get('plausibility_flag')}")
    elif _bound is None:
        logger.info(
            f"[PLAUSIBILITY] no bound defined for {effect_measure} "
            f"(scale-dependent) - check skipped.")
    else:
        logger.info(
            f"[PLAUSIBILITY] 0 flagged of {n_extracted} extracted "
            f"studies (bound={_bound}).")

    # --- [SD/SE CHECK] ---------------------------------------------------
    # Keeps its own partial denominator (_n_checkable), because the check
    # only runs on the text-fallback path (Known Issue #9); a vision-path
    # study is not "clean", it is "not checkable". Guard against
    # _n_checkable=0 so the "0 of 0" case doesn't assert positives.
    se_flagged = [r for r in meta_audit if r.get("sd_se_warning")]
    _n_checkable = sum(
        1 for r in er
        if isinstance(r, dict)
        and str(r.get("extraction_method") or "").startswith("text"))
    if se_flagged:
        logger.warning(
            f"[SD/SE CHECK] {len(se_flagged)} of {n_extracted} extracted "
            f"studies had a value extracted into an SD field from a "
            f"source line also containing 'SE'/'SEM'/'standard error' - "
            f"verify these are genuine SDs, not standard errors, before "
            f"trusting this pooled estimate (see REVIEWER_GUIDE.md 3.1):")
        for r in se_flagged:
            logger.warning(
                f"  - {r.get('first_author','?')} ({r.get('year','')}): "
                f"{r.get('sd_se_warning')}")
    else:
        logger.info(
            f"[SD/SE CHECK] 0 flagged of {_n_checkable} checkable "
            f"studies ({n_extracted - _n_checkable} vision-path studies "
            f"NOT checkable - the check needs literal source text; "
            f"Known Issue #9). Manual verification still required.")

    # --- [GROUP/TIMEPOINT CHECK] -----------------------------------------
    group_flagged = [r for r in meta_audit if r.get("group_timepoint_warning")]
    if group_flagged:
        logger.warning(
            f"[GROUP/TIMEPOINT CHECK] {len(group_flagged)} of "
            f"{n_extracted} extracted studies had a group label that "
            f"looks like a timepoint, or identical intervention/control "
            f"labels - possible within- vs between-group confusion. "
            f"Verify against the source PDF before trusting this pooled "
            f"estimate (see REVIEWER_GUIDE.md 2.2):")
        for r in group_flagged:
            logger.warning(
                f"  - {r.get('first_author','?')} ({r.get('year','')}): "
                f"{r.get('group_timepoint_warning')}")
    else:
        logger.info(
            f"[GROUP/TIMEPOINT CHECK] 0 flagged of {n_extracted} "
            f"extracted studies. NOTE: this check validates group "
            f"LABELS only, not whether the extracted numbers come from "
            f"a between-group comparison - that is the SOURCE QUOTE "
            f"check's job (Known Issue #48/#38). Manual verification "
            f"still required.")

    # --- [SOURCE QUOTE CHECK] --------------------------------------------
    quote_flagged = [r for r in meta_audit if r.get("source_quote_warning")]
    if quote_flagged:
        logger.warning(
            f"[SOURCE QUOTE CHECK] {len(quote_flagged)} of {n_extracted} "
            f"extracted studies had extracted values that could not be "
            f"bound to a clean verbatim source quote (missing quote, "
            f"number absent from its quote, SE-labelled quote for an "
            f"SD, or within-subject timepoint language in the quote) - "
            f"verify each against the source PDF before trusting this "
            f"pooled estimate (Known Issue #48):")
        for r in quote_flagged:
            logger.warning(
                f"  - {r.get('first_author','?')} ({r.get('year','')}): "
                f"{r.get('source_quote_warning')}")
    elif n_extracted == 0:
        logger.info(
            f"[SOURCE QUOTE CHECK] 0 flagged of 0 extracted studies "
            f"(nothing to check). Manual verification still required.")
    else:
        logger.info(
            f"[SOURCE QUOTE CHECK] 0 flagged of {n_extracted} extracted "
            f"studies - every extracted value was bound to a verbatim "
            f"source quote with no SE labels or within-subject "
            f"timepoint language. Manual verification still required.")

    # --- [OUTCOME/TIMEPOINT] provenance ----------------------------------
    # Skip rows where the extractor produced nothing AND has no author
    # label - those emit the ugly "? ():" line called out in #66.
    _op_rows = []
    for r in er:
        if not isinstance(r, dict):
            continue
        m_ = r.get("study_metadata", {}) or {}
        po_ = r.get("primary_outcome", {}) or {}
        author = m_.get("first_author")
        year = m_.get("year")
        outcome_sel = po_.get("outcome_selected")
        timepoint_sel = po_.get("timepoint_selected")
        # Drop fully-empty rows: no author, no year, no selection. Emitting
        # "? (): outcome=(not recorded) | timepoint=(not recorded)" told
        # the reviewer nothing and looked like a bug.
        if not any([author, year, outcome_sel, timepoint_sel]):
            continue
        _op_rows.append({
            "author": author or "?",
            "year": year or "",
            "filename": r.get("filename", "?"),
            "outcome_selected": outcome_sel,
            "timepoint_selected": timepoint_sel,
        })
    _op_recorded = sum(
        1 for x in _op_rows
        if x["outcome_selected"] is not None or x["timepoint_selected"] is not None)
    logger.info(
        f"[OUTCOME/TIMEPOINT] {_op_recorded} of {len(_op_rows)} studies "
        f"recorded outcome_selected and/or timepoint_selected. These "
        f"fields document WHICH outcome and WHICH timepoint each run "
        f"drew from - a run whose numbers change between executions "
        f"(#11) will show the change here without opening the CSV.")
    for x in _op_rows:
        logger.info(
            f"[OUTCOME/TIMEPOINT]   {x['author']} ({x['year']}): "
            f"outcome={x['outcome_selected'] if x['outcome_selected'] is not None else '(not recorded)'} "
            f"| timepoint={x['timepoint_selected'] if x['timepoint_selected'] is not None else '(not recorded)'}")

def load_config(p=None):
    path = Path(p) if p else SR_DIR / "config" / "prisma_criteria.yaml"
    with open(path, encoding="utf-8-sig") as f:
        return yaml.safe_load(f)

def main():
    ap = argparse.ArgumentParser(
        description="SR Automation Pipeline  - PRISMA 2020 / Cochrane Handbook v6.5")
    ap.add_argument("--pdf-dir",        default=None,
                    help="Override PDF input folder (default: input/sr/)")
    ap.add_argument("--config",         default=None,
                    help="Path to prisma_criteria.yaml")
    ap.add_argument("--effect-measure", default=None,
                    choices=["OR", "RR", "MD", "SMD"])
    ap.add_argument("--model",          default=None,
                    help="Model name (default: provider's configured model)")
    ap.add_argument("--provider",       default="qwen",
                    choices=["ollama", "openai", "anthropic",
                             "deepseek", "groq", "qwen"],
                    help="AI provider for screening and extraction")
    ap.add_argument("--run-id",         default=None,
                    help="Override run timestamp (e.g. for re-runs)")

    args = ap.parse_args()
    args.model = resolve_model(args.provider, args.model)
    logger.info(f"Provider {args.provider} / model {args.model}")

    cfg = load_config(args.config)

    #  Effect measure resolution: CLI > yaml > fallback OR
    VALID = ("OR", "RR", "MD", "SMD")
    yaml_em = cfg.get("effect_measure")
    if yaml_em and yaml_em not in VALID:
        logger.error(
            f"effect_measure '{yaml_em}' in prisma_criteria.yaml "
            f"is not one of {VALID}.")
        return
    args.effect_measure = args.effect_measure or yaml_em
    if not args.effect_measure:
        args.effect_measure = "OR"
        logger.warning(
            "No effect_measure specified  - defaulting to OR. "
            "Add 'effect_measure: MD' (or SMD/RR) to prisma_criteria.yaml.")

    #  Resolve PDF input folder
    if args.pdf_dir:
        pdf_dir = Path(args.pdf_dir)
    else:
        pdf_dir = PROJECT_ROOT / "input" / "sr"

    #  Initialise project layo
    layout = SRProjectLayout(run_id=args.run_id)
    logger.info(f"Project folder: {layout.project}")
    # Every audit CSV row carries this run's id: #17 (extraction
    # non-determinism) means the same paper can carry different values
    # in different runs' CSVs, and a CSV without a run id is silently
    # conflatable across runs (observed in Session 14).
    _run_id = str(getattr(layout, "run_id", "") or Path(str(layout.project)).name)

    #  Stage 1: Upload
    logger.info("=== STAGE 1: Upload ===")
    if args.provider == "anthropic":
        fm   = FileManager()
        recs = fm.upload_directory(pdf_dir)
    else:
        from .src.upload.file_manager import local_records
        recs = local_records(pdf_dir)
        logger.info(
            f"[UPLOAD] Non-Anthropic provider  - "
            f"using local PDF paths ({len(recs)} files)")

    # Copy PDFs into project uploads\ and update pdf_path in each record
    pdf_sources = [Path(r["pdf_path"]) for r in recs if r.get("pdf_path")]
    copied      = layout.initialise(pdf_sources)
    path_map    = {p.name: p for p in copied}
    for r in recs:
        name = Path(r.get("pdf_path", "")).name
        if name in path_map:
            r["pdf_path"] = str(path_map[name])

    # Write upload manifest
    pd.DataFrame(recs).to_csv(
        layout.uploads / "upload_manifest.csv", index=False)

    # Stage 2: Screening
    logger.info("=== STAGE 2: Screening ===")
    sr = RelevanceScreener(
        pico_criteria      = cfg["pico"],
        inclusion_criteria = cfg.get("inclusion_criteria", []),
        exclusion_criteria = cfg.get("exclusion_criteria", []),
        model              = args.model,
        provider           = args.provider,
    ).screen_batch(recs)

    for _r in sr:
        if isinstance(_r, dict):
            _r.setdefault("run_id", _run_id)
    write_screens(layout.screens_csv, sr)

    included = [r for r in recs
                if any(s["filename"] == r["filename"]
                       and s["decision"] == "INCLUDE"
                       for s in sr)]

    # --- Screening accounting: a paper must never vanish silently ---------
    # Observed in a real run: one transient network error during screening
    # (error -> UNCERTAIN -> not INCLUDE) removed a paper from the entire
    # review, shifted the pooled SMD by ~0.26, and the only trace was a
    # single ERROR line mid-log. Every non-INCLUDE outcome is now stated,
    # and error-based drops are labelled as what they are: not scientific
    # judgments and not valid PRISMA exclusions.
    _screen_errors    = [s for s in sr if s.get("error")]
    _screen_excluded  = [s for s in sr
                         if s.get("decision") == "EXCLUDE" and not s.get("error")]
    _screen_uncertain = [s for s in sr
                         if s.get("decision") not in ("INCLUDE", "EXCLUDE")
                         and not s.get("error")]
    logger.info(
        f"[SCREENING] {len(included)} INCLUDE / {len(_screen_excluded)} "
        f"EXCLUDE / {len(_screen_uncertain)} UNCERTAIN / "
        f"{len(_screen_errors)} ERROR of {len(sr)} papers")
    for s in _screen_excluded:
        logger.info(f"[SCREENING]   EXCLUDE {s.get('filename')}: "
                    f"{str(s.get('rationale', ''))[:160]}")
    for s in _screen_uncertain:
        logger.warning(
            f"[SCREENING] UNCERTAIN - {s.get('filename')} will NOT proceed "
            f"in this run. The model could not decide; adjudicate manually "
            f"(REVIEWER_GUIDE.md) and re-run, or record a PRISMA exclusion "
            f"reason.")
    for s in _screen_errors:
        logger.warning(
            f"[SCREENING] ERROR - {s.get('filename')} will NOT proceed in "
            f"this run because the screening CALL FAILED "
            f"({str(s.get('error'))[:160]}). This is NOT a scientific "
            f"judgment and NOT a valid PRISMA exclusion - re-run the "
            f"pipeline or screen this paper manually.")

    if not included:
        logger.error("No studies included after screening. Stopping.")
        return

    # Stage 3: Extraction
    logger.info("=== STAGE 3: Extraction ===")
    er = DataExtractor(
        pico_criteria = cfg.get("pico", {}),
        model         = args.model,
        provider      = args.provider,
    ).extract_batch(included)

    for _r in er:
        if isinstance(_r, dict):
            _r.setdefault("run_id", _run_id)

    write_extracts(layout.extracted_csv, er)

    # Stage 3.5: RoB 2.0
    logger.info("=== STAGE 3.5: RoB 2.0 Assessment ===")
    rob = RoB2Assessor(
        model    = args.model,
        provider = args.provider,
    ).assess_batch(included)

    for _r in rob:
        if isinstance(_r, dict):
            _r.setdefault("run_id", _run_id)
    write_rob2(layout.rob2_csv, rob)

    # Stage 4: Meta-Analysis
    logger.info("=== STAGE 4: Meta-Analysis ===")
    reported = [r.get("primary_outcome", {}).get("effect_measure") for r in er
                if r.get("primary_outcome", {}).get("outcome_match", True) is not False]
    reported = [x for x in reported if x]
    if reported:
        n_ratio = sum(1 for x in reported if x in ("OR", "RR", "HR"))
        n_diff  = sum(1 for x in reported if x in ("MD", "SMD"))
        if args.effect_measure in ("OR", "RR") and n_diff > n_ratio:
            logger.warning(
                f"Chosen {args.effect_measure} but {n_diff}/{len(reported)} "
                f"studies report continuous measures  - consider --effect-measure MD/SMD.")
        elif args.effect_measure in ("MD", "SMD") and n_ratio > n_diff:
            logger.warning(
                f"Chosen {args.effect_measure} but {n_ratio}/{len(reported)} "
                f"studies report ratio measures  - consider --effect-measure OR/RR.")

    rows      = []
    meta_audit= []
    for r in er:
        m  = r.get("study_metadata",  {})
        po = r.get("primary_outcome", {})
        pt = r.get("participants",    {})
        # sd_se_warning lives at the top level of r, not inside
        # primary_outcome - the extraction restructuring step only moves a
        # fixed list of known keys into primary_outcome, and this isn't on
        # it. Only ever set on the text-fallback path (see data_extractor.py
        # _flag_possible_se_as_sd); Anthropic-provider extractions never
        # get this flag, since _extract_anthropic has no text-fallback path.
        sd_se_warning = r.get("sd_se_warning")
        group_timepoint_warning = r.get("group_timepoint_warning")
        # #48: deterministic verification bound to the NUMBERS - checks
        # each extracted value against the verbatim source quote the
        # extraction schema now requires per arm (data_extractor.py
        # _flag_suspect_source_quotes). Set on both extraction paths.
        source_quote_warning = r.get("source_quote_warning")
        audit_row = {
            # NOTE: audit_logger.write_results uses a fixed fieldnames
            # list with extrasaction="ignore" (#47) - "run_id" must be
            # added there too, or this key is silently dropped from
            # meta_analysis_results.csv.
            "run_id"            : _run_id,
            "first_author"      : m.get("first_author"),
            "year"              : m.get("year"),
            "filename"          : r.get("filename"),
            "outcome_match"     : po.get("outcome_match"),
            "effect_measure"    : args.effect_measure,
            "hedges_g"          : None,
            "ci_lower"          : None,
            "ci_upper"          : None,
            "n_intervention"    : pt.get("n_intervention"),
            "n_control"         : pt.get("n_control"),
            "mean_intervention" : po.get("mean_intervention"),
            "sd_intervention"   : po.get("sd_intervention"),
            "mean_control"      : po.get("mean_control"),
            "sd_control"        : po.get("sd_control"),
            "included_in_meta"  : False,
            "skip_reason"       : None,
            "plausibility_flag" : None,
            "sd_se_warning"     : sd_se_warning,
            "group_timepoint_warning" : group_timepoint_warning,
            "source_quote_warning"    : source_quote_warning,
        }
        try:
            if po.get("outcome_match") is False:
                raise ValueError(
                    f"outcome_match=False: {po.get('match_rationale', '')}")
            est, cl, cu = (po.get("effect_estimate"),
                           po.get("ci_lower_95"),
                           po.get("ci_upper_95"))
            if est is None or cl is None or cu is None:
                if args.effect_measure not in ("MD", "SMD"):
                    raise ValueError(
                        "missing effect_estimate/CI "
                        "(no raw-mean fallback for OR/RR)")
                mi, si = po.get("mean_intervention"), po.get("sd_intervention")
                mc, sc = po.get("mean_control"),      po.get("sd_control")
                ni, nc = pt.get("n_intervention"),    pt.get("n_control")
                # fallback: split n_total evenly if per-arm N not extracted
                if (ni is None or nc is None) and pt.get("n_total"):
                    half = float(pt["n_total"]) / 2
                    ni = ni if ni is not None else half
                    nc = nc if nc is not None else half
                if None in (mi, si, mc, sc, ni, nc) or \
                        float(ni) <= 0 or float(nc) <= 0:
                    raise ValueError(
                        "insufficient mean/SD/N to derive effect size")
                mi,si,mc,sc,ni,nc = (float(mi), float(si),
                                     float(mc), float(sc),
                                     float(ni), float(nc))
                if args.effect_measure == "SMD":
                    df2  = ni + nc - 2
                    if df2 <= 0:
                        raise ValueError("insufficient df for Hedges g")
                    sd_p = (((ni-1)*si**2 + (nc-1)*sc**2) / df2) ** 0.5
                    if sd_p == 0:
                        raise ValueError("pooled SD is zero")
                    d   = (mi - mc) / sd_p
                    J   = 1 - 3 / (4 * df2 - 1)
                    est = J * d
                    se  = (J**2 * ((ni+nc)/(ni*nc) +
                                   d**2 / (2*(ni+nc)))) ** 0.5
                    cl, cu = est - 1.96*se, est + 1.96*se
                    logger.info(
                        f"Hedges g for {m.get('first_author','?')}: "
                        f"g={est:.3f} [{cl:.3f},{cu:.3f}]")
                else:
                    est = mi - mc
                    se  = (si**2/ni + sc**2/nc) ** 0.5
                    cl, cu = est - 1.96*se, est + 1.96*se
                    logger.info(
                        f"MD for {m.get('first_author','?')}: "
                        f"MD={est:.3f} [{cl:.3f},{cu:.3f}]")
            else:
                # Extraction supplied effect_estimate/ci_lower_95/
                # ci_upper_95 directly - previously used with no log
                # line at all. Model-reported effect sizes are the
                # least-verifiable input this stage accepts, so say so.
                logger.info(
                    f"Using MODEL-REPORTED effect estimate for "
                    f"{m.get('first_author','?')}: {args.effect_measure}="
                    f"{float(est):.3f} [{float(cl):.3f},{float(cu):.3f}] "
                    f"(supplied by extraction, not recomputed from "
                    f"means/SDs - verify against the source PDF)")

            author_label = f"{m.get('first_author','?')} ({m.get('year','')})"
            plausibility_flag = _check_plausibility(
                args.effect_measure, float(est), author_label)

            rows.append({
                "study"               : author_label,
                "effect_estimate"     : float(est),
                "ci_lower"            : float(cl),
                "ci_upper"            : float(cu),
                "n_intervention"      : pt.get("n_intervention"),
                "n_control"           : pt.get("n_control"),
                "n_events_intervention": po.get("n_events_intervention"),
                "n_events_control"    : po.get("n_events_control"),
                "mean_intervention"   : po.get("mean_intervention"),
                "sd_intervention"     : po.get("sd_intervention"),
                "mean_control"        : po.get("mean_control"),
                "sd_control"          : po.get("sd_control"),
            })
            audit_row.update({
                "hedges_g"          : float(est),
                "ci_lower"          : float(cl),
                "ci_upper"          : float(cu),
                "included_in_meta"  : True,
                "plausibility_flag" : plausibility_flag,
            })

        except Exception as e:
            logger.warning(f"Skip study: {e}")
            audit_row["skip_reason"] = str(e)

        meta_audit.append(audit_row)

    write_results(layout.results_csv, meta_audit)

    _log_stage4_summary(meta_audit, er, args.effect_measure)

    # ---------------------------------------------------------------------
    # [OUTCOME/TIMEPOINT] provenance surfacing (#22 / #51).
    # Extraction is non-deterministic (#11): the same paper can draw its
    # numbers from different outcomes or different timepoints across runs
    # (Ang's bimodal g=+0.075 vs -0.248 was the motivating case). The
    # schema records outcome_selected and timepoint_selected per study;
    # the fields land in primary_outcome after the restructure step on
    # both extraction paths. Surface them here so a reviewer sees WHICH
    # row of each paper's results the pooled estimate is keyed to,
    # without opening extracted_data.csv.
    # ---------------------------------------------------------------------
    _op_rows = []
    for r in er:
        if not isinstance(r, dict):
            continue
        m_ = r.get("study_metadata", {}) or {}
        po_ = r.get("primary_outcome", {}) or {}
        outcome_sel = po_.get("outcome_selected")
        timepoint_sel = po_.get("timepoint_selected")
        _op_rows.append({
            "author": m_.get("first_author") or "?",
            "year": m_.get("year") or "",
            "filename": r.get("filename", "?"),
            "outcome_selected": outcome_sel,
            "timepoint_selected": timepoint_sel,
        })
    _op_recorded = sum(
        1 for x in _op_rows
        if x["outcome_selected"] is not None or x["timepoint_selected"] is not None)
    logger.info(
        f"[OUTCOME/TIMEPOINT] {_op_recorded} of {len(_op_rows)} studies "
        f"recorded outcome_selected and/or timepoint_selected. These "
        f"fields document WHICH outcome and WHICH timepoint each run "
        f"drew from - a run whose numbers change between executions "
        f"(#11) will show the change here without opening the CSV.")
    for x in _op_rows:
        logger.info(
            f"[OUTCOME/TIMEPOINT]   {x['author']} ({x['year']}): "
            f"outcome={x['outcome_selected'] if x['outcome_selected'] is not None else '(not recorded)'} "
            f"| timepoint={x['timepoint_selected'] if x['timepoint_selected'] is not None else '(not recorded)'}")

    if len(rows) < 2:
        logger.error("< 2 studies with usable data. Aborting meta-analysis.")
        layout.mirror_all()
        return

    ma = MetaAnalyzer().run(
        data           = pd.DataFrame(rows),
        effect_measure = args.effect_measure)
    logger.info(
        f"Pooled {args.effect_measure}={ma['pooled_effect']:.3f} "
        f"[{ma['ci_lower']:.3f},{ma['ci_upper']:.3f}] "
        f"I2={ma['I2']:.1f}%")
    if _screen_errors or _screen_uncertain:
        logger.warning(
            f"[SCREENING] REMINDER: this pooled estimate is missing "
            f"{len(_screen_errors) + len(_screen_uncertain)} paper(s) "
            f"dropped at screening for NON-SCIENTIFIC reasons (call "
            f"errors / unadjudicated UNCERTAIN) - see the [SCREENING] "
            f"block above and screening_log.csv. The estimate may be "
            f"biased by their absence.")

    # Stage 5: Forest Plot
    logger.info("=== STAGE 5: Forest Plot ===")
    fp = str(layout.figures / "forest_plot.png")
    ForestPlotGenerator().generate(
        ma_result      = ma,
        effect_measure = args.effect_measure,
        output_path    = fp)

    # Stage 6: Reports
    logger.info("=== STAGE 6: Reports ===")
    title = cfg.get("review_title", "Systematic Review")
    pico  = cfg.get("pico",  {})
    inc   = cfg.get("inclusion_criteria", [])
    exc   = cfg.get("exclusion_criteria", [])

    docx_path = str(layout.docx)
    ReportGenerator().generate(
        title              = title,
        authors            = "",
        pico               = pico,
        ma_result          = ma,
        extraction_results = er,
        screening_results  = sr,
        forest_plot_path   = fp,
        effect_measure     = args.effect_measure,
        output_path        = docx_path)

    pdf_paths = PDFReportGenerator().generate(
        title              = title,
        authors            = "",
        pico               = pico,
        inclusion_criteria = inc,
        exclusion_criteria = exc,
        ma_result          = ma,
        extraction_results = er,
        screening_results  = sr,
        rob_results        = rob,
        forest_plot_path   = fp,
        effect_measure     = args.effect_measure,
        model_name         = args.model,
        output_path        = str(layout.pdf),
        also_save_html     = True)

    # Mirror to output\sr\
    layout.mirror_all()

    logger.info("Pipeline complete.")
    logger.info(f"  Project  -> {layout.project}")
    logger.info(f"  DOCX     -> {layout.docx}")
    logger.info(f"  HTML     -> {pdf_paths.get('html', 'N/A')}")
    logger.info(f"  PDF      -> {pdf_paths.get('pdf',  'N/A')}")
    logger.info(f"  Plot     -> {fp}")
    logger.info(f"  Screens  -> {layout.screens_csv}")
    logger.info(f"  Extracts -> {layout.extracted_csv}")
    logger.info(f"  RoB2     -> {layout.rob2_csv}")
    logger.info(f"  Results  -> {layout.results_csv}")

if __name__ == "__main__":
    main()