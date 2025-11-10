#!/usr/bin/env python3
"""
Patch Open-Sora config files to use Hugging Face Hub checkpoint.
This fixes the hardcoded './ckpts/Open_Sora_v2.safetensors' path.
"""

import os
import sys
import re
from pathlib import Path

def patch_config_file(config_path: Path, checkpoint_repo: str = "hpcai-tech/OpenSora-STDiT-v3") -> bool:
    """Patch the config file to use HF Hub checkpoint."""

    if not config_path.exists():
        print(f"Config file not found: {config_path}")
        return False

    print(f"Patching {config_path}...")

    with open(config_path, 'r') as f:
        content = f.read()

    # Check if already patched
    if checkpoint_repo in content:
        print("✓ Config already patched")
        return True

    # Find and replace checkpoint path patterns
    # Pattern 1: ckpt="./ckpts/..." or ckpt='./ckpts/...'
    pattern1 = r'ckpt\s*=\s*["\']\.\/ckpts\/[^"\']+["\']'
    if re.search(pattern1, content):
        content = re.sub(pattern1, f'ckpt="{checkpoint_repo}"', content)
        print("✓ Replaced ckpt path in config")

    # Pattern 2: checkpoint_path="./ckpts/..." or similar variables
    pattern2 = r'checkpoint[_-]?path\s*=\s*["\']\.\/ckpts\/[^"\']+["\']'
    if re.search(pattern2, content, re.IGNORECASE):
        content = re.sub(pattern2, f'checkpoint_path="{checkpoint_repo}"', content, flags=re.IGNORECASE)
        print("✓ Replaced checkpoint_path in config")

    # Write back
    with open(config_path, 'w') as f:
        f.write(content)

    print("✓ Config patched successfully")
    return True

def main():
    # Get OPENSORA_PATH from environment
    opensora_path = os.environ.get('OPENSORA_PATH')

    if not opensora_path:
        print("ERROR: OPENSORA_PATH environment variable not set")
        sys.exit(1)

    opensora_path = Path(opensora_path)

    if not opensora_path.exists():
        print(f"ERROR: Open-Sora path does not exist: {opensora_path}")
        sys.exit(1)

    # Patch both 256px and 768px configs
    configs_to_patch = [
        opensora_path / "configs/diffusion/inference/256px.py",
        opensora_path / "configs/diffusion/inference/768px.py",
    ]

    checkpoint_repo = os.environ.get('CHECKPOINT_PATH', 'hpcai-tech/OpenSora-STDiT-v3')

    print(f"Open-Sora path: {opensora_path}")
    print(f"Checkpoint repo: {checkpoint_repo}")
    print()

    success = True
    for config_path in configs_to_patch:
        if config_path.exists():
            if not patch_config_file(config_path, checkpoint_repo):
                success = False
        else:
            print(f"⚠ Config not found (skipping): {config_path}")

    if success:
        print("\n✓ All configs patched successfully!")
    else:
        print("\n⚠ Some configs failed to patch")
        sys.exit(1)

if __name__ == '__main__':
    main()
