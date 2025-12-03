#!/bin/bash

#============================================================================
# Local Mode - Run everything on this machine (requires local GPU)
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
echo -e "${BLUE}║        WAN Video Generation - LOCAL MODE                       ║${NC}"
echo -e "${BLUE}║        (Runs on your local GPU)                                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Force local mode
export USE_REMOTE_GPU=false
export HOST="127.0.0.1"
export PORT="${PORT:-8000}"

echo -e "${GREEN}Configuration:${NC}"
echo -e "  Mode:        ${YELLOW}LOCAL (using local GPU)${NC}"
echo -e "  Model:       ${YELLOW}${WAN_MODEL_ID:-Wan-AI/Wan2.1-T2V-1.3B-Diffusers}${NC}"
echo -e "  Resolution:  ${YELLOW}${WAN_WIDTH:-832}x${WAN_HEIGHT:-480}${NC}"
echo -e "  Port:        ${YELLOW}$PORT${NC}"
echo ""

# Cleanup any existing services on our ports
echo "Cleaning up any existing services..."
for port in 8000 8001; do
    port_pid=$(lsof -ti:$port 2>/dev/null || true)
    if [ ! -z "$port_pid" ]; then
        echo "  Freeing port $port (PID: $port_pid)..."
        kill -15 $port_pid 2>/dev/null || true
        sleep 1
        kill -9 $port_pid 2>/dev/null || true
    fi
done
echo "✓ Cleanup complete"
echo ""

echo -e "Web interface: ${GREEN}http://127.0.0.1:$PORT${NC}"
echo ""
echo "Press Ctrl+C to stop"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cd "$SCRIPT_DIR"
python3 -m backend.main
