#!/bin/bash
# =============================================================================
#  Mac_kcMedicalResearch_UI.sh - Streamlit UI Launcher for macOS (Docker)
#  v2.4.6
#
#  Location: scripts/mac/   (resolves project root two levels up)
# =============================================================================

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
IMAGE="ai-kcmedicalresearch"
PORT=8501
URL="http://localhost:${PORT}"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

echo ""
echo "============================================================"
echo " AI kcMedicalResearch - UI Mode (macOS)  |  v2.4.6"
echo "============================================================"
echo " Project : $SCRIPT_DIR"
echo "============================================================"
echo ""

# --- .env present? -----------------------------------------------------------
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo -e "${YELLOW}[WARNING]${NC} .env file not found."
    for tmpl in .env.example .env.template; do
        if [ -f "$SCRIPT_DIR/$tmpl" ]; then
            echo "Copy $tmpl to .env and add your API keys:"
            echo "  cp \"$SCRIPT_DIR/$tmpl\" \"$SCRIPT_DIR/.env\""
            break
        fi
    done
    echo ""
    read -r -p "Press Enter to exit..."
    exit 1
fi

# --- Docker installed and running? -------------------------------------------
if ! command -v docker &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Docker not found."
    echo "Install Docker Desktop: https://www.docker.com/products/docker-desktop"
    echo ""
    read -r -p "Press Enter to exit..."
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Docker is installed but not running."
    echo "Start Docker Desktop (whale icon in the menu bar), then re-run this script."
    echo ""
    read -r -p "Press Enter to exit..."
    exit 1
fi

# --- Port already in use? ----------------------------------------------------
if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN &> /dev/null; then
    echo -e "${YELLOW}[WARNING]${NC} Port $PORT is already in use."
    echo "Another instance may be running. Open $URL, or stop the other process."
    echo ""
    read -r -p "Press Enter to exit..."
    exit 1
fi

# --- Build image if missing --------------------------------------------------
if ! docker image inspect "$IMAGE" &> /dev/null; then
    echo -e "${BLUE}[BUILD]${NC} Building Docker image (first time only, 5-10 minutes)..."
    echo ""
    if ! docker build -f "$SCRIPT_DIR/docker/Dockerfile" -t "$IMAGE" "$SCRIPT_DIR"; then
        echo ""
        echo -e "${RED}[ERROR]${NC} Docker build failed."
        read -r -p "Press Enter to exit..."
        exit 1
    fi
    echo ""
    echo -e "${GREEN}[OK]${NC} Image built."
    echo ""
fi

echo -e "${BLUE}[RUN]${NC} Starting Streamlit UI..."
echo " Browser : $URL  - opens once the server is ready"
echo " Startup : ~15 seconds (container start + dependency load)"
echo " Stop    : Ctrl+C in this window"
echo ""

# Open the browser only once the port is actually accepting connections.
# The previous version called `open` immediately, which lands on a
# connection-refused page well before Streamlit is listening.
(
    for _ in $(seq 1 60); do
        sleep 1
        if curl -s -o /dev/null "$URL/_stcore/health" 2>/dev/null; then
            open "$URL"
            exit 0
        fi
    done
    echo ""
    echo -e "${YELLOW}[WARNING]${NC} Server did not respond within 60s. Open $URL manually."
) &
BROWSER_PID=$!
trap 'kill "$BROWSER_PID" 2>/dev/null || true' EXIT

# OLLAMA_HOST is overridden because inside a container "localhost" is the
# container itself, not the Mac. host.docker.internal reaches the host.
docker run -it --rm \
    -p "${PORT}:8501" \
    -v "$SCRIPT_DIR/input:/app/input" \
    -v "$SCRIPT_DIR/output:/app/output" \
    -v "$SCRIPT_DIR/data:/app/data" \
    -v "$SCRIPT_DIR/reports:/app/reports" \
    --env-file "$SCRIPT_DIR/.env" \
    -e OLLAMA_HOST=http://host.docker.internal:11434 \
    --add-host host.docker.internal:host-gateway \
    "$IMAGE" \
    streamlit run SOURCE_CODE/ui/app.py \
        --server.port=8501 \
        --server.address=0.0.0.0 \
        --server.headless=true \
        --browser.gatherUsageStats=false

RC=$?
echo ""
if [ "$RC" -ne 0 ]; then
    echo -e "${YELLOW}[EXIT]${NC} Streamlit exited with code $RC."
else
    echo "Streamlit UI stopped."
fi
echo ""
exit "$RC"
