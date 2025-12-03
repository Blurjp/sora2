#!/bin/bash

#============================================================================
# Remote Mode - Connect to a remote GPU server
#============================================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load environment from .env file
ENV_FILE="$SCRIPT_DIR/.env"
if [ -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}Loading environment from ${ENV_FILE}${NC}"
    set -a
    source "$ENV_FILE"
    set +a
fi

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        WAN Video Generation - REMOTE MODE                      ║${NC}"
echo -e "${BLUE}║        (Connects to remote GPU server)                         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --gpu-url)
            GPU_SERVICE_URL="$2"
            shift 2
            ;;
        --api-key)
            GPU_API_KEY="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        *)
            # Assume first positional arg is GPU URL
            GPU_SERVICE_URL="$1"
            shift
            ;;
    esac
done

if [ -z "$GPU_SERVICE_URL" ]; then
    echo -e "${YELLOW}ERROR: GPU service URL not specified${NC}"
    echo ""
    echo "Usage:"
    echo "  $0 http://your-gpu-server:8001"
    echo "  $0 --gpu-url http://your-gpu-server:8001 --api-key YOUR_KEY"
    echo ""
    echo "Or set in .env file:"
    echo "  GPU_SERVICE_URL=http://your-gpu-server:8001"
    exit 1
fi

# Force remote mode
export USE_REMOTE_GPU=true
export GPU_SERVICE_URL
export HOST="127.0.0.1"
export PORT="${PORT:-8000}"
if [ -n "$GPU_API_KEY" ]; then
    export GPU_API_KEY
fi

echo -e "${GREEN}Configuration:${NC}"
echo -e "  Mode:        ${YELLOW}REMOTE (connecting to GPU server)${NC}"
echo -e "  GPU Server:  ${YELLOW}$GPU_SERVICE_URL${NC}"
echo -e "  Local Port:  ${YELLOW}$PORT${NC}"
if [ -n "$GPU_API_KEY" ]; then
    echo -e "  API Key:     ${GREEN}✓ Set${NC}"
else
    echo -e "  API Key:     ${YELLOW}Not set${NC}"
fi
echo ""

echo -e "Web interface: ${GREEN}http://127.0.0.1:$PORT${NC}"
echo ""
echo "Press Ctrl+C to stop"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cd "$SCRIPT_DIR"
python3 -m backend.main
