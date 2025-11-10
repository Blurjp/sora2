"""
Configuration for Open-Sora Video Generation Service
"""
import os
from pathlib import Path

# Open-Sora Installation Path
# IMPORTANT: Update this path to your Open-Sora installation directory
OPENSORA_PATH = os.environ.get("OPENSORA_PATH", "/path/to/Open-Sora")

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
DEFAULT_DURATION = 15  # seconds
MIN_DURATION = 10
MAX_DURATION = 20

# Frame calculation: Open-Sora uses 4k+1 formula
# Assuming 8 FPS for longer videos
FRAMES_PER_SECOND = 8

# Supported aspect ratios
ASPECT_RATIOS = ["16:9", "9:16", "1:1", "2.39:1"]

# Model configuration
MODEL_RESOLUTION = "256px"  # or "768px" for higher quality
MODEL_CONFIG_PATH = f"configs/diffusion/inference/{MODEL_RESOLUTION}.py"

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
