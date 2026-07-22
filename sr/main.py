# sr/main.py  --  python sr/main.py --pdf-dir sr/data/uploads --effect-measure SMD
import argparse, logging, sys
import pandas as pd
from pathlib import Path
import yaml

# Ensure project root is on sys.path so sr.src.* imports work
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sr.src.upload.file_manager          import FileManager
from sr.src.screening.relevance_screener import RelevanceScreener
from sr.src.screening.rob2_tool          import RoB2Assessor
from sr.src.extraction.data_extractor    import DataExtractor
from sr.src.analysis.meta_analysis       import MetaAnalyzer
from sr.src.visualization.forest_plot    import ForestPlotGenerator
from sr.src.reporting.report_generator   import ReportGenerator
from sr.src.reporting.pdf_report         import PDFReportGenerator

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
        description="SR Automation Pipeline — PRISMA 2020 / Cochrane Handbook v6.5")
    ap.add_argument("--pdf-dir",    default=str(SR_DIR / "data" / "uploads"))
    ap.add_argument("--config",     default=None, help="Path to prisma_criteria.yaml")
    ap.add_argument("--effect-measure", default=None, choices=["OR","RR","MD","SMD"])
    ap.add_argument("--model",      default="claude-opus-4-7")
    args = ap.parse_args()

    cfg     = load_config(args.config)
    pdf_dir = Path(args.pdf_dir)

    # Effect measure resolution: CLI flag > yaml field > fallback OR (with warning)
    VALID = ("OR","RR","MD","SMD")
    yaml_em = cfg.get("effect_measure")
    if yaml_em and yaml_em not in VALID:
        logger.error(f"effect_measure '{yaml_em}' in prisma_criteria.yaml is not one of {VALID}."); return
    args.effect_measure = args.effect_measure or yaml_em
    if not args.effect_measure:
        args.effect_measure = "OR"
        logger.warning("No effect_measure specified — defaulting to OR. "
                       "Add 'effect_measure: MD' (or SMD/RR) to prisma_criteria.yaml.")

    out_base = SR_DIR / "outputs"

    # ── Stage 1: Upload ──────────────────────────────────────────────────────
    logger.info("=== STAGE 1: Upload ===")
    fm   = FileManager()
    recs = fm.upload_directory(pdf_dir)
    (SR_DIR / "data" / "uploads").mkdir(parents=True, exist_ok=True)
    pd.DataFrame(recs).to_csv(SR_DIR / "data" / "uploads" / "upload_manifest.csv", index=False)

    # ── Stage 2: Screening ───────────────────────────────────────────────────
    logger.info("=== STAGE 2: Screening ===")
    sr = RelevanceScreener(
        pico_criteria=cfg["pico"],
        inclusion_criteria=cfg.get("inclusion_criteria", []),
        exclusion_criteria=cfg.get("exclusion_criteria", []),
        model=args.model,
    ).screen_batch(recs)
    (SR_DIR / "data" / "screened").mkdir(parents=True, exist_ok=True)
    pd.DataFrame(sr).to_csv(SR_DIR / "data" / "screened" / "screening_log.csv", index=False)
    included = [r for r in recs
                if any(s["file_id"]==r["file_id"] and s["decision"]=="INCLUDE" for s in sr)]
    if not included:
        logger.error("No studies included after screening. Stopping."); return

    # ── Stage 3: Extraction ──────────────────────────────────────────────────
    logger.info("=== STAGE 3: Extraction ===")
    er = DataExtractor(pico_criteria=cfg.get("pico",{}), model=args.model).extract_batch(included)
    (SR_DIR / "data" / "extracted").mkdir(parents=True, exist_ok=True)
    pd.json_normalize(er).to_csv(SR_DIR / "data" / "extracted" / "extracted_data.csv", index=False)

    # ── Stage 3.5: RoB 2.0 ──────────────────────────────────────────────────
    logger.info("=== STAGE 3.5: RoB 2.0 Assessment ===")
    rob = RoB2Assessor(model=args.model).assess_batch(included)
    pd.json_normalize(rob).to_csv(SR_DIR / "data" / "extracted" / "rob2_assessment.csv", index=False)

    # ── Stage 4: Meta-Analysis ───────────────────────────────────────────────
    logger.info("=== STAGE 4: Meta-Analysis ===")
    reported = [r.get("primary_outcome",{}).get("effect_measure") for r in er
                if r.get("primary_outcome",{}).get("outcome_match", True) is not False]
    reported = [x for x in reported if x]
    if reported:
        n_ratio = sum(1 for x in reported if x in ("OR","RR","HR"))
        n_diff  = sum(1 for x in reported if x in ("MD","SMD"))
        if args.effect_measure in ("OR","RR") and n_diff > n_ratio:
            logger.warning(f"Chosen {args.effect_measure} but {n_diff}/{len(reported)} "
                           f"studies report continuous measures — consider --effect-measure MD/SMD.")
        elif args.effect_measure in ("MD","SMD") and n_ratio > n_diff:
            logger.warning(f"Chosen {args.effect_measure} but {n_ratio}/{len(reported)} "
                           f"studies report ratio measures — consider --effect-measure OR/RR.")

    rows = []
    for r in er:
        m=r.get("study_metadata",{}); po=r.get("primary_outcome",{}); pt=r.get("participants",{})
        try:
            if po.get("outcome_match") is False:
                raise ValueError(f"outcome_match=False: {po.get('match_rationale','')}")
            est,cl,cu = po.get("effect_estimate"),po.get("ci_lower_95"),po.get("ci_upper_95")
            if est is None or cl is None or cu is None:
                if args.effect_measure not in ("MD","SMD"):
                    raise ValueError("missing effect_estimate/CI (no raw-mean fallback for OR/RR)")
                mi,si = po.get("mean_intervention"),po.get("sd_intervention")
                mc,sc = po.get("mean_control"),po.get("sd_control")
                ni,nc = pt.get("n_intervention"),pt.get("n_control")
                if None in (mi,si,mc,sc,ni,nc) or float(ni)<=0 or float(nc)<=0:
                    raise ValueError("insufficient mean/SD/N to derive effect size")
                mi,si,mc,sc,ni,nc = float(mi),float(si),float(mc),float(sc),float(ni),float(nc)
                if args.effect_measure == "SMD":
                    df2 = ni+nc-2
                    if df2 <= 0: raise ValueError("insufficient df for Hedges g")
                    sd_p = (((ni-1)*si**2+(nc-1)*sc**2)/df2)**0.5
                    if sd_p == 0: raise ValueError("pooled SD is zero")
                    d = (mi-mc)/sd_p; J = 1-3/(4*df2-1)
                    est = J*d
                    se  = (J**2*((ni+nc)/(ni*nc)+d**2/(2*(ni+nc))))**0.5
                    cl,cu = est-1.96*se, est+1.96*se
                    logger.info(f"Hedges g for {m.get('first_author','?')}: g={est:.3f} [{cl:.3f},{cu:.3f}]")
                else:
                    est = mi-mc; se = (si**2/ni+sc**2/nc)**0.5
                    cl,cu = est-1.96*se, est+1.96*se
                    logger.info(f"MD for {m.get('first_author','?')}: MD={est:.3f} [{cl:.3f},{cu:.3f}]")
            rows.append({"study":f"{m.get('first_author','?')} ({m.get('year','')})",
                "effect_estimate":float(est),"ci_lower":float(cl),"ci_upper":float(cu),
                "n_intervention":pt.get("n_intervention"),"n_control":pt.get("n_control"),
                "n_events_intervention":po.get("n_events_intervention"),
                "n_events_control":po.get("n_events_control"),
                "mean_intervention":po.get("mean_intervention"),
                "sd_intervention":po.get("sd_intervention"),
                "mean_control":po.get("mean_control"),"sd_control":po.get("sd_control")})
        except Exception as e:
            logger.warning(f"Skip study: {e}")

    if len(rows) < 2:
        logger.error("< 2 studies with usable data. Aborting meta-analysis."); return

    ma = MetaAnalyzer().run(data=pd.DataFrame(rows), effect_measure=args.effect_measure)
    (SR_DIR / "data" / "results").mkdir(parents=True, exist_ok=True)
    pd.DataFrame([{k:v for k,v in ma.items() if k!="study_effects"}]).to_csv(
        SR_DIR / "data" / "results" / "meta_analysis_results.csv", index=False)
    logger.info(f"Pooled {args.effect_measure}={ma['pooled_effect']:.3f} "
                f"[{ma['ci_lower']:.3f},{ma['ci_upper']:.3f}] I2={ma['I2']:.1f}%")

    # ── Stage 5: Forest Plot ─────────────────────────────────────────────────
    logger.info("=== STAGE 5: Forest Plot ===")
    fp = str(out_base / "figures" / "forest_plot.png")
    ForestPlotGenerator().generate(ma_result=ma, effect_measure=args.effect_measure, output_path=fp)

    # ── Stage 6: Reports ─────────────────────────────────────────────────────
    logger.info("=== STAGE 6: Reports ===")
    title = cfg.get("review_title","Systematic Review")
    pico  = cfg.get("pico",{})
    inc   = cfg.get("inclusion_criteria",[])
    exc   = cfg.get("exclusion_criteria",[])

    ReportGenerator().generate(
        title=title, authors="", pico=pico, ma_result=ma,
        extraction_results=er, screening_results=sr,
        forest_plot_path=fp, effect_measure=args.effect_measure,
        output_path=str(out_base / "reports" / "systematic_review.docx"))

    paths = PDFReportGenerator().generate(
        title=title, authors="", pico=pico,
        inclusion_criteria=inc, exclusion_criteria=exc,
        ma_result=ma, extraction_results=er, screening_results=sr,
        rob_results=rob, forest_plot_path=fp,
        effect_measure=args.effect_measure, model_name=args.model,
        output_path=str(out_base / "reports" / "systematic_review.pdf"),
        also_save_html=True)

    logger.info("Pipeline complete.")
    logger.info(f"  DOCX -> {out_base}/reports/systematic_review.docx")
    logger.info(f"  HTML -> {paths.get('html','N/A')}")
    logger.info(f"  PDF  -> {paths.get('pdf','N/A')}")
    logger.info(f"  Plot -> {fp}")


if __name__ == "__main__":
    main()
