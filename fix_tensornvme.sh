#!/bin/bash

################################################################################
# Fix TensorNVMe Import Error
# Run this if you see: ModuleNotFoundError: No module named 'tensornvme'
################################################################################

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Fixing TensorNVMe Import Error${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"
echo ""

echo -e "${YELLOW}Issue:${NC} Open-Sora requires tensornvme module which is optional"
echo -e "${YELLOW}Solution:${NC} Patch Open-Sora to make tensornvme import optional"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if patch script exists
if [ ! -f "$SCRIPT_DIR/patch_opensora_tensornvme.py" ]; then
    echo -e "${RED}❌ Error: patch_opensora_tensornvme.py not found${NC}"
    echo "Please ensure you're in the sora2 directory"
    exit 1
fi

# Run the patch
echo -e "${YELLOW}Running patch script...${NC}"
python3 "$SCRIPT_DIR/patch_opensora_tensornvme.py"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✅ Fix Applied Successfully!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
    echo ""
    echo "You can now restart your service:"
    echo -e "  ${YELLOW}sudo systemctl restart opensora-gpu${NC}"
    echo ""
    echo "Or if running directly:"
    echo -e "  ${YELLOW}./lambda_run.sh${NC}"
    echo ""
else
    echo ""
    echo -e "${RED}═══════════════════════════════════════════════════${NC}"
    echo -e "${RED}❌ Fix Failed${NC}"
    echo -e "${RED}═══════════════════════════════════════════════════${NC}"
    echo ""
    echo "Please check the error messages above."
    echo ""
    echo "Manual fix:"
    echo "1. Find the file: opensora/utils/ckpt.py"
    echo "2. Replace the line:"
    echo "   from tensornvme.async_file_io import AsyncFileWriter"
    echo ""
    echo "3. With:"
    echo "   try:"
    echo "       from tensornvme.async_file_io import AsyncFileWriter"
    echo "       TENSORNVME_AVAILABLE = True"
    echo "   except ImportError:"
    echo "       TENSORNVME_AVAILABLE = False"
    echo "       AsyncFileWriter = None"
    echo ""
    exit 1
fi
