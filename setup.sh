#!/bin/bash

# Open-Sora Video Generation Service Setup Script

set -e

echo "=================================="
echo "Open-Sora Video Generator Setup"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.10"

if [[ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]]; then
    echo -e "${RED}Error: Python 3.10 or higher is required. Found: $PYTHON_VERSION${NC}"
    exit 1
fi

echo -e "${GREEN}Python version $PYTHON_VERSION is compatible${NC}"
echo ""

# Check if Open-Sora is installed
echo -e "${YELLOW}Checking for Open-Sora installation...${NC}"

if [ -z "$OPENSORA_PATH" ]; then
    echo -e "${YELLOW}OPENSORA_PATH not set. Please enter the path to your Open-Sora installation:${NC}"
    read -p "Open-Sora path: " OPENSORA_PATH
    export OPENSORA_PATH
fi

if [ ! -d "$OPENSORA_PATH" ]; then
    echo -e "${RED}Open-Sora directory not found at: $OPENSORA_PATH${NC}"
    echo ""
    echo "Would you like to clone and install Open-Sora? (y/n)"
    read -p "Choice: " INSTALL_OPENSORA

    if [ "$INSTALL_OPENSORA" = "y" ]; then
        echo -e "${YELLOW}Cloning Open-Sora...${NC}"
        OPENSORA_PATH="$HOME/Open-Sora"
        git clone https://github.com/hpcaitech/Open-Sora.git "$OPENSORA_PATH"

        echo -e "${YELLOW}Installing Open-Sora...${NC}"
        cd "$OPENSORA_PATH"
        pip install -v .
        pip install xformers==0.0.27.post2 --index-url https://download.pytorch.org/whl/cu121
        pip install flash-attn --no-build-isolation

        cd -
        echo -e "${GREEN}Open-Sora installed successfully${NC}"
    else
        echo -e "${RED}Open-Sora is required. Please install it first.${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}Open-Sora found at: $OPENSORA_PATH${NC}"
echo ""

# Update config.py with Open-Sora path
echo -e "${YELLOW}Updating configuration...${NC}"
sed -i "s|OPENSORA_PATH = os.environ.get(\"OPENSORA_PATH\", \".*\")|OPENSORA_PATH = os.environ.get(\"OPENSORA_PATH\", \"$OPENSORA_PATH\")|" backend/config.py
echo -e "${GREEN}Configuration updated${NC}"
echo ""

# Install service dependencies
echo -e "${YELLOW}Installing service dependencies...${NC}"
pip install -r requirements.txt
echo -e "${GREEN}Dependencies installed${NC}"
echo ""

# Create necessary directories
echo -e "${YELLOW}Creating output directories...${NC}"
mkdir -p outputs temp
echo -e "${GREEN}Directories created${NC}"
echo ""

# Check GPU
echo -e "${YELLOW}Checking GPU availability...${NC}"
if command -v nvidia-smi &> /dev/null; then
    GPU_INFO=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | head -n1)
    echo -e "${GREEN}GPU detected: $GPU_INFO${NC}"
else
    echo -e "${YELLOW}Warning: nvidia-smi not found. GPU may not be available.${NC}"
    echo -e "${YELLOW}Open-Sora requires a CUDA-compatible GPU for generation.${NC}"
fi
echo ""

# Setup complete
echo -e "${GREEN}=================================="
echo "Setup Complete!"
echo "==================================${NC}"
echo ""
echo "To start the service:"
echo "  python backend/main.py"
echo ""
echo "Or use the run script:"
echo "  ./run.sh"
echo ""
echo "The service will be available at:"
echo "  http://localhost:8000"
echo ""
