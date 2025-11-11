#!/usr/bin/env python3
"""
Patch Open-Sora to make tensornvme optional.
This script modifies opensora/utils/ckpt.py to wrap tensornvme imports in try/except blocks.
"""

import os
import sys
import site
import subprocess

def find_opensora_ckpt():
    """Find ALL opensora/utils/ckpt.py files."""
    locations = []

    # 1. Check site-packages
    site_packages = site.getsitepackages()
    for sp in site_packages:
        ckpt_path = os.path.join(sp, 'opensora', 'utils', 'ckpt.py')
        if os.path.exists(ckpt_path):
            locations.append(ckpt_path)

    # 2. Check user site-packages
    user_site = site.getusersitepackages()
    ckpt_path = os.path.join(user_site, 'opensora', 'utils', 'ckpt.py')
    if os.path.exists(ckpt_path):
        locations.append(ckpt_path)

    # 3. Check ~/Open-Sora (source installation)
    home = os.path.expanduser('~')
    source_path = os.path.join(home, 'Open-Sora', 'opensora', 'utils', 'ckpt.py')
    if os.path.exists(source_path):
        locations.append(source_path)

    # 4. Check environment variable
    opensora_path = os.environ.get('OPENSORA_PATH')
    if opensora_path:
        env_path = os.path.join(opensora_path, 'opensora', 'utils', 'ckpt.py')
        if os.path.exists(env_path):
            locations.append(env_path)

    # 5. Use find command to search for any remaining locations
    try:
        result = subprocess.run(
            ['find', home, '-name', 'ckpt.py', '-path', '*/opensora/utils/ckpt.py'],
            capture_output=True,
            text=True,
            timeout=10
        )
        for line in result.stdout.strip().split('\n'):
            if line and os.path.exists(line) and line not in locations:
                locations.append(line)
    except:
        pass

    return locations

def patch_file(file_path):
    """Patch the file to make tensornvme optional."""
    print(f"\nPatching {file_path}...")

    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except Exception as e:
        print(f"✗ Error reading file: {e}")
        return False

    # Check if already patched
    if 'TENSORNVME_AVAILABLE' in content:
        print("  ✓ File already patched")
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
        try:
            with open(file_path, 'w') as f:
                f.write(content)
            print("  ✓ Successfully patched tensornvme import")
            return True
        except Exception as e:
            print(f"  ✗ Error writing file: {e}")
            return False
    else:
        print("  ⚠ Could not find expected import line")
        print("  The file may have been updated or already modified")
        return False

def main():
    print("=" * 60)
    print("Searching for Open-Sora ckpt.py files...")
    print("=" * 60)

    ckpt_files = find_opensora_ckpt()

    if not ckpt_files:
        print("\n✗ ERROR: Could not find opensora/utils/ckpt.py")
        print("Open-Sora may not be installed correctly")
        print("\nSearched locations:")
        print("  - Site packages")
        print("  - ~/Open-Sora")
        print("  - $OPENSORA_PATH")
        sys.exit(1)

    print(f"\nFound {len(ckpt_files)} Open-Sora installation(s):")
    for f in ckpt_files:
        print(f"  • {f}")

    success_count = 0
    for ckpt_file in ckpt_files:
        if patch_file(ckpt_file):
            success_count += 1

    print("\n" + "=" * 60)
    if success_count == len(ckpt_files):
        print(f"✓ Successfully patched {success_count}/{len(ckpt_files)} file(s)!")
        print("Open-Sora will now work without tensornvme")
        print("=" * 60)
        sys.exit(0)
    else:
        print(f"⚠ Only patched {success_count}/{len(ckpt_files)} file(s)")
        print("Some patches may have failed")
        print("=" * 60)
        sys.exit(1)

if __name__ == '__main__':
    main()
