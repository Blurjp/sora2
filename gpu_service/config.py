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

# Advanced generation parameters (can be overridden per request or via .env)
DEFAULT_NUM_STEPS = int(os.environ.get("DEFAULT_NUM_STEPS", "120"))  # Diffusion steps (more = better quality but slower)
MIN_NUM_STEPS = 20
MAX_NUM_STEPS = 300  # Increased for INSANE quality mode

DEFAULT_GUIDANCE = float(os.environ.get("DEFAULT_GUIDANCE", "12.0"))  # Text guidance strength
MIN_GUIDANCE = 1.0
MAX_GUIDANCE = 20.0

DEFAULT_GUIDANCE_IMG = float(os.environ.get("DEFAULT_GUIDANCE_IMG", "3.5"))  # Image guidance - face preservation
MIN_GUIDANCE_IMG = 0.5
MAX_GUIDANCE_IMG = 10.0  # Increased for maximum image fidelity

# Model configuration - Use existing inference config
MODEL_CONFIG_PATH = "configs/diffusion/inference/256px.py"

# Checkpoint configuration
# Optional: Override model checkpoint via environment variable
# If not set, the config file's from_pretrained will be used
# Example: CHECKPOINT_PATH=hpcai-tech/OpenSora-STDiT-v3/model.safetensors
CHECKPOINT_PATH = os.environ.get("CHECKPOINT_PATH", None)

# Cleanup settings
CLEANUP_AFTER_HOURS = 24  # Delete generated videos after 24 hours

# Security
API_KEY = os.environ.get("GPU_API_KEY", None)  # Optional API key for auth
