#!/usr/bin/env python3
"""
Fix Open-Sora 256px.py config file to use correct HuggingFace model paths
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
    backup_file = config_file.with_suffix('.py.backup_fix')
    with open(backup_file, 'w') as f:
        f.write(content)
    print(f"💾 Backup created: {backup_file}")

    # Check current model path
    if 'hpcai-tech/Open-Sora-v2/Open_Sora_v2.safetensors' in content:
        print("🔧 Fixing incorrect model path...")
        content = content.replace(
            'from_pretrained="hpcai-tech/Open-Sora-v2/Open_Sora_v2.safetensors"',
            'from_pretrained="hpcai-tech/OpenSora-STDiT-v3/model.safetensors"'
        )

        # Write fixed config
        with open(config_file, 'w') as f:
            f.write(content)
        print("✅ Model path fixed!")
        print(f"   OLD: hpcai-tech/Open-Sora-v2/Open_Sora_v2.safetensors")
        print(f"   NEW: hpcai-tech/OpenSora-STDiT-v3/model.safetensors")
        return True
    else:
        print("✅ Model path already correct")
        return True

if __name__ == "__main__":
    success = fix_config()
    sys.exit(0 if success else 1)
