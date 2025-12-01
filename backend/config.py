"""
Configuration for WAN 2.2 Video Generation Service
"""
import os
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "outputs"
TEMP_DIR = BASE_DIR / "temp"
STATIC_DIR = BASE_DIR / "frontend"

# Create directories if they don't exist
OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

# Server configuration
# Default to 127.0.0.1 for security (SSH tunnel mode)
# Set HOST env var to "0.0.0.0" for public access
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8000"))

# Video generation settings
DEFAULT_ASPECT_RATIO = "16:9"
DEFAULT_DURATION = 5  # seconds (WAN generates 81 frames at 16fps = ~5s)
MIN_DURATION = 3
MAX_DURATION = 10  # WAN supports shorter but higher quality videos

# Frame calculation: WAN uses 4k+1 formula (same as Open-Sora)
# WAN 2.2 generates at 16 FPS natively
FRAMES_PER_SECOND = 16

# Supported aspect ratios
ASPECT_RATIOS = ["16:9", "9:16", "1:1"]

# Advanced generation parameters (can be overridden per request or via .env)
# WAN 2.2 defaults are different from Open-Sora
DEFAULT_NUM_STEPS = int(os.environ.get("DEFAULT_NUM_STEPS", "40"))  # WAN default: 40 steps
MIN_NUM_STEPS = 20
MAX_NUM_STEPS = 100  # WAN doesn't benefit as much from very high steps

DEFAULT_GUIDANCE = float(os.environ.get("DEFAULT_GUIDANCE", "5.0"))  # WAN text guidance (lower than Open-Sora)
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
# Options: "480P", "720P"
WAN_MODEL_VARIANT = os.environ.get("WAN_MODEL_VARIANT", "720P")

# Resolution settings for WAN 2.2
# I2V-A14B: 1280x720 (720P) or 832x480 (480P)
# TI2V-5B: 1280x704 or 704x1280 (720P only)
WAN_WIDTH = int(os.environ.get("WAN_WIDTH", "1280"))
WAN_HEIGHT = int(os.environ.get("WAN_HEIGHT", "720"))

# Memory optimization options
WAN_ENABLE_MODEL_CPU_OFFLOAD = os.environ.get("WAN_ENABLE_MODEL_CPU_OFFLOAD", "false").lower() == "true"
WAN_ENABLE_VAE_SLICING = os.environ.get("WAN_ENABLE_VAE_SLICING", "true").lower() == "true"
WAN_ENABLE_VAE_TILING = os.environ.get("WAN_ENABLE_VAE_TILING", "false").lower() == "true"

# Data type for model (bfloat16 recommended for modern GPUs)
WAN_TORCH_DTYPE = os.environ.get("WAN_TORCH_DTYPE", "bfloat16")  # "float16" or "bfloat16"

# Legacy compatibility (these are kept for backward compatibility but not used)
OPENSORA_PATH = os.environ.get("OPENSORA_PATH", None)
MODEL_RESOLUTION = os.environ.get("MODEL_RESOLUTION", "720P")
MODEL_CONFIG_PATH = None
CHECKPOINT_PATH = os.environ.get("CHECKPOINT_PATH", None)

# Generation limits
MAX_CONCURRENT_JOBS = 2
ENABLE_QUEUE = True

# File upload settings
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

# Cleanup settings
CLEANUP_AFTER_HOURS = 24  # Delete generated videos after 24 hours

# Remote GPU Configuration
# Set USE_REMOTE_GPU to True to use remote GPU service instead of local
USE_REMOTE_GPU = os.environ.get("USE_REMOTE_GPU", "true").lower() == "true"

# GPU service endpoint (when USE_REMOTE_GPU is True)
# Example: "http://your-lambda-instance:8001" or "http://192.168.1.100:8001"
GPU_SERVICE_URL = os.environ.get("GPU_SERVICE_URL", "http://localhost:8001")

# Optional API key for GPU service authentication
GPU_API_KEY = os.environ.get("GPU_API_KEY", None)
