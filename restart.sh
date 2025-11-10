#!/bin/bash

#============================================================================
# Restart Script - Kill all Python processes and start fresh
# Works for both local backend and GPU service
#============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              Restart Open-Sora Service                     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Kill all Python processes
echo -e "${YELLOW}[1/3] Stopping all Python processes...${NC}"

# Find all python processes
PYTHON_PIDS=$(pgrep -f "python.*backend/main.py|python.*gpu_service.main|uvicorn" || true)

if [ -z "$PYTHON_PIDS" ]; then
    echo -e "${GREEN}✓ No Python processes running${NC}"
else
    echo "Found Python processes: $PYTHON_PIDS"
    kill $PYTHON_PIDS 2>/dev/null || true
    sleep 2

    # Force kill if still running
    REMAINING=$(pgrep -f "python.*backend/main.py|python.*gpu_service.main|uvicorn" || true)
    if [ ! -z "$REMAINING" ]; then
        echo -e "${YELLOW}Force killing remaining processes...${NC}"
        kill -9 $REMAINING 2>/dev/null || true
    fi

    echo -e "${GREEN}✓ All Python processes stopped${NC}"
fi

echo ""

# Step 2: Detect mode and configuration
echo -e "${YELLOW}[2/3] Detecting configuration...${NC}"

MODE=""
GPU_URL=""
API_KEY=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --local)
            MODE="local"
            shift
            ;;
        --gpu-service)
            MODE="gpu_service"
            shift
            ;;
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
            echo -e "${RED}Unknown option: $1${NC}"
            echo ""
            echo "Usage:"
            echo "  Local backend with remote GPU:"
            echo "    $0 --local --gpu-url http://lambda-ip:8001 [--api-key KEY]"
            echo ""
            echo "  GPU service only (on Lambda):"
            echo "    $0 --gpu-service [--api-key KEY] [--port 8001]"
            echo ""
            exit 1
            ;;
    esac
done

# Auto-detect mode if not specified
if [ -z "$MODE" ]; then
    # Check if we have GPU_SERVICE_URL env var or --gpu-url was provided
    if [ ! -z "$GPU_URL" ] || [ ! -z "$GPU_SERVICE_URL" ]; then
        MODE="local"
    # Check if OPENSORA_PATH exists (likely GPU service)
    elif [ -d "${OPENSORA_PATH:-$HOME/Open-Sora}" ]; then
        MODE="gpu_service"
    else
        MODE="local"
    fi
fi

echo -e "Mode: ${GREEN}$MODE${NC}"
echo ""

# Step 3: Start service
echo -e "${YELLOW}[3/3] Starting service...${NC}"
echo ""

cd "$(dirname "$0")"

if [ "$MODE" = "local" ]; then
    # Local backend mode
    echo -e "${GREEN}Starting Local Backend (Remote GPU Mode)${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if [ -z "$GPU_URL" ]; then
        GPU_URL="${GPU_SERVICE_URL:-http://localhost:8001}"
    fi

    export USE_REMOTE_GPU=true
    export GPU_SERVICE_URL="$GPU_URL"
    export HOST="127.0.0.1"
    export PORT="${PORT:-8000}"

    if [ ! -z "$API_KEY" ]; then
        export GPU_API_KEY="$API_KEY"
    fi

    echo -e "Configuration:"
    echo -e "  GPU Service: ${YELLOW}$GPU_SERVICE_URL${NC}"
    echo -e "  Local Port:  ${YELLOW}$PORT${NC}"
    if [ ! -z "$GPU_API_KEY" ]; then
        echo -e "  API Key:     ${GREEN}✓ Set${NC}"
    fi
    echo ""
    echo -e "Open browser at: ${GREEN}http://localhost:$PORT${NC}"
    echo ""

    python3 backend/main.py

elif [ "$MODE" = "gpu_service" ]; then
    # GPU service mode
    echo -e "${GREEN}Starting GPU Service${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    OPENSORA_PATH="${OPENSORA_PATH:-$HOME/Open-Sora}"

    if [ ! -d "$OPENSORA_PATH" ]; then
        echo -e "${RED}ERROR: Open-Sora not found at $OPENSORA_PATH${NC}"
        exit 1
    fi

    export OPENSORA_PATH="$OPENSORA_PATH"
    export HOST="0.0.0.0"
    export PORT="${PORT:-8001}"

    if [ ! -z "$API_KEY" ]; then
        export GPU_API_KEY="$API_KEY"
    fi

    INSTANCE_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "localhost")

    echo -e "Configuration:"
    echo -e "  Instance IP:   ${YELLOW}$INSTANCE_IP${NC}"
    echo -e "  Port:          ${YELLOW}$PORT${NC}"
    echo -e "  Open-Sora:     ${YELLOW}$OPENSORA_PATH${NC}"
    if [ ! -z "$GPU_API_KEY" ]; then
        echo -e "  API Key:       ${GREEN}✓ Set${NC}"
    else
        echo -e "  API Key:       ${YELLOW}⚠ Not set (insecure)${NC}"
    fi
    echo ""
    echo -e "Service URL: ${GREEN}http://$INSTANCE_IP:$PORT${NC}"
    echo ""

    python3 -m gpu_service.main
fi
