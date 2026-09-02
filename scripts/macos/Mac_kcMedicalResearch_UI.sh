#!/bin/bash
# =============================================================================
#  Mac_kcMedicalResearch_UI.sh
#  v2.4.13  |  Streamlit UI launcher
#
#  Run with:  bash scripts/macos/Mac_kcMedicalResearch_UI.sh
#  (Running via bash avoids zsh choking on '#' comment lines.)
# =============================================================================
set -uo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_DIR"

PY="$PROJECT_DIR/.venv/bin/python"
PIP="$PROJECT_DIR/.venv/bin/pip"
APP="$PROJECT_DIR/SOURCE_CODE/ui/app.py"

echo ""
echo "  ============================================================"
echo "   AI kcMedical Research  |  Streamlit UI  |  v2.4.13"
echo "   Project: $PROJECT_DIR"
echo "  ============================================================"
echo ""

show_install_message() {
    echo ""
    echo "  ------------------------------------------------------------"
    echo "   This app needs Python 3.11."
    echo ""
    echo "   1. Download it here:"
    echo "      https://www.python.org/downloads/release/python-3119/"
    echo "      (choose \"macOS 64-bit universal2 installer\")"
    echo ""
    echo "   2. Open the downloaded file and click through Install."
    echo ""
    echo "   3. Start this app again."
    echo "  ------------------------------------------------------------"
    echo ""
    read -r -p "  Press Enter to close..."
}

# --- GUARD: app present ------------------------------------------------------
if [ ! -f "$APP" ]; then
    echo "  [ERROR] UI app not found at SOURCE_CODE/ui/app.py"
    read -r -p "  Press Enter to close..."
    exit 1
fi

# --- CHECK / CREATE .venv ----------------------------------------------------
if [ ! -x "$PY" ]; then
    # Find a genuine python.org / non-conda Python 3.11.
    PYBIN=""
    for candidate in \
        /Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11 \
        /usr/local/bin/python3.11 \
        /opt/homebrew/bin/python3.11 \
        python3.11; do
        found="$(command -v "$candidate" 2>/dev/null || true)"
        [ -z "$found" ] && continue
        case "$found" in *conda*|*anaconda*|*miniconda*) continue ;; esac
        if "$found" -c 'import sys; raise SystemExit(0 if sys.version_info[:2]==(3,11) else 1)' 2>/dev/null; then
            PYBIN="$found"; break
        fi
    done

    if [ -z "$PYBIN" ]; then
        show_install_message
        exit 1
    fi

    echo "  Using Python: $PYBIN"
    echo ""
    "$PYBIN" -m venv .venv || { echo "  [ERROR] Could not create the app environment."; read -r -p "  Press Enter to close..."; exit 1; }

    echo "  Setting up, please wait - this can take a few minutes."
    echo "  The screen may look frozen. That is normal - do NOT close this window."
    echo ""
    "$PIP" install --upgrade pip
    if ! "$PIP" install -r requirements-local.txt; then
        echo ""
        echo "  [ERROR] Could not install the app's components."
        show_install_message
        exit 1
    fi
    echo ""
    echo "  Setup complete."
    echo ""
fi

# --- WARN IF .env MISSING ----------------------------------------------------
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "  ------------------------------------------------------------"
    echo "   NOTE: no .env file found."
    echo "   To use a cloud provider, copy .env.example to .env and add"
    echo "   your API key. To use the free local option, set up Ollama"
    echo "   (see README Step 2)."
    echo "  ------------------------------------------------------------"
    echo ""
fi

# --- LAUNCH (Streamlit UI) ---------------------------------------------------
echo "  Starting the web interface at http://localhost:8501"
echo "  (Close this window or press Ctrl+C to stop.)"
echo ""
"$PY" -m streamlit run "$APP" --server.port=8501 --browser.gatherUsageStats=false
RC=$?
exit "$RC"

