#!/bin/bash
# =============================================================================
#  Mac_Setup_Instruction_to_Users.sh - AI kcMedicalResearch Complete Setup for Mac
#  v1.0.0  |  One-click setup with Docker for macOS
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ─────────────────────────────────────────────────────────────────────────────
#  1.  WELCOME
# ─────────────────────────────────────────────────────────────────────────────
clear
echo ""
echo "============================================================"
echo " AI kcMedicalResearch - Setup & Run (macOS)"
echo "============================================================"
echo ""
echo "This will:"
echo " 1. Check if Docker is installed"
echo " 2. Clone the repository (if needed)"
echo " 3. Create .env file (if missing)"
echo " 4. Build Docker image (first time only)"
echo " 5. Run the app"
echo ""
echo "============================================================"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
#  2.  CHECK DOCKER
# ─────────────────────────────────────────────────────────────────────────────
echo -e "${BLUE}[CHECK]${NC} Checking Docker..."

if ! command -v docker &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Docker not found!"
    echo ""
    echo "Please install Docker Desktop for Mac:"
    echo "https://www.docker.com/products/docker-desktop"
    echo ""
    echo "Or install via Homebrew:"
    echo "  brew install --cask docker"
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
echo -e "${GREEN}[OK]${NC} Docker is running."
echo ""

# ─────────────────────────────────────────────────────────────────────────────
#  3.  SET INSTALL DIRECTORY
# ─────────────────────────────────────────────────────────────────────────────
echo "============================================================"
echo " Where would you like to install?"
echo "============================================================"
echo ""
echo "  [1]  ~/Projects/AI_kcMedicalResearch"
echo "  [2]  ~/Documents/AI_kcMedicalResearch"
echo "  [3]  ~/Desktop/AI_kcMedicalResearch"
echo "  [4]  Custom location"
echo ""
read -p "  Enter 1, 2, 3, or 4: " LOCATION_CHOICE

case $LOCATION_CHOICE in
    1)
        INSTALL_DIR="$HOME/Projects/AI_kcMedicalResearch"
        ;;
    2)
        INSTALL_DIR="$HOME/Documents/AI_kcMedicalResearch"
        ;;
    3)
        INSTALL_DIR="$HOME/Desktop/AI_kcMedicalResearch"
        ;;
    4)
        read -p "  Enter full path: " CUSTOM_DIR
        INSTALL_DIR="$CUSTOM_DIR"
        ;;
    *)
        echo -e "${RED}[ERROR]${NC} Invalid choice. Using ~/Projects..."
        INSTALL_DIR="$HOME/Projects/AI_kcMedicalResearch"
        ;;
esac

echo ""
echo -e "${BLUE}[INFO]${NC} Installing to: ${CYAN}$INSTALL_DIR${NC}"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
#  4.  CHECK IF ALREADY INSTALLED
# ─────────────────────────────────────────────────────────────────────────────
RUN_AFTER_UPDATE=false

if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}[INFO]${NC} AI_kcMedicalResearch already exists at:"
    echo "  $INSTALL_DIR"
    echo ""
    echo "What would you like to do?"
    echo ""
    echo "  [1]  Update (git pull) and run"
    echo "  [2]  Remove and reinstall fresh"
    echo "  [3]  Exit and do nothing"
    echo ""
    read -p "  Enter 1, 2, or 3: " EXISTING_ACTION

    if [ "$EXISTING_ACTION" == "3" ]; then
        echo ""
        echo "Exiting..."
        exit 0
    fi

    if [ "$EXISTING_ACTION" == "2" ]; then
        echo ""
        echo -e "${YELLOW}[REMOVE]${NC} Removing existing installation..."
        rm -rf "$INSTALL_DIR"
        echo -e "${GREEN}[OK]${NC} Removed."
        echo ""
        RUN_AFTER_UPDATE=false
    else
        echo ""
        echo -e "${BLUE}[UPDATE]${NC} Updating existing installation..."
        cd "$INSTALL_DIR"
        git pull
        echo -e "${GREEN}[OK]${NC} Update complete."
        echo ""
        RUN_AFTER_UPDATE=true
    fi
fi

# ─────────────────────────────────────────────────────────────────────────────
#  5.  CLONE IF NEEDED
# ─────────────────────────────────────────────────────────────────────────────
if [ ! -d "$INSTALL_DIR" ]; then
    echo -e "${BLUE}[CLONE]${NC} Creating directory and cloning repository..."
    echo ""

    mkdir -p "$(dirname "$INSTALL_DIR")"
    cd "$(dirname "$INSTALL_DIR")"

    git clone https://github.com/KW75/AI_kcMedicalResearch.git "$(basename "$INSTALL_DIR")"
    if [ $? -ne 0 ]; then
        echo ""
        echo -e "${RED}[ERROR]${NC} Failed to clone repository."
        echo "Please check your internet connection."
        echo ""
        read -p "Press Enter to exit..."
        exit 1
    fi

    echo ""
    echo -e "${GREEN}[OK]${NC} Repository cloned successfully."
    echo ""
    RUN_AFTER_UPDATE=true
fi

# ─────────────────────────────────────────────────────────────────────────────
#  6.  ENTER DIRECTORY
# ─────────────────────────────────────────────────────────────────────────────
cd "$INSTALL_DIR"

# ─────────────────────────────────────────────────────────────────────────────
#  7.  CREATE .env FILE
# ─────────────────────────────────────────────────────────────────────────────
if [ ! -f ".env" ]; then
    echo -e "${BLUE}[CONFIG]${NC} Creating .env file..."

    cat > .env << 'EOF'
# AI kcMedicalResearch - API Keys
# ================================

# Local Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Cloud Providers - Add your API keys below
# Get free key from: https://console.groq.com
GROQ_API_KEY=

# Get key from: https://dashscope.aliyuncs.com
DASHSCOPE_API_KEY=
DASHSCOPE_BASE_URL=https://ws-uv5pi4kkqbrg1vpe.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1
DASHSCOPE_ANTHROPIC_URL=https://ws-uv5pi4kkqbrg1vpe.ap-southeast-1.maas.aliyuncs.com/apps/anthropic

# Optional: OpenAI, Anthropic, DeepSeek
# OPENAI_API_KEY=
# ANTHROPIC_API_KEY=
# DEEPSEEK_API_KEY=
EOF

    echo ""
    echo -e "${GREEN}[OK]${NC} .env file created."
    echo ""
    echo -e "${YELLOW}IMPORTANT:${NC} Edit .env to add your API keys before running!"
    echo ""

    # Ask if they want to edit .env now
    read -p "Would you like to edit .env now? (y/n): " EDIT_ENV

    if [[ "$EDIT_ENV" =~ ^[Yy]$ ]]; then
        echo ""
        echo -e "${BLUE}[EDIT]${NC} Opening .env in default editor..."
        echo "Add your API keys, save, and close the editor."
        echo ""

        # Use default editor (nano, vim, or open with TextEdit)
        if command -v nano &> /dev/null; then
            nano .env
        elif command -v vim &> /dev/null; then
            vim .env
        else
            open -e .env  # TextEdit on Mac
        fi

        echo ""
        echo -e "${GREEN}[OK]${NC} .env saved."
    else
        echo ""
        echo -e "${YELLOW}[INFO]${NC} Remember to edit .env before running!"
        echo "  $INSTALL_DIR/.env"
        echo ""
    fi
else
    echo ""
    echo -e "${GREEN}[CONFIG]${NC} .env already exists. Keeping existing."
    echo ""
fi

# ─────────────────────────────────────────────────────────────────────────────
#  8.  CREATE INPUT/OUTPUT DIRECTORIES
# ─────────────────────────────────────────────────────────────────────────────
echo -e "${BLUE}[SETUP]${NC} Creating input/output directories..."

mkdir -p input/{coding,writing,appraisal,search,rct_search,sr}
mkdir -p output/{coding,writing,appraisal,search,rct_search,sr}
mkdir -p reports data

echo -e "${GREEN}[OK]${NC} Directories created."
echo ""

# ─────────────────────────────────────────────────────────────────────────────
#  9.  BUILD DOCKER IMAGE (if not exists)
# ─────────────────────────────────────────────────────────────────────────────
echo -e "${BLUE}[DOCKER]${NC} Checking for existing image..."

if ! docker images --format "{{.Repository}}" | grep -i "ai-kcmedicalresearch" > /dev/null; then
    echo ""
    echo -e "${BLUE}[DOCKER]${NC} Building Docker image (first time only)..."
    echo "This may take 5-10 minutes..."
    echo ""

    docker build -t ai-kcmedicalresearch .
    if [ $? -ne 0 ]; then
        echo ""
        echo -e "${RED}[ERROR]${NC} Failed to build Docker image."
        read -p "Press Enter to exit..."
        exit 1
    fi

    echo ""
    echo -e "${GREEN}[OK]${NC} Docker image built successfully."
    echo ""
else
    echo ""
    echo -e "${GREEN}[DOCKER]${NC} Image already exists. Skipping build."
    echo ""
fi

# ─────────────────────────────────────────────────────────────────────────────
#  10. RUN THE APP
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "============================================================"
echo " SETUP COMPLETE!"
echo "============================================================"
echo ""
echo "Installation location: $INSTALL_DIR"
echo ""
echo "Choose how to run:"
echo ""
echo "  [1]  CLI Mode  (interactive menu)"
echo "  [2]  UI Mode   (Streamlit web interface)"
echo ""
read -p "  Enter 1 or 2: " RUN_CHOICE

echo ""
echo "============================================================"
echo " Starting AI kcMedicalResearch..."
echo "============================================================"
echo ""

if [ "$RUN_CHOICE" == "2" ]; then
    echo -e "${BLUE}UI Mode starting...${NC}"
    echo "Browser will open at: http://localhost:8501"
    echo "Press Ctrl+C to stop"
    echo ""

    open http://localhost:8501

    docker run -it --rm \
        -p 8501:8501 \
        -v "$INSTALL_DIR/input:/app/input" \
        -v "$INSTALL_DIR/output:/app/output" \
        -v "$INSTALL_DIR/data:/app/data" \
        -v "$INSTALL_DIR/reports:/app/reports" \
        --env-file .env \
        --add-host host.docker.internal:host-gateway \
        ai-kcmedicalresearch \
        streamlit run src/ui/app.py --server.port=8501 --server.address=0.0.0.0
else
    echo -e "${BLUE}CLI Mode starting...${NC}"
    echo "Use the menu to select pipeline and provider"
    echo ""

    docker run -it --rm \
        -v "$INSTALL_DIR/input:/app/input" \
        -v "$INSTALL_DIR/output:/app/output" \
        -v "$INSTALL_DIR/data:/app/data" \
        -v "$INSTALL_DIR/reports:/app/reports" \
        --env-file .env \
        --add-host host.docker.internal:host-gateway \
        ai-kcmedicalresearch \
        python launcher.py
fi

echo ""
echo "============================================================"
echo " AI kcMedicalResearch stopped."
echo "============================================================"
read -p "Press Enter to exit..."