#!/bin/bash

#============================================================================
# Lambda Labs GPU Service Runner
# Runs ONLY the GPU service (for remote generation)
#============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Load environment variables from .env so manual runs match systemd settings
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"
if [ -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}Loading environment from ${ENV_FILE}${NC}"
    set -a
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +a
fi

# Get instance IP
INSTANCE_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 || echo "localhost")

# Get Open-Sora path
OPENSORA_PATH="${OPENSORA_PATH:-$HOME/Open-Sora}"

# Check if Open-Sora exists
if [ ! -d "$OPENSORA_PATH" ]; then
    echo -e "${RED}ERROR: Open-Sora not found at $OPENSORA_PATH${NC}"
    echo "Please run ./lambda_setup.sh first or set OPENSORA_PATH environment variable"
    exit 1
fi

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        Open-Sora GPU Service - Lambda Labs               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Instance IP: ${GREEN}$INSTANCE_IP${NC}"
echo -e "${YELLOW}Open-Sora Path: ${GREEN}$OPENSORA_PATH${NC}"
echo ""

# Parse arguments
API_KEY=""
PORT=8001

while [[ $# -gt 0 ]]; do
    case $1 in
        --api-key)
            API_KEY="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Usage: $0 [--api-key YOUR_KEY] [--port 8001]"
            exit 1
            ;;
    esac
done

# Display service info
echo -e "${GREEN}GPU SERVICE MODE${NC}"
echo ""
echo "Service will be accessible at:"
echo -e "  ${GREEN}http://$INSTANCE_IP:$PORT${NC}"
echo ""
if [ -n "$API_KEY" ]; then
    echo -e "${GREEN}✓ API Key protection enabled${NC}"
else
    echo -e "${YELLOW}⚠ WARNING: No API key set - service is unprotected!${NC}"
    echo -e "${YELLOW}  Use --api-key flag to add authentication${NC}"
fi
echo ""
echo -e "${BLUE}Service starting...${NC}"
echo ""
echo "Press Ctrl+C to stop the service"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Start the GPU service
cd "$SCRIPT_DIR"

# Export environment variables
export OPENSORA_PATH="$OPENSORA_PATH"
export HOST="0.0.0.0"
export PORT="$PORT"
if [ -n "$API_KEY" ]; then
    export GPU_API_KEY="$API_KEY"
fi

# Fix Open-Sora config paths automatically
echo -e "${BLUE}Checking Open-Sora configuration...${NC}"
MODEL_RESOLUTION_EFFECTIVE="${MODEL_RESOLUTION:-768px}"
CONFIG_FILE="$OPENSORA_PATH/configs/diffusion/inference/${MODEL_RESOLUTION_EFFECTIVE}.py"

if [ -f "$CONFIG_FILE" ]; then
    # Check if config needs fixing (contains ./ckpts/ paths)
    if grep -q "from_pretrained.*['\"]\\./ckpts/" "$CONFIG_FILE" 2>/dev/null; then
        echo -e "${YELLOW}⚠ Fixing Open-Sora component paths...${NC}"

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

        echo -e "${GREEN}✓ Config paths fixed${NC}"
    else
        echo -e "${GREEN}✓ Config paths already correct${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Config file not found, will use defaults${NC}"
fi
echo ""

# Reduce CUDA memory fragmentation and large-split issues
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True,max_split_size_mb:128}"

# Run the GPU service
python3 -m gpu_service.main
