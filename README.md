# Open-Sora 2.0 Video Generation Service

A simple web-based service for generating 10-20 second videos using Open-Sora 2.0, with image and text input.

## Features

- 🎬 Generate high-quality videos (10-20 seconds)
- 🖼️ Image + Text conditioning for better control
- 🚀 Simple web interface
- 📥 Direct video download
- 🔓 No content restrictions

## Architecture

- **Backend**: FastAPI (Python)
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Model**: Open-Sora 2.0 (11B model)

## Prerequisites

- Python 3.10+
- CUDA-compatible GPU (H100/H800 recommended)
- 40GB+ VRAM for optimal performance
- PyTorch >= 2.4.0

## Quick Start Options

### Option 1: Remote GPU (Recommended) ⚡⚡⚡

**NEW: Run frontend & backend locally, use remote GPU for generation!**

This is the most cost-effective and flexible setup:
- ✅ No local GPU required
- ✅ Pay for GPU only when generating
- ✅ Works on Windows, Mac, Linux
- ✅ Quick 5-minute setup

```bash
# On Lambda GPU instance
./lambda_run_gpu_service.sh --api-key your-secret-key

# On your local machine
./run_local.sh --gpu-url http://lambda-ip:8001 --api-key your-secret-key

# Open browser
http://localhost:8000
```

**Complete guide**: See [QUICKSTART_REMOTE.md](QUICKSTART_REMOTE.md) and [REMOTE_GPU_SETUP.md](REMOTE_GPU_SETUP.md)

### Option 2: All-in-One Lambda Instance

Run everything (frontend + backend + GPU) on a single Lambda instance.

```bash
# 1. Launch instance at https://cloud.lambdalabs.com
# 2. SSH into instance
ssh ubuntu@<instance-ip>

# 3. Run automated setup
git clone <your-repo-url> ~/sora2
cd ~/sora2
./lambda_setup.sh

# 4. Start service
./lambda_run.sh
```

**Complete guide**: See [LAMBDA_LABS.md](LAMBDA_LABS.md)

### Option 3: Local Installation

For local GPU servers or other cloud providers.

## Installation

### 1. Clone Open-Sora Repository

```bash
git clone https://github.com/hpcaitech/Open-Sora.git
cd Open-Sora
pip install -v .
pip install xformers==0.0.27.post2 --index-url https://download.pytorch.org/whl/cu121
pip install flash-attn --no-build-isolation
```

### 2. Install Service Dependencies

```bash
cd /path/to/sora2
pip install -r requirements.txt
```

### 3. Configure Open-Sora Path

Edit `backend/config.py` and set the `OPENSORA_PATH` to your Open-Sora installation directory.

## Usage

### Start the Service

```bash
# From the project root
python backend/main.py
```

The service will start on `http://localhost:8000`

### Using the Web Interface

1. Open `http://localhost:8000` in your browser
2. Upload an input image (PNG/JPG)
3. Enter your text prompt
4. Configure video settings:
   - Duration (10-20 seconds)
   - Aspect ratio (16:9, 9:16, 1:1, 2.39:1)
   - Motion intensity
5. Click "Generate Video"
6. Wait for generation (1-5 minutes depending on GPU)
7. Preview and download your video

### API Endpoints

#### Generate Video

```bash
POST /api/generate
Content-Type: multipart/form-data

Parameters:
- image: File (required)
- prompt: string (required)
- duration: integer (10-20, default: 15)
- aspect_ratio: string (default: "16:9")
- motion_score: float (0.0-1.0, default: 0.5)

Response:
{
  "video_id": "uuid",
  "status": "processing"
}
```

#### Check Status

```bash
GET /api/status/{video_id}

Response:
{
  "status": "completed",
  "video_url": "/api/download/{video_id}"
}
```

#### Download Video

```bash
GET /api/download/{video_id}
```

## Configuration

Edit `backend/config.py`:

```python
OPENSORA_PATH = "/path/to/Open-Sora"
OUTPUT_DIR = "./outputs"
MAX_CONCURRENT_JOBS = 2
ENABLE_QUEUE = True
```

## Performance Notes

- **256px**: ~60 seconds on single H100/H800
- **768px**: ~276 seconds with 8 GPUs
- Use `--offload True` for memory optimization on GPUs with <40GB VRAM

## Deployment Options

- **Lambda Labs** (Recommended): See [LAMBDA_LABS.md](LAMBDA_LABS.md) - Quick 5-minute setup
- **Docker**: See [DEPLOYMENT.md](DEPLOYMENT.md#option-3-docker-deployment)
- **Production**: See [DEPLOYMENT.md](DEPLOYMENT.md) for systemd, nginx, SSL setup

## Troubleshooting

### Out of Memory

Add `--offload True` to the generation command in `backend/generator.py`

### Slow Generation

- Use multiple GPUs with `--nproc_per_node`
- Reduce resolution or frame count
- Enable sequence parallelism

### Model Download Issues

Models are downloaded automatically from HuggingFace. If you experience issues:
- Use ModelScope mirror (Chinese users)
- Download manually and update config paths

## License

This service wrapper is provided as-is. Open-Sora 2.0 is licensed under Apache 2.0.

## Credits

- [Open-Sora](https://github.com/hpcaitech/Open-Sora) by HPC-AI Tech
