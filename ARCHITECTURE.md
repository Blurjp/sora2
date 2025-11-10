# Architecture Overview

## Two Deployment Modes

### Mode 1: Remote GPU (Recommended)

```
┌─────────────────────────────────────────┐
│  Your Local Machine                     │
│  ┌───────────────────────────────────┐  │
│  │  Browser → http://localhost:8000  │  │
│  └──────────────┬────────────────────┘  │
│                 │                        │
│  ┌──────────────▼────────────────────┐  │
│  │  Local Backend (FastAPI)          │  │
│  │  - Serves frontend                │  │
│  │  - Manages jobs/status            │  │
│  │  - Stores generated videos        │  │
│  └──────────────┬────────────────────┘  │
└─────────────────┼────────────────────────┘
                  │ HTTP/HTTPS
                  │
┌─────────────────▼────────────────────────┐
│  Lambda Labs GPU Instance                │
│  ┌────────────────────────────────────┐  │
│  │  GPU Service (FastAPI)             │  │
│  │  - Port 8001                       │  │
│  │  - Video generation only           │  │
│  │  - Optional API key auth           │  │
│  └──────────────┬─────────────────────┘  │
│                 │                        │
│  ┌──────────────▼─────────────────────┐  │
│  │  Open-Sora 2.0                     │  │
│  │  - torchrun                        │  │
│  │  - GPU acceleration                │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

**Files:**
- `gpu_service/` - GPU-only service
- `backend/gpu_client.py` - HTTP client
- `backend/remote_generator.py` - Remote orchestrator
- `run_local.sh` - Start local backend
- `lambda_run_gpu_service.sh` - Start GPU service

**Configuration:**
```bash
export USE_REMOTE_GPU=true
export GPU_SERVICE_URL=http://lambda-ip:8001
export GPU_API_KEY=your-secret-key
```

### Mode 2: All-in-One (Legacy)

```
┌──────────────────────────────────────────┐
│  Lambda GPU Instance                     │
│  ┌────────────────────────────────────┐  │
│  │  Browser → http://instance:8000    │  │
│  └──────────────┬─────────────────────┘  │
│                 │                        │
│  ┌──────────────▼─────────────────────┐  │
│  │  Backend (FastAPI)                 │  │
│  │  - Serves frontend                 │  │
│  │  - Manages generation locally      │  │
│  └──────────────┬─────────────────────┘  │
│                 │                        │
│  ┌──────────────▼─────────────────────┐  │
│  │  Open-Sora 2.0                     │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

**Files:**
- `backend/generator.py` - Local generator
- `lambda_run.sh` - Start all-in-one

**Configuration:**
```bash
export USE_REMOTE_GPU=false
export OPENSORA_PATH=/path/to/Open-Sora
```

## Component Breakdown

### GPU Service (`gpu_service/`)

Lightweight FastAPI service that:
- Accepts video generation requests
- Runs torchrun subprocess
- Returns generated video files
- Cleans up after download

**Endpoints:**
- `POST /api/generate` - Start generation
- `GET /api/status/{id}` - Check status
- `GET /api/download/{id}` - Download video
- `DELETE /api/video/{id}` - Delete video
- `GET /api/health` - Health check

### GPU Client (`backend/gpu_client.py`)

Async HTTP client that:
- Sends generation requests
- Polls for completion
- Downloads results
- Handles errors/retries

**Key Methods:**
- `generate_video()` - Send request
- `check_status()` - Poll status
- `download_video()` - Retrieve file
- `health_check()` - Verify connectivity

### Remote Generator (`backend/remote_generator.py`)

Orchestrator that:
- Manages job state locally
- Proxies to GPU service
- Downloads completed videos
- Provides status to frontend

**Key Methods:**
- `start_generation()` - Initiate remote job
- `is_processing()` - Check if busy
- `get_job_status()` - Return status
- `_generate_and_download()` - Internal workflow

### Local Backend (`backend/main.py`)

FastAPI application that:
- Serves frontend (HTML/CSS/JS)
- Handles file uploads
- Routes to active generator
- Manages output files

**Configuration:**
```python
active_generator = remote_generator if USE_REMOTE_GPU else generator
```

## Request Flow (Remote Mode)

1. **User uploads image + prompt**
   - Browser → Local Backend

2. **Backend validates and forwards**
   - Local Backend → GPU Service (`/api/generate`)

3. **GPU service starts generation**
   - GPU Service → torchrun subprocess
   - Returns video_id immediately

4. **Backend polls for status**
   - Local Backend → GPU Service (`/api/status/{id}`)
   - Every 1 second, max 5 minutes

5. **Download on completion**
   - Local Backend → GPU Service (`/api/download/{id}`)
   - Saves to local `outputs/`

6. **Cleanup GPU service**
   - Local Backend → GPU Service (`/api/video/{id}` DELETE)

7. **Frontend displays result**
   - Browser → Local Backend (`/api/download/{id}`)

## Security

### API Key Authentication

Optional but recommended for GPU service:

```python
# GPU Service
@app.post("/api/generate")
async def generate(
    ...,
    api_key: str = Depends(verify_api_key)
):
    ...

# Client
client = GPUClient(url, api_key="secret")
# Sends: X-API-Key: secret
```

### Network Security

**Recommended setup:**
1. GPU service binds to `0.0.0.0:8001`
2. Lambda firewall restricts to your IP
3. API key required for all requests
4. HTTPS in production (nginx reverse proxy)

**Alternative (SSH tunnel):**
```bash
ssh -L 8001:localhost:8001 ubuntu@lambda-ip
# Then use http://localhost:8001
```

## Performance Characteristics

### Remote GPU Mode

**Latency:**
- Request → GPU: ~50-200ms (network)
- Generation: 60-300s (same as local)
- Download: ~1-5s (video file transfer)

**Benefits:**
- Local machine: minimal CPU/RAM
- GPU instance: pay only when running
- Multiple users can share one GPU

**Trade-offs:**
- Slight network overhead
- Requires stable connection
- Download time for large videos

### Local GPU Mode

**Latency:**
- Request → GPU: ~1-5ms (local)
- Generation: 60-300s
- Download: ~1ms (local filesystem)

**Benefits:**
- No network dependency
- Instant file access
- Simpler deployment

**Trade-offs:**
- Requires local GPU (40GB+ VRAM)
- Higher infrastructure cost
- All components on one machine

## Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_REMOTE_GPU` | `true` | Use remote GPU service |
| `GPU_SERVICE_URL` | `http://localhost:8001` | GPU service endpoint |
| `GPU_API_KEY` | `None` | API key for auth |
| `HOST` | `127.0.0.1` | Local backend bind address |
| `PORT` | `8000` | Local backend port |
| `OPENSORA_PATH` | - | Path to Open-Sora (GPU mode) |

### Files Structure

```
sora2/
├── frontend/              # HTML/CSS/JS
├── backend/               # Local backend
│   ├── main.py           # FastAPI app
│   ├── generator.py      # Local GPU generator
│   ├── remote_generator.py  # Remote orchestrator
│   ├── gpu_client.py     # HTTP client
│   └── config.py         # Configuration
├── gpu_service/          # GPU service
│   ├── main.py           # FastAPI app
│   ├── generator.py      # Video generation
│   └── config.py         # Configuration
├── outputs/              # Generated videos
├── run_local.sh          # Start local backend
└── lambda_run_gpu_service.sh  # Start GPU service
```

## Monitoring & Debugging

### Health Checks

**GPU Service:**
```bash
curl http://lambda-ip:8001/api/health
```

**Local Backend:**
```bash
curl http://localhost:8000/
```

### Logs

**GPU Service:**
```bash
# If running in tmux
tmux attach -t gpu

# If background
tail -f ~/sora2/gpu_service.log
```

**Local Backend:**
```bash
# Console output where run_local.sh was executed
```

### Common Issues

1. **Connection refused**
   - Check GPU service is running
   - Verify firewall settings
   - Confirm IP/port are correct

2. **API key mismatch**
   - Ensure keys match on both sides
   - No spaces or special chars

3. **Generation timeout**
   - Check GPU service logs
   - Increase timeout in `gpu_client.py`
   - Verify VRAM availability

## Future Enhancements

Potential improvements:

1. **Load Balancing**
   - Support multiple GPU endpoints
   - Round-robin or least-busy routing

2. **Queue System**
   - Accept multiple requests
   - Process sequentially

3. **Webhooks**
   - Notify on completion
   - Instead of polling

4. **Caching**
   - Cache similar prompts
   - Reduce redundant generation

5. **WebSocket**
   - Real-time progress updates
   - Better than polling
