# WAN 2.2 Video Generation Service

A web-based service for generating high-quality videos using Alibaba's WAN 2.2 model, with image and text input.

## Features

- Generate high-quality 720P videos (up to 5 seconds at 16fps)
- Image-to-Video (I2V) generation with reference image
- Text-to-Video (T2V) generation
- Simple web interface
- Direct video download
- Diffusers integration for easy deployment

## Model Options

| Model | Parameters | VRAM Required | Resolution | Best For |
|-------|------------|---------------|------------|----------|
| **I2V-A14B** | 14B (MoE) | 80GB | 1280x720 | H100, A100 enterprise GPUs |
| **TI2V-5B** | 5B | 24GB | 1280x704 | RTX 4090, consumer GPUs |

## Architecture

- **Backend**: FastAPI (Python)
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Model**: WAN 2.2 via HuggingFace Diffusers

## Prerequisites

- Python 3.10+
- CUDA-compatible GPU
  - 80GB+ VRAM for I2V-A14B (recommended)
  - 24GB+ VRAM for TI2V-5B
- PyTorch >= 2.4.0

## Quick Start

### Option 1: Remote GPU (Recommended)

Run frontend locally, use remote GPU for generation:

```bash
# On GPU instance (Lambda Labs, etc.)
./gpu_setup.sh
sudo systemctl start wan-gpu

# On your local machine
./run_local.sh --gpu-url http://gpu-instance-ip:8001

# Open browser
http://localhost:8000
```

### Option 2: All-in-One Setup

Run everything on a single GPU instance:

```bash
# SSH into GPU instance
ssh ubuntu@<instance-ip>

# Clone and setup
git clone https://github.com/Blurjp/sora2.git ~/sora2
cd ~/sora2
./gpu_setup.sh

# Start service
sudo systemctl start wan-gpu
```

### Option 3: Local Installation

```bash
# Clone repository
git clone https://github.com/Blurjp/sora2.git
cd sora2

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env to set WAN_MODEL_ID based on your GPU

# Start service
python -m gpu_service.main
```

## Configuration

Edit `.env` or set environment variables:

```bash
# Model selection (based on GPU VRAM)
WAN_MODEL_ID=Wan-AI/Wan2.2-I2V-A14B-Diffusers  # 80GB VRAM
# WAN_MODEL_ID=Wan-AI/Wan2.2-TI2V-5B-Diffusers  # 24GB VRAM

# Quality settings
DEFAULT_NUM_STEPS=40          # Diffusion steps (20-100)
DEFAULT_GUIDANCE=5.0          # Text guidance (1.0-15.0)
DEFAULT_GUIDANCE_IMG=3.5      # Image guidance (0.5-10.0)

# Memory optimization (for low VRAM)
WAN_ENABLE_MODEL_CPU_OFFLOAD=false
WAN_ENABLE_VAE_SLICING=true
```

## API Endpoints

### Generate Video

```bash
POST /api/generate
Content-Type: multipart/form-data

Parameters:
- image: File (required for I2V)
- prompt: string (required)
- duration: integer (3-10, default: 5)
- aspect_ratio: string (default: "16:9")
- num_steps: integer (default: 40)
- guidance: float (default: 5.0)

Response:
{
  "video_id": "uuid",
  "status": "processing"
}
```

### Check Status

```bash
GET /api/status/{video_id}

Response:
{
  "status": "completed",
  "video_url": "/api/download/{video_id}"
}
```

### Download Video

```bash
GET /api/download/{video_id}
```

## Performance

| Model | GPU | Generation Time (5s video) |
|-------|-----|---------------------------|
| I2V-A14B | H100 80GB | ~2-3 minutes |
| TI2V-5B | RTX 4090 | ~5-8 minutes |

**Note**: First run downloads the model (~30-60GB) from HuggingFace.

## Memory Optimization

For GPUs with limited VRAM:

```bash
# Enable CPU offloading
WAN_ENABLE_MODEL_CPU_OFFLOAD=true

# Enable VAE optimizations
WAN_ENABLE_VAE_SLICING=true
WAN_ENABLE_VAE_TILING=true
```

## Troubleshooting

### Out of Memory

1. Switch to TI2V-5B model (requires only 24GB)
2. Enable `WAN_ENABLE_MODEL_CPU_OFFLOAD=true`
3. Reduce `num_frames` or resolution

### Model Download Issues

Models are downloaded automatically from HuggingFace. If you experience issues:
- Check your internet connection
- Set `HF_HUB_OFFLINE=1` after initial download
- Use `huggingface-cli download` manually

### Slow Generation

- Use I2V-A14B on H100 for fastest results
- Reduce `num_steps` (40 is usually sufficient)
- Ensure VAE slicing is enabled

## License

This service wrapper is provided as-is. WAN 2.2 is licensed under Apache 2.0.

## Credits

- [WAN Video Models](https://github.com/Wan-Video/Wan2.2) by Alibaba
- [HuggingFace Diffusers](https://huggingface.co/docs/diffusers)

## Sources

- [WAN 2.2 GitHub](https://github.com/Wan-Video/Wan2.2)
- [WAN 2.2 I2V-A14B on HuggingFace](https://huggingface.co/Wan-AI/Wan2.2-I2V-A14B-Diffusers)
- [WAN 2.2 TI2V-5B on HuggingFace](https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B-Diffusers)
- [Diffusers WAN Documentation](https://huggingface.co/docs/diffusers/main/api/pipelines/wan)
