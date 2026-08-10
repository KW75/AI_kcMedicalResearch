#!/bin/bash
# =============================================================================
#  Mac_kcMedicalResearch_CLI.sh - Quick CLI Launcher for Mac
#  v2.0.0  |  Updated for SOURCE_CODE structure
# =============================================================================

# Get the directory where this script is located (project root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo ""
echo "============================================================"
echo " AI kcMedicalResearch - CLI Mode (macOS)"
echo "============================================================"
echo ""

# Check if .env exists
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo -e "\033[33m[WARNING]\033[0m .env file not found!"
    echo "Please copy .env.template to .env and add your API keys."
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "\033[31m[ERROR]\033[0m Docker not found!"
    echo "Please install Docker Desktop for Mac:"
    echo "https://www.docker.com/products/docker-desktop"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Build image if missing
if ! docker images --format "{{.Repository}}" | grep -i "ai-kcmedicalresearch" > /dev/null; then
    echo -e "\033[34m[BUILD]\033[0m Building Docker image (first time only)..."
    echo "This may take 5-10 minutes..."
    echo ""
    docker build -f docker/Dockerfile -t ai-kcmedicalresearch "$SCRIPT_DIR"
fi

echo -e "\033[34m[RUN]\033[0m Starting CLI..."
echo "Use the menu to select pipeline and provider"
echo ""

docker run -it --rm \
    -v "$SCRIPT_DIR/input:/app/input" \
    -v "$SCRIPT_DIR/output:/app/output" \
    -v "$SCRIPT_DIR/data:/app/data" \
    -v "$SCRIPT_DIR/reports:/app/reports" \
    --env-file "$SCRIPT_DIR/.env" \
    --add-host host.docker.internal:host-gateway \
    ai-kcmedicalresearch \
    python SOURCE_CODE/main.py