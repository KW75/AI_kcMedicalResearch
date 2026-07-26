"""
src/ui/app.py  –  Main Streamlit UI for AI kcMedicalResearch v2.2.0
Landing page: six mode cards (2×3 grid)
Each mode page: instructions, settings, file upload, run, output, downloads
"""

from __future__ import annotations

import base64
import os
import subprocess
import sys
import time
from pathlib import Path

import streamlit as st

# ── paths ──────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent.parent.parent
ASSETS_DIR = BASE_DIR / "assets"
INPUT_DIR  = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
REPORTS_DIR = BASE_DIR / "reports"
MAIN_PY    = BASE_DIR / "src" / "main.py"

# ── mode configuration ─────────────────────────────────────────────────────────
MODES: dict[str, dict] = {
    "coding": {
        "label":        "Coding",
        "icon":         ASSETS_DIR / "icon_coding.png",
        "accent":       "#4A90D9",
        "bg":           "#EBF4FF",
        "description":  "AI-assisted code generation, review, and revision.",
        "extensions":   [".py", ".js", ".ts", ".html", ".css", ".java",
                         ".c", ".cpp", ".cs", ".rb", ".go", ".rs", ".txt", ".md"],
        "instructions": (
            "**How to use Coding mode**\n\n"
            "1. Drop source files into `input/coding/`.\n"
            "2. Choose your provider and model below.\n"
            "3. Click **Run Coding** — the AI will review / generate code.\n"
            "4. Outputs (code files + markdown report) appear in `output/coding/`.\n\n"
            "_Tip: use the **--revise** flag from the CLI for a Builder→Reviewer→Tester pipeline._"
        ),
    },
    "writing": {
        "label":        "Writing",
        "icon":         ASSETS_DIR / "icon_writing.png",
        "accent":       "#27AE60",
        "bg":           "#EAFAF1",
        "description":  "Generate structured medical writing reports from documents.",
        "extensions":   [".txt", ".md", ".docx", ".pdf"],
        "instructions": (
            "**How to use Writing mode**\n\n"
            "1. Drop `.txt`, `.md`, `.docx`, or `.pdf` files into `input/writing/`.\n"
            "2. Choose your provider and model.\n"
            "3. Click **Run Writing** — a structured report is generated.\n"
            "4. Markdown and Word outputs appear in `output/writing/`."
        ),
    },
    "appraisal": {
        "label":        "Appraisal",
        "icon":         ASSETS_DIR / "icon_appraisal.png",
        "accent":       "#8E44AD",
        "bg":           "#F5EEF8",
        "description":  "Critical appraisal of research articles (RCT, cohort, diagnostic).",
        "extensions":   [".pdf", ".txt", ".md", ".docx"],
        "instructions": (
            "**How to use Appraisal mode**\n\n"
            "1. Drop article PDFs or text files into `input/appraisal/`.\n"
            "2. Choose your provider and model.\n"
            "3. Click **Run Appraisal** — three parallel agents assess the article.\n"
            "4. Merged report (`.md` + `.docx`) appears in `output/appraisal/`."
        ),
    },
    "rct_search": {
        "label":        "RCT Search",
        "icon":         ASSETS_DIR / "icon_rct_search.png",
        "accent":       "#E67E22",
        "bg":           "#FEF9E7",
        "description":  "Build and validate RCT search strategies for PubMed / Embase.",
        "extensions":   [".txt", ".md"],
        "instructions": (
            "**How to use RCT Search mode**\n\n"
            "1. Enter your PICO topic in the text box below, or place a `topic.md` "
            "file in `input/rct_search/`.\n"
            "2. Choose your provider and model.\n"
            "3. Click **Run RCT Search** — the pipeline builds, validates, and refines "
            "a search strategy.\n"
            "4. Outputs appear in `output/rct_search/`."
        ),
    },
    "search": {
        "label":        "Search",
        "icon":         ASSETS_DIR / "icon_search.png",
        "accent":       "#16A085",
        "bg":           "#E8F8F5",
        "description":  "Evidence-based clinical or paper search with structured results.",
        "extensions":   [".txt", ".md"],
        "instructions": (
            "**How to use Search mode**\n\n"
            "1. Enter your clinical topic or paper title in the text box below, or "
            "place a `topic.md` file in `input/search/`.\n"
            "2. Choose provider and model.\n"
            "3. Click **Run Search** — results are saved to `output/search/`."
        ),
    },
    "sr": {
        "label":        "Systematic Review",
        "icon":         ASSETS_DIR / "icon_sr.png",
        "accent":       "#C0392B",
        "bg":           "#FDEDEC",
        "description":  "Full systematic review pipeline: PRISMA screening, data extraction, meta-analysis.",
        "extensions":   [".pdf"],
        "instructions": (
            "**How to use Systematic Review mode**\n\n"
            "1. Drop article PDFs into `input/sr/`.\n"
            "2. Edit `docs/sr/prisma_criteria.md` with your inclusion/exclusion criteria.\n"
            "3. Click **Launch SR UI** — the dedicated SR Streamlit app opens.\n"
            "4. Results are saved to `output/sr/`."
        ),
    },
}

PROVIDERS = ["ollama", "openai", "anthropic", "deepseek", "groq", "qwen"]

# ── helpers ────────────────────────────────────────────────────────────────────

def _icon_b64(path: Path) -> str | None:
    """Return base64-encoded PNG/JPEG as data-URI, or None if file missing."""
    if not path.exists():
        return None
    ext = path.suffix.lower().lstrip(".")
    mime = "jpeg" if ext in ("jpg", "jpeg") else "png"
    return f"data:image/{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def _logo_b64() -> str | None:
    for name in ("logo_AI_kcMedicalResearch.png", "logo_AI_kcMedicalResearch.jpg"):
        p = ASSETS_DIR / name
        if p.exists():
            return _icon_b64(p)
    return None


def _open_folder(folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    if sys.platform == "win32":
        os.startfile(str(folder))
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(folder)])
    else:
        subprocess.Popen(["xdg-open", str(folder)])


def _count_files(folder: Path, exts: list[str]) -> int:
    if not folder.exists():
        return 0
    return sum(1 for f in folder.iterdir() if f.is_file() and f.suffix.lower() in exts)


def _latest_outputs(folder: Path, suffixes: tuple[str, ...] = (".md", ".docx")) -> list[Path]:
    if not folder.exists():
        return []
    files = [f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in suffixes]
    return sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)[:4]


def _run_mode(mode: str, provider: str, model: str, topic: str = "") -> str:
    """Run src/main.py in the requested mode, return combined stdout+stderr."""
    # Write topic file for search / rct_search
    if mode in ("search", "rct_search") and topic.strip():
        topic_file = INPUT_DIR / mode / "topic.md"
        topic_file.parent.mkdir(parents=True, exist_ok=True)
        topic_file.write_text(topic.strip(), encoding="utf-8")

    cmd = [sys.executable, str(MAIN_PY), "--mode", mode, "--provider", provider]
    if model.strip():
        cmd += ["--model", model.strip()]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(BASE_DIR),
            timeout=600,
        )
        output = result.stdout + ("\n" + result.stderr if result.stderr.strip() else "")
        return output.strip()
    except subprocess.TimeoutExpired:
        return "⚠️  Process timed out after 10 minutes."
    except Exception as exc:  # noqa: BLE001
        return f"⚠️  Error launching process: {exc}"


# ── global CSS ─────────────────────────────────────────────────────────────────

def _inject_css() -> None:
    st.markdown(
        """
        <style>
        /* ── global ── */
        body { font-family: "Segoe UI", sans-serif; }
        .block-container { padding-top: 1.5rem; }

        /* ── mode cards ── */
        .mode-card {
            border-radius: 14px;
            padding: 1.4rem 1.2rem 1.2rem;
            text-align: center;
            transition: transform .15s, box-shadow .15s;
            cursor: default;
            height: 100%;
        }
        .mode-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 24px rgba(0,0,0,.12);
        }
        .mode-card img { width: 64px; height: 64px; object-fit: contain; margin-bottom: .6rem; }
        .mode-card h3 { margin: .4rem 0 .2rem; font-size: 1.1rem; }
        .mode-card p  { font-size: .85rem; color: #555; margin: 0; }

        /* ── action buttons row ── */
        .btn-row { display: flex; gap: .5rem; justify-content: center; margin-top: .8rem; flex-wrap: wrap; }

        /* ── header ── */
        .app-header {
            display: flex; align-items: center; gap: 1rem;
            padding: .6rem 0 1rem;
            border-bottom: 2px solid #e0e0e0;
            margin-bottom: 1.2rem;
        }
        .app-header img { height: 56px; }
        .app-header h1 { font-size: 1.6rem; margin: 0; color: #1a1a2e; }

        /* ── output box ── */
        .output-box {
            background: #1e1e1e; color: #d4d4d4;
            border-radius: 8px; padding: 1rem;
            font-family: "Consolas", monospace; font-size: .82rem;
            max-height: 420px; overflow-y: auto;
            white-space: pre-wrap; word-break: break-word;
        }

        /* ── file badge ── */
        .file-badge {
            display: inline-block;
            background: #f0f0f0; border-radius: 6px;
            padding: .15rem .55rem; font-size: .78rem;
            margin: .15rem; color: #333;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ── header ─────────────────────────────────────────────────────────────────────

def _render_header(subtitle: str = "") -> None:
    logo = _logo_b64()
    logo_html = f'<img src="{logo}" alt="logo">' if logo else ""
    sub_html = f"<small style='color:#666'>{subtitle}</small>" if subtitle else ""
    st.markdown(
        f"""
        <div class="app-header">
            {logo_html}
            <div>
                <h1>AI kcMedicalResearch</h1>
                {sub_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── home page ──────────────────────────────────────────────────────────────────

def _home_page() -> None:
    _render_header("Select a mode to begin")

    mode_keys = list(MODES.keys())
    rows = [mode_keys[:3], mode_keys[3:]]

    for row in rows:
        cols = st.columns(3, gap="medium")
        for col, key in zip(cols, row):
            cfg = MODES[key]
            icon_uri = _icon_b64(cfg["icon"]) or ""
            icon_html = f'<img src="{icon_uri}" alt="{cfg["label"]}">' if icon_uri else "🔬"
            n_in = _count_files(INPUT_DIR / key, cfg["extensions"])

            with col:
                st.markdown(
                    f"""
                    <div class="mode-card" style="background:{cfg['bg']};
                         border: 2px solid {cfg['accent']}20;">
                        {icon_html}
                        <h3 style="color:{cfg['accent']}">{cfg['label']}</h3>
                        <p>{cfg['description']}</p>
                        <p style="margin-top:.5rem;font-size:.78rem;color:#888">
                            📂 {n_in} file(s) in input
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                # Four action buttons
                b1, b2 = st.columns(2)
                with b1:
                    if st.button("📂 Input",  key=f"inp_{key}",  use_container_width=True):
                        _open_folder(INPUT_DIR / key)
                    if st.button("📤 Output", key=f"out_{key}",  use_container_width=True):
                        _open_folder(OUTPUT_DIR / key)
                with b2:
                    if st.button(f"▶ {cfg['label']}", key=f"go_{key}", use_container_width=True):
                        st.session_state["page"] = key
                        st.rerun()
                    if st.button("🚪 Exit",   key=f"exit_{key}", use_container_width=True):
                        st.markdown("### Session ended. You may close this tab.")
                        st.stop()


# ── mode page ──────────────────────────────────────────────────────────────────

def _mode_page(mode: str) -> None:
    cfg = MODES[mode]
    _render_header(f"Mode: {cfg['label']}")

    # ── top nav ────────────────────────────────────────────────────────────────
    nav_l, nav_r = st.columns([1, 5])
    with nav_l:
        if st.button("⬅ Home", use_container_width=True):
            st.session_state["page"] = "home"
            st.rerun()
    with nav_r:
        if st.button("🚪 Exit", use_container_width=True):
            st.markdown("### Session ended. You may close this tab.")
            st.stop()

    st.divider()

    # ── instructions ───────────────────────────────────────────────────────────
    with st.expander("📖 Instructions", expanded=False):
        st.markdown(cfg["instructions"])

    # ── icon + title ───────────────────────────────────────────────────────────
    icon_uri = _icon_b64(cfg["icon"])
    if icon_uri:
        ic, ti = st.columns([1, 8])
        with ic:
            st.image(str(cfg["icon"]), width=72)
        with ti:
            st.subheader(cfg["label"])
    else:
        st.subheader(cfg["label"])

    # ── settings ───────────────────────────────────────────────────────────────
    with st.expander("⚙️ Provider / Model settings", expanded=True):
        col_p, col_m = st.columns(2)
        with col_p:
            provider = st.selectbox("Provider", PROVIDERS,
                                    index=0, key=f"provider_{mode}")
        with col_m:
            model = st.text_input("Model (leave blank for default)", "",
                                  key=f"model_{mode}")

    # ── topic input (search / rct_search) ─────────────────────────────────────
    topic = ""
    if mode in ("search", "rct_search"):
        topic = st.text_area(
            "Enter topic / PICO question (or leave blank if `topic.md` already in input folder)",
            height=100,
            key=f"topic_{mode}",
        )

    # ── file uploader ──────────────────────────────────────────────────────────
    if mode != "sr":
        st.markdown(f"**Upload files to `input/{mode}/`**")
        uploaded = st.file_uploader(
            f"Accepted: {', '.join(cfg['extensions'])}",
            accept_multiple_files=True,
            type=[e.lstrip(".") for e in cfg["extensions"]],
            key=f"upload_{mode}",
        )
        if uploaded:
            dest = INPUT_DIR / mode
            dest.mkdir(parents=True, exist_ok=True)
            saved = []
            for uf in uploaded:
                fp = dest / uf.name
                fp.write_bytes(uf.read())
                saved.append(uf.name)
            st.success(f"Saved {len(saved)} file(s) to `input/{mode}/`: "
                       + ", ".join(f"`{n}`" for n in saved))

    # ── current input files ────────────────────────────────────────────────────
    in_files = list((INPUT_DIR / mode).iterdir()) if (INPUT_DIR / mode).exists() else []
    in_files = [f for f in in_files if f.is_file() and f.suffix.lower() in cfg["extensions"]]
    if in_files:
        st.markdown("**Files currently in input folder:**")
        badges = " ".join(
            f'<span class="file-badge">📄 {f.name}</span>' for f in sorted(in_files)
        )
        st.markdown(badges, unsafe_allow_html=True)
    else:
        st.info(f"No files yet in `input/{mode}/`.")

    st.divider()

    # ── folder quick-access ────────────────────────────────────────────────────
    fa1, fa2 = st.columns(2)
    with fa1:
        if st.button("📂 Open Input Folder",  key=f"opn_in_{mode}",  use_container_width=True):
            _open_folder(INPUT_DIR / mode)
    with fa2:
        if st.button("📤 Open Output Folder", key=f"opn_out_{mode}", use_container_width=True):
            _open_folder(OUTPUT_DIR / mode)

    st.divider()

    # ── run button ─────────────────────────────────────────────────────────────
    run_label = "🚀 Launch SR UI" if mode == "sr" else f"▶ Run {cfg['label']}"

    if st.button(run_label, type="primary", use_container_width=True, key=f"run_{mode}"):
        if mode == "sr":
            sr_app = BASE_DIR / "sr" / "src" / "ui" / "app.py"
            subprocess.Popen(
                [sys.executable, "-m", "streamlit", "run", str(sr_app)],
                cwd=str(BASE_DIR),
            )
            st.success("SR UI launched — check for a new browser tab on port 8502.")
        else:
            with st.spinner(f"Running {cfg['label']} mode…"):
                t0 = time.time()
                output = _run_mode(mode, provider, model, topic)
                elapsed = time.time() - t0
            st.success(f"✅ Completed in {elapsed:.1f}s")

            # output panel
            st.markdown("**Pipeline output:**")
            st.markdown(f'<div class="output-box">{output}</div>',
                        unsafe_allow_html=True)

            # download buttons for latest outputs
            latest = _latest_outputs(OUTPUT_DIR / mode)
            if latest:
                st.markdown("**Download latest outputs:**")
                dl_cols = st.columns(min(len(latest), 4))
                for col, fp in zip(dl_cols, latest):
                    with col:
                        mime = ("text/markdown" if fp.suffix == ".md"
                                else "application/vnd.openxmlformats-officedocument"
                                     ".wordprocessingml.document")
                        st.download_button(
                            label=f"⬇ {fp.name}",
                            data=fp.read_bytes(),
                            file_name=fp.name,
                            mime=mime,
                            use_container_width=True,
                            key=f"dl_{fp.name}",
                        )


# ── router ─────────────────────────────────────────────────────────────────────

def main() -> None:
    st.set_page_config(
        page_title="AI kcMedicalResearch",
        page_icon=str(ASSETS_DIR / "logo_AI_kcMedicalResearch.png")
        if (ASSETS_DIR / "logo_AI_kcMedicalResearch.png").exists()
        else "🔬",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    _inject_css()

    if "page" not in st.session_state:
        st.session_state["page"] = "home"

    page = st.session_state["page"]

    if page == "home":
        _home_page()
    elif page in MODES:
        _mode_page(page)
    else:
        st.session_state["page"] = "home"
        st.rerun()


if __name__ == "__main__":
    main()
