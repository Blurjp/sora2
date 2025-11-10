#!/usr/bin/env python3
"""
Patch Open-Sora config files to use Hugging Face Hub checkpoint.
This fixes the hardcoded './ckpts/Open_Sora_v2.safetensors' path.
"""

import os
import sys
import re
import site
from pathlib import Path

def find_opensora_configs():
    """Find Open-Sora config directory in site-packages."""
    # Check all site-packages locations
    site_packages = site.getsitepackages() + [site.getusersitepackages()]

    for sp in site_packages:
        config_dir = Path(sp) / "opensora" / "configs" / "diffusion" / "inference"
        if config_dir.exists():
            return config_dir

    # Also check OPENSORA_PATH if set
    opensora_path = os.environ.get('OPENSORA_PATH')
    if opensora_path:
        config_dir = Path(opensora_path) / "configs" / "diffusion" / "inference"
        if config_dir.exists():
            return config_dir

    return None

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

    original_content = content

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

    # Only write if content changed
    if content != original_content:
        with open(config_path, 'w') as f:
            f.write(content)
        print("✓ Config file updated")
        return True
    else:
        print("⚠ No matching patterns found to replace")
        # Show first few lines for debugging
        print("Config content preview:")
        print("\n".join(content.split("\n")[:20]))
        return False

def main():
    # Find config directory
    config_dir = find_opensora_configs()

    if not config_dir:
        print("ERROR: Could not find Open-Sora config directory")
        print("Checked site-packages and OPENSORA_PATH")
        sys.exit(1)

    print(f"Found Open-Sora configs at: {config_dir}")

    # Patch both 256px and 768px configs
    configs_to_patch = [
        config_dir / "256px.py",
        config_dir / "768px.py",
    ]

    checkpoint_repo = os.environ.get('CHECKPOINT_PATH', 'hpcai-tech/OpenSora-STDiT-v3')
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
