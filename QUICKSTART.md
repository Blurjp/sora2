# Quick Start Guide

Get your Open-Sora video generation service running in minutes!

## Prerequisites Check

Before starting, ensure you have:

- ✅ Python 3.10 or higher
- ✅ CUDA-compatible GPU (NVIDIA H100/H800 recommended)
- ✅ 40GB+ GPU VRAM
- ✅ CUDA drivers installed
- ✅ Git

## Installation (5 minutes)

### Step 1: Install Open-Sora

```bash
# Clone Open-Sora repository
git clone https://github.com/hpcaitech/Open-Sora.git
cd Open-Sora

# Install dependencies
pip install -v .
pip install xformers==0.0.27.post2 --index-url https://download.pytorch.org/whl/cu121
pip install flash-attn --no-build-isolation

cd ..
```

### Step 2: Install Service

```bash
# Clone this repository
cd sora2

# Set Open-Sora path
export OPENSORA_PATH="/path/to/Open-Sora"

# Run automated setup
chmod +x setup.sh run.sh
./setup.sh
```

### Step 3: Start the Service

```bash
./run.sh
```

That's it! Open http://localhost:8000 in your browser.

## Manual Installation

If the automated setup doesn't work:

### 1. Install Service Dependencies

```bash
pip install fastapi uvicorn python-multipart aiofiles pydantic pillow
```

### 2. Configure Open-Sora Path

Edit `backend/config.py`:

```python
OPENSORA_PATH = "/path/to/your/Open-Sora"
```

### 3. Create Directories

```bash
mkdir -p outputs temp
```

### 4. Start Server

```bash
python backend/main.py
```

## First Video Generation

### Using the Web Interface

1. Open http://localhost:8000
2. Upload an image (PNG, JPG, or WEBP)
3. Enter a text prompt (e.g., "ocean waves crashing on a beach at sunset")
4. Set duration (10-20 seconds)
5. Choose aspect ratio (16:9 recommended)
6. Click "Generate Video"
7. Wait 1-5 minutes (depending on your GPU)
8. Download your video!

### Using the API

```bash
# Generate video
curl -X POST "http://localhost:8000/api/generate" \
  -F "image=@/path/to/image.jpg" \
  -F "prompt=ocean waves at sunset" \
  -F "duration=15" \
  -F "aspect_ratio=16:9" \
  -F "motion_score=0.5"

# Response: {"video_id": "abc-123", "status": "processing"}

# Check status
curl "http://localhost:8000/api/status/abc-123"

# Download when complete
curl "http://localhost:8000/api/download/abc-123" -o video.mp4
```

## Configuration

### Change Resolution

Edit `backend/config.py`:

```python
# For higher quality (but slower)
MODEL_RESOLUTION = "768px"

# For faster generation (lower quality)
MODEL_RESOLUTION = "256px"
```

### Adjust Performance

```python
# Maximum concurrent video generations
MAX_CONCURRENT_JOBS = 2  # Increase if you have multiple GPUs

# Enable job queuing
ENABLE_QUEUE = True
```

### Change Server Port

```python
PORT = 8000  # Change to your preferred port
```

## Common Issues

### "Open-Sora not found"

**Solution:** Set the OPENSORA_PATH environment variable:

```bash
export OPENSORA_PATH="/path/to/Open-Sora"
```

Or update `backend/config.py`.

### "Out of memory"

**Solution:** The service automatically uses `--offload True`. If still failing:

1. Close other applications using GPU
2. Use 256px resolution instead of 768px
3. Reduce `MAX_CONCURRENT_JOBS` to 1

### "Generation is slow"

**Solutions:**

1. **Use multiple GPUs:** Edit `backend/generator.py`:
   ```python
   "--nproc_per_node", "8",  # Number of GPUs
   ```

2. **Use lower resolution:** Change to 256px in config

3. **Check GPU usage:**
   ```bash
   nvidia-smi
   ```

### "Connection refused"

**Solutions:**

1. Check if service is running:
   ```bash
   ps aux | grep python
   ```

2. Check logs:
   ```bash
   python backend/main.py
   ```

3. Try different port in `backend/config.py`

## Video Generation Tips

### Best Prompts

Good prompts are:
- **Descriptive:** "a serene mountain lake at dawn with mist"
- **Specific:** Include details about lighting, weather, movement
- **Focused:** Describe one main scene or action

Avoid:
- ❌ Too vague: "nice video"
- ❌ Too complex: Multiple scenes or rapid changes
- ❌ Too long: Keep under 200 characters for best results

### Best Input Images

For optimal results:
- ✅ High resolution (1024x1024 or higher)
- ✅ Clear subject
- ✅ Good lighting
- ✅ Relevant to your prompt
- ❌ Avoid: Blurry, dark, or complex images

### Duration Recommendations

- **10-12s:** Quick animations, simple movements
- **13-16s:** Standard scenes with moderate action
- **17-20s:** Complex scenes with multiple elements

### Motion Score

- **0.0-0.3:** Minimal motion (camera pans, subtle movement)
- **0.4-0.6:** Moderate motion (people walking, flowing water)
- **0.7-1.0:** High motion (action scenes, fast movement)

### Aspect Ratios

- **16:9:** YouTube, landscape videos, general purpose
- **9:16:** Instagram Stories, TikTok, mobile
- **1:1:** Instagram feed, square videos
- **2.39:1:** Cinematic, movie-style videos

## Performance Benchmarks

Based on Open-Sora 2.0 documentation:

| Resolution | GPU        | Single GPU | 8 GPUs |
|------------|------------|------------|--------|
| 256px      | H100/H800  | ~60s       | ~15s   |
| 768px      | H100/H800  | ~1656s     | ~276s  |

## Next Steps

- Read [README.md](README.md) for detailed API documentation
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for production setup
- Explore configuration options in `backend/config.py`
- Monitor generation with `nvidia-smi`

## Getting Help

1. Check server logs for errors
2. Verify GPU is working: `nvidia-smi`
3. Review [Open-Sora documentation](https://github.com/hpcaitech/Open-Sora)
4. Check configuration in `backend/config.py`

## Example Workflow

```bash
# Terminal 1: Start service
./run.sh

# Terminal 2: Monitor GPU
watch -n 1 nvidia-smi

# Terminal 3: Generate video
curl -X POST "http://localhost:8000/api/generate" \
  -F "image=@sample.jpg" \
  -F "prompt=peaceful forest with sunlight filtering through trees" \
  -F "duration=15"
```

---

Happy video generating! 🎬
