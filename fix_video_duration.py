#!/usr/bin/env python3
"""
Fix video duration issue: FPS mismatch between generation and saving
"""
import os
import sys
from pathlib import Path
import re

def fix_fps():
    opensora_path = os.environ.get("OPENSORA_PATH", os.path.expanduser("~/Open-Sora"))
    config_file = Path(opensora_path) / "configs/diffusion/inference/256px.py"

    if not config_file.exists():
        print(f"❌ Config file not found: {config_file}")
        return False

    print(f"📝 Reading config: {config_file}")
    with open(config_file, 'r') as f:
        content = f.read()

    # Backup
    import time
    backup_file = config_file.parent / f"256px.py.backup_{int(time.time())}"
    with open(backup_file, 'w') as f:
        f.write(content)
    print(f"💾 Backup created: {backup_file.name}\n")

    # Find current fps_save
    fps_match = re.search(r'fps_save\s*=\s*([0-9]+)', content)
    if not fps_match:
        print("❌ Could not find fps_save in config")
        return False

    current_fps = int(fps_match.group(1))
    print(f"🔍 Current fps_save: {current_fps}")

    if current_fps == 8:
        print("✅ FPS already set to 8 (matches generation rate)")
        return True

    print(f"\n🔧 Problem detected:")
    print(f"   - Frames generated at: 8 FPS")
    print(f"   - Video saved at: {current_fps} FPS")
    print(f"   - This causes {current_fps/8:.1f}x speedup!")
    print()
    print(f"Example: 15s video with 117 frames:")
    print(f"   - Expected: 117 ÷ 8 = 14.6s")
    print(f"   - Actual: 117 ÷ {current_fps} = {117/current_fps:.1f}s ❌")
    print()

    # Fix fps_save to 8
    content = re.sub(r'fps_save\s*=\s*[0-9]+', 'fps_save = 8', content)

    with open(config_file, 'w') as f:
        f.write(content)

    print("✅ Fixed fps_save to 8 FPS")
    print(f"   Now 15s videos will be actual 15s duration!")

    return True

if __name__ == "__main__":
    print("=" * 70)
    print("🎬 Fixing Video Duration (FPS Mismatch)")
    print("=" * 70)
    print()

    success = fix_fps()

    print()
    print("=" * 70)
    if success:
        print("✅ Fix complete!")
        print()
        print("Next steps:")
        print("1. Restart your backend service")
        print("2. Generate a new video")
        print("3. Check the duration - should match your request now")
    else:
        print("❌ Fix failed")
    print("=" * 70)

    sys.exit(0 if success else 1)
