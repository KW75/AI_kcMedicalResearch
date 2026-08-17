#!/bin/bash
# =============================================================================
#  Mac_kcMedicalResearch_CLI.sh - CLI Launcher for macOS (Docker)
#  v2.4.6
#
#  Location: scripts/mac/   (resolves project root two levels up)
# =============================================================================

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
IMAGE="ai-kcmedicalresearch"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

echo ""
echo "============================================================"
echo " AI kcMedicalResearch - CLI Mode (macOS)  |  v2.4.6"
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

echo -e "${BLUE}[RUN]${NC} Starting CLI. Startup takes ~10 seconds while dependencies load."
echo "Use the menu to select a pipeline and provider."
echo ""

# -it gives the container a real TTY, which the interactive PICO and sub-mode
# prompts require. Do not remove.
#
# OLLAMA_HOST is overridden here because inside a container "localhost" is the
# container itself, not the Mac. host.docker.internal reaches the host, where
# Ollama is listening.
docker run -it --rm \
    -v "$SCRIPT_DIR/input:/app/input" \
    -v "$SCRIPT_DIR/output:/app/output" \
    -v "$SCRIPT_DIR/data:/app/data" \
    -v "$SCRIPT_DIR/reports:/app/reports" \
    --env-file "$SCRIPT_DIR/.env" \
    -e OLLAMA_HOST=http://host.docker.internal:11434 \
    --add-host host.docker.internal:host-gateway \
    "$IMAGE" \
    python SOURCE_CODE/main.py

RC=$?
echo ""
if [ "$RC" -ne 0 ]; then
    echo -e "${YELLOW}[EXIT]${NC} CLI exited with code $RC."
else
    echo "CLI session ended."
fi
echo ""
exit "$RC"
