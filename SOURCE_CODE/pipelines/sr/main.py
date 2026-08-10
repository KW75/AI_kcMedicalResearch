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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s -- %(message)s")
logger = logging.getLogger("sr.main")

SR_DIR = Path(__file__).resolve().parent


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
    ap.add_argument("--model",          default="qwen3.7-plus")
    ap.add_argument("--provider",       default="qwen",
                    choices=["ollama", "openai", "anthropic",
                             "deepseek", "groq", "qwen"],
                    help="AI provider for screening and extraction")
    ap.add_argument("--run-id",         default=None,
                    help="Override run timestamp (e.g. for re-runs)")

    args = ap.parse_args()

    cfg = load_config(args.config)

    # ?? Effect measure resolution: CLI > yaml > fallback OR ??????????????????
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

    # ?? Resolve PDF input folder ??????????????????????????????????????????????
    if args.pdf_dir:
        pdf_dir = Path(args.pdf_dir)
    else:
        pdf_dir = PROJECT_ROOT / "input" / "sr"

    # ?? Initialise project layout ?????????????????????????????????????????????
    layout = SRProjectLayout(run_id=args.run_id)
    logger.info(f"Project folder: {layout.project}")

    # ?? Stage 1: Upload ???????????????????????????????????????????????????????
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

    # ?? Stage 2: Screening ????????????????????????????????????????????????????
    logger.info("=== STAGE 2: Screening ===")
    sr = RelevanceScreener(
        pico_criteria      = cfg["pico"],
        inclusion_criteria = cfg.get("inclusion_criteria", []),
        exclusion_criteria = cfg.get("exclusion_criteria", []),
        model              = args.model,
        provider           = args.provider,
    ).screen_batch(recs)

    write_screens(layout.screens_csv, sr)

    included = [r for r in recs
                if any(s["filename"] == r["filename"]
                       and s["decision"] == "INCLUDE"
                       for s in sr)]
    if not included:
        logger.error("No studies included after screening. Stopping.")
        return

    # ?? Stage 3: Extraction ???????????????????????????????????????????????????
    logger.info("=== STAGE 3: Extraction ===")
    er = DataExtractor(
        pico_criteria = cfg.get("pico", {}),
        model         = args.model,
        provider      = args.provider,
    ).extract_batch(included)

    write_extracts(layout.extracted_csv, er)

    # ?? Stage 3.5: RoB 2.0 ???????????????????????????????????????????????????
    logger.info("=== STAGE 3.5: RoB 2.0 Assessment ===")
    rob = RoB2Assessor(
        model    = args.model,
        provider = args.provider,
    ).assess_batch(included)

    write_rob2(layout.rob2_csv, rob)

    # ?? Stage 4: Meta-Analysis ????????????????????????????????????????????????
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
        audit_row = {
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

            rows.append({
                "study"               : f"{m.get('first_author','?')} ({m.get('year','')})",
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
                "hedges_g"         : float(est),
                "ci_lower"         : float(cl),
                "ci_upper"         : float(cu),
                "included_in_meta" : True,
            })

        except Exception as e:
            logger.warning(f"Skip study: {e}")
            audit_row["skip_reason"] = str(e)

        meta_audit.append(audit_row)

    write_results(layout.results_csv, meta_audit)

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

    # ?? Stage 5: Forest Plot ??????????????????????????????????????????????????
    logger.info("=== STAGE 5: Forest Plot ===")
    fp = str(layout.figures / "forest_plot.png")
    ForestPlotGenerator().generate(
        ma_result      = ma,
        effect_measure = args.effect_measure,
        output_path    = fp)

    # ?? Stage 6: Reports ??????????????????????????????????????????????????????
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

    # ?? Mirror to output\sr\ ??????????????????????????????????????????????????
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