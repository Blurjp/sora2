#!/bin/bash

# Auto-migration script for 768px default
# Run this on GPU server after pulling latest code

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Auto-migrating to 768px Resolution${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env from .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env${NC}"
fi

# Update or add MODEL_RESOLUTION in .env
if grep -q "^MODEL_RESOLUTION=" .env; then
    echo -e "${YELLOW}Updating MODEL_RESOLUTION in .env...${NC}"
    sed -i.bak 's/^MODEL_RESOLUTION=.*/MODEL_RESOLUTION=768px/' .env
    rm -f .env.bak
    echo -e "${GREEN}✓ Updated MODEL_RESOLUTION=768px${NC}"
else
    echo -e "${YELLOW}Adding MODEL_RESOLUTION to .env...${NC}"
    echo "" >> .env
    echo "# Model Resolution (auto-added by migration script)" >> .env
    echo "MODEL_RESOLUTION=768px" >> .env
    echo -e "${GREEN}✓ Added MODEL_RESOLUTION=768px${NC}"
fi

# Verify OpenSora path
OPENSORA_PATH=$(grep "^OPENSORA_PATH=" .env | cut -d'=' -f2)
if [ -z "$OPENSORA_PATH" ]; then
    OPENSORA_PATH="/home/ubuntu/Open-Sora"
fi

# Check if 768px.py exists
if [ ! -f "$OPENSORA_PATH/configs/diffusion/inference/768px.py" ]; then
    echo -e "${RED}Error: 768px.py not found at $OPENSORA_PATH/configs/diffusion/inference/${NC}"
    echo -e "${YELLOW}Available configs:${NC}"
    ls -1 "$OPENSORA_PATH/configs/diffusion/inference/" 2>/dev/null || echo "Directory not found"
    exit 1
fi

echo -e "${GREEN}✓ Found 768px.py config${NC}"
echo ""

# Restart service
echo -e "${YELLOW}Restarting service...${NC}"

if systemctl is-active --quiet opensora-gpu 2>/dev/null; then
    sudo systemctl restart opensora-gpu
    echo -e "${GREEN}✓ Restarted systemd service${NC}"
    echo ""
    echo -e "${YELLOW}Checking service status...${NC}"
    sleep 2
    sudo systemctl status opensora-gpu --no-pager | head -20
elif pgrep -f "python.*gpu_service.main" > /dev/null; then
    echo -e "${YELLOW}Killing manual python process...${NC}"
    pkill -f "python.*gpu_service.main"
    sleep 1
    echo -e "${GREEN}✓ Stopped old process${NC}"
    echo -e "${YELLOW}Please restart manually with: python3 -m gpu_service.main${NC}"
else
    echo -e "${YELLOW}No service running. Start with:${NC}"
    echo "  sudo systemctl start opensora-gpu"
    echo "  OR"
    echo "  python3 -m gpu_service.main"
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Migration Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Summary:${NC}"
echo "  • MODEL_RESOLUTION set to 768px in .env"
echo "  • Service restarted (if systemd)"
echo "  • Now using production-quality 768px config"
echo ""
echo -e "${YELLOW}⚠️  Requirements:${NC}"
echo "  • GPU with 24-32GB VRAM (A100/H100)"
echo "  • Videos will take 2-3x longer but 9x better quality"
echo ""
