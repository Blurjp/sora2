#!/bin/bash

#============================================================================
# Local Backend Runner
# Runs backend + frontend locally, connects to remote GPU
#============================================================================

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        Open-Sora Local Backend (Remote GPU Mode)          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Get GPU service URL from argument or environment
GPU_URL="${GPU_SERVICE_URL:-}"
API_KEY="${GPU_API_KEY:-}"
PORT=8000

while [[ $# -gt 0 ]]; do
    case $1 in
        --gpu-url)
            GPU_URL="$2"
            shift 2
            ;;
        --api-key)
            API_KEY="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        *)
            echo -e "${YELLOW}Unknown option: $1${NC}"
            echo "Usage: $0 --gpu-url http://gpu-instance:8001 [--api-key KEY] [--port 8000]"
            exit 1
            ;;
    esac
done

if [ -z "$GPU_URL" ]; then
    echo -e "${YELLOW}ERROR: GPU service URL not specified${NC}"
    echo ""
    echo "Usage:"
    echo "  $0 --gpu-url http://your-lambda-ip:8001"
    echo ""
    echo "Or set environment variable:"
    echo "  export GPU_SERVICE_URL=http://your-lambda-ip:8001"
    exit 1
fi

echo -e "${GREEN}Configuration:${NC}"
echo -e "  GPU Service: ${YELLOW}$GPU_URL${NC}"
echo -e "  Local Port:  ${YELLOW}$PORT${NC}"
if [ -n "$API_KEY" ]; then
    echo -e "  API Key:     ${GREEN}✓ Set${NC}"
else
    echo -e "  API Key:     ${YELLOW}Not set${NC}"
fi
echo ""
echo -e "${BLUE}Starting local backend...${NC}"
echo ""
echo "Open your browser at:"
echo -e "  ${GREEN}http://localhost:$PORT${NC}"
echo ""
echo "Press Ctrl+C to stop"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Start the local backend
cd "$(dirname "$0")"

# Export environment variables
export USE_REMOTE_GPU=true
export GPU_SERVICE_URL="$GPU_URL"
export HOST="127.0.0.1"
export PORT="$PORT"
if [ -n "$API_KEY" ]; then
    export GPU_API_KEY="$API_KEY"
fi

# Run the backend
python3 backend/main.py
