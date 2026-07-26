
"""
src/ui/app.py  -  Main Streamlit UI for AI kcMedicalResearch v2.2.0
Landing page: six mode cards in a single row
Each mode page: instructions, settings, file upload, run, output, downloads
"""

from __future__ import annotations

import base64
import io
import os
import subprocess
import sys
from pathlib import Path

import streamlit as st

# -- paths ---------------------------------------------------------------------
BASE_DIR    = Path(__file__).resolve().parent.parent.parent
ASSETS_DIR  = BASE_DIR / "assets"
INPUT_DIR   = BASE_DIR / "input"
OUTPUT_DIR  = BASE_DIR / "output"
REPORTS_DIR = BASE_DIR / "reports"
MAIN_PY     = BASE_DIR / "src" / "main.py"

# -- mode configuration --------------------------------------------------------
MODES: dict[str, dict] = {
    "coding": {
        "label":       "Coding",
        "icon":        ASSETS_DIR / "icon_Coding_agent.png",
        "accent":      "#4A90D9",
        "bg":          "#EBF4FF",
        "description": "Code generation,\nReview & Revision.",
        "extensions":  [".py", ".js", ".ts", ".html", ".css", ".java",
                        ".c", ".cpp", ".cs", ".rb", ".go", ".rs", ".txt", ".md"],
        "instructions": (
            "**How to use Coding mode**\n\n"
            "1. Drop source files into `input/coding/`.\n"
            "2. Choose your provider and model below.\n"
            "3. Click **Run Coding** \u2014 the AI will review / generate code.\n"
            "4. Outputs (code files + markdown report) appear in `output/coding/`.\n\n"
            "_Tip: use the **--revise** flag from the CLI for a "
            "Builder -> Reviewer -> Tester pipeline._"
        ),
    },
    "writing": {
        "label":       "Writing",
        "icon":        ASSETS_DIR / "icon_Writing_agent.png",
        "accent":      "#27AE60",
        "bg":          "#EAFAF1",
        "description": "Medical Writing\nReports from docs.",
        "extensions":  [".txt", ".md", ".docx", ".pdf"],
        "instructions": (
            "**How to use Writing mode**\n\n"
            "1. Drop `.txt`, `.md`, `.docx`, or `.pdf` files into `input/writing/`.\n"
            "2. Choose your provider and model.\n"
            "3. Click **Run Writing** \u2014 a structured report is generated.\n"
            "4. Markdown and Word outputs appear in `output/writing/`."
        ),
    },
    "appraisal": {
        "label":       "Appraisal",
        "icon":        ASSETS_DIR / "icon_Appraisal_agent.png",
        "accent":      "#8E44AD",
        "bg":          "#F5EEF8",
        "description": "Critical Appraisal\nof Research Articles.",
        "extensions":  [".pdf", ".txt", ".md", ".docx"],
        "instructions": (
            "**How to use Appraisal mode**\n\n"
            "1. Drop article PDFs or text files into `input/appraisal/`.\n"
            "2. Choose your provider and model.\n"
            "3. Click **Run Appraisal** \u2014 three parallel agents assess the article.\n"
            "4. Merged report (`.md` + `.docx`) appears in `output/appraisal/`."
        ),
    },
    "rct_search": {
        "label":       "RCT Search",
        "icon":        ASSETS_DIR / "icon_RCT_Search_agent.png",
        "accent":      "#E67E22",
        "bg":          "#FEF9E7",
        "description": "RCT Articles Search\nfrom PubMed & Embase.",
        "extensions":  [".txt", ".md"],
        "instructions": (
            "**How to use RCT Search mode**\n\n"
            "1. Enter your PICO topic in the text box below, or place a `topic.md` "
            "file in `input/rct_search/`.\n"
            "2. Choose your provider and model.\n"
            "3. Click **Run RCT Search** \u2014 the pipeline builds, validates, and "
            "refines a search strategy.\n"
            "4. Outputs appear in `output/rct_search/`."
        ),
    },
    "search": {
        "label":       "Search",
        "icon":        ASSETS_DIR / "icon_Search_agent.png",
        "accent":      "#16A085",
        "bg":          "#E8F8F5",
        "description": "Evidence-based\nClinical Search.",
        "extensions":  [".txt", ".md"],
        "instructions": (
            "**How to use Search mode**\n\n"
            "1. Enter your clinical topic or paper title in the text box below, or "
            "place a `topic.md` file in `input/search/`.\n"
            "2. Choose provider and model.\n"
            "3. Click **Run Search** \u2014 results are saved to `output/search/`."
        ),
    },
    "sr": {
        "label":       "Systematic Review",
        "icon":        ASSETS_DIR / "icon_SR_agent.png",
        "accent":      "#C0392B",
        "bg":          "#FDEDEC",
        "description": "Full SR Pipeline:\nPRISMA to Meta-analysis.",
        "extensions":  [".pdf"],
        "instructions": (
            "**How to use Systematic Review mode**\n\n"
            "1. Drop article PDFs into `input/sr/`.\n"
            "2. Edit `docs/sr/prisma_criteria.md` with your inclusion/exclusion criteria.\n"
            "3. Click **Run Systematic Review** \u2014 a new terminal window opens.\n"
            "4. Results are saved to `output/sr/`."
        ),
    },
}

PROVIDERS = ["ollama", "openai", "anthropic", "deepseek", "groq", "qwen"]


# -- helpers -------------------------------------------------------------------

def _icon_b64(path: Path) -> str | None:
    """Resize icon to 96x96, preserve transparency, return base64 data-URI."""
    if not path.exists():
        return None
    try:
        from PIL import Image
        img = Image.open(path).convert("RGBA")
        img.thumbnail((96, 96), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        data = base64.b64encode(buf.getvalue()).decode()
        return "data:image/png;base64," + data
    except Exception:
        try:
            ext  = path.suffix.lower().lstrip(".")
            mime = "jpeg" if ext in ("jpg", "jpeg") else "png"
            return "data:image/" + mime + ";base64," + base64.b64encode(path.read_bytes()).decode()
        except Exception:
            return None

def _logo_b64() -> str | None:
    for name in ("logo_AI_kcMedicalResearch.png", "logo_AI_kcMedicalResearch.jpg"):
        p = ASSETS_DIR / name
        if p.exists():
            return _icon_b64(p)
    return None


def _open_folder(folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    if sys.platform == "win32":
        subprocess.Popen(["explorer", str(folder)])
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(folder)])
    else:
        subprocess.Popen(["xdg-open", str(folder)])


def _show_folder_contents(folder: Path, exts: list[str], label: str) -> None:
    """Show folder contents with download buttons. No Explorer button."""
    folder.mkdir(parents=True, exist_ok=True)
    files = (
        sorted(
            f for f in folder.iterdir()
            if f.is_file() and f.suffix.lower() in exts
        )
        if folder.exists() else []
    )
    with st.expander(
        f"\U0001f4c2 {label}  \u2014  `{folder.relative_to(BASE_DIR)}`",
        expanded=True,
    ):
        if files:
            for f in files:
                c1, c2 = st.columns([6, 1])
                with c1:
                    st.markdown(
                        f'<span class="file-badge">\U0001f4c4 {f.name}</span>',
                        unsafe_allow_html=True,
                    )
                with c2:
                    ext  = f.suffix.lower()
                    mime = (
                        "text/markdown" if ext == ".md" else
                        "application/vnd.openxmlformats-officedocument"
                        ".wordprocessingml.document" if ext == ".docx" else
                        "application/pdf" if ext == ".pdf" else
                        "application/octet-stream"
                    )
                    st.download_button(
                        label="\u2b07",
                        data=f.read_bytes(),
                        file_name=f.name,
                        mime=mime,
                        key=f"browse_{label}_{f.name}",
                    )
        else:
            st.info("No files found.")


def _count_files(folder: Path, exts: list[str]) -> int:
    if not folder.exists():
        return 0
    return sum(
        1 for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in exts
    )


def _latest_outputs(
    folder: Path,
    suffixes: tuple[str, ...] = (".md", ".docx"),
) -> list[Path]:
    if not folder.exists():
        return []
    files = [
        f for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in suffixes
    ]
    return sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)[:4]


def _launch_terminal(
    mode: str, provider: str, model: str, topic: str = ""
) -> str:
    """Launch main.py in a new terminal window for interactive use."""
    if mode in ("search", "rct_search") and topic.strip():
        topic_file = INPUT_DIR / mode / "topic.md"
        topic_file.parent.mkdir(parents=True, exist_ok=True)
        topic_file.write_text(topic.strip(), encoding="utf-8")

    py   = sys.executable
    mp   = str(MAIN_PY)
    base = str(BASE_DIR)

    try:
        if sys.platform == "win32":
            # Use & call operator so PowerShell does not misparse --flags
            py_ps   = py.replace("'", "''")
            mp_ps   = mp.replace("'", "''")
            base_ps = base.replace("'", "''")
            model_part = f" --model {model.strip()}" if model.strip() else ""
            ps_cmd = (
                f"& '{py_ps}' '{mp_ps}'"
                f" --mode {mode} --provider {provider}{model_part}"
            )
            subprocess.Popen(
                ["powershell", "-NoExit", "-Command",
                 f"Set-Location '{base_ps}'; {ps_cmd}"],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                cwd=base,
            )
        elif sys.platform == "darwin":
            py_sh   = py.replace("'", "'\\''")
            mp_sh   = mp.replace("'", "'\\''")
            base_sh = base.replace("'", "'\\''")
            model_part = f" --model {model.strip()}" if model.strip() else ""
            script = (
                f"cd '{base_sh}' && '{py_sh}' '{mp_sh}'"
                f" --mode {mode} --provider {provider}{model_part}"
            )
            subprocess.Popen(
                ["osascript", "-e",
                 f'tell app "Terminal" to do script "{script}"'],
            )
        else:
            args = [py, mp, "--mode", mode, "--provider", provider]
            if model.strip():
                args += ["--model", model.strip()]
            subprocess.Popen(
                ["x-terminal-emulator", "-e"] + args,
                cwd=base,
            )
        return "ok"
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"


# -- global CSS ----------------------------------------------------------------

def _inject_css() -> None:
    st.markdown(
        """
        <style>
        /* ── root font size: makes all rem units behave as expected ── */
        :root { font-size: 16px !important; }
        html, body { font-size: 16px !important; }
        .main .block-container { font-size: 16px !important; }
        /* global */
        body { font-family: "Segoe UI", sans-serif; }
        .block-container {
            padding-top: 1rem;
            padding-left: 1.2rem;
            padding-right: 1.2rem;
        }

        /* header */
        .app-header {
            display: flex;
            align-items: center;
            gap: 1.2rem;
            padding: .4rem 0 .8rem;
            border-bottom: 2px solid #e0e0e0;
            margin-bottom: 1rem;
        }
        .app-header img   { height: 72px; }
        .app-header h1    { font-size: 2.4rem; margin: 0; color: #1a1a2e; }
        .app-header small { font-size: 1.2rem; color: #666; }

        /* mode cards */
        .mode-card {
            border-radius: 14px;
            padding: 1.2rem 0.6rem 1rem;
            text-align: center;
            transition: transform .15s, box-shadow .15s;
            height: 100%;
            min-height: 280px;
        }
        .mode-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 24px rgba(0,0,0,.15);
        }
        .mode-card img {
            width: 96px;
            height: 96px;
            object-fit: contain;
            margin: 0 auto .8rem;
            display: block;
        }
        .mode-card h3 {
            font-size: 1.55rem;
            font-weight: 700;
            margin: .35rem 0 .3rem;
        }
        .mode-card p.desc {
            font-size: 1.2rem;
            color: #333;
            margin: 0 0 .3rem;
            line-height: 1.5;
            white-space: pre-line;
        }
        .mode-card p.fcount {
            font-size: 1.05rem;
            color: #777;
            margin-top: .35rem;
        }

        /* ALL buttons - strongest possible selectors */
        button[kind="secondary"],
        button[kind="primary"],
        div[data-testid="stButton"] > button,
        div[data-testid="stFormSubmitButton"] > button,
        section[data-testid="stSidebar"] button,
        .stButton button {
            font-size: 1.9rem !important;
            padding: .6rem 1.1rem !important;
            line-height: 1.5 !important;
            min-height: 3.4rem !important;
        }

        /* download buttons */
        div[data-testid="stDownloadButton"] > button,
        .stDownloadButton button {
            font-size: 1.7rem !important;
            padding: .5rem 1rem !important;
            min-height: 3rem !important;
        }

        /* expander header text */
        details > summary p,
        details > summary span,
        div[data-testid="stExpander"] summary p {
            font-size: 1.25rem !important;
        }

        /* form labels */
        .stSelectbox label,
        .stTextInput label,
        .stTextArea label,
        .stFileUploader label {
            font-size: 1.2rem !important;
        }

        /* selectbox / input values */
        .stSelectbox div[data-baseweb="select"] *,
        .stTextInput input,
        .stTextArea textarea {
            font-size: 1.15rem !important;
        }

        /* alerts */
        .stAlert p,
        div[data-testid="stAlert"] p {
            font-size: 1.15rem !important;
        }

        /* markdown body text */
        .stMarkdown p,
        .stMarkdown li {
            font-size: 1.15rem;
            line-height: 1.6;
        }

        /* file badge */
        .file-badge {
            display: inline-block;
            background: #f0f0f0;
            border-radius: 6px;
            padding: .2rem .65rem;
            font-size: 1.1rem;
            margin: .2rem;
            color: #333;
        }

        /* headings */
        h2 { font-size: 1.9rem !important; }
        h3 { font-size: 1.6rem !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# -- header --------------------------------------------------------------------

def _render_header(subtitle: str = "") -> None:
    logo      = _logo_b64()
    logo_html = f'<img src="{logo}" alt="logo">' if logo else ""
    sub_html  = f"<small>{subtitle}</small>" if subtitle else ""
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


# -- home page -----------------------------------------------------------------

def _home_page() -> None:
    _render_header("Select a mode to begin")

    st.markdown(
        '''
        <div style="background:#e8f4fd;border-left:5px solid #1a73e8;
        padding:1rem 1.4rem;border-radius:8px;margin-bottom:.5rem;">
        <p style="margin:0;font-size:1.2rem;font-weight:700;color:#1a1a2e;">
        📂  Files uploaded to <strong>Input</strong> are automatically transferred to their respective input folder.</p>
        </div>
        ''',
        unsafe_allow_html=True,
    )
    st.markdown(
        '''
        <div style="background:#e8f9f0;border-left:5px solid #34a853;
        padding:1rem 1.4rem;border-radius:8px;margin-bottom:1.2rem;">
        <p style="margin:0;font-size:1.2rem;font-weight:700;color:#1a1a2e;">
        📤  Processed results are placed in their respective <strong>Output</strong> folder and available for download.</p>
        </div>
        ''',
        unsafe_allow_html=True,
    )

    cols = st.columns(6, gap="small")

    for col, (key, cfg) in zip(cols, MODES.items()):
        icon_uri  = _icon_b64(cfg["icon"]) or ""
        icon_html = (
            f'<img src="{icon_uri}" alt="{cfg["label"]}" '
            f'style="width:96px;height:96px;object-fit:contain;'
            f'display:block;margin:0 auto .8rem;">'
            if icon_uri else
            f'<div style="font-size:3.5rem;text-align:center;">'
            f'\U0001f52c</div>'
        )
        n_in = _count_files(INPUT_DIR / key, cfg["extensions"])

        with col:
            # card HTML
            st.markdown(
                f"""
                <div class="mode-card"
                     style="background:{cfg['bg']};
                            border:2px solid {cfg['accent']}60;">
                    {icon_html}
                    <h3 style="color:{cfg['accent']}">{cfg['label']}</h3>
                    <p class="desc">{cfg['description']}</p>
                    <p class="fcount">\U0001f4c2 {n_in} file(s) in input</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.write("")

            # Input toggle
            if st.button("\U0001f4c2 Input", key=f"inp_{key}",
                         use_container_width=True):
                current = st.session_state.get(f"show_input_{key}", False)
                for k in MODES:
                    st.session_state[f"show_input_{k}"]  = False
                    st.session_state[f"show_output_{k}"] = False
                st.session_state[f"show_input_{key}"] = not current
                st.rerun()

            if st.session_state.get(f"show_input_{key}", False):
                dest = INPUT_DIR / key
                dest.mkdir(parents=True, exist_ok=True)
                existing = sorted(
                    f for f in dest.iterdir()
                    if f.is_file() and f.suffix.lower() in cfg["extensions"]
                )
                if existing:
                    st.markdown(
                        " ".join(
                            f'<span class="file-badge">'
                            f'\U0001f4c4 {f.name}</span>'
                            for f in existing
                        ),
                        unsafe_allow_html=True,
                    )
                # uploader — no st.rerun() so buttons below remain reachable
                ups = st.file_uploader(
                    f"Add files \u2192 `input/{key}/`",
                    accept_multiple_files=True,
                    type=[e.lstrip(".") for e in cfg["extensions"]],
                    key=f"home_upload_{key}",
                )
                if ups:
                    saved = []
                    for uf in ups:
                        fp = dest / uf.name
                        fp.write_bytes(uf.read())
                        saved.append(uf.name)
                    st.success(
                        f"\u2705 Saved {len(saved)} file(s): "
                        + ", ".join(f"`{n}`" for n in saved)
                    )
                    st.rerun()
                # explicit close so user can reach buttons below
                if st.button("\u2716 Close", key=f"close_inp_{key}",
                             use_container_width=True):
                    st.session_state[f"show_input_{key}"] = False
                    st.rerun()

            # Output toggle
            if st.button("\U0001f4e4 Output", key=f"out_{key}",
                         use_container_width=True):
                current = st.session_state.get(f"show_output_{key}", False)
                for k in MODES:
                    st.session_state[f"show_input_{k}"]  = False
                    st.session_state[f"show_output_{k}"] = False
                st.session_state[f"show_output_{key}"] = not current
                st.rerun()

            if st.session_state.get(f"show_output_{key}", False):
                out_folder = OUTPUT_DIR / key
                out_folder.mkdir(parents=True, exist_ok=True)
                out_files = sorted(
                    (f for f in out_folder.iterdir() if f.is_file()),
                    key=lambda f: f.stat().st_mtime,
                    reverse=True,
                )
                if out_files:
                    for fp in out_files[:3]:
                        ext  = fp.suffix.lower()
                        mime = (
                            "text/markdown" if ext == ".md" else
                            "application/vnd.openxmlformats-officedocument"
                            ".wordprocessingml.document" if ext == ".docx" else
                            "application/octet-stream"
                        )
                        st.download_button(
                            label=f"\u2b07 {fp.name}",
                            data=fp.read_bytes(),
                            file_name=fp.name,
                            mime=mime,
                            key=f"dl_home_{key}_{fp.name}",
                            use_container_width=True,
                        )
                    if len(out_files) > 3:
                        st.caption(f"+ {len(out_files) - 3} older file(s)")
                else:
                    st.info("No output files yet.")
                # explicit close
                if st.button("\u2716 Close", key=f"close_out_{key}",
                             use_container_width=True):
                    st.session_state[f"show_output_{key}"] = False
                    st.rerun()

            # Navigate to mode page
            if st.button(f"\u25b6 {cfg['label']}", key=f"go_{key}",
                         use_container_width=True):
                for k in MODES:
                    st.session_state[f"show_input_{k}"]  = False
                    st.session_state[f"show_output_{k}"] = False
                st.session_state["page"] = key
                st.rerun()

            # Exit — close all panels and stay on home
            if st.button("\U0001f6aa Exit", key=f"exit_{key}",
                         use_container_width=True):
                for k in list(st.session_state.keys()):
                    if (k.startswith("show_input_")
                            or k.startswith("show_output_")):
                        st.session_state[k] = False
                st.session_state["page"] = "home"
                st.rerun()


# -- mode page -----------------------------------------------------------------

def _mode_page(mode: str) -> None:
    cfg = MODES[mode]
    _render_header(f"Mode: {cfg['label']}")

    # top nav — both buttons return to home
    nav_l, nav_r, nav_spacer = st.columns([2, 2, 8])
    with nav_l:
        if st.button("\U0001f3e0 Home", use_container_width=True):
            st.session_state["page"] = "home"
            st.rerun()
    with nav_r:
        if st.button("\U0001f6aa Exit", use_container_width=True):
            st.session_state["page"] = "home"
            st.rerun()
    with nav_spacer:
        pass
    st.divider()

    # instructions
    with st.expander("\U0001f4cb Instructions", expanded=False):
        st.markdown(cfg["instructions"])

    # icon + mode title — base64 img tag only, no st.image()
    icon_uri = _icon_b64(cfg["icon"])
    if icon_uri:
        ic, ti = st.columns([1, 10])
        with ic:
            st.markdown(
                f'<img src="{icon_uri}" alt="{cfg["label"]}" '
                f'style="width:64px;height:64px;'
                f'object-fit:contain;margin-top:.4rem;">',
                unsafe_allow_html=True,
            )
        with ti:
            st.subheader(cfg["label"])
    else:
        st.subheader(cfg["label"])

    # provider / model settings
    with st.expander("\u2699\ufe0f Provider / Model settings", expanded=True):
        col_p, col_m = st.columns(2)
        with col_p:
            provider = st.selectbox(
                "Provider", PROVIDERS, index=0, key=f"provider_{mode}"
            )
        with col_m:
            model = st.text_input(
                "Model (leave blank for default)", "", key=f"model_{mode}"
            )

    # topic input for search modes only
    topic = ""
    if mode in ("search", "rct_search"):
        topic = st.text_area(
            "Enter topic / PICO question  "
            "(or leave blank if `topic.md` is already in the input folder)",
            height=110,
            key=f"topic_{mode}",
        )

    # file uploader — single widget, sr mode has no uploader (uses input/sr/)
    if mode != "sr":
        st.markdown(
            f"**Upload files to** `input/{mode}/`  \u2014  "
            f"Accepted: {', '.join(cfg['extensions'])}"
        )
        uploaded = st.file_uploader(
            "Choose files",
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
            st.success(
                f"\u2705 Saved {len(saved)} file(s) to `input/{mode}/`: "
                + ", ".join(f"`{n}`" for n in saved)
            )
            st.rerun()

    st.divider()

    # folder browsers — no Explorer button
    fb1, fb2 = st.columns(2)
    with fb1:
        _show_folder_contents(
            INPUT_DIR / mode,
            cfg["extensions"],
            f"Input \u2014 {cfg['label']}",
        )
    with fb2:
        _show_folder_contents(
            OUTPUT_DIR / mode,
            [".md", ".docx", ".pdf", ".py", ".txt"],
            f"Output \u2014 {cfg['label']}",
        )

    st.divider()

    # run button
    if st.button(
        f"\u25b6\ufe0f Run {cfg['label']}",
        type="primary",
        use_container_width=True,
        key=f"run_{mode}",
    ):
        result = _launch_terminal(mode, provider, model, topic)
        if result == "ok":
            st.success(
                f"\u2705 **{cfg['label']}** session launched "
                f"in a new terminal window."
            )
            st.info(
                "\U0001f4bb Work in the terminal window. "
                f"When done, use the Output browser above to find your "
                f"results in `output/{mode}/`."
            )
        else:
            st.error(f"Could not open terminal: {result}")

    # download latest outputs — always visible below run button
    latest = _latest_outputs(OUTPUT_DIR / mode)
    if latest:
        st.markdown("**Download previous outputs:**")
        dl_cols = st.columns(min(len(latest), 4))
        for dl_col, fp in zip(dl_cols, latest):
            with dl_col:
                ext  = fp.suffix.lower()
                mime = (
                    "text/markdown" if ext == ".md" else
                    "application/vnd.openxmlformats-officedocument"
                    ".wordprocessingml.document" if ext == ".docx" else
                    "application/octet-stream"
                )
                st.download_button(
                    label=f"\u2b07 {fp.name}",
                    data=fp.read_bytes(),
                    file_name=fp.name,
                    mime=mime,
                    use_container_width=True,
                    key=f"dl_{mode}_{fp.name}",
                )


# -- router --------------------------------------------------------------------

def main() -> None:
    st.set_page_config(
        page_title="AI kcMedicalResearch",
        page_icon=(
            str(ASSETS_DIR / "logo_AI_kcMedicalResearch.png")
            if (ASSETS_DIR / "logo_AI_kcMedicalResearch.png").exists()
            else "\U0001f9ec"
        ),
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    _inject_css()
    import streamlit.components.v1 as _components
    _components.html("""
        <script>
        (function() {
            const FONT_RULES = [
                ['button', '20px'],
                ['p', '18px'],
                ['li', '18px'],
                ['label', '18px'],
                ['input', '17px'],
                ['textarea', '17px'],
            ];
            function applyFonts() {
                FONT_RULES.forEach(([sel, size]) => {
                    try {
                        parent.document.querySelectorAll(sel).forEach(el => {
                            el.style.setProperty('font-size', size, 'important');
                        });
                    } catch(e) {}
                });
            }
            // Run once immediately
            applyFonts();
            // Re-run whenever DOM changes (Streamlit rerenders)
            const observer = new MutationObserver(applyFonts);
            observer.observe(parent.document.body, {
                childList: true,
                subtree: true
            });
        })();
        </script>
    """, height=0)

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
