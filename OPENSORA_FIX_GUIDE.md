# Open-Sora Component Configuration Fix

## Problem

You're seeing this error:
```
Missing key(s) in state_dict for AutoencoderKLCausal3D
```

## Root Cause

Open-Sora inference configs point **all components** (model, VAE, T5, CLIP) to the same checkpoint file. This causes the VAE to try loading from the main model weights, which have different keys.

**Incorrect (current):**
- Model: `hpcai-tech/OpenSora-STDiT-v3/model.safetensors`
- VAE: `hpcai-tech/OpenSora-STDiT-v3/model.safetensors` ❌ **WRONG!**
- T5: `hpcai-tech/OpenSora-STDiT-v3/model.safetensors` ❌ **WRONG!**
- CLIP: `hpcai-tech/OpenSora-STDiT-v3/model.safetensors` ❌ **WRONG!**

**Correct:**
- Model: `hpcai-tech/OpenSora-STDiT-v3/model.safetensors` ✅
- VAE: `hpcai-tech/OpenSora-STDiT-v3/hunyuan_vae.safetensors` ✅
- T5: `google/t5-v1_1-xxl` ✅
- CLIP: `openai/clip-vit-large-patch14` ✅

## Solution

Run the patch script on your Lambda instance to fix all component paths.

### On Lambda Instance (After SSH)

```bash
# 1. Navigate to repo
cd ~/sora2

# 2. Pull latest code (includes the patch script)
git pull

# 3. Set Open-Sora path
export OPENSORA_PATH=~/Open-Sora

# 4. Run the patch script
python3 patch_opensora_config.py

# Expected output:
# ======================================================================
# Open-Sora Component Config Patcher
# ======================================================================
#
# Config directory: /home/ubuntu/Open-Sora/configs/diffusion/inference
#
# Patching /home/ubuntu/Open-Sora/configs/diffusion/inference/256px.py...
#   → Backup saved: 256px.py.backup
#   ✓ Patched: VAE, T5 encoder, CLIP encoder
#
# Patching /home/ubuntu/Open-Sora/configs/diffusion/inference/768px.py...
#   → Backup saved: 768px.py.backup
#   ✓ Patched: VAE, T5 encoder, CLIP encoder
#
# ======================================================================
# ✓ Successfully patched 2 config file(s)
```

### Verify the Fix

```bash
# Check that models can be downloaded
python3 - <<'PY'
from huggingface_hub import hf_hub_download as d
print('Model:', d('hpcai-tech/OpenSora-STDiT-v3','model.safetensors'))
print('VAE  :', d('hpcai-tech/Open-Sora-v2','hunyuan_vae.safetensors'))
PY
```

### Restart GPU Service

```bash
# Kill any running service
pkill -f python

# Restart with proper config
./lambda_run_gpu_service.sh --api-key secret_sora2_3e1296ff401d44c5b476387cda212173.PmVHz6bzECPi06mihPABbHObqOo5RiBs
```

Or use the restart script:
```bash
./restart.sh --gpu-service --api-key secret_sora2_3e1296ff401d44c5b476387cda212173.PmVHz6bzECPi06mihPABbHObqOo5RiBs
```

## What the Patch Does

The `patch_opensora_config.py` script:

1. **Locates** Open-Sora config files (256px.py, 768px.py)
2. **Creates backups** (.backup files)
3. **Updates** component paths:
   - VAE: `hunyuan_vae.safetensors`
   - T5: `google/t5-v1_1-xxl`
   - CLIP: `openai/clip-vit-large-patch14`
4. **Sets** main model path to `hpcai-tech/OpenSora-STDiT-v3/model.safetensors`

## Manual Verification

After patching, you can check the config files:

```bash
# Check 256px config
grep -A 2 "ae = dict" ~/Open-Sora/configs/diffusion/inference/256px.py

# Should show:
# ae = dict(
#     ...
#     from_pretrained="hpcai-tech/Open-Sora-v2/hunyuan_vae.safetensors"
# )
```

## If Patch Fails

### Option 1: Manual Edit

Edit the config files directly:

```bash
# Edit 256px config
nano ~/Open-Sora/configs/diffusion/inference/256px.py
```

Find and update:
```python
# VAE configuration
ae = dict(
    ...
    from_pretrained="hpcai-tech/Open-Sora-v2/hunyuan_vae.safetensors",  # Fix this
)

# T5 text encoder
text_encoder = dict(
    type="t5",
    ...
    from_pretrained="google/t5-v1_1-xxl",  # Fix this
)

# CLIP text encoder
text_encoder = dict(
    type="clip",
    ...
    from_pretrained="openai/clip-vit-large-patch14",  # Fix this
)
```

Repeat for `768px.py`.

### Option 2: Re-run Setup

If configs are corrupted:

```bash
cd ~/Open-Sora
git checkout configs/diffusion/inference/256px.py
git checkout configs/diffusion/inference/768px.py
cd ~/sora2
python3 patch_opensora_config.py
```

## Troubleshooting

### "Config directory not found"

```bash
# Set OPENSORA_PATH
export OPENSORA_PATH=~/Open-Sora

# Verify it exists
ls $OPENSORA_PATH/configs/diffusion/inference/
```

### "No changes needed"

The configs are already correct! Just restart the service.

### "HuggingFace download error"

Check internet connectivity and HF Hub access:
```bash
ping huggingface.co
```

If behind a firewall, you may need to:
```bash
export HF_ENDPOINT=https://hf-mirror.com  # China mirror
```

### Still Getting state_dict Error

1. Check backup wasn't used:
   ```bash
   ls ~/Open-Sora/configs/diffusion/inference/*.backup
   ```

2. Verify patch was applied:
   ```bash
   grep hunyuan_vae ~/Open-Sora/configs/diffusion/inference/256px.py
   ```

3. Clear cache and retry:
   ```bash
   rm -rf ~/.cache/huggingface/
   ```

## Optional: Fix Library Warnings

These warnings don't affect generation but can be silenced:

```bash
# Update requests/urllib3
pip install -U "requests>=2.32,<3" "urllib3<3"

# Remove chardet if causing issues
pip uninstall -y chardet
```

## After Fix

Once patched and restarted, try generating a video:

1. Open local backend: http://localhost:8000
2. Upload an image
3. Enter prompt
4. Generate!

The VAE, T5, and CLIP will now load from their correct repositories, and you should no longer see the `Missing key(s)` error.

## Backup Strategy

The patch script creates `.backup` files. To restore:

```bash
cd ~/Open-Sora/configs/diffusion/inference/

# Restore from backup
cp 256px.py.backup 256px.py
cp 768px.py.backup 768px.py
```

## Summary

| Component | Wrong Path | Correct Path |
|-----------|-----------|--------------|
| Model | ❌ Open_Sora_v2.safetensors | ✅ OpenSora-STDiT-v3/model.safetensors |
| VAE | ❌ Open_Sora_v2.safetensors | ✅ OpenSora-STDiT-v3/hunyuan_vae.safetensors |
| T5 | ❌ Open_Sora_v2.safetensors | ✅ google/t5-v1_1-xxl |
| CLIP | ❌ Open_Sora_v2.safetensors | ✅ openai/clip-vit-large-patch14 |

Run `python3 patch_opensora_config.py` to fix all paths automatically!



