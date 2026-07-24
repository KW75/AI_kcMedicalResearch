"""
sr/src/ui/app.py — Streamlit UI for the SR Automation Pipeline.

Run with:
    streamlit run sr/src/ui/app.py

Wraps sr/main.py pipeline stages with a browser-based interface.
Allows: config editing, PDF upload, pipeline execution, results viewing.
"""
from __future__ import annotations

import logging
import sys
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st
import yaml

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SR_DIR = Path(__file__).resolve().parent.parent.parent

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI kcMedical — SR Pipeline",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Sidebar — navigation
# ---------------------------------------------------------------------------
st.sidebar.title("🔬 SR Pipeline")
st.sidebar.markdown("**AI kcMedical Research v2.1.0**")
st.sidebar.markdown("---")

PAGES = [
    "📋  Configure",
    "📂  Upload PDFs",
    "▶️  Run Pipeline",
    "📊  Results",
    "📄  Reports",
]
page = st.sidebar.radio("Navigation", PAGES, label_visibility="collapsed")

st.sidebar.markdown("---")
st.sidebar.markdown("**Pipeline stages:**")
st.sidebar.markdown("""
1. Upload & parse PDFs
2. Relevance screening
3. Data extraction
4. RoB 2.0 assessment
5. Meta-analysis
6. Forest plot
7. Report generation
""")
st.sidebar.markdown("---")
st.sidebar.markdown(
    "📖 Full guide: open `docs/flashcard-help.html` in File Explorer",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _load_config() -> dict:
    """Load prisma_criteria.yaml."""
    path = SR_DIR / "config" / "prisma_criteria.yaml"
    if path.exists():
        with open(path, encoding="utf-8-sig") as f:
            return yaml.safe_load(f) or {}
    return {}


def _save_config(cfg: dict) -> None:
    """Save updated config to prisma_criteria.yaml."""
    path = SR_DIR / "config" / "prisma_criteria.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False)


def _csv_table(path: Path, label: str) -> None:
    """Display a CSV file as a styled dataframe if it exists."""
    if path.exists():
        df = pd.read_csv(path)
        st.markdown(f"**{label}** — {len(df)} rows")
        st.dataframe(df, use_container_width=True)
    else:
        st.info(f"{label}: not yet generated.")


# ---------------------------------------------------------------------------
# PAGE 1 — Configure
# ---------------------------------------------------------------------------
if page == "📋  Configure":
    st.title("📋 Configure SR Pipeline")
    st.markdown(
        "Edit your PRISMA criteria below. Changes are saved to "
        "`sr/config/prisma_criteria.yaml`."
    )

    cfg = _load_config()

    with st.form("config_form"):
        st.subheader("Review Title")
        title = st.text_input(
            "Review title",
            value=cfg.get("review_title", ""),
            label_visibility="collapsed",
        )

        st.subheader("PICO")
        pico = cfg.get("pico", {})
        col1, col2 = st.columns(2)
        with col1:
            population    = st.text_input("Population",    value=pico.get("population", ""))
            intervention  = st.text_input("Intervention",  value=pico.get("intervention", ""))
        with col2:
            comparator    = st.text_input("Comparator",    value=pico.get("comparator", ""))
            outcome       = st.text_input("Outcome",       value=pico.get("outcome", ""))
        study_design      = st.text_input("Study design",  value=pico.get("study_design", ""))

        st.subheader("Effect Measure")
        effect_measure = st.selectbox(
            "Effect measure",
            ["OR", "RR", "MD", "SMD"],
            index=["OR", "RR", "MD", "SMD"].index(cfg.get("effect_measure", "OR")),
            label_visibility="collapsed",
        )

        st.subheader("Inclusion Criteria")
        inc_text = st.text_area(
            "One criterion per line",
            value="\n".join(cfg.get("inclusion_criteria", [])),
            height=150,
            label_visibility="collapsed",
        )

        st.subheader("Exclusion Criteria")
        exc_text = st.text_area(
            "One criterion per line",
            value="\n".join(cfg.get("exclusion_criteria", [])),
            height=150,
            label_visibility="collapsed",
        )

        submitted = st.form_submit_button("💾 Save Configuration", type="primary")

    if submitted:
        new_cfg = {
            "review_title": title,
            "pico": {
                "population":   population,
                "intervention": intervention,
                "comparator":   comparator,
                "outcome":      outcome,
                "study_design": study_design,
            },
            "effect_measure": effect_measure,
            "inclusion_criteria": [
                line.strip()
                for line in inc_text.splitlines()
                if line.strip()
            ],
            "exclusion_criteria": [
                line.strip()
                for line in exc_text.splitlines()
                if line.strip()
            ],
        }
        _save_config(new_cfg)
        st.success("✅ Configuration saved to sr/config/prisma_criteria.yaml")


# ---------------------------------------------------------------------------
# PAGE 2 — Upload PDFs
# ---------------------------------------------------------------------------
elif page == "📂  Upload PDFs":
    st.title("📂 Upload PDF Articles")
    st.markdown(
        "Upload PDF files to `sr/data/uploads/`. "
        "These will be processed by the pipeline."
    )

    upload_dir = SR_DIR / "data" / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    uploaded_files = st.file_uploader(
        "Choose PDF files",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if uploaded_files:
        saved = []
        for uf in uploaded_files:
            dest = upload_dir / uf.name
            dest.write_bytes(uf.read())
            saved.append(uf.name)
        st.success(f"✅ Saved {len(saved)} file(s) to `sr/data/uploads/`")
        for name in saved:
            st.markdown(f"- {name}")

    st.markdown("---")
    st.subheader("Files currently in upload folder")
    existing = sorted(upload_dir.glob("*.pdf"))
    if existing:
        for f in existing:
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                st.markdown(f"📄 {f.name}")
            with col2:
                st.markdown(f"`{f.stat().st_size // 1024} KB`")
            with col3:
                if st.button("🗑️", key=f"del_{f.name}", help=f"Delete {f.name}"):
                    f.unlink()
                    st.rerun()
        st.markdown(f"**Total: {len(existing)} PDF(s)**")
    else:
        st.info("No PDFs uploaded yet.")


# ---------------------------------------------------------------------------
# PAGE 3 — Run Pipeline
# ---------------------------------------------------------------------------
elif page == "▶️  Run Pipeline":
    st.title("▶️ Run SR Pipeline")

    cfg = _load_config()
    upload_dir = SR_DIR / "data" / "uploads"
    pdf_count  = len(list(upload_dir.glob("*.pdf"))) if upload_dir.exists() else 0

    # Pre-flight checks
    st.subheader("Pre-flight checks")
    col1, col2, col3 = st.columns(3)
    with col1:
        if cfg.get("review_title"):
            st.success("✅ Review title set")
        else:
            st.error("❌ Review title missing")
    with col2:
        if pdf_count > 0:
            st.success(f"✅ {pdf_count} PDF(s) uploaded")
        else:
            st.error("❌ No PDFs uploaded")
    with col3:
        if cfg.get("effect_measure"):
            st.success(f"✅ Effect measure: {cfg.get('effect_measure')}")
        else:
            st.warning("⚠️ Effect measure not set")

    st.markdown("---")

    # Provider + Model selection
    st.subheader("AI Provider & Model")
    provider = st.selectbox(
        "Provider",
        ["qwen", "groq", "deepseek", "openai", "anthropic", "ollama"],
        index=0,
    )
    MODEL_OPTIONS = {
        "qwen":      ["qwen3.7-plus", "qwen3.7-max", "qwen3.6-flash"],
        "groq":      ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "qwen/qwen3.6-27b"],
        "deepseek":  ["deepseek-v4-flash", "deepseek-v4-pro"],
        "openai":    ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
        "anthropic": ["claude-sonnet-4-6", "claude-opus-4-6", "claude-sonnet-4-5"],
        "ollama":    ["llama3.2", "llama3.1", "mistral", "phi3"],
    }
    model = st.selectbox("AI model", MODEL_OPTIONS[provider])
    if provider == "anthropic":
        st.warning(
            "⚠️ Anthropic may be geo-restricted in your region. "
            "Qwen or Groq are recommended alternatives."
        )
    elif provider != "anthropic":
        st.info(
            "ℹ️ PDF pages are converted to images for processing. "
            "Qwen (qwen3.7-plus) is recommended — fast, capable, and geo-unrestricted."
        )

    MODEL_OPTIONS = {
        "anthropic": ["claude-sonnet-4-6", "claude-opus-4-6", "claude-sonnet-4-5"],
        "openai":    ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
        "deepseek":  ["deepseek-chat", "deepseek-reasoner"],
        "groq":      ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
        "ollama":    ["llama3.2", "llama3.1", "mistral", "phi3"],
    }

    model = st.selectbox(
        "AI model",
        ["claude-sonnet-4-6", "claude-opus-4-6", "claude-sonnet-4-5"],
        label_visibility="collapsed",
    )

    effect_override = st.selectbox(
        "Override effect measure (optional)",
        ["— use config —", "OR", "RR", "MD", "SMD"],
        label_visibility="visible",
    )

    st.markdown("---")
    ready = cfg.get("review_title") and pdf_count > 0

    if not ready:
        st.warning("Complete the pre-flight checks before running.")

    if st.button(
        "🚀 Run Full Pipeline",
        type="primary",
        disabled=not ready,
    ):
        em = (
            effect_override
            if effect_override != "— use config —"
            else cfg.get("effect_measure", "OR")
        )

        progress = st.progress(0, text="Starting pipeline...")
        log_box  = st.empty()
        logs: list[str] = []

        # Stream logs via a custom handler
        class StreamlitHandler(logging.Handler):
            def emit(self, record):
                logs.append(self.format(record))
                log_box.code("\n".join(logs[-30:]), language="text")

        handler = StreamlitHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        logging.getLogger("sr").addHandler(handler)

        try:
            # Import and run each stage with progress updates
            progress.progress(10, text="Stage 1: Uploading...")
            from sr.src.upload.file_manager import FileManager
            fm   = FileManager()
            recs = fm.upload_directory(upload_dir)
            (SR_DIR / "data" / "uploads").mkdir(parents=True, exist_ok=True)
            pd.DataFrame(recs).to_csv(
                SR_DIR / "data" / "uploads" / "upload_manifest.csv", index=False
            )

            progress.progress(25, text="Stage 2: Screening...")
            from sr.src.screening.relevance_screener import RelevanceScreener
            sr_results = RelevanceScreener(
                pico_criteria=cfg["pico"],
                inclusion_criteria=cfg.get("inclusion_criteria", []),
                exclusion_criteria=cfg.get("exclusion_criteria", []),
                model=model,
            ).screen_batch(recs)
            (SR_DIR / "data" / "screened").mkdir(parents=True, exist_ok=True)
            pd.DataFrame(sr_results).to_csv(
                SR_DIR / "data" / "screened" / "screening_log.csv", index=False
            )
            included = [
                r for r in recs
                if any(
                    s["file_id"] == r["file_id"] and s["decision"] == "INCLUDE"
                    for s in sr_results
                )
            ]
            if not included:
                st.error("❌ No studies included after screening. Pipeline stopped.")
                st.stop()

            progress.progress(45, text="Stage 3: Extracting data...")
            from sr.src.extraction.data_extractor import DataExtractor
            er = DataExtractor(
                pico_criteria=cfg.get("pico", {}),
                pico_outcome=cfg.get("pico", {}).get("outcome"),
                model=model,
                provider=provider,
            ).extract_batch(included)


            (SR_DIR / "data" / "extracted").mkdir(parents=True, exist_ok=True)
            pd.json_normalize(er).to_csv(
                SR_DIR / "data" / "extracted" / "extracted_data.csv", index=False
            )

            progress.progress(55, text="Stage 3.5: RoB 2.0 assessment...")
            from sr.src.screening.rob2_tool import RoB2Assessor
            rob = RoB2Assessor(model=model, provider=provider).assess_batch(included)
            pd.json_normalize(rob).to_csv(
                SR_DIR / "data" / "extracted" / "rob2_assessment.csv", index=False
            )

            progress.progress(65, text="Stage 4: Meta-analysis...")
            from sr.src.analysis.meta_analysis import MetaAnalyzer
            rows = []
            for r in er:
                m_  = r.get("study_metadata", {})
                po  = r.get("primary_outcome", {})
                pt  = r.get("participants", {})
                try:
                    est = po.get("effect_estimate")
                    cl  = po.get("ci_lower_95")
                    cu  = po.get("ci_upper_95")
                    if None in (est, cl, cu):
                        raise ValueError("missing effect estimate/CI")
                    rows.append({
                        "study":            f"{m_.get('first_author','?')} ({m_.get('year','')})",
                        "effect_estimate":  float(est),
                        "ci_lower":         float(cl),
                        "ci_upper":         float(cu),
                        "n_intervention":   pt.get("n_intervention"),
                        "n_control":        pt.get("n_control"),
                    })
                except Exception as exc:
                    logs.append(f"  Skip study: {exc}")

            if len(rows) < 2:
                st.error("❌ Fewer than 2 studies with usable data. Cannot run meta-analysis.")
                st.stop()

            ma = MetaAnalyzer().run(
                data=pd.DataFrame(rows), effect_measure=em
            )
            (SR_DIR / "data" / "results").mkdir(parents=True, exist_ok=True)
            pd.DataFrame([{
                k: v for k, v in ma.items() if k != "study_effects"
            }]).to_csv(
                SR_DIR / "data" / "results" / "meta_analysis_results.csv", index=False
            )

            progress.progress(75, text="Stage 5: Forest plot...")
            from sr.src.visualization.forest_plot import ForestPlotGenerator
            fp_path = str(SR_DIR / "outputs" / "figures" / "forest_plot.png")
            (SR_DIR / "outputs" / "figures").mkdir(parents=True, exist_ok=True)
            ForestPlotGenerator().generate(
                ma_result=ma, effect_measure=em, output_path=fp_path
            )

            progress.progress(90, text="Stage 6: Generating reports...")
            from sr.src.reporting.report_generator import ReportGenerator
            from sr.src.reporting.pdf_report import PDFReportGenerator
            title_str = cfg.get("review_title", "Systematic Review")
            (SR_DIR / "outputs" / "reports").mkdir(parents=True, exist_ok=True)

            ReportGenerator().generate(
                title=title_str, authors="", pico=cfg.get("pico", {}),
                ma_result=ma, extraction_results=er, screening_results=sr_results,
                forest_plot_path=fp_path, effect_measure=em,
                output_path=str(SR_DIR / "outputs" / "reports" / "systematic_review.docx"),
            )
            PDFReportGenerator().generate(
                title=title_str, authors="", pico=cfg.get("pico", {}),
                inclusion_criteria=cfg.get("inclusion_criteria", []),
                exclusion_criteria=cfg.get("exclusion_criteria", []),
                ma_result=ma, extraction_results=er, screening_results=sr_results,
                rob_results=rob, forest_plot_path=fp_path,
                effect_measure=em, model_name=model,
                output_path=str(SR_DIR / "outputs" / "reports" / "systematic_review.pdf"),
                also_save_html=True,
            )

            progress.progress(100, text="✅ Pipeline complete!")
            st.success(
                f"✅ Pipeline complete! "
                f"{len(included)}/{len(recs)} studies included. "
                f"Pooled {em} = {ma['pooled_effect']:.3f} "
                f"[{ma['ci_lower']:.3f}, {ma['ci_upper']:.3f}], "
                f"I² = {ma['I2']:.1f}%"
            )
            st.balloons()

        except Exception as exc:
            st.error(f"❌ Pipeline error: {exc}")
        finally:
            logging.getLogger("sr").removeHandler(handler)


# ---------------------------------------------------------------------------
# PAGE 4 — Results
# ---------------------------------------------------------------------------
elif page == "📊  Results":
    st.title("📊 Results")

    tab1, tab2, tab3, tab4 = st.tabs([
        "Screening Log", "Extracted Data", "RoB 2.0", "Meta-Analysis"
    ])

    with tab1:
        _csv_table(
            SR_DIR / "data" / "screened" / "screening_log.csv",
            "Screening Log"
        )

    with tab2:
        _csv_table(
            SR_DIR / "data" / "extracted" / "extracted_data.csv",
            "Extracted Data"
        )

    with tab3:
        _csv_table(
            SR_DIR / "data" / "extracted" / "rob2_assessment.csv",
            "RoB 2.0 Assessment"
        )

    with tab4:
        _csv_table(
            SR_DIR / "data" / "results" / "meta_analysis_results.csv",
            "Meta-Analysis Results"
        )
        fp = SR_DIR / "outputs" / "figures" / "forest_plot.png"
        if fp.exists():
            st.subheader("Forest Plot")
            st.image(str(fp), use_container_width=True)
        else:
            st.info("Forest plot not yet generated.")


# ---------------------------------------------------------------------------
# PAGE 5 — Reports
# ---------------------------------------------------------------------------
elif page == "📄  Reports":
    st.title("📄 Reports")

    reports_dir = SR_DIR / "outputs" / "reports"

    # DOCX download
    docx_path = reports_dir / "systematic_review.docx"
    if docx_path.exists():
        with open(docx_path, "rb") as f:
            st.download_button(
                label="⬇️ Download DOCX report",
                data=f,
                file_name="systematic_review.docx",
                mime="application/vnd.openxmlformats-officedocument"
                     ".wordprocessingml.document",
            )
    else:
        st.info("DOCX report not yet generated.")

    # HTML preview
    html_path = reports_dir / "systematic_review.html"
    if html_path.exists():
        st.subheader("HTML Report Preview")
        html_content = html_path.read_text(encoding="utf-8", errors="replace")
        # Truncate for preview if very large
        if len(html_content) > 50_000:
            html_content = html_content[:50_000] + "\n<!-- preview truncated -->"
        st.components.v1.html(html_content, height=800, scrolling=True)
        with open(html_path, "rb") as f:
            st.download_button(
                label="⬇️ Download HTML report",
                data=f,
                file_name="systematic_review.html",
                mime="text/html",
            )
    else:
        st.info("HTML report not yet generated.")

    # PDF download
    pdf_path = reports_dir / "systematic_review.pdf"
    if pdf_path.exists():
        with open(pdf_path, "rb") as f:
            st.download_button(
                label="⬇️ Download PDF report",
                data=f,
                file_name="systematic_review.pdf",
                mime="application/pdf",
            )
    else:
        st.info("PDF report not yet generated.")
