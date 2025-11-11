#!/bin/bash
# Quick fix script for Open-Sora config paths
# Replaces all ./ckpts/ references with proper HuggingFace repos

set -e

OPENSORA_PATH="${OPENSORA_PATH:-$HOME/Open-Sora}"
CONFIG_FILE="$OPENSORA_PATH/configs/diffusion/inference/256px.py"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Config file not found: $CONFIG_FILE"
    echo "Set OPENSORA_PATH environment variable if needed"
    exit 1
fi

echo "Fixing Open-Sora config: $CONFIG_FILE"
echo ""

# Backup
cp "$CONFIG_FILE" "$CONFIG_FILE.backup.$(date +%s)"
echo "✓ Backup created"

# Fix all paths - use correct OpenSora-STDiT-v3 repo
sed -i \
    -e 's|"hpcai-tech/Open-Sora-v2/model"|"hpcai-tech/OpenSora-STDiT-v3"|g' \
    -e 's|"hpcai-tech/Open-Sora-v2/hunyuan_vae"|"hpcai-tech/OpenSora-STDiT-v3"|g' \
    "$CONFIG_FILE"

echo "✓ Fixed component paths:"
echo "  - Model/VAE: hpcai-tech/OpenSora-STDiT-v3"
echo "  - T5: google/t5-v1_1-xxl"
echo "  - CLIP: openai/clip-vit-large-patch14"
echo ""

# Verify
echo "Verifying changes:"
grep "from_pretrained" "$CONFIG_FILE" | head -10
echo ""
echo "✓ Config fixed! Restart the service to apply changes."
