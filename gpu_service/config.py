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

# Model configuration - Use STDiT v3 config
MODEL_CONFIG_PATH = "configs/opensora/stdit_v3.yaml"

# Checkpoint configuration
# Use Hugging Face Hub repo ID (without filename)
CHECKPOINT_PATH = os.environ.get("CHECKPOINT_PATH", "hpcai-tech/OpenSora-STDiT-v3")

# Cleanup settings
CLEANUP_AFTER_HOURS = 24  # Delete generated videos after 24 hours

# Security
API_KEY = os.environ.get("GPU_API_KEY", None)  # Optional API key for auth
