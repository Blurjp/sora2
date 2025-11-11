#!/usr/bin/env python3
"""
Fix Open-Sora config to use the full 11B Open-Sora v2 checkpoint
instead of the smaller 1B STDiT-v3 checkpoint.
"""

import os
import re
import sys
from pathlib import Path
import site

def find_config_dir() -> Path | None:
    """Locate the Open-Sora configs directory."""
    opensora_path = os.environ.get("OPENSORA_PATH")
    if opensora_path:
        cfg = Path(opensora_path) / "configs" / "diffusion" / "inference"
        if cfg.exists():
            return cfg

    candidates = [
        Path.home() / "Open-Sora" / "configs" / "diffusion" / "inference",
        Path("/opt/Open-Sora/configs/diffusion/inference"),
        Path("/home/ubuntu/Open-Sora/configs/diffusion/inference"),
    ]

    for path in candidates:
        if path.exists():
            return path

    for sp in list(site.getsitepackages()) + [site.getusersitepackages()]:
        if sp:
            cfg = Path(sp) / "opensora" / "configs" / "diffusion" / "inference"
            if cfg.exists():
                return cfg

    return None


def fix_checkpoint_path(file_path: Path) -> bool:
    """Fix the model checkpoint path to use the full Open-Sora v2 model."""
    if not file_path.exists():
        print(f"❌ Config file not found: {file_path}")
        return False

    print(f"\n📝 Processing {file_path.name}...")
    content = file_path.read_text()
    original = content

    # Pattern to match the model checkpoint path
    # Matches: from_pretrained="hpcai-tech/OpenSora-STDiT-v3/model.safetensors"

    # Try alternative patterns
    patterns = [
        (r'from_pretrained\s*=\s*"hpcai-tech/OpenSora-STDiT-v3/model\.safetensors"',
         'from_pretrained="hpcai-tech/Open-Sora-v2/Open_Sora_v2.safetensors"'),
        (r"from_pretrained\s*=\s*'hpcai-tech/OpenSora-STDiT-v3/model\.safetensors'",
         'from_pretrained="hpcai-tech/Open-Sora-v2/Open_Sora_v2.safetensors"'),
        # Also catch if it's already pointing to tree/main format
        (r'from_pretrained\s*=\s*"hpcai-tech/OpenSora-STDiT-v3/tree/main/model\.safetensors"',
         'from_pretrained="hpcai-tech/Open-Sora-v2/Open_Sora_v2.safetensors"'),
    ]

    changed = False
    for pattern, replacement in patterns:
        new_content, count = re.subn(pattern, replacement, content)
        if count > 0:
            content = new_content
            changed = True
            print(f"   ✓ Fixed model checkpoint path ({count} occurrence(s))")
            break

    if not changed:
        print(f"   ⚠️  Pattern not found. Current from_pretrained lines:")
        # Show current model from_pretrained line
        for i, line in enumerate(content.split('\n'), 1):
            if 'from_pretrained' in line:
                stripped = line.strip()
                if stripped and not stripped.startswith('#'):
                    print(f"      Line {i}: {stripped}")
        return False

    # Create backup
    backup = file_path.with_suffix(file_path.suffix + ".bak")
    if not backup.exists():
        backup.write_text(original)
        print(f"   💾 Backup saved: {backup.name}")

    # Write updated config
    file_path.write_text(content)
    print(f"   ✅ Updated successfully!")

    return True


def main():
    print("=" * 70)
    print("Fix Open-Sora Checkpoint Path")
    print("=" * 70)
    print("\nChanging from:")
    print("  hpcai-tech/OpenSora-STDiT-v3/model.safetensors (1B params)")
    print("To:")
    print("  hpcai-tech/Open-Sora-v2/Open_Sora_v2.safetensors (11B params)")
    print()

    config_dir = find_config_dir()
    if not config_dir:
        print("❌ ERROR: Could not locate Open-Sora inference configs.")
        print("Set OPENSORA_PATH or install open-sora in the current environment.")
        sys.exit(1)

    print(f"📁 Config directory: {config_dir}\n")

    any_changes = False
    for name in ("256px.py", "768px.py"):
        path = config_dir / name
        if path.exists():
            any_changes |= fix_checkpoint_path(path)
        else:
            print(f"⏭️  Skipping {name} (not found)")

    print("\n" + "=" * 70)
    if any_changes:
        print("✅ Done! The config now points to the full 11B Open-Sora v2 model.")
        print("\nNext steps:")
        print("  1. Restart your GPU service")
        print("  2. The model will download automatically on first use (~42GB)")
    else:
        print("⚠️  No changes made. Please check the config file manually.")
        print(f"\nConfig location: {config_dir}")
    print("=" * 70)


if __name__ == "__main__":
    main()
