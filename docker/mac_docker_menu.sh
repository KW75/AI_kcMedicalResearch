#!/bin/bash
# =============================================================================
#  docker_menu.sh - AI kcMedicalResearch Docker Menu for macOS
#  v2.0.0  |  Interactive menu (CLI/UI selection)
# =============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo ""
echo "============================================================"
echo " AI kcMedicalResearch - Docker Menu (macOS)"
echo "============================================================"
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Docker not found!"
    echo ""
    echo "Please install Docker Desktop for Mac:"
    echo "https://www.docker.com/products/docker-desktop"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Check Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Docker is not running!"
    echo ""
    echo "Please start Docker Desktop first."
    echo "Look for the Docker icon in your menu bar."
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}[Setup]${NC} Creating .env file..."
    cp .env.template .env
    echo -e "${GREEN}[Setup]${NC} .env created. Edit it to add your API keys."
    echo ""
fi

# Build image if missing
if ! docker images --format "{{.Repository}}" | grep -i "ai-kcmedicalresearch" > /dev/null; then
    echo -e "${BLUE}[Setup]${NC} Building Docker image (first time only)..."
    echo "This may take 5-10 minutes..."
    echo ""
    docker build -f docker/Dockerfile -t ai-kcmedicalresearch .
    if [ $? -ne 0 ]; then
        echo -e "${RED}[ERROR]${NC} Failed to build Docker image."
        read -p "Press Enter to exit..."
        exit 1
    fi
    echo -e "${GREEN}[Setup]${NC} Build complete!"
    echo ""
fi

# Choose run mode
echo "============================================================"
echo " Choose how to run:"
echo ""
echo "  1) CLI Mode  (interactive menu)"
echo "  2) UI Mode   (Streamlit web interface)"
echo ""
read -p "  Enter 1 or 2: " CHOICE

if [ "$CHOICE" == "2" ]; then
    echo ""
    echo "============================================================"
    echo " Starting Streamlit UI..."
    echo " Browser will open at: http://localhost:8501"
    echo " Press Ctrl+C to stop"
    echo "============================================================"
    echo ""
    
    open http://localhost:8501
    
    docker run -it --rm \
        -p 8501:8501 \
        -v "$PROJECT_DIR/input:/app/input" \
        -v "$PROJECT_DIR/output:/app/output" \
        -v "$PROJECT_DIR/data:/app/data" \
        -v "$PROJECT_DIR/reports:/app/reports" \
        --env-file .env \
        --add-host host.docker.internal:host-gateway \
        ai-kcmedicalresearch \
        streamlit run SOURCE_CODE/ui/app.py --server.port=8501 --server.address=0.0.0.0
else
    echo ""
    echo "============================================================"
    echo " Starting CLI Launcher..."
    echo " Use the menu to select pipeline and provider"
    echo "============================================================"
    echo ""
    
    docker run -it --rm \
        -v "$PROJECT_DIR/input:/app/input" \
        -v "$PROJECT_DIR/output:/app/output" \
        -v "$PROJECT_DIR/data:/app/data" \
        -v "$PROJECT_DIR/reports:/app/reports" \
        --env-file .env \
        --add-host host.docker.internal:host-gateway \
        ai-kcmedicalresearch \
        python SOURCE_CODE/main.py
fi

echo ""
echo "============================================================"
echo " AI kcMedicalResearch stopped."
echo "============================================================"
read -p "Press Enter to exit..."