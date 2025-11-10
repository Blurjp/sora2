#!/usr/bin/env python3
"""
Patch Open-Sora to make tensornvme optional.
This script modifies opensora/utils/ckpt.py to wrap tensornvme imports in try/except blocks.
"""

import os
import sys
import site

def find_opensora_ckpt():
    """Find the opensora/utils/ckpt.py file in site-packages."""
    site_packages = site.getsitepackages()

    for sp in site_packages:
        ckpt_path = os.path.join(sp, 'opensora', 'utils', 'ckpt.py')
        if os.path.exists(ckpt_path):
            return ckpt_path

    # Also check user site-packages
    user_site = site.getusersitepackages()
    ckpt_path = os.path.join(user_site, 'opensora', 'utils', 'ckpt.py')
    if os.path.exists(ckpt_path):
        return ckpt_path

    return None

def patch_file(file_path):
    """Patch the file to make tensornvme optional."""
    print(f"Patching {file_path}...")

    with open(file_path, 'r') as f:
        content = f.read()

    # Check if already patched
    if 'TENSORNVME_AVAILABLE' in content:
        print("✓ File already patched")
        return True

    # Replace the tensornvme import
    original_import = "from tensornvme.async_file_io import AsyncFileWriter"

    patched_import = """# TensorNVMe is optional - not required for A100/H100 with sufficient VRAM
try:
    from tensornvme.async_file_io import AsyncFileWriter
    TENSORNVME_AVAILABLE = True
except ImportError:
    TENSORNVME_AVAILABLE = False
    AsyncFileWriter = None  # Will be checked before use"""

    if original_import in content:
        content = content.replace(original_import, patched_import)

        # Write back
        with open(file_path, 'w') as f:
            f.write(content)

        print("✓ Successfully patched tensornvme import")
        return True
    else:
        print("⚠ Could not find expected import line")
        print("The file may have been updated or already modified")
        return False

def main():
    ckpt_file = find_opensora_ckpt()

    if not ckpt_file:
        print("ERROR: Could not find opensora/utils/ckpt.py in site-packages")
        print("Open-Sora may not be installed correctly")
        sys.exit(1)

    print(f"Found Open-Sora ckpt.py at: {ckpt_file}")

    if patch_file(ckpt_file):
        print("\n✓ Patch completed successfully!")
        print("Open-Sora will now work without tensornvme")
    else:
        print("\n⚠ Patch may not have been applied correctly")
        print("Please check the file manually")
        sys.exit(1)

if __name__ == '__main__':
    main()
