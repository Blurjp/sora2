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
