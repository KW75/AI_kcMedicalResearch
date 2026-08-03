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
        "submodes":    ["Builder (pipeline)", "Reviewer", "Tester"],
        "instructions": (
            "**How to use Coding mode**\n\n"
            "1. Drop source files into `input/coding/`.\n"
            "2. Choose your provider and model below.\n"
            "3. Select a sub-mode:\n"
            "   - **Builder**: Full pipeline (Builder → Reviewer → Tester)\n"
            "   - **Reviewer**: Standalone code review\n"
            "   - **Tester**: Standalone test generation\n"
            "4. Click **Run Coding** — the AI will process your code.\n"
            "5. Outputs appear in `output/coding/`."
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
            "2. Choose your provider and model below.\n"
            "3. Click **Run Writing** — you will be prompted in the terminal to select:\n"
            "   - **Topic Track**: Editorial/opinion style (newspaper)\n"
            "   - **Article Track**: Medical journal article style\n"
            "4. A structured report is generated.\n"
            "5. Markdown and Word outputs appear in `output/writing/`."
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
            "2. Choose your provider and model below.\n"
            "3. Click **Run Appraisal** — you will be prompted in the terminal to select:\n"
            "   - **Appraiser**: Critical appraisal of methodology\n"
            "   - **Methodologist**: Statistical and design assessment\n"
            "   - **Summariser**: Concise article summary\n"
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
            "1. Place a `topic.md` file in `input/rct_search/`, or enter your PICO topic "
            "when prompted in the terminal.\n"
            "2. Choose your provider and model below.\n"
            "3. Click **Run RCT Search** — the pipeline builds, validates, and "
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
            "1. Place a `topic.md` file in `input/search/`, or enter your clinical topic "
            "when prompted in the terminal.\n"
            "2. Choose your provider and model below.\n"
            "3. Click **Run Search** — you will be prompted in the terminal to select:\n"
            "   - **Topic Search**: Web synopsis with reference links\n"
            "   - **Article Search**: PubMed search by article type + comparison\n"
            "4. Results are saved to `output/search/`."
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
            "**Phase 1 — Discovery (optional):**\n"
            "1. Run RCT Search mode first to generate a ranked article list.\n"
            "2. Use **Import PICO from RCT Search** below to pre-fill your PICO fields.\n\n"
            "**Phase 2 — Synthesis:**\n"
            "3. Upload your chosen article PDFs to `input/sr/`.\n"
            "4. Review or edit the imported PICO fields.\n"
            "5. Click **Run Systematic Review** — results saved to `output/sr/`."
        ),
    },
}

PROVIDERS = ["ollama", "openai", "anthropic", "deepseek", "groq", "qwen"]


# -- helpers -------------------------------------------------------------------

def _icon_b64(path: Path) -> str | None:
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
            ext = path.suffix.lower().lstrip(".")
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


def _show_folder_contents(folder: Path, exts: list[str], label: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    files = sorted(
        [f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in exts]
    ) if folder.exists() else []
    with st.expander(f"\U0001f4c2 {label}  \u2014  `{folder.relative_to(BASE_DIR)}`", expanded=True):
        if files:
            for f in files:
                c1, c2 = st.columns([6, 1])
                with c1:
                    st.markdown(f'<span class="file-badge">\U0001f4c4 {f.name}</span>', unsafe_allow_html=True)
                with c2:
                    ext = f.suffix.lower()
                    mime = (
                        "text/markdown" if ext == ".md" else
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document" if ext == ".docx" else
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
    return sum(1 for f in folder.iterdir() if f.is_file() and f.suffix.lower() in exts)


def _latest_outputs(folder: Path, suffixes: tuple[str, ...] = (".md", ".docx")) -> list[Path]:
    if not folder.exists():
        return []
    files = [f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in suffixes]
    return sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)[:4]


# -- Cloud / Local terminal launcher -------------------------------------------

def _launch_terminal(mode: str, provider: str, model: str, submode: str = "", prompt: str = "") -> str:
    """Launch CLI - detects environment and runs appropriately"""
    import os
    import sys
    import subprocess
    from pathlib import Path
    import streamlit as st

    # Check if running in cloud environment
    is_cloud = (os.environ.get('STREAMLIT_SHARING') or
                os.environ.get('REPL_ID') or
                os.environ.get('CODESPACES') or
                os.environ.get('STREAMLIT_SERVER_PORT'))

    if is_cloud:
        return _run_cli_cloud(mode, provider, model, submode, prompt)
    else:
        return _launch_terminal_local(mode, provider, model, submode)


def _run_cli_cloud(mode: str, provider: str, model: str, submode: str = "", prompt: str = "") -> str:
    """Run CLI directly in cloud environment"""
    import subprocess
    import sys
    from pathlib import Path
    import streamlit as st

    # Save prompt if provided
    if prompt.strip():
        prompt_file = INPUT_DIR / mode / "instructions.txt"
        prompt_file.parent.mkdir(parents=True, exist_ok=True)
        prompt_file.write_text(prompt.strip(), encoding="utf-8")

    # Build command
    cmd_parts = [sys.executable, "src/main.py", "--mode", mode, "--provider", provider]
    if model.strip():
        cmd_parts += ["--model", model.strip()]

    # Add submode flags for coding
    if mode == "coding" and submode:
        if "Builder" in submode:
            cmd_parts += ["--role", "Builder"]
        elif "Reviewer" in submode:
            cmd_parts += ["--role", "Reviewer"]
        elif "Tester" in submode:
            cmd_parts += ["--role", "Tester"]

    st.code("$ " + " ".join(cmd_parts))

    # Check if we have API keys (for cloud providers)
    if provider in ["qwen", "openai", "anthropic", "deepseek", "groq"]:
        import os
        env_var_map = {
            "qwen": "QWEN_API_KEY",
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "groq": "GROQ_API_KEY"
        }
        env_var = env_var_map.get(provider)
        if env_var and not os.getenv(env_var):
            st.warning(f"⚠️ {env_var} not set. Please add it to Streamlit Secrets.")
            st.info("Go to your Streamlit Cloud dashboard → Settings → Secrets")
            return "error: missing API key"

    with st.spinner(f"Running {mode} mode..."):
        try:
            result = subprocess.run(
                cmd_parts,
                cwd=str(Path(__file__).resolve().parent.parent.parent),
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.stdout:
                st.text_area("Output", result.stdout, height=300)
            if result.stderr:
                st.text_area("Errors", result.stderr, height=100)

            if result.returncode == 0:
                st.success("✅ Command completed successfully!")
                return "ok"
            else:
                st.error(f"❌ Command failed with exit code {result.returncode}")
                return f"error: code {result.returncode}"

        except subprocess.TimeoutExpired:
            st.error("⏰ Command timed out after 5 minutes")
            return "error: timeout"
        except Exception as exc:
            st.error(f"❌ Error: {exc}")
            return f"error: {exc}"


def _launch_terminal_local(mode: str, provider: str, model: str, submode: str = "") -> str:
    """Original terminal launch for local use"""
    import subprocess
    import sys
    from pathlib import Path

    py = sys.executable
    mp = str(MAIN_PY)
    base = str(BASE_DIR)

    cmd_parts = [py, mp, "--mode", mode, "--provider", provider]
    if model.strip():
        cmd_parts += ["--model", model.strip()]

    if mode == "coding" and submode:
        if "Builder" in submode:
            cmd_parts += ["--role", "Builder"]
        elif "Reviewer" in submode:
            cmd_parts += ["--role", "Reviewer"]
        elif "Tester" in submode:
            cmd_parts += ["--role", "Tester"]

    cmd_str = " ".join(f'"{p}"' if " " in p else p for p in cmd_parts)

    try:
        if sys.platform == "win32":
            subprocess.Popen(
                ["powershell", "-NoExit", "-Command",
                 f"Set-Location '{base}'; {cmd_str}; Write-Host ''; Write-Host 'Session completed. Press any key to close this window...'; $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')"],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                cwd=base,
            )
        elif sys.platform == "darwin":
            subprocess.Popen(
                ["osascript", "-e",
                 f'tell app "Terminal" to do script "cd \'{base}\' && {cmd_str} && echo \'Session completed. Press any key to close...\' && read"']
            )
        else:
            subprocess.Popen(
                ["x-terminal-emulator", "-e", "bash", "-c",
                 f"cd '{base}' && {cmd_str} && echo 'Session completed. Press any key to close...' && read"],
                cwd=base,
            )
        return "ok"
    except Exception as exc:
        return f"error: {exc}"


def _exit_to_launcher() -> None:
    """Display exit message and clear session state."""
    st.markdown(
        """
        <div style="text-align:center;padding:60px 20px;">
            <h1 style="font-size:3rem;">👋</h1>
            <h2 style="color:#1a1a2e;">Return to Launcher</h2>
            <p style="font-size:1.2rem;color:#555;margin-top:20px;">
                Close this browser tab and return to the terminal where the launcher is running.
            </p>
            <p style="font-size:1rem;color:#888;margin-top:10px;">
                Press <strong>Ctrl+C</strong> in the terminal to stop the UI server when done.
            </p>
            <div style="margin-top:30px;">
                <a href="#" onclick="window.close();return false;"
                   style="font-size:1.2rem;padding:10px 30px;background:#4A90D9;color:white;border:none;border-radius:8px;cursor:pointer;text-decoration:none;display:inline-block;">
                    Close this tab
                </a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    for key in list(st.session_state.keys()):
        if key != "page":
            del st.session_state[key]
    st.session_state["page"] = "home"
    st.stop()


# -- CSS -----------------------------------------------------------------------

def _inject_css() -> None:
    st.markdown(
        """
        <style>
        :root { font-size: 16px !important; }
        html, body { font-size: 16px !important; }
        .main .block-container { font-size: 16px !important; }
        body { font-family: "Segoe UI", sans-serif; }
        .block-container { padding-top: 1rem; padding-left: 1.2rem; padding-right: 1.2rem; }

        .app-header {
            display: flex;
            align-items: center;
            gap: 1.2rem;
            padding: .4rem 0 .8rem;
            border-bottom: 2px solid #e0e0e0;
            margin-bottom: 1rem;
        }
        .app-header img { height: 72px; }
        .app-header h1 { font-size: 2.4rem; margin: 0; color: #1a1a2e; }
        .app-header .subtitle {
            font-size: 1.4rem;
            color: #555;
            font-weight: 700;
            letter-spacing: .05em;
        }

        .mode-card {
            border-radius: 14px;
            padding: 1.2rem 0.6rem 1rem;
            text-align: center;
            transition: transform .15s, box-shadow .15s;
            height: 100%;
            min-height: 280px;
            cursor: pointer;
        }
        .mode-card:hover { transform: translateY(-3px); box-shadow: 0 8px 24px rgba(0,0,0,.15); }
        .mode-card img { width: 96px; height: 96px; object-fit: contain; margin: 0 auto .8rem; display: block; }
        .mode-card h3 { font-size: 1.55rem; font-weight: 700; margin: .35rem 0 .3rem; }
        .mode-card p.desc { font-size: 1.2rem; color: #333; margin: 0 0 .3rem; line-height: 1.5; white-space: pre-line; }
        .mode-card p.fcount { font-size: 1.05rem; color: #777; margin-top: .35rem; }

        /* Navigation buttons - more visible */
        div[data-testid="stButton"] button:has(span:contains("🏠 Home")) {
            background-color: #4A90D9 !important;
            color: white !important;
            font-weight: 700 !important;
            font-size: 1.6rem !important;
            padding: 0.6rem 1.5rem !important;
            border-radius: 8px !important;
            border: none !important;
        }
        div[data-testid="stButton"] button:has(span:contains("🏠 Home")):hover {
            background-color: #357ABD !important;
        }
        div[data-testid="stButton"] button:has(span:contains("🚪 Exit to Launcher")) {
            background-color: #E74C3C !important;
            color: white !important;
            font-weight: 700 !important;
            font-size: 1.6rem !important;
            padding: 0.6rem 1.5rem !important;
            border-radius: 8px !important;
            border: none !important;
        }
        div[data-testid="stButton"] button:has(span:contains("🚪 Exit to Launcher")):hover {
            background-color: #C0392B !important;
        }

        /* ALL buttons */
        button[kind="secondary"], button[kind="primary"],
        div[data-testid="stButton"] > button, .stButton button {
            font-size: 1.9rem !important;
            padding: .6rem 1.1rem !important;
            line-height: 1.5 !important;
            min-height: 3.4rem !important;
        }
        div[data-testid="stDownloadButton"] > button, .stDownloadButton button {
            font-size: 1.7rem !important;
            padding: .5rem 1rem !important;
            min-height: 3rem !important;
        }
        details > summary p, div[data-testid="stExpander"] summary p { font-size: 1.25rem !important; }
        .stSelectbox label, .stTextInput label, .stFileUploader label { font-size: 1.2rem !important; }
        .stSelectbox div[data-baseweb="select"] *, .stTextInput input { font-size: 1.15rem !important; }
        .stAlert p, div[data-testid="stAlert"] p { font-size: 1.15rem !important; }
        .stMarkdown p, .stMarkdown li { font-size: 1.15rem; line-height: 1.6; }
        .file-badge { display: inline-block; background: #f0f0f0; border-radius: 6px; padding: .2rem .65rem; font-size: 1.1rem; margin: .2rem; color: #333; }
        h2 { font-size: 1.9rem !important; }
        h3 { font-size: 1.6rem !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# -- HEADER --------------------------------------------------------------------

def _render_header(subtitle: str = "") -> None:
    logo = _logo_b64()
    logo_html = f'<img src="{logo}" alt="logo">' if logo else ""
    st.markdown(
        f"""
        <div class="app-header">
            {logo_html}
            <div>
                <h1>AI kcMedicalResearch</h1>
                <p style="margin:0;font-size:1.4rem;font-weight:700;color:#555;letter-spacing:.05em;">Pipeline User Interface</p>
                {f'<span class="subtitle">{subtitle}</span>' if subtitle else ''}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# -- HOME PAGE -----------------------------------------------------------------

def _home_page() -> None:
    _render_header("Select a mode to begin")

    col_exit, col_spacer = st.columns([1, 11])
    with col_exit:
        if st.button("\U0001f6aa Exit to Launcher", key="exit_launcher_home"):
            _exit_to_launcher()

    st.markdown(
        '''
        <div style="background:#e8f4fd;border-left:5px solid #1a73e8;padding:1rem 1.4rem;border-radius:8px;margin-bottom:.5rem;">
        <p style="margin:0;font-size:1.2rem;font-weight:700;color:#1a1a2e;">📂 Files uploaded to <strong>Input</strong> are automatically transferred to their respective input folder.</p>
        </div>
        ''',
        unsafe_allow_html=True,
    )
    st.markdown(
        '''
        <div style="background:#e8f9f0;border-left:5px solid #34a853;padding:1rem 1.4rem;border-radius:8px;margin-bottom:1.2rem;">
        <p style="margin:0;font-size:1.2rem;font-weight:700;color:#1a1a2e;">📤 Processed results are placed in their respective <strong>Output</strong> folder and available for download.</p>
        </div>
        ''',
        unsafe_allow_html=True,
    )

    cols = st.columns(6, gap="small")

    for col, (key, cfg) in zip(cols, MODES.items()):
        icon_uri = _icon_b64(cfg["icon"]) or ""
        icon_html = (
            f'<img src="{icon_uri}" alt="{cfg["label"]}" style="width:96px;height:96px;object-fit:contain;display:block;margin:0 auto .8rem;">'
            if icon_uri else
            f'<div style="font-size:3.5rem;text-align:center;">\U0001f52c</div>'
        )
        n_in = _count_files(INPUT_DIR / key, cfg["extensions"])

        with col:
            st.markdown(
                f"""
                <div class="mode-card" style="background:{cfg['bg']};border:2px solid {cfg['accent']}60;">
                    {icon_html}
                    <h3 style="color:{cfg['accent']}">{cfg['label']}</h3>
                    <p class="desc">{cfg['description']}</p>
                    <p class="fcount">\U0001f4c2 {n_in} file(s) in input</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.write("")

            if st.button("\U0001f4c2 Input", key=f"inp_{key}", use_container_width=True):
                current = st.session_state.get(f"show_input_{key}", False)
                for k in MODES:
                    st.session_state[f"show_input_{k}"] = False
                    st.session_state[f"show_output_{k}"] = False
                st.session_state[f"show_input_{key}"] = not current
                st.rerun()

            if st.session_state.get(f"show_input_{key}", False):
                dest = INPUT_DIR / key
                dest.mkdir(parents=True, exist_ok=True)
                existing = sorted(f for f in dest.iterdir() if f.is_file() and f.suffix.lower() in cfg["extensions"])
                if existing:
                    st.markdown(" ".join(f'<span class="file-badge">\U0001f4c4 {f.name}</span>' for f in existing), unsafe_allow_html=True)
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
                    st.success(f"\u2705 Saved {len(saved)} file(s): " + ", ".join(f"`{n}`" for n in saved))
                    st.rerun()
                if st.button("\u2716 Close", key=f"close_inp_{key}", use_container_width=True):
                    st.session_state[f"show_input_{key}"] = False
                    st.rerun()

            if st.button("\U0001f4e4 Output", key=f"out_{key}", use_container_width=True):
                current = st.session_state.get(f"show_output_{key}", False)
                for k in MODES:
                    st.session_state[f"show_input_{k}"] = False
                    st.session_state[f"show_output_{k}"] = False
                st.session_state[f"show_output_{key}"] = not current
                st.rerun()

            if st.session_state.get(f"show_output_{key}", False):
                out_folder = OUTPUT_DIR / key
                out_folder.mkdir(parents=True, exist_ok=True)
                out_files = sorted([f for f in out_folder.iterdir() if f.is_file()], key=lambda f: f.stat().st_mtime, reverse=True)
                if out_files:
                    for fp in out_files[:3]:
                        ext = fp.suffix.lower()
                        mime = "text/markdown" if ext == ".md" else "application/octet-stream"
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
                if st.button("\u2716 Close", key=f"close_out_{key}", use_container_width=True):
                    st.session_state[f"show_output_{key}"] = False
                    st.rerun()

            if st.button(f"\u25b6 {cfg['label']}", key=f"go_{key}", use_container_width=True):
                for k in MODES:
                    st.session_state[f"show_input_{k}"] = False
                    st.session_state[f"show_output_{k}"] = False
                st.session_state["page"] = key
                st.rerun()


# -- MODE PAGE -----------------------------------------------------------------

def _mode_page(mode: str) -> None:
    cfg = MODES[mode]
    _render_header(f"Mode: {cfg['label']}")

    # Navigation - Home and Exit only
    nav_l, nav_m, nav_spacer = st.columns([1, 1, 10])
    with nav_l:
        if st.button("🏠 Home", use_container_width=True):
            st.session_state["page"] = "home"
            st.rerun()
    with nav_m:
        if st.button("🚪 Exit to Launcher", use_container_width=True):
            _exit_to_launcher()
    with nav_spacer:
        pass
    st.divider()

    with st.expander("\U0001f4cb Instructions", expanded=False):
        st.markdown(cfg["instructions"])

    icon_uri = _icon_b64(cfg["icon"])
    if icon_uri:
        ic, ti = st.columns([1, 10])
        with ic:
            st.markdown(f'<img src="{icon_uri}" alt="{cfg["label"]}" style="width:64px;height:64px;object-fit:contain;margin-top:.4rem;">', unsafe_allow_html=True)
        with ti:
            st.subheader(cfg["label"])
    else:
        st.subheader(cfg["label"])

    # Sub-mode selection - ONLY for Coding mode
    submode = None
    if mode == "coding" and cfg.get("submodes"):
        submode = st.selectbox("Select sub-mode / pipeline", cfg["submodes"], key=f"submode_{mode}")

    # Provider / Model
    with st.expander("\u2699\ufe0f Provider / Model settings", expanded=True):
        col_p, col_m = st.columns(2)
        with col_p:
            provider = st.selectbox("Provider", PROVIDERS, index=0, key=f"provider_{mode}")
        with col_m:
            model = st.text_input("Model (leave blank for default)", "", key=f"model_{mode}")

    # File upload
    if mode == "sr":
        st.markdown("**Upload article PDFs to** `input/sr/`  \u2014  Accepted: .pdf")
        uploaded_sr = st.file_uploader("Choose PDF files", accept_multiple_files=True, type=["pdf"], key="upload_sr")
        if uploaded_sr:
            dest_sr = INPUT_DIR / "sr"
            dest_sr.mkdir(parents=True, exist_ok=True)
            saved_sr = []
            for uf in uploaded_sr:
                fp = dest_sr / uf.name
                fp.write_bytes(uf.read())
                saved_sr.append(uf.name)
            st.success(f"\u2705 Saved {len(saved_sr)} PDF(s) to `input/sr/`: " + ", ".join(f"`{n}`" for n in saved_sr))
            st.rerun()

        # PICO import
        pico_dir = OUTPUT_DIR / "rct_search"
        pico_files = sorted(pico_dir.glob("pico_*.json"), reverse=True) if pico_dir.exists() else []
        with st.expander("\U0001f4e5 Import PICO from RCT Search", expanded=bool(pico_files)):
            if not pico_files:
                st.info("No PICO files found in `output/rct_search/`. Run RCT Search mode first.")
            else:
                chosen = st.selectbox("Select a saved PICO file", [p.name for p in pico_files], key="pico_select_sr")
                chosen_path = pico_dir / chosen
                import json as _json
                pico_data = _json.loads(chosen_path.read_text(encoding="utf-8"))

                st.markdown("**Review / edit PICO fields before importing:**")
                col_a, col_b = st.columns(2)
                with col_a:
                    p_pop = st.text_input("Population", pico_data.get("population", ""), key="pico_pop")
                    p_int = st.text_input("Intervention", pico_data.get("intervention", ""), key="pico_int")
                with col_b:
                    p_com = st.text_input("Comparator", pico_data.get("comparator", ""), key="pico_com")
                    p_out = st.text_input("Outcome", pico_data.get("outcome", ""), key="pico_out")
                    p_eff = st.selectbox("Effect measure", ["SMD", "MD", "OR", "RR"],
                                         index=["SMD", "MD", "OR", "RR"].index(pico_data.get("effect_measure", "SMD")) if pico_data.get("effect_measure", "SMD") in ["SMD", "MD", "OR", "RR"] else 0,
                                         key="pico_eff")

                if st.button("\u2705 Apply PICO to SR config", key="pico_apply"):
                    import yaml as _yaml
                    yaml_path = BASE_DIR / "sr" / "config" / "prisma_criteria.yaml"
                    cfg_yaml = _yaml.safe_load(yaml_path.read_text(encoding="utf-8")) if yaml_path.exists() else {}
                    cfg_yaml.setdefault("pico", {})
                    cfg_yaml["pico"]["population"] = p_pop
                    cfg_yaml["pico"]["intervention"] = p_int
                    cfg_yaml["pico"]["comparator"] = p_com
                    cfg_yaml["pico"]["outcome"] = p_out
                    cfg_yaml["effect_measure"] = p_eff
                    yaml_path.parent.mkdir(parents=True, exist_ok=True)
                    yaml_path.write_text(_yaml.dump(cfg_yaml, allow_unicode=True, sort_keys=False), encoding="utf-8")
                    st.success(f"\u2705 PICO written to `sr/config/prisma_criteria.yaml`")
                    st.rerun()
    else:
        st.markdown(f"**Upload files to** `input/{mode}/`  \u2014  Accepted: {', '.join(cfg['extensions'])}")
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
            st.success(f"\u2705 Saved {len(saved)} file(s) to `input/{mode}/`: " + ", ".join(f"`{n}`" for n in saved))
            st.rerun()

    st.divider()

    fb1, fb2 = st.columns(2)
    with fb1:
        _show_folder_contents(INPUT_DIR / mode, cfg["extensions"], f"Input \u2014 {cfg['label']}")
    with fb2:
        _show_folder_contents(OUTPUT_DIR / mode, [".md", ".docx", ".pdf", ".py", ".txt"], f"Output \u2014 {cfg['label']}")

    st.divider()

    run_label = f"\u25b6\ufe0f Run {cfg['label']}"
    if mode == "coding" and submode:
        run_label += f" ({submode})"

    if st.button(run_label, type="primary", use_container_width=True, key=f"run_{mode}"):
        result = _launch_terminal(mode, provider, model, submode or "")
        if result == "ok":
            st.success(f"\u2705 **{cfg['label']}** session launched in a new terminal window.")
            st.info(f"\U0001f4bb Work in the terminal window. When done, use the Output browser above to find your results in `output/{mode}/`.")
        else:
            st.error(f"Could not open terminal: {result}")

    latest = _latest_outputs(OUTPUT_DIR / mode)
    if latest:
        st.markdown("**Download previous outputs:**")
        dl_cols = st.columns(min(len(latest), 4))
        for dl_col, fp in zip(dl_cols, latest):
            with dl_col:
                ext = fp.suffix.lower()
                mime = "text/markdown" if ext == ".md" else "application/octet-stream"
                st.download_button(
                    label=f"\u2b07 {fp.name}",
                    data=fp.read_bytes(),
                    file_name=fp.name,
                    mime=mime,
                    use_container_width=True,
                    key=f"dl_{mode}_{fp.name}",
                )


# -- ROUTER --------------------------------------------------------------------

def main() -> None:
    st.set_page_config(
        page_title="AI kcMedicalResearch",
        page_icon=str(ASSETS_DIR / "logo_AI_kcMedicalResearch.png") if (ASSETS_DIR / "logo_AI_kcMedicalResearch.png").exists() else "\U0001f9ec",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    _inject_css()

    if "page" not in st.session_state:
        st.session_state["page"] = "home"

    if st.session_state["page"] == "home":
        _home_page()
    elif st.session_state["page"] in MODES:
        _mode_page(st.session_state["page"])
    else:
        st.session_state["page"] = "home"
        st.rerun()


if __name__ == "__main__":
    main()