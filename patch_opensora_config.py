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
    """Find Open-Sora config directory."""
    # Check OPENSORA_PATH first (most likely location for cloned repo)
    opensora_path = os.environ.get('OPENSORA_PATH')
    if opensora_path:
        config_dir = Path(opensora_path) / "configs" / "diffusion" / "inference"
        if config_dir.exists():
            print(f"Found configs in OPENSORA_PATH: {config_dir}")
            return config_dir

    # Check Open-Sora repo in common locations
    common_paths = [
        Path.home() / "Open-Sora" / "configs" / "diffusion" / "inference",
        Path("/home/ubuntu/Open-Sora/configs/diffusion/inference"),
        Path("/lambda/nfs/sora2/Open-Sora/configs/diffusion/inference"),
    ]

    for config_dir in common_paths:
        if config_dir.exists():
            print(f"Found configs at: {config_dir}")
            return config_dir

    # Finally check site-packages
    site_packages = site.getsitepackages() + [site.getusersitepackages()]
    for sp in site_packages:
        config_dir = Path(sp) / "opensora" / "configs" / "diffusion" / "inference"
        if config_dir.exists():
            print(f"Found configs in site-packages: {config_dir}")
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
    replacements_made = 0

    # Pattern 1: Quoted strings - ckpt="./ckpts/..." or ckpt='./ckpts/...'
    pattern1 = r'(["\'])\.\/ckpts\/[^"\']+\1'
    if re.search(pattern1, content):
        content = re.sub(pattern1, f'"{checkpoint_repo}"', content)
        replacements_made += len(re.findall(pattern1, original_content))
        print(f"✓ Replaced {len(re.findall(pattern1, original_content))} quoted ckpts paths")

    # Pattern 2: Any line with ./ckpts/ (more aggressive)
    # This catches cases like: ckpt=./ckpts/file.safetensors without quotes
    pattern2 = r'\.\/ckpts\/[\w\-\.\/]+'
    if re.search(pattern2, content):
        matches = re.findall(pattern2, content)
        content = re.sub(pattern2, checkpoint_repo, content)
        replacements_made += len(matches)
        print(f"✓ Replaced {len(matches)} ./ckpts/ paths")

    # Only write if content changed
    if content != original_content:
        with open(config_path, 'w') as f:
            f.write(content)
        print(f"✓ Config file updated ({replacements_made} replacements)")
        return True
    else:
        print("⚠ No ./ckpts/ patterns found to replace")
        # Show full content for debugging
        print("\n=== Config content ===")
        print(content)
        print("=== End of config ===\n")
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
