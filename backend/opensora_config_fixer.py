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

        # Fix 2: Ensure aspect_ratio in config is NOT hardcoded
        # The config should not override command-line aspect_ratio parameter
        # Check if aspect_ratio is hardcoded in sampling_option
        aspect_ratio_match = re.search(r'sampling_option\s*=\s*dict\([^}]+aspect_ratio\s*=\s*["\']([^"\']+)["\']', content, re.DOTALL)
        if aspect_ratio_match:
            logger.info(f"Config has default aspect_ratio: {aspect_ratio_match.group(1)} (will be overridden by request)")

        # Fix 3: AGGRESSIVE prompt following optimization
        # Reduce image guidance SIGNIFICANTLY - allows more freedom from reference image
        img_guidance = re.search(r'guidance_img\s*=\s*([0-9.]+)', content)
        if img_guidance and float(img_guidance.group(1)) != 1.5:
            old_val = img_guidance.group(1)
            content = re.sub(r'guidance_img\s*=\s*[0-9.]+', 'guidance_img=1.5', content)
            fixes_applied.append(f"guidance_img: {old_val} → 1.5 (more freedom from image)")

        # MAXIMIZE text guidance - much stronger prompt adherence
        text_guidance = re.search(r'(?<!_)guidance\s*=\s*([0-9.]+)', content)
        if text_guidance and float(text_guidance.group(1)) != 10.0:
            old_val = text_guidance.group(1)
            content = re.sub(r'(?<!_)guidance\s*=\s*[0-9.]+', 'guidance=10.0', content)
            fixes_applied.append(f"guidance: {old_val} → 10.0 (MAXIMUM prompt adherence)")

        # Increase diffusion steps for better quality and prompt following
        num_steps = re.search(r'num_steps\s*=\s*([0-9]+)', content)
        if num_steps and int(num_steps.group(1)) < 75:
            old_val = num_steps.group(1)
            content = re.sub(r'num_steps\s*=\s*[0-9]+', 'num_steps=75', content)
            fixes_applied.append(f"num_steps: {old_val} → 75 (better quality)")

        # Disable guidance oscillation - it reduces prompt effectiveness
        if 'text_osci' in content:
            text_osci = re.search(r'text_osci\s*=\s*(True|False)', content)
            if text_osci and text_osci.group(1) == 'True':
                content = re.sub(r'text_osci\s*=\s*True', 'text_osci=False', content)
                fixes_applied.append(f"text_osci: True → False (consistent prompt guidance)")

        if 'image_osci' in content:
            image_osci = re.search(r'image_osci\s*=\s*(True|False)', content)
            if image_osci and image_osci.group(1) == 'True':
                content = re.sub(r'image_osci\s*=\s*True', 'image_osci=False', content)
                fixes_applied.append(f"image_osci: True → False (consistent image guidance)")

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
