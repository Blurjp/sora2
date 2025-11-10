#!/bin/bash

################################################################################
# Open-Sora Video Generation Service - Lambda Labs Run Script
################################################################################

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Set environment
export OPENSORA_PATH="${OPENSORA_PATH:-$HOME/Open-Sora}"

# Parse arguments
PUBLIC_ACCESS=false
for arg in "$@"; do
    case $arg in
        --public)
            PUBLIC_ACCESS=true
            shift
            ;;
    esac
done

echo -e "${BLUE}Starting Open-Sora Video Generation Service on Lambda Labs${NC}"
echo ""

# Check if Open-Sora exists
if [ ! -d "$OPENSORA_PATH" ]; then
    echo -e "${YELLOW}⚠ Open-Sora not found at $OPENSORA_PATH${NC}"
    echo "Please run ./lambda_setup.sh first"
    exit 1
fi

# Check GPU
if ! command -v nvidia-smi &> /dev/null; then
    echo -e "${YELLOW}⚠ Warning: nvidia-smi not found. GPU may not be available.${NC}"
else
    echo -e "${GREEN}GPU Status:${NC}"
    nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader
    echo ""
fi

# Get instance IP
if command -v hostname &> /dev/null; then
    INSTANCE_IP=$(hostname -I | awk '{print $1}')
    echo -e "${BLUE}Instance IP: ${YELLOW}$INSTANCE_IP${NC}"
fi

echo -e "${BLUE}Open-Sora Path: ${YELLOW}$OPENSORA_PATH${NC}"
echo ""

# Display access information
if [ "$PUBLIC_ACCESS" = true ]; then
    echo -e "${YELLOW}⚠ PUBLIC ACCESS MODE${NC}"
    echo ""
    echo "Service will be accessible at:"
    echo -e "  ${GREEN}http://$INSTANCE_IP:8000${NC}"
    echo ""
    echo -e "${YELLOW}WARNING: Your service is exposed to the internet!${NC}"
    echo "Consider using SSH tunnel for better security."
    echo ""
else
    echo -e "${GREEN}SECURE ACCESS MODE${NC}"
    echo ""
    echo "To access the service, open a new terminal and run:"
    echo -e "  ${YELLOW}ssh -L 8000:localhost:8000 ubuntu@$INSTANCE_IP${NC}"
    echo ""
    echo "Then open in your browser:"
    echo -e "  ${GREEN}http://localhost:8000${NC}"
    echo ""
fi

echo -e "${BLUE}Service starting...${NC}"
echo ""
echo "Press Ctrl+C to stop the service"
echo "Or run in background with: tmux new -s sora"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Start the service
cd "$(dirname "$0")"

# Pre-flight dependency check
echo "Checking dependencies..."

# Check numpy version
NUMPY_VERSION=$(python3 -c "import numpy; print(numpy.__version__)" 2>/dev/null)
if [[ ! $NUMPY_VERSION == 1.* ]]; then
    echo "Fixing NumPy version..."
    pip install "numpy<2" > /dev/null 2>&1
fi

# Check rich
if ! python3 -c "from rich.progress import MofNCompleteColumn" 2>/dev/null; then
    echo "Fixing rich library..."
    pip install --upgrade rich > /dev/null 2>&1
fi

# Check tensornvme (optional - Open-Sora will handle it at runtime)
if ! python3 -c "from tensornvme.async_file_io import AsyncFileWriter" 2>/dev/null; then
    echo "Note: tensornvme not installed (this is OK - Open-Sora will handle it)"
fi

echo "Dependencies OK"

# Set host binding based on public access mode
if [ "$PUBLIC_ACCESS" = true ]; then
    export HOST="0.0.0.0"
else
    # Secure mode: only bind to localhost for SSH tunnel access
    export HOST="127.0.0.1"
fi

# Use local GPU (not remote) for all-in-one Lambda setup
export USE_REMOTE_GPU=false

# Run as a module to support relative imports
python3 -m backend.main
