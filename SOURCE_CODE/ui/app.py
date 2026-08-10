# SOURCE_CODE/ui/app.py
from __future__ import annotations

import base64
import io
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional, Dict, List, Any

import streamlit as st

# ============================================================================
# CONFIGURATION
# ============================================================================

class UIConfig:
    """Centralized configuration for UI."""
    # Timeouts
    TIMEOUT = 600  # 10 minutes
    LLM_TIMEOUT = 300  # 5 minutes for LLM calls
    
    # Display limits
    MAX_OUTPUT_FILES = 4
    MAX_PREVIEW_FILES = 3
    MAX_PICO_FILES = 5
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    
    # Image settings
    LOGO_SIZE = (96, 96)
    THUMBNAIL_SIZE = (64, 64)
    
    # Cache TTL
    CACHE_TTL = 300  # 5 minutes

# ============================================================================
# PATHS
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SOURCE_CODE_DIR = PROJECT_ROOT / "SOURCE_CODE"
SR_DIR = SOURCE_CODE_DIR / "pipelines" / "sr"

ASSETS_DIR = PROJECT_ROOT / "assets"
INPUT_DIR = PROJECT_ROOT / "input"
OUTPUT_DIR = PROJECT_ROOT / "output"
REPORTS_DIR = PROJECT_ROOT / "reports"
MAIN_PY = SOURCE_CODE_DIR / "main.py"

# ============================================================================
# MODE CONFIGURATION
# ============================================================================

MODES: Dict[str, Dict[str, Any]] = {
    "coding": {
        "label": "Coding",
        "icon": ASSETS_DIR / "icon_Coding_agent.png",
        "accent": "#4A90D9",
        "bg": "#EBF4FF",
        "description": "Code generation,\nReview & Revision.",
        "extensions": [".py", ".js", ".ts", ".html", ".css", ".java",
                       ".c", ".cpp", ".cs", ".rb", ".go", ".rs", ".txt", ".md"],
        "submodes": ["Builder (pipeline)", "Reviewer", "Tester"],
        "instructions": (
            "**How to use Coding mode**\n\n"
            "1. Drop source files into `input/coding/`.\n"
            "2. Choose your provider and model below.\n"
            "3. Select a sub-mode:\n"
            "   - **Builder**: Full pipeline (Builder → Reviewer → Tester)\n"
            "   - **Reviewer**: Standalone code review\n"
            "   - **Tester**: Standalone test generation\n"
            "4. Click **Run Coding** → the AI will process your code.\n"
            "5. Outputs appear in `output/coding/`."
        ),
    },
    "writing": {
        "label": "Writing",
        "icon": ASSETS_DIR / "icon_Writing_agent.png",
        "accent": "#27AE60",
        "bg": "#EAFAF1",
        "description": "Medical Writing\nReports from docs.",
        "extensions": [".txt", ".md", ".docx", ".pdf"],
        "instructions": (
            "**How to use Writing mode**\n\n"
            "1. Drop `.txt`, `.md`, `.docx`, or `.pdf` files into `input/writing/`.\n"
            "2. Choose your provider and model below.\n"
            "3. Click **Run Writing** → you will be prompted in the terminal to select:\n"
            "   - **Topic Track**: Editorial/opinion style (newspaper)\n"
            "   - **Article Track**: Medical journal article style\n"
            "4. A structured report is generated.\n"
            "5. Markdown and Word outputs appear in `output/writing/`."
        ),
    },
    "appraisal": {
        "label": "Appraisal",
        "icon": ASSETS_DIR / "icon_Appraisal_agent.png",
        "accent": "#8E44AD",
        "bg": "#F5EEF8",
        "description": "Critical Appraisal\nof Research Articles.",
        "extensions": [".pdf", ".txt", ".md", ".docx"],
        "instructions": (
            "**How to use Appraisal mode**\n\n"
            "1. Drop article PDFs or text files into `input/appraisal/`.\n"
            "2. Choose your provider and model below.\n"
            "3. Click **Run Appraisal** → you will be prompted in the terminal to select:\n"
            "   - **Appraiser**: Critical appraisal of methodology\n"
            "   - **Methodologist**: Statistical and design assessment\n"
            "   - **Summariser**: Concise article summary\n"
            "4. Merged report (`.md` + `.docx`) appears in `output/appraisal/`."
        ),
    },
    "rct_search": {
        "label": "RCT Search",
        "icon": ASSETS_DIR / "icon_RCT_Search_agent.png",
        "accent": "#E67E22",
        "bg": "#FEF9E7",
        "description": "RCT Articles Search\nfrom PubMed & Embase.",
        "extensions": [".txt", ".md"],
        "instructions": (
            "**How to use RCT Search mode**\n\n"
            "1. Place a `topic.md` file in `input/rct_search/`, or enter your PICO topic "
            "when prompted in the terminal.\n"
            "2. Choose your provider and model below.\n"
            "3. Click **Run RCT Search** → the pipeline builds, validates, and "
            "refines a search strategy.\n"
            "4. Outputs appear in `output/rct_search/`."
        ),
    },
    "search": {
        "label": "Search",
        "icon": ASSETS_DIR / "icon_Search_agent.png",
        "accent": "#16A085",
        "bg": "#E8F8F5",
        "description": "Evidence-based\nClinical Search.",
        "extensions": [".txt", ".md"],
        "instructions": (
            "**How to use Search mode**\n\n"
            "1. Place a `topic.md` file in `input/search/`, or enter your clinical topic "
            "when prompted in the terminal.\n"
            "2. Choose your provider and model below.\n"
            "3. Click **Run Search** → you will be prompted in the terminal to select:\n"
            "   - **Topic Search**: Web synopsis with reference links\n"
            "   - **Article Search**: PubMed search by article type + comparison\n"
            "4. Results are saved to `output/search/`."
        ),
    },
    "sr": {
        "label": "Systematic Review",
        "icon": ASSETS_DIR / "icon_SR_agent.png",
        "accent": "#C0392B",
        "bg": "#FDEDEC",
        "description": "Full SR Pipeline:\nPRISMA to Meta-analysis.",
        "extensions": [".pdf"],
        "instructions": (
            "**How to use Systematic Review mode**\n\n"
            "**Phase 1 – Discovery (optional):**\n"
            "1. Run RCT Search mode first to generate a ranked article list.\n"
            "2. Use **Import PICO from RCT Search** below to pre-fill your PICO fields.\n\n"
            "**Phase 2 – Synthesis:**\n"
            "3. Upload your chosen article PDFs to `input/sr/`.\n"
            "4. Review or edit the imported PICO fields.\n"
            "5. Click **Run Systematic Review** → results saved to `output/sr/`."
        ),
    },
}

PROVIDERS = ["ollama", "openai", "anthropic", "deepseek", "groq", "qwen"]

PROVIDER_ENV_MAP = {
    "qwen": "DASHSCOPE_API_KEY",
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "groq": "GROQ_API_KEY",
}

# ============================================================================
# SESSION STATE MANAGEMENT
# ============================================================================

def _initialize_session_state() -> None:
    """Initialize all session state variables."""
    defaults = {
        "page": "home",
        "api_keys": {},
    }
    # Add dynamic keys for input/output visibility
    for mode in MODES:
        defaults[f"show_input_{mode}"] = False
        defaults[f"show_output_{mode}"] = False
    
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default

# ============================================================================
# VALIDATION HELPERS
# ============================================================================

def _validate_mode(mode: str) -> bool:
    """Validate that mode exists."""
    return mode in MODES

def _validate_provider(provider: str) -> bool:
    """Validate that provider exists."""
    return provider in PROVIDERS

def _validate_file_size(uploaded_file) -> bool:
    """Check if file size is within limits."""
    return uploaded_file.size <= UIConfig.MAX_FILE_SIZE

def _validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
    """Check if file extension is allowed."""
    ext = Path(filename).suffix.lower()
    return ext in allowed_extensions

# ============================================================================
# API KEY HELPERS
# ============================================================================

def _get_api_key_env_name(provider: str) -> str:
    """Get environment variable name for a provider."""
    return PROVIDER_ENV_MAP.get(provider, f"{provider.upper()}_API_KEY")

def _get_env_with_api_keys() -> Dict[str, str]:
    """Get environment with API keys merged from session."""
    env_vars = os.environ.copy()
    
    for key, value in st.session_state.get('api_keys', {}).items():
        if value:
            env_var = _get_api_key_env_name(key)
            env_vars[env_var] = value
    
    return env_vars

def _has_api_key(provider: str) -> bool:
    """Check if API key is available for a provider."""
    if provider == "ollama":
        return True
    env_var = _get_api_key_env_name(provider)
    session_keys = st.session_state.get('api_keys', {})
    return bool(session_keys.get(provider) or os.getenv(env_var))

# ============================================================================
# UI HELPERS
# ============================================================================

def _icon_b64(path: Path) -> Optional[str]:
    """Convert icon to base64 data URI."""
    if not path.exists():
        return None
    try:
        from PIL import Image
        img = Image.open(path).convert("RGBA")
        img.thumbnail(UIConfig.LOGO_SIZE, Image.Resampling.LANCZOS)
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

def _logo_b64() -> Optional[str]:
    """Get logo as base64 data URI."""
    for name in ("logo_AI_kcMedicalResearch.png", "logo_AI_kcMedicalResearch.jpg"):
        p = ASSETS_DIR / name
        if p.exists():
            return _icon_b64(p)
    return None

def _count_files(folder: Path, exts: List[str]) -> int:
    """Count files in folder with given extensions."""
    if not folder.exists():
        return 0
    return sum(1 for f in folder.iterdir() if f.is_file() and f.suffix.lower() in exts)

def _latest_outputs(folder: Path, suffixes: tuple = (".md", ".docx")) -> List[Path]:
    """Get latest output files."""
    if not folder.exists():
        return []
    files = [f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in suffixes]
    return sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)[:UIConfig.MAX_OUTPUT_FILES]

@st.cache_data(ttl=UIConfig.CACHE_TTL)
def _get_cached_pico_files(directory: Path) -> List[Path]:
    """Cache PICO file list."""
    if not directory.exists():
        return []
    return sorted(directory.glob("pico_*.json"), reverse=True)

def _upload_files_with_progress(files: List, dest: Path, progress_text: str = "Uploading...") -> int:
    """Upload files with progress bar."""
    if not files:
        return 0
    
    progress = st.progress(0)
    status = st.status(progress_text, expanded=True)
    
    saved_count = 0
    for i, uf in enumerate(files):
        # Validate file size
        if not _validate_file_size(uf):
            status.write(f"⚠️ {uf.name} exceeds size limit ({UIConfig.MAX_FILE_SIZE // (1024*1024)}MB)")
            continue
        
        status.write(f"📤 Uploading {uf.name}...")
        fp = dest / uf.name
        fp.write_bytes(uf.read())
        saved_count += 1
        progress.progress((i + 1) / len(files))
    
    status.update(label=f"✅ Uploaded {saved_count} file(s)", state="complete")
    return saved_count

# ============================================================================
# DISPLAY HELPERS
# ============================================================================

def _show_folder_contents(folder: Path, exts: List[str], label: str) -> None:
    """Display folder contents with download buttons."""
    folder.mkdir(parents=True, exist_ok=True)
    files = sorted(
        [f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in exts]
    ) if folder.exists() else []
    
    with st.expander(f"📂 {label}  —  `{folder.relative_to(PROJECT_ROOT)}`", expanded=True):
        if files:
            for f in files[:UIConfig.MAX_PREVIEW_FILES]:
                c1, c2 = st.columns([6, 1])
                with c1:
                    st.markdown(f'<span class="file-badge">📄 {f.name}</span>', unsafe_allow_html=True)
                with c2:
                    ext = f.suffix.lower()
                    mime = (
                        "text/markdown" if ext == ".md" else
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document" if ext == ".docx" else
                        "application/pdf" if ext == ".pdf" else
                        "application/octet-stream"
                    )
                    st.download_button(
                        label="⬇",
                        data=f.read_bytes(),
                        file_name=f.name,
                        mime=mime,
                        key=f"browse_{label}_{f.name}",
                    )
            if len(files) > UIConfig.MAX_PREVIEW_FILES:
                st.caption(f"+ {len(files) - UIConfig.MAX_PREVIEW_FILES} more file(s)")
        else:
            st.info("No files found.")

def _render_header(subtitle: str = "") -> None:
    """Render the app header."""
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

def _api_key_sidebar() -> None:
    """Render API key sidebar."""
    with st.sidebar:
        st.header("🔑 API Keys")
        st.caption("Enter your API keys here (optional)")
        
        # Check if env keys exist
        has_env = any(os.environ.get(_get_api_key_env_name(p)) for p in PROVIDER_ENV_MAP.keys())
        
        if has_env:
            st.success("✅ Using environment API keys")
        
        # Initialize session state for API keys
        if 'api_keys' not in st.session_state:
            st.session_state.api_keys = {}
        
        # Provider-specific key inputs
        for provider, label in {
            'openai': 'OpenAI',
            'anthropic': 'Anthropic',
            'groq': 'Groq',
            'deepseek': 'DeepSeek',
            'qwen': 'Qwen (Alibaba)',
        }.items():
            env_var = _get_api_key_env_name(provider)
            env_exists = os.environ.get(env_var, '')
            
            input_key = st.text_input(
                label,
                type="password",
                placeholder="Enter API key..." if not env_exists else "Override environment key",
                key=f"api_{provider}",
                help=f"Set {env_var} in environment or enter here"
            )
            
            if input_key:
                st.session_state.api_keys[provider] = input_key
        
        # Show current status
        if st.session_state.api_keys:
            st.divider()
            st.caption("Current session keys:")
            for key in st.session_state.api_keys:
                st.caption(f"✅ {key.title()}: ********")

# ============================================================================
# TERMINAL LAUNCHER
# ============================================================================

def _is_cloud_environment() -> bool:
    """Detect if running in cloud environment."""
    return any([
        os.environ.get('STREAMLIT_SHARING'),
        os.environ.get('REPL_ID'),
        os.environ.get('CODESPACES'),
        os.environ.get('STREAMLIT_SERVER_PORT'),
        os.environ.get('RENDER'),
        os.environ.get('RENDER_SERVICE_ID'),
        os.environ.get('RENDER_GIT_COMMIT'),
    ])

def _launch_terminal(mode: str, provider: str, model: str, submode: str = "", prompt: str = "") -> str:
    """Launch CLI - detects environment and runs appropriately."""
    if _is_cloud_environment():
        return _run_cli_cloud(mode, provider, model, submode, prompt)
    return _launch_terminal_local(mode, provider, model, submode)

def _run_cli_cloud(mode: str, provider: str, model: str, submode: str = "", prompt: str = "") -> str:
    """Run CLI directly in cloud environment."""
    # Save prompt if provided
    if prompt.strip():
        prompt_file = INPUT_DIR / mode / "instructions.txt"
        prompt_file.parent.mkdir(parents=True, exist_ok=True)
        prompt_file.write_text(prompt.strip(), encoding="utf-8")
    
    # Build command
    cmd_parts = [sys.executable, str(SOURCE_CODE_DIR / "main.py"), "--mode", mode, "--provider", provider]
    
    # Add sub-mode for search
    if mode == "search" and submode:
        cmd_parts += ["--sub", submode]
    
    # Add submode flags for coding
    if mode == "coding" and submode:
        if "Builder" in submode:
            cmd_parts += ["--role", "Builder"]
        elif "Reviewer" in submode:
            cmd_parts += ["--role", "Reviewer"]
        elif "Tester" in submode:
            cmd_parts += ["--role", "Tester"]
    
    st.code("$ " + " ".join(cmd_parts))
    
    # Check for API keys
    if provider != "ollama" and not _has_api_key(provider):
        env_var = _get_api_key_env_name(provider)
        st.warning(f"⚠️ {env_var} not set. Please enter it in the sidebar or add to environment.")
        st.info("Go to sidebar → API Keys → Enter your key")
        return "error: missing API key"
    
    with st.spinner(f"Running {mode} mode..."):
        try:
            env_vars = _get_env_with_api_keys()
            
            result = subprocess.run(
                cmd_parts,
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                timeout=UIConfig.TIMEOUT,
                env=env_vars
            )
            
            if result.stdout:
                st.text_area("📤 Output", result.stdout, height=300)
            if result.stderr:
                st.text_area("⚠️ Errors/Warnings", result.stderr, height=100)
            
            if result.returncode == 0:
                st.success("✅ Command completed successfully!")
                return "ok"
            else:
                st.error(f"❌ Command failed with exit code {result.returncode}")
                return f"error: code {result.returncode}"
        
        except subprocess.TimeoutExpired:
            st.error(f"⏰ Command timed out after {UIConfig.TIMEOUT} seconds")
            st.info("💡 Try running with fewer files or a faster provider.")
            return "error: timeout"
        except Exception as exc:
            st.error(f"❌ Error: {exc}")
            return f"error: {exc}"

def _launch_terminal_local(mode: str, provider: str, model: str, submode: str = "") -> str:
    """Launch terminal locally with API keys from session."""
    py = sys.executable
    mp = str(MAIN_PY)
    base = str(PROJECT_ROOT)
    
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
    env_vars = _get_env_with_api_keys()
    
    try:
        if sys.platform == "win32":
            return _launch_windows(cmd_str, base, env_vars, mode, provider)
        elif sys.platform == "darwin":
            return _launch_macos(cmd_str, base, env_vars)
        else:
            return _launch_linux(cmd_str, base, env_vars)
    except Exception as exc:
        return f"error: {exc}"

def _launch_windows(cmd_str: str, base: str, env_vars: Dict, mode: str, provider: str) -> str:
    """Launch on Windows."""
    script_lines = []
    
    # Set API keys from session
    for key, value in env_vars.items():
        if key.endswith('_API_KEY') or key in ['DASHSCOPE_BASE_URL', 'DASHSCOPE_ANTHROPIC_URL']:
            script_lines.append(f'set "{key}={value}"')
    
    script_lines.append(f'cd /d "{base}"')
    script_lines.append(cmd_str)
    script_lines.append('')
    script_lines.append('echo.')
    script_lines.append('echo Session completed. Press any key to close this window...')
    script_lines.append('pause >nul')
    
    script_content = "\r\n".join(script_lines)
    temp_bat = Path(tempfile.gettempdir()) / f"ai_km_run_{mode}_{provider}.bat"
    temp_bat.write_text(script_content, encoding='utf-8')
    
    subprocess.Popen(
        ["cmd", "/k", str(temp_bat)],
        creationflags=subprocess.CREATE_NEW_CONSOLE,
        cwd=base,
        env=env_vars
    )
    return "ok"

def _launch_macos(cmd_str: str, base: str, env_vars: Dict) -> str:
    """Launch on macOS."""
    env_exports = " && ".join([f'export {k}="{v}"' for k, v in env_vars.items() if k.endswith('_API_KEY')])
    subprocess.Popen(
        ["osascript", "-e",
         f'tell app "Terminal" to do script "cd \'{base}\' && {env_exports} && {cmd_str} && echo \'Session completed. Press any key to close...\' && read"'],
        env=env_vars
    )
    return "ok"

def _launch_linux(cmd_str: str, base: str, env_vars: Dict) -> str:
    """Launch on Linux."""
    env_exports = " && ".join([f'export {k}="{v}"' for k, v in env_vars.items() if k.endswith('_API_KEY')])
    subprocess.Popen(
        ["x-terminal-emulator", "-e", "bash", "-c",
         f"cd '{base}' && {env_exports} && {cmd_str} && echo 'Session completed. Press any key to close...' && read"],
        cwd=base,
        env=env_vars
    )
    return "ok"

def _exit_to_launcher() -> None:
    """Display exit message and clear session state."""
    st.markdown(
        """
        <div style="text-align:center;padding:60px 20px;">
            <h1 style="font-size:3rem;">🚪</h1>
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

# ============================================================================
# CSS
# ============================================================================

def _inject_css() -> None:
    """Inject custom CSS."""
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

        /* Navigation buttons */
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

        /* All buttons */
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

# ============================================================================
# PAGES
# ============================================================================

def _home_page() -> None:
    """Render the home page."""
    _api_key_sidebar()
    _render_header("Select a mode to begin")
    
    col_exit, col_spacer = st.columns([1, 11])
    with col_exit:
        if st.button("🚪 Exit to Launcher", key="exit_launcher_home"):
            _exit_to_launcher()
    
    st.markdown(
        '''
        <div style="background:#e8f4fd;border-left:5px solid #1a73e8;padding:1rem 1.4rem;border-radius:8px;margin-bottom:.5rem;">
        <p style="margin:0;font-size:1.2rem;font-weight:700;color:#1a1a2e;">📁 Files uploaded to <strong>Input</strong> are automatically transferred to their respective input folder.</p>
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
            f'<div style="font-size:3.5rem;text-align:center;">🔬</div>'
        )
        n_in = _count_files(INPUT_DIR / key, cfg["extensions"])
        
        with col:
            st.markdown(
                f"""
                <div class="mode-card" style="background:{cfg['bg']};border:2px solid {cfg['accent']}60;">
                    {icon_html}
                    <h3 style="color:{cfg['accent']}">{cfg['label']}</h3>
                    <p class="desc">{cfg['description']}</p>
                    <p class="fcount">📂 {n_in} file(s) in input</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.write("")
            
            if st.button("📂 Input", key=f"inp_{key}", use_container_width=True):
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
                    st.markdown(" ".join(f'<span class="file-badge">📄 {f.name}</span>' for f in existing[:5]), unsafe_allow_html=True)
                    if len(existing) > 5:
                        st.caption(f"+ {len(existing) - 5} more")
                
                ups = st.file_uploader(
                    f"Add files → `input/{key}/`",
                    accept_multiple_files=True,
                    type=[e.lstrip(".") for e in cfg["extensions"]],
                    key=f"home_upload_{key}",
                )
                if ups:
                    saved = _upload_files_with_progress(ups, dest)
                    if saved > 0:
                        st.rerun()
                
                if st.button("✖ Close", key=f"close_inp_{key}", use_container_width=True):
                    st.session_state[f"show_input_{key}"] = False
                    st.rerun()
            
            if st.button("📤 Output", key=f"out_{key}", use_container_width=True):
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
                            label=f"⬇ {fp.name}",
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
                if st.button("✖ Close", key=f"close_out_{key}", use_container_width=True):
                    st.session_state[f"show_output_{key}"] = False
                    st.rerun()
            
            if st.button(f"▶ {cfg['label']}", key=f"go_{key}", use_container_width=True):
                for k in MODES:
                    st.session_state[f"show_input_{k}"] = False
                    st.session_state[f"show_output_{k}"] = False
                st.session_state["page"] = key
                st.rerun()

def _mode_page(mode: str) -> None:
    """Render a mode page."""
    if not _validate_mode(mode):
        st.error(f"Invalid mode: {mode}")
        return
    
    _api_key_sidebar()
    cfg = MODES[mode]
    _render_header(f"Mode: {cfg['label']}")
    
    # Navigation
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
    
    with st.expander("📋 Instructions", expanded=False):
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
    
    # Sub-mode selection (only for Coding)
    submode = None
    if mode == "coding" and cfg.get("submodes"):
        submode = st.selectbox("Select sub-mode / pipeline", cfg["submodes"], key=f"submode_{mode}")
    
    # Provider / Model
    with st.expander("⚙️ Provider / Model settings", expanded=True):
        col_p, col_m = st.columns(2)
        with col_p:
            provider = st.selectbox("Provider", PROVIDERS, index=0, key=f"provider_{mode}")
        with col_m:
            model = st.text_input("Model (leave blank for default)", "", key=f"model_{mode}")
            if provider != "ollama":
                st.caption(f"💡 Requires {_get_api_key_env_name(provider)} in environment or sidebar")
    
    # File upload
    if mode == "sr":
        st.markdown("**Upload article PDFs to** `input/sr/`  —  Accepted: .pdf")
        uploaded_sr = st.file_uploader("Choose PDF files", accept_multiple_files=True, type=["pdf"], key="upload_sr")
        if uploaded_sr:
            dest_sr = INPUT_DIR / "sr"
            dest_sr.mkdir(parents=True, exist_ok=True)
            saved_sr = _upload_files_with_progress(uploaded_sr, dest_sr, "Uploading PDFs...")
            if saved_sr > 0:
                st.rerun()
        
        # PICO import
        pico_dir = OUTPUT_DIR / "rct_search"
        pico_files = _get_cached_pico_files(pico_dir)
        with st.expander("📥 Import PICO from RCT Search", expanded=bool(pico_files)):
            if not pico_files:
                st.info("No PICO files found in `output/rct_search/`. Run RCT Search mode first.")
            else:
                chosen = st.selectbox("Select a saved PICO file", [p.name for p in pico_files], key="pico_select_sr")
                chosen_path = pico_dir / chosen
                import json as _json
                try:
                    pico_data = _json.loads(chosen_path.read_text(encoding="utf-8"))
                except Exception as e:
                    st.error(f"Failed to load PICO: {e}")
                    return
                
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
                
                if st.button("✅ Apply PICO to SR config", key="pico_apply"):
                    import yaml as _yaml
                    yaml_path = SR_DIR / "config" / "prisma_criteria.yaml"
                    cfg_yaml = _yaml.safe_load(yaml_path.read_text(encoding="utf-8")) if yaml_path.exists() else {}
                    cfg_yaml.setdefault("pico", {})
                    cfg_yaml["pico"]["population"] = p_pop
                    cfg_yaml["pico"]["intervention"] = p_int
                    cfg_yaml["pico"]["comparator"] = p_com
                    cfg_yaml["pico"]["outcome"] = p_out
                    cfg_yaml["effect_measure"] = p_eff
                    yaml_path.parent.mkdir(parents=True, exist_ok=True)
                    yaml_path.write_text(_yaml.dump(cfg_yaml, allow_unicode=True, sort_keys=False), encoding="utf-8")
                    st.success(f"✅ PICO written to `SOURCE_CODE/pipelines/sr/config/prisma_criteria.yaml`")
                    st.rerun()
    else:
        st.markdown(f"**Upload files to** `input/{mode}/`  —  Accepted: {', '.join(cfg['extensions'])}")
        uploaded = st.file_uploader(
            "Choose files",
            accept_multiple_files=True,
            type=[e.lstrip(".") for e in cfg["extensions"]],
            key=f"upload_{mode}",
        )
        if uploaded:
            dest = INPUT_DIR / mode
            dest.mkdir(parents=True, exist_ok=True)
            saved = _upload_files_with_progress(uploaded, dest)
            if saved > 0:
                st.rerun()
    
    st.divider()
    
    fb1, fb2 = st.columns(2)
    with fb1:
        _show_folder_contents(INPUT_DIR / mode, cfg["extensions"], f"Input — {cfg['label']}")
    with fb2:
        _show_folder_contents(OUTPUT_DIR / mode, [".md", ".docx", ".pdf", ".py", ".txt"], f"Output — {cfg['label']}")
    
    st.divider()
    
    run_label = f"▶️ Run {cfg['label']}"
    if mode == "coding" and submode:
        run_label += f" ({submode})"
    
    if st.button(run_label, type="primary", use_container_width=True, key=f"run_{mode}"):
        if not _validate_mode(mode):
            st.error(f"Invalid mode: {mode}")
            return
        
        if not _validate_provider(provider):
            st.error(f"Invalid provider: {provider}")
            return
        
        result = _launch_terminal(mode, provider, model, submode or "")
        if result == "ok":
            st.success(f"✅ **{cfg['label']}** session launched in a new terminal window.")
            st.info("💻 Work in the terminal window. When done, use the Output browser above to find your results in `output/{mode}/`.")
        else:
            st.error(f"❌ Could not open terminal: {result}")
    
    latest = _latest_outputs(OUTPUT_DIR / mode)
    if latest:
        st.markdown("**Download previous outputs:**")
        dl_cols = st.columns(min(len(latest), 4))
        for dl_col, fp in zip(dl_cols, latest):
            with dl_col:
                ext = fp.suffix.lower()
                mime = "text/markdown" if ext == ".md" else "application/octet-stream"
                st.download_button(
                    label=f"⬇ {fp.name}",
                    data=fp.read_bytes(),
                    file_name=fp.name,
                    mime=mime,
                    use_container_width=True,
                    key=f"dl_{mode}_{fp.name}",
                )

# ============================================================================
# MAIN
# ============================================================================

def main() -> None:
    """Main entry point."""
    st.set_page_config(
        page_title="AI kcMedicalResearch",
        page_icon=str(ASSETS_DIR / "logo_AI_kcMedicalResearch.png") if (ASSETS_DIR / "logo_AI_kcMedicalResearch.png").exists() else "🧬",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _inject_css()
    _initialize_session_state()
    
    if st.session_state["page"] == "home":
        _home_page()
    elif st.session_state["page"] in MODES:
        _mode_page(st.session_state["page"])
    else:
        st.session_state["page"] = "home"
        st.rerun()

if __name__ == "__main__":
    main()