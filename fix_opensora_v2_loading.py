#!/usr/bin/env python3
"""
Fix Open-Sora v2 model loading to use correct HuggingFace cache format

The issue: Path 'hpcai-tech/Open-Sora-v2/Open_Sora_v2.safetensors' doesn't load correctly
Solution: Use the repo ID directly and let HuggingFace find the cached file
"""
import os
import sys
from pathlib import Path
import re

def fix_config():
    opensora_path = os.environ.get("OPENSORA_PATH", os.path.expanduser("~/Open-Sora"))
    config_file = Path(opensora_path) / "configs/diffusion/inference/256px.py"

    if not config_file.exists():
        print(f"❌ Config file not found: {config_file}")
        return False

    print(f"📝 Reading config file: {config_file}")
    with open(config_file, 'r') as f:
        content = f.read()

    # Backup
    import time
    backup_file = config_file.parent / f"256px.py.backup_{int(time.time())}"
    with open(backup_file, 'w') as f:
        f.write(content)
    print(f"💾 Backup created: {backup_file.name}\n")

    original_content = content
    changes_made = []

    # Fix model path - use hf:// prefix to force HuggingFace Hub loading
    # The hf:// prefix tells the loader to use HuggingFace's caching system
    model_patterns = [
        (
            r'from_pretrained\s*=\s*["\']hpcai-tech/Open-Sora-v2/Open_Sora_v2\.safetensors["\']',
            'from_pretrained="hf://hpcai-tech/Open-Sora-v2/Open_Sora_v2.safetensors"',
            "Model path (Open_Sora_v2)"
        ),
        (
            r'from_pretrained\s*=\s*["\']hpcai-tech/Open-Sora-v2/hunyuan_vae\.safetensors["\']',
            'from_pretrained="hf://hpcai-tech/Open-Sora-v2/hunyuan_vae.safetensors"',
            "VAE path (hunyuan_vae)"
        ),
    ]

    for pattern, replacement, description in model_patterns:
        matches = re.findall(pattern, content)
        if matches:
            content = re.sub(pattern, replacement, content)
            changes_made.append(description)

    # If no changes with hf:// prefix, try alternative format
    if not changes_made:
        # Try using just the repo with filename in config
        alt_pattern = r'(model\s*=\s*dict\([^)]*from_pretrained\s*=\s*["\'])hpcai-tech/Open-Sora-v2/Open_Sora_v2\.safetensors(["\'][^)]*\))'
        if re.search(alt_pattern, content):
            # Change to use repo only and add filename parameter
            content = re.sub(
                alt_pattern,
                r'\1hpcai-tech/Open-Sora-v2\2',
                content
            )
            # Add filename parameter after from_pretrained
            content = re.sub(
                r'(from_pretrained\s*=\s*["\']hpcai-tech/Open-Sora-v2["\'])',
                r'\1,\n    filename="Open_Sora_v2.safetensors"',
                content
            )
            changes_made.append("Model path (using filename parameter)")

    if not changes_made:
        print("⚠️  No changes needed or pattern not recognized\n")
        print("Current model path:")
        match = re.search(r'from_pretrained\s*=\s*["\']([^"\']+)["\']', content)
        if match:
            print(f"   {match.group(1)}")
        return False

    # Write fixed config
    with open(config_file, 'w') as f:
        f.write(content)

    print("✅ Configuration fixed!\n")
    print("Changes made:")
    for change in changes_made:
        print(f"   ✓ {change}")
    print()
    print("💡 The hf:// prefix tells the loader to use HuggingFace's cache system")
    print("   This ensures the 22GB cached model file is found and loaded correctly.")
    print()

    return True

if __name__ == "__main__":
    print("=" * 70)
    print("🔧 Fixing Open-Sora v2 Model Loading")
    print("=" * 70)
    print()

    success = fix_config()

    print("=" * 70)
    if success:
        print("✅ Fix complete!")
        print()
        print("Next steps:")
        print("1. Restart your backend service")
        print("2. Try generating a video")
        print("3. Check logs for 'Model loaded' or 'Loading checkpoint' messages")
    else:
        print("❌ Fix failed or not needed")
        print()
        print("The current path format might already be correct,")
        print("or the issue might be elsewhere in the loading pipeline.")
    print("=" * 70)

    sys.exit(0 if success else 1)
