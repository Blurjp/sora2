#!/bin/bash

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Upgrading to 768px Resolution (9x Better Quality)${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"
echo ""

# Check if 768px config exists
OPENSORA_PATH="${OPENSORA_PATH:-/home/ubuntu/Open-Sora}"
CONFIG_768="${OPENSORA_PATH}/configs/diffusion/inference/768px.py"

if [ ! -f "$CONFIG_768" ]; then
    echo -e "${RED}Error: 768px.py config not found at $CONFIG_768${NC}"
    echo ""
    echo "Available configs:"
    ls -1 "${OPENSORA_PATH}/configs/diffusion/inference/"
    exit 1
fi

echo -e "${GREEN}✓ Found 768px.py config${NC}"
echo ""

# Update gpu_service/config.py
cd ~/sora2

echo -e "${YELLOW}Updating gpu_service/config.py...${NC}"
sed -i 's|MODEL_CONFIG_PATH = "configs/diffusion/inference/256px.py"|MODEL_CONFIG_PATH = "configs/diffusion/inference/768px.py"|g' gpu_service/config.py

echo -e "${GREEN}✓ Updated to 768px resolution${NC}"
echo ""

echo -e "${YELLOW}Restarting service...${NC}"
if systemctl is-active --quiet opensora-gpu 2>/dev/null; then
    sudo systemctl restart opensora-gpu
    echo -e "${GREEN}✓ Service restarted${NC}"
else
    echo -e "${YELLOW}⚠ Service not running. Start with: sudo systemctl start opensora-gpu${NC}"
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
echo ""
echo -e "${YELLOW}💡 Tip:${NC}"
echo "  Combine with maximum quality settings for best results:"
echo "  ./enable_max_quality.sh"
echo ""
