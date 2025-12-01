"""
Configuration for WAN 2.2 GPU Service (runs on Lambda/remote GPU)
"""
import os
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "outputs"
TEMP_DIR = BASE_DIR / "temp"

# Create directories if they don't exist
OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

# Server configuration
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8001"))

# Video generation settings
# WAN 2.2 generates at 16 FPS natively
FRAMES_PER_SECOND = 16

# Advanced generation parameters (can be overridden per request or via .env)
# WAN 2.2 defaults are different from Open-Sora
DEFAULT_NUM_STEPS = int(os.environ.get("DEFAULT_NUM_STEPS", "40"))  # WAN default: 40 steps
MIN_NUM_STEPS = 20
MAX_NUM_STEPS = 100

DEFAULT_GUIDANCE = float(os.environ.get("DEFAULT_GUIDANCE", "5.0"))  # WAN text guidance
MIN_GUIDANCE = 1.0
MAX_GUIDANCE = 15.0

DEFAULT_GUIDANCE_IMG = float(os.environ.get("DEFAULT_GUIDANCE_IMG", "3.5"))  # Image guidance for I2V
MIN_GUIDANCE_IMG = 0.5
MAX_GUIDANCE_IMG = 10.0

# WAN 2.2 Model Configuration
# Available models:
# - "Wan-AI/Wan2.2-I2V-A14B-Diffusers" (14B params, 80GB VRAM, best quality)
# - "Wan-AI/Wan2.2-TI2V-5B-Diffusers" (5B params, 24GB VRAM, consumer GPU friendly)
WAN_MODEL_ID = os.environ.get("WAN_MODEL_ID", "Wan-AI/Wan2.2-I2V-A14B-Diffusers")

# Model variant for I2V (used only with I2V-A14B model)
WAN_MODEL_VARIANT = os.environ.get("WAN_MODEL_VARIANT", "720P")

# Resolution settings for WAN 2.2
WAN_WIDTH = int(os.environ.get("WAN_WIDTH", "1280"))
WAN_HEIGHT = int(os.environ.get("WAN_HEIGHT", "720"))

# Memory optimization options
WAN_ENABLE_MODEL_CPU_OFFLOAD = os.environ.get("WAN_ENABLE_MODEL_CPU_OFFLOAD", "false").lower() == "true"
WAN_ENABLE_VAE_SLICING = os.environ.get("WAN_ENABLE_VAE_SLICING", "true").lower() == "true"
WAN_ENABLE_VAE_TILING = os.environ.get("WAN_ENABLE_VAE_TILING", "false").lower() == "true"

# Data type for model (bfloat16 recommended for modern GPUs)
WAN_TORCH_DTYPE = os.environ.get("WAN_TORCH_DTYPE", "bfloat16")

# Legacy compatibility (kept for backward compatibility but not used)
OPENSORA_PATH = os.environ.get("OPENSORA_PATH", None)
MODEL_RESOLUTION = os.environ.get("MODEL_RESOLUTION", "720P")
MODEL_CONFIG_PATH = None
CHECKPOINT_PATH = os.environ.get("CHECKPOINT_PATH", None)

# Cleanup settings
CLEANUP_AFTER_HOURS = 24  # Delete generated videos after 24 hours

# Security
API_KEY = os.environ.get("GPU_API_KEY", None)  # Optional API key for auth
