#!/usr/bin/env python3
"""
Diagnose Open-Sora config files to understand their structure.
"""

import os
import sys
import site
from pathlib import Path

def find_and_show_configs():
    """Find and display Open-Sora config files."""
    # Check all site-packages locations
    site_packages = site.getsitepackages() + [site.getusersitepackages()]

    for sp in site_packages:
        config_dir = Path(sp) / "opensora" / "configs" / "diffusion" / "inference"
        if config_dir.exists():
            print(f"✓ Found config directory: {config_dir}")

            config_256 = config_dir / "256px.py"
            if config_256.exists():
                print(f"\n=== 256px.py config ===")
                with open(config_256, 'r') as f:
                    content = f.read()
                print(content)
                print("\n" + "="*60 + "\n")

            return

    print("ERROR: Could not find config directory")

if __name__ == '__main__':
    find_and_show_configs()
