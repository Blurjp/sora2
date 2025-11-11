#!/bin/bash

################################################################################
# Install TensorNVMe (Optional GPU Acceleration)
# Only needed if you see: ModuleNotFoundError: No module named 'tensornvme'
################################################################################

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Installing TensorNVMe${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"
echo ""

echo -e "${YELLOW}TensorNVMe provides GPU-to-SSD offloading for large models${NC}"
echo -e "${YELLOW}It's optional - only needed if you have limited GPU VRAM${NC}"
echo ""

# Clone repository
echo -e "${YELLOW}Cloning TensorNVMe repository...${NC}"
cd /tmp
rm -rf TensorNVMe 2>/dev/null || true
git clone https://github.com/hpcaitech/TensorNVMe.git
cd TensorNVMe

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -r requirements.txt

# Install TensorNVMe
echo -e "${YELLOW}Installing TensorNVMe...${NC}"
pip install -v .

# Cleanup
cd /tmp
rm -rf TensorNVMe

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ TensorNVMe Installed Successfully!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo ""
echo "You can now restart your service:"
echo -e "  ${YELLOW}sudo systemctl restart opensora-gpu${NC}"
echo ""
