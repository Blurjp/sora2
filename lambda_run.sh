#!/bin/bash

################################################################################
# Open-Sora Video Generation Service - Lambda Labs Run Script
################################################################################

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Load environment variables from .env so manual runs mirror systemd defaults
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"
if [ -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}Loading environment from ${ENV_FILE}${NC}"
    set -a
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +a
fi

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
cd "$SCRIPT_DIR"

# Pre-flight dependency check
echo "Checking dependencies..."

# Check service dependencies (fastapi, aiohttp, etc.)
if ! python3 -c "import aiohttp, fastapi, uvicorn, aiofiles" 2>/dev/null; then
    echo "Installing service dependencies..."
    pip install -r requirements.txt > /dev/null 2>&1
    if ! python3 -c "import aiohttp, fastapi, uvicorn, aiofiles" 2>/dev/null; then
        echo "ERROR: Failed to install service dependencies"
        echo "Please run: pip install -r requirements.txt"
        exit 1
    fi
fi

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

# Check if Open-Sora needs tensornvme patch
echo "Checking Open-Sora tensornvme compatibility..."
if python3 -c "import sys; import site; import os; sp = site.getsitepackages() + [site.getusersitepackages()]; ckpt_file = next((os.path.join(p, 'opensora', 'utils', 'ckpt.py') for p in sp if os.path.exists(os.path.join(p, 'opensora', 'utils', 'ckpt.py'))), None); sys.exit(0 if not ckpt_file or 'TENSORNVME_AVAILABLE' in open(ckpt_file).read() else 1)" 2>/dev/null; then
    echo "✓ Open-Sora already patched for optional tensornvme"
else
    echo "Patching Open-Sora to make tensornvme optional..."
    python3 "$(dirname "$0")/patch_opensora_tensornvme.py"
    if [ $? -eq 0 ]; then
        echo "✓ Open-Sora patched successfully"
    else
        echo "⚠ Patch failed - service may not start"
    fi
fi

# Check tensornvme (optional - not required for A100/H100)
if ! python3 -c "from tensornvme.async_file_io import AsyncFileWriter" 2>/dev/null; then
    echo "Note: tensornvme not installed (this is OK for A100/H100 GPUs)"
fi

# Fix Open-Sora config paths automatically
echo "Checking Open-Sora configuration..."
MODEL_RESOLUTION_EFFECTIVE="${MODEL_RESOLUTION:-768px}"
CONFIG_FILE="$OPENSORA_PATH/configs/diffusion/inference/${MODEL_RESOLUTION_EFFECTIVE}.py"

if [ -f "$CONFIG_FILE" ]; then
    # Check if config needs fixing (contains ./ckpts/ paths)
    if grep -q "from_pretrained.*['\"]\\./ckpts/" "$CONFIG_FILE" 2>/dev/null; then
        echo "⚠ Fixing Open-Sora component paths..."

        # Create backup
        cp "$CONFIG_FILE" "$CONFIG_FILE.backup.$(date +%s)"

        # Fix all component paths (both old ./ckpts/ format and old subfolder format)
        sed -i \
            -e "s|from_pretrained.*=.*['\"]\\./ckpts/hunyuan_vae\\.safetensors['\"]|from_pretrained=\"hpcai-tech/Open-Sora-v2/hunyuan_vae.safetensors\"|g" \
            -e "s|from_pretrained.*=.*['\"]\\./ckpts/google/t5-v1_1-xxl['\"]|from_pretrained=\"google/t5-v1_1-xxl\"|g" \
            -e "s|from_pretrained.*=.*['\"]\\./ckpts/openai/clip-vit-large-patch14['\"]|from_pretrained=\"openai/clip-vit-large-patch14\"|g" \
            -e "s|from_pretrained.*=.*['\"]\\./ckpts/Open_Sora_v2\\.safetensors['\"]|from_pretrained=\"hpcai-tech/OpenSora-STDiT-v3/model.safetensors\"|g" \
            -e "s|from_pretrained[[:space:]]*=[[:space:]]*['\"]hpcai-tech/Open-Sora-v2[^'\"]*['\"][[:space:]]*,[[:space:]]*subfolder[[:space:]]*=[[:space:]]*['\"]hunyuan_vae['\"]|from_pretrained=\"hpcai-tech/Open-Sora-v2/hunyuan_vae.safetensors\"|g" \
            -e "s|from_pretrained[[:space:]]*=[[:space:]]*['\"]hpcai-tech/Open-Sora-v2[^'\"]*['\"][[:space:]]*,[[:space:]]*subfolder[[:space:]]*=[[:space:]]*['\"]model['\"]|from_pretrained=\"hpcai-tech/OpenSora-STDiT-v3/model.safetensors\"|g" \
            "$CONFIG_FILE"

        echo "✓ Config paths fixed"
    else
        echo "✓ Config paths already correct"
    fi

    # Also run Python patcher as fallback
    python3 "$(dirname "$0")/hf_patch_opensora_config.py"
else
    echo "⚠ Config file not found, will use defaults"
    # Still try Python patcher
    python3 "$(dirname "$0")/hf_patch_opensora_config.py" || true
fi

echo "Dependencies OK"

################################################################################
# Kill any existing Python services
################################################################################
echo ""
echo -e "${YELLOW}Cleaning up any existing Python services...${NC}"

# Function to safely kill processes
kill_processes() {
    local pattern="$1"
    local description="$2"
    local pids=$(ps aux | grep -E "$pattern" | grep -v grep | awk '{print $2}')

    if [ ! -z "$pids" ]; then
        echo "  Stopping $description..."
        for pid in $pids; do
            kill -15 $pid 2>/dev/null && echo "    Killed PID $pid" || true
        done
        sleep 1

        # Force kill if still running
        for pid in $pids; do
            if kill -0 $pid 2>/dev/null; then
                kill -9 $pid 2>/dev/null && echo "    Force killed PID $pid" || true
            fi
        done
    fi
}

# Kill backend services
kill_processes "python.*backend\.main" "backend services"
kill_processes "python.*backend/main\.py" "backend services"

# Kill GPU services
kill_processes "python.*gpu_service\.main" "GPU services"
kill_processes "python.*gpu_service/main\.py" "GPU services"

# Kill uvicorn processes (FastAPI)
kill_processes "uvicorn.*backend" "uvicorn workers"
kill_processes "uvicorn.*gpu_service" "uvicorn workers"

# Kill any Python processes using our ports
for port in 8000 8001; do
    port_pid=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$port_pid" ]; then
        echo "  Freeing port $port (PID: $port_pid)..."
        kill -15 $port_pid 2>/dev/null && sleep 1
        if kill -0 $port_pid 2>/dev/null; then
            kill -9 $port_pid 2>/dev/null
        fi
        echo "    Port $port freed"
    fi
done

# Kill any stray torchrun processes (Open-Sora inference)
kill_processes "torchrun.*inference\.py" "Open-Sora inference processes"

echo -e "${GREEN}✓ Cleanup complete${NC}"
echo ""

# Set host binding based on public access mode
if [ "$PUBLIC_ACCESS" = true ]; then
    export HOST="0.0.0.0"
else
    # Secure mode: only bind to localhost for SSH tunnel access
    export HOST="127.0.0.1"
fi

# Use local GPU (not remote) for all-in-one Lambda setup
export USE_REMOTE_GPU=false

# Ensure project directory is in PYTHONPATH
PROJECT_DIR="$(pwd)"
export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"

# Run as a module to support relative imports
python3 -m backend.main
