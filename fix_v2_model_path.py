#!/usr/bin/env python3
"""
Fix Open-Sora v2 model path to use correct Hugging Face format
The path needs to use 'resolve/main' to directly access the file
"""
import os
import sys
from pathlib import Path

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
    print(f"💾 Backup created: {backup_file}")

    # Fix the model path to use resolve/main format for direct file access
    old_path = 'from_pretrained="hpcai-tech/Open-Sora-v2/Open_Sora_v2.safetensors"'
    new_path = 'from_pretrained="hpcai-tech/Open-Sora-v2/resolve/main/Open_Sora_v2.safetensors"'

    if old_path in content:
        print("🔧 Fixing model path to use resolve/main format...")
        content = content.replace(old_path, new_path)

        # Write fixed config
        with open(config_file, 'w') as f:
            f.write(content)

        print("✅ Model path fixed!")
        print(f"   OLD: hpcai-tech/Open-Sora-v2/Open_Sora_v2.safetensors")
        print(f"   NEW: hpcai-tech/Open-Sora-v2/resolve/main/Open_Sora_v2.safetensors")
        print()
        print("This format tells HuggingFace to download the file directly from the main branch.")
        return True
    elif new_path in content:
        print("✅ Model path already uses resolve/main format")
        return True
    else:
        print("⚠️  Current model path format not recognized")
        print("Current content around model definition:")
        import re
        match = re.search(r'from_pretrained\s*=\s*["\']([^"\']+)["\']', content)
        if match:
            print(f"   {match.group(0)}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("🔧 Fixing Open-Sora v2 Model Path")
    print("=" * 70)
    print()

    success = fix_config()

    print()
    print("=" * 70)
    if success:
        print("✅ Fix complete! Restart your service to apply changes.")
    else:
        print("❌ Fix failed. Please check the output above.")
    print("=" * 70)

    sys.exit(0 if success else 1)
