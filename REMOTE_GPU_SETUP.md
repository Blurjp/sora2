## Remote GPU Setup Guide

This guide explains how to run the frontend and backend locally while using a remote GPU instance (e.g., Lambda Labs) for video generation.

## Architecture

```
┌──────────────────────┐         ┌─────────────────────────┐
│  Local Machine       │         │  Lambda GPU Instance    │
│  ┌────────────────┐  │         │                         │
│  │   Frontend     │  │         │  ┌──────────────────┐   │
│  │   (Browser)    │  │         │  │  GPU Service     │   │
│  └───────┬────────┘  │         │  │  (Port 8001)     │   │
│          │           │         │  └────────┬─────────┘   │
│  ┌───────▼────────┐  │  HTTP   │           │             │
│  │   Backend      │  │────────►│  ┌────────▼─────────┐   │
│  │   (Port 8000)  │  │         │  │   Open-Sora      │   │
│  └────────────────┘  │         │  │   (torchrun)     │   │
└──────────────────────┘         └──┴──────────────────┴───┘
```

## Benefits

- ✅ Run frontend/backend on any machine (no GPU required locally)
- ✅ Pay for GPU only when generating videos
- ✅ Easy to spin up/down GPU instances
- ✅ Keep your data and UI local
- ✅ Support multiple GPU endpoints for redundancy

## Setup Instructions

### Step 1: Set Up GPU Service on Lambda Labs

1. **Launch a Lambda Labs GPU instance**
   ```bash
   # Recommended: 1x A100 (40GB) or H100
   # Visit https://cloud.lambdalabs.com
   ```

2. **SSH into the instance**
   ```bash
   ssh ubuntu@<your-lambda-ip>
   ```

3. **Clone and setup**
   ```bash
   git clone <your-repo-url> ~/sora2
   cd ~/sora2
   ./lambda_setup.sh
   ```

4. **Start the GPU service**
   ```bash
   # With API key (recommended)
   ./lambda_run_gpu_service.sh --api-key your-secret-key

   # Without API key (testing only)
   ./lambda_run_gpu_service.sh
   ```

   The GPU service will start on port 8001 and display:
   ```
   Service will be accessible at:
     http://<lambda-ip>:8001
   ```

5. **Keep it running**
   ```bash
   # Option 1: Run in tmux (recommended)
   tmux new -s gpu
   ./lambda_run_gpu_service.sh --api-key your-secret-key
   # Press Ctrl+B then D to detach

   # Option 2: Run as background service
   nohup ./lambda_run_gpu_service.sh --api-key your-secret-key > gpu_service.log 2>&1 &
   ```

### Step 2: Run Backend Locally

On your local machine:

1. **Install dependencies**
   ```bash
   cd /path/to/sora2
   pip install -r requirements.txt
   ```

2. **Start the local backend**

   **Linux/Mac:**
   ```bash
   ./run_local.sh --gpu-url http://<lambda-ip>:8001 --api-key your-secret-key
   ```

   **Windows:**
   ```cmd
   set GPU_SERVICE_URL=http://<lambda-ip>:8001
   set GPU_API_KEY=your-secret-key
   run_local.bat
   ```

3. **Open your browser**
   ```
   http://localhost:8000
   ```

## Configuration

### Environment Variables

**GPU Service (on Lambda):**
```bash
export OPENSORA_PATH=/path/to/Open-Sora
export HOST=0.0.0.0
export PORT=8001
export GPU_API_KEY=your-secret-key  # Optional but recommended
```

**Local Backend:**
```bash
export USE_REMOTE_GPU=true
export GPU_SERVICE_URL=http://lambda-ip:8001
export GPU_API_KEY=your-secret-key  # Must match GPU service
export HOST=127.0.0.1
export PORT=8000
```

### Security Recommendations

1. **Always use API keys in production**
   ```bash
   # Generate a strong key
   openssl rand -hex 32

   # Use it on both sides
   ./lambda_run_gpu_service.sh --api-key <generated-key>
   ./run_local.sh --gpu-url http://... --api-key <generated-key>
   ```

2. **Configure Lambda Labs firewall**
   - Only allow your IP address to access port 8001
   - Or use SSH tunnel for extra security:
     ```bash
     # Create tunnel
     ssh -L 8001:localhost:8001 ubuntu@<lambda-ip>

     # Then use localhost URL
     ./run_local.sh --gpu-url http://localhost:8001 --api-key your-key
     ```

3. **Use HTTPS in production**
   - Put GPU service behind nginx with SSL
   - See [DEPLOYMENT.md](DEPLOYMENT.md) for details

## Testing the Setup

1. **Check GPU service health**
   ```bash
   curl http://<lambda-ip>:8001/api/health
   ```

   Expected response:
   ```json
   {
     "status": "healthy",
     "gpu_busy": false,
     "opensora_path": "/home/ubuntu/Open-Sora",
     "opensora_exists": true
   }
   ```

2. **Generate a test video**
   - Open http://localhost:8000
   - Upload an image
   - Enter a prompt
   - Click "Generate Video"
   - Monitor the progress

3. **Check logs**

   **GPU Service:**
   ```bash
   # If running in tmux
   tmux attach -t gpu

   # If running in background
   tail -f gpu_service.log
   ```

   **Local Backend:**
   - Check console output where you ran `run_local.sh`

## Troubleshooting

### "Connection refused" or "Connection timeout"

1. Check GPU service is running:
   ```bash
   ssh ubuntu@<lambda-ip>
   curl localhost:8001/api/health
   ```

2. Check firewall settings on Lambda Labs dashboard

3. Verify the IP and port are correct

### "Invalid API key"

1. Ensure API keys match on both sides
2. Check for typos or extra spaces
3. Restart both services after changing keys

### "GPU busy" error

- Only one video can be generated at a time
- Wait for current generation to complete
- Check status: `curl http://<lambda-ip>:8001/`

### Slow generation or timeout

1. Check GPU service logs for errors
2. Ensure you have enough VRAM (40GB+ recommended)
3. Increase timeout in `backend/gpu_client.py` if needed

## Cost Optimization

1. **Spin down when not in use**
   ```bash
   # On Lambda instance
   sudo shutdown -h now
   ```

2. **Use on-demand pricing**
   - Lambda Labs charges by the hour
   - Shut down when not generating videos

3. **Monitor usage**
   - Keep track of how long instances run
   - Set up auto-shutdown scripts

## Advanced Configuration

### Multiple GPU Endpoints

You can configure multiple GPU services for load balancing or redundancy.

See `backend/config.py` and modify to support a list of GPU_SERVICE_URLs.

### Custom Ports

**GPU Service:**
```bash
./lambda_run_gpu_service.sh --api-key KEY --port 9000
```

**Local Backend:**
```bash
./run_local.sh --gpu-url http://lambda-ip:9000 --api-key KEY --port 7000
```

### Docker Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for containerized deployment options.

## Next Steps

- [Lambda Labs Quickstart](LAMBDA_QUICKSTART.md) - Quick Lambda setup
- [Deployment Guide](DEPLOYMENT.md) - Production deployment
- [API Documentation](README.md#api-endpoints) - API reference
