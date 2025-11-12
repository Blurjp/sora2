#!/bin/bash

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Upgrading to 768px Resolution${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}⚠️  Note: Fresh installations already default to 768px!${NC}"
echo -e "${YELLOW}This script is only needed for existing installations.${NC}"
echo ""

# Get script directory and change to repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Source .env file if it exists to get OPENSORA_PATH
if [ -f .env ]; then
    echo -e "${YELLOW}Loading configuration from .env...${NC}"
    # Export variables from .env (only OPENSORA_PATH for now)
    export $(grep -v '^#' .env | grep 'OPENSORA_PATH=' | xargs)
    echo -e "${GREEN}✓ Loaded OPENSORA_PATH from .env${NC}"
fi

# Check if 768px config exists
OPENSORA_PATH="${OPENSORA_PATH:-/home/ubuntu/Open-Sora}"
CONFIG_768="${OPENSORA_PATH}/configs/diffusion/inference/768px.py"

echo ""
echo -e "${YELLOW}Checking for 768px.py config at: $OPENSORA_PATH${NC}"

if [ ! -f "$CONFIG_768" ]; then
    echo -e "${RED}Error: 768px.py config not found at $CONFIG_768${NC}"
    echo ""
    echo "Available configs:"
    ls -1 "${OPENSORA_PATH}/configs/diffusion/inference/" 2>/dev/null || echo "Directory not found!"
    echo ""
    echo -e "${YELLOW}💡 Tip: Set OPENSORA_PATH in your .env file:${NC}"
    echo "   echo 'OPENSORA_PATH=/path/to/Open-Sora' >> .env"
    exit 1
fi

echo -e "${GREEN}✓ Found 768px.py config${NC}"
echo ""

# Update .env file to set MODEL_RESOLUTION
echo -e "${YELLOW}Updating .env with MODEL_RESOLUTION=768px...${NC}"

if [ -f .env ]; then
    # Remove old MODEL_RESOLUTION if exists
    sed -i.bak '/^MODEL_RESOLUTION=/d' .env
    rm -f .env.bak
fi

# Add MODEL_RESOLUTION to .env
cat >> .env << 'EOF'

# Model Resolution (set by upgrade_to_768px.sh)
MODEL_RESOLUTION=768px
EOF

echo -e "${GREEN}✓ Updated .env with MODEL_RESOLUTION=768px${NC}"
echo ""

# Check if service is running and how
echo -e "${YELLOW}Checking service status...${NC}"

if systemctl is-active --quiet opensora-gpu 2>/dev/null; then
    # Systemd service is running
    echo -e "${YELLOW}Restarting systemd service...${NC}"
    sudo systemctl restart opensora-gpu
    echo -e "${GREEN}✓ Systemd service restarted${NC}"
elif pgrep -f "python.*gpu_service.main" > /dev/null; then
    # Manual python process is running
    echo -e "${YELLOW}⚠ Detected manual python process running${NC}"
    echo -e "${RED}Please manually restart your process:${NC}"
    echo "  1. Stop current process (Ctrl+C or kill)"
    echo "  2. Restart with: python3 -m gpu_service.main"
    echo ""
    echo -e "${YELLOW}Or kill it automatically:${NC}"
    read -p "Kill running python process? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pkill -f "python.*gpu_service.main"
        echo -e "${GREEN}✓ Killed manual process. Restart with: python3 -m gpu_service.main${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Service not running${NC}"
    echo "Start with one of:"
    echo "  • sudo systemctl start opensora-gpu"
    echo "  • python3 -m gpu_service.main"
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Upgraded to 768px Resolution!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}⚠️  Important:${NC}"
echo "  • Quality: 9x better (768x768 vs 256x256)"
echo "  • VRAM: Requires ~24-32GB (vs ~16GB for 256px)"
echo "  • Speed: ~2-3x slower generation"
echo "  • Works for both GPU service AND local backend"
echo ""
echo -e "${YELLOW}Changes made:${NC}"
echo "  • Set MODEL_RESOLUTION=768px in .env"
echo "  • Both backend and gpu_service will use 768px config"
echo "  • Service restart required (handled above if systemd)"
echo ""
echo -e "${YELLOW}💡 Tip:${NC}"
echo "  Combine with maximum quality settings for best results:"
echo "  ./enable_max_quality.sh"
echo ""
