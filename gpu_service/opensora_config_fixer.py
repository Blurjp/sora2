"""
Automatic Open-Sora configuration fixer
Runs on service startup to ensure correct settings
"""
import os
import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def fix_opensora_config():
    """
    Automatically fix common Open-Sora configuration issues
    - FPS mismatch (fps_save should match generation FPS)
    - Motion settings optimization
    """
    opensora_path = os.environ.get("OPENSORA_PATH", os.path.expanduser("~/Open-Sora"))
    config_file = Path(opensora_path) / "configs/diffusion/inference/256px.py"

    if not config_file.exists():
        logger.warning(f"Open-Sora config not found: {config_file}")
        return False

    try:
        with open(config_file, 'r') as f:
            content = f.read()

        original_content = content
        fixes_applied = []

        # Fix 1: FPS mismatch (fps_save should be 8 to match generation rate)
        fps_match = re.search(r'fps_save\s*=\s*([0-9]+)', content)
        if fps_match and int(fps_match.group(1)) != 8:
            old_fps = fps_match.group(1)
            content = re.sub(r'fps_save\s*=\s*[0-9]+', 'fps_save = 8', content)
            fixes_applied.append(f"fps_save: {old_fps} → 8 (match generation FPS)")

        # Fix 2: Optimize motion settings
        # Reduce image guidance for more motion freedom
        img_guidance = re.search(r'guidance_img\s*=\s*([0-9.]+)', content)
        if img_guidance and float(img_guidance.group(1)) > 2.0:
            old_val = img_guidance.group(1)
            content = re.sub(r'guidance_img\s*=\s*[0-9.]+', 'guidance_img=2.0', content)
            fixes_applied.append(f"guidance_img: {old_val} → 2.0 (better motion)")

        # Increase text guidance for stronger prompt adherence
        text_guidance = re.search(r'(?<!_)guidance\s*=\s*([0-9.]+)', content)
        if text_guidance and float(text_guidance.group(1)) < 8.0:
            old_val = text_guidance.group(1)
            content = re.sub(r'(?<!_)guidance\s*=\s*[0-9.]+', 'guidance=8.5', content)
            fixes_applied.append(f"guidance: {old_val} → 8.5 (stronger prompts)")

        # Only write if changes were made
        if content != original_content:
            # Create backup
            import time
            backup_file = config_file.parent / f"256px.py.backup_auto_{int(time.time())}"
            with open(backup_file, 'w') as f:
                f.write(original_content)

            # Write fixed config
            with open(config_file, 'w') as f:
                f.write(content)

            logger.info("✅ Open-Sora config auto-fixed:")
            for fix in fixes_applied:
                logger.info(f"   - {fix}")
            logger.info(f"   Backup: {backup_file.name}")
            return True
        else:
            logger.info("✅ Open-Sora config already optimized")
            return True

    except Exception as e:
        logger.error(f"Failed to fix Open-Sora config: {e}")
        return False
