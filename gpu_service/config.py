"""
Configuration for GPU Service (runs on Lambda/remote GPU)
"""
import os
from pathlib import Path

# Open-Sora Installation Path
OPENSORA_PATH = os.environ.get("OPENSORA_PATH", "/path/to/Open-Sora")

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
FRAMES_PER_SECOND = 8

# Model configuration
MODEL_RESOLUTION = "256px"  # or "768px" for higher quality
MODEL_CONFIG_PATH = f"configs/diffusion/inference/{MODEL_RESOLUTION}.py"

# Cleanup settings
CLEANUP_AFTER_HOURS = 24  # Delete generated videos after 24 hours

# Security
API_KEY = os.environ.get("GPU_API_KEY", None)  # Optional API key for auth
