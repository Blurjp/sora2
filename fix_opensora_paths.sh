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

# Fix all paths
sed -i \
    -e "s|from_pretrained.*=.*['\"]\\./ckpts/hunyuan_vae\\.safetensors['\"]|from_pretrained=\"hpcai-tech/Open-Sora-v2/hunyuan_vae\"|g" \
    -e "s|from_pretrained.*=.*['\"]\\./ckpts/google/t5-v1_1-xxl['\"]|from_pretrained=\"google/t5-v1_1-xxl\"|g" \
    -e "s|from_pretrained.*=.*['\"]\\./ckpts/openai/clip-vit-large-patch14['\"]|from_pretrained=\"openai/clip-vit-large-patch14\"|g" \
    -e "s|from_pretrained.*=.*['\"]\\./ckpts/Open_Sora_v2\\.safetensors['\"]|from_pretrained=\"hpcai-tech/Open-Sora-v2/model\"|g" \
    "$CONFIG_FILE"

echo "✓ Fixed component paths:"
echo "  - VAE: hpcai-tech/Open-Sora-v2/hunyuan_vae"
echo "  - T5: google/t5-v1_1-xxl"
echo "  - CLIP: openai/clip-vit-large-patch14"
echo "  - Model: hpcai-tech/Open-Sora-v2/model"
echo ""

# Verify
echo "Verifying changes:"
grep "from_pretrained" "$CONFIG_FILE" | head -10
echo ""
echo "✓ Config fixed! Restart the service to apply changes."
