#!/bin/bash
# =============================================================================
#  Mac_kcMedicalResearch_UI.sh
#  v2.4.8  |  Streamlit UI launcher
#
#  Mirrors scripts/windows/AI_kcMedicalResearch_UI.bat - runs in the project
#  virtualenv, NOT in Docker. For Docker use:  cd docker && docker compose up ui
#
#  Location: scripts/macos/   (resolves project root two levels up)
# =============================================================================

set -uo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_DIR"

PY="$PROJECT_DIR/.venv/bin/python"
PIP="$PROJECT_DIR/.venv/bin/pip"
APP="$PROJECT_DIR/SOURCE_CODE/ui/app.py"
PORT=8501
URL="http://localhost:${PORT}"

echo ""
echo "  ============================================================"
echo "   AI kcMedical Research  |  Streamlit UI  |  v2.4.8"
echo "  ============================================================"
echo "   Project : $PROJECT_DIR"
echo "  ============================================================"
echo ""

# --- Guard: app present ------------------------------------------------------
if [ ! -f "$APP" ]; then
    echo -e "  ${RED}[ERROR]${NC} UI app not found at SOURCE_CODE/ui/app.py"
    echo "   Expected: $APP"
    echo ""
    read -r -p "Press Enter to exit..."
    exit 1
fi

# --- Guard: port free --------------------------------------------------------
if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN &> /dev/null; then
    echo -e "  ${YELLOW}[WARNING]${NC} Port $PORT is already in use."
    echo "   Another instance may be running. Try opening $URL"
    echo ""
    read -r -p "Press Enter to exit..."
    exit 1
fi

# --- Create .venv if missing --------------------------------------------------
if [ ! -x "$PY" ]; then
    echo -e "  ${BLUE}[SETUP]${NC} .venv not found. Looking for a supported Python..."

    PYBIN=""
    for candidate in python3.12 python3.11 python3; do
        if command -v "$candidate" &> /dev/null; then
            if "$candidate" -c 'import sys; raise SystemExit(0 if (3,11) <= sys.version_info[:2] < (3,13) else 1)' 2>/dev/null; then
                PYBIN="$candidate"
                break
            fi
        fi
    done

    if [ -z "$PYBIN" ]; then
        echo -e "  ${RED}[ERROR]${NC} No Python 3.11 or 3.12 found."
        echo ""
        echo "   This project does not support Python 3.13+ - several pinned"
        echo "   dependencies have no wheels for it."
        echo ""
        echo "   Install 3.12:  brew install python@3.12"
        echo "              or  https://www.python.org/downloads/release/python-3129/"
        echo ""
        echo "   Or use Docker, which supplies its own Python:"
        echo "     cd docker && docker compose up ui"
        echo ""
        read -r -p "Press Enter to exit..."
        exit 1
    fi

    echo -e "  ${BLUE}[SETUP]${NC} Using $("$PYBIN" -c 'import sys; print(sys.executable)')"
    echo ""
    if ! "$PYBIN" -m venv .venv; then
        echo -e "  ${RED}[ERROR]${NC} Failed to create .venv."
        read -r -p "Press Enter to exit..."
        exit 1
    fi

    echo -e "  ${BLUE}[SETUP]${NC} Installing dependencies - this takes a few minutes..."
    "$PIP" install --upgrade pip --quiet
    if ! "$PIP" install -r requirements.txt --quiet; then
        echo -e "  ${RED}[ERROR]${NC} Failed to install dependencies."
        read -r -p "Press Enter to exit..."
        exit 1
    fi
    echo -e "  ${GREEN}[OK]${NC} Dependencies installed."
    echo ""
fi

# --- Warn if .env missing ----------------------------------------------------
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "  ------------------------------------------------------------"
    echo -e "   ${YELLOW}NOTE${NC}: no .env file found in the project root."
    echo "   Cloud providers need API keys:  cp .env.example .env"
    echo "   Or run offline with:  --provider ollama"
    echo "  ------------------------------------------------------------"
    echo ""
fi

# --- Launch ------------------------------------------------------------------
echo "  ------------------------------------------------------------"
echo "   Launching Streamlit UI"
echo "   Browser : $URL  - opens automatically"
echo "   Startup : ~7 seconds - please wait"
echo "   Stop    : Ctrl+C in this window"
echo "  ------------------------------------------------------------"
echo ""

# Streamlit opens the browser itself once the server is listening. Do not add
# a separate `open` call - it produces a second tab and fires too early.
"$PY" -m streamlit run "$APP" \
    --server.port="$PORT" \
    --server.headless=false \
    --server.runOnSave=false \
    --browser.gatherUsageStats=false
RC=$?

echo ""
if [ "$RC" -ne 0 ]; then
    echo -e "  ${YELLOW}[EXIT]${NC} Streamlit exited with code $RC."
else
    echo "  Streamlit UI stopped."
fi
echo ""
exit "$RC"
