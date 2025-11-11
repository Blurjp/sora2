#!/usr/bin/env python3
"""
Tune Open-Sora motion settings for more dramatic movement
"""
import os
import sys
from pathlib import Path
import re

def tune_config():
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

    # Show current settings
    print("🔍 Current motion-related settings:")
    for line in content.split('\n'):
        if any(keyword in line for keyword in ['guidance', 'num_steps', 'motion_score', 'temporal']):
            print(f"   {line.strip()}")
    print()

    # Tuning recommendations
    changes = []

    # 1. Reduce image guidance (allows more deviation from reference image)
    if 'guidance_img' in content:
        old_val = re.search(r'guidance_img\s*=\s*([0-9.]+)', content)
        if old_val and float(old_val.group(1)) > 1.5:
            content = re.sub(
                r'guidance_img\s*=\s*[0-9.]+',
                'guidance_img=1.5',
                content
            )
            changes.append(f"guidance_img: {old_val.group(1)} → 1.5 (allow more motion)")

    # 2. Increase text guidance (stronger adherence to prompt)
    if 'guidance\s*=' in content:
        old_val = re.search(r'(?<!_)guidance\s*=\s*([0-9.]+)', content)
        if old_val and float(old_val.group(1)) < 9.0:
            content = re.sub(
                r'(?<!_)guidance\s*=\s*[0-9.]+',
                'guidance=9.0',
                content
            )
            changes.append(f"guidance: {old_val.group(1)} → 9.0 (stronger prompt adherence)")

    # 3. Increase diffusion steps for better quality
    if 'num_steps' in content:
        old_val = re.search(r'num_steps\s*=\s*([0-9]+)', content)
        if old_val and int(old_val.group(1)) < 75:
            content = re.sub(
                r'num_steps\s*=\s*[0-9]+',
                'num_steps=75',
                content
            )
            changes.append(f"num_steps: {old_val.group(1)} → 75 (better quality/motion)")

    if not changes:
        print("✅ Settings already optimized for motion")
        return True

    # Write updated config
    with open(config_file, 'w') as f:
        f.write(content)

    print("✅ Configuration tuned for more motion!\n")
    print("Changes made:")
    for change in changes:
        print(f"   ✓ {change}")
    print()

    return True

if __name__ == "__main__":
    print("=" * 70)
    print("🎬 Tuning Open-Sora for More Dramatic Motion")
    print("=" * 70)
    print()

    success = tune_config()

    print("=" * 70)
    if success:
        print("✅ Tuning complete!")
        print()
        print("Recommendations:")
        print("1. Restart your backend service")
        print("2. Use motion score 0.9-1.0 in the UI")
        print("3. Try prompts like: 'she is dancing energetically'")
        print("4. Shorter durations (10s) can show more concentrated motion")
    else:
        print("❌ Tuning failed")
    print("=" * 70)

    sys.exit(0 if success else 1)
