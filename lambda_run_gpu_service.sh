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
cd "$(dirname "$0")"

# Export environment variables
export OPENSORA_PATH="$OPENSORA_PATH"
export HOST="0.0.0.0"
export PORT="$PORT"
if [ -n "$API_KEY" ]; then
    export GPU_API_KEY="$API_KEY"
fi

# Reduce CUDA memory fragmentation and large-split issues
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True,max_split_size_mb:128}"

# Run the GPU service
python3 -m gpu_service.main
