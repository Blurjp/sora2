# Quick Start - Remote GPU Mode

Get up and running with remote GPU in 5 minutes!

## What You Need

- A Lambda Labs account (or any GPU cloud provider)
- Your local machine (Windows, Mac, or Linux)
- 5-10 minutes

## Quick Setup

### 1. Launch Lambda GPU Instance (2 minutes)

1. Go to https://cloud.lambdalabs.com
2. Click "Launch Instance"
3. Choose: **1x A100 (40GB)** or **1x A10 (24GB)**
4. Select region
5. Click "Launch"
6. Note the instance IP address

### 2. Setup GPU Service on Lambda (2 minutes)

```bash
# SSH into Lambda instance
ssh ubuntu@<YOUR_LAMBDA_IP>

# Clone and setup (one command!)
git clone https://github.com/YOUR_USERNAME/sora2.git ~/sora2 && \
cd ~/sora2 && \
./lambda_setup.sh

# Start GPU service with API key
./lambda_run_gpu_service.sh --api-key my-secret-key-123
```

✅ GPU service is now running on `http://<LAMBDA_IP>:8001`

### 3. Run Backend Locally (1 minute)

On your local machine:

**Windows:**
```cmd
cd C:\path\to\sora2
pip install -r requirements.txt
set GPU_SERVICE_URL=http://<LAMBDA_IP>:8001
set GPU_API_KEY=my-secret-key-123
run_local.bat
```

**Mac/Linux:**
```bash
cd /path/to/sora2
pip install -r requirements.txt
./run_local.sh --gpu-url http://<LAMBDA_IP>:8001 --api-key my-secret-key-123
```

### 4. Generate Your First Video!

1. Open browser: http://localhost:8000
2. Upload an image
3. Enter prompt: "A serene ocean wave at sunset"
4. Click "Generate Video"
5. Wait 1-3 minutes
6. Download your video!

## That's It!

You're now running Open-Sora with:
- ✅ Frontend/backend on your local machine
- ✅ GPU processing on Lambda Labs
- ✅ Secure API key authentication

## Tips

**Keep GPU Service Running:**
```bash
# Use tmux to keep it alive
tmux new -s gpu
./lambda_run_gpu_service.sh --api-key my-secret-key-123
# Press Ctrl+B then D to detach

# Reattach later
tmux attach -t gpu
```

**Stop Lambda Instance (Save Money!):**
```bash
# When done generating videos
ssh ubuntu@<LAMBDA_IP>
sudo shutdown -h now
```

**Restart Lambda Instance:**
1. Go to Lambda Labs dashboard
2. Start the instance
3. Wait for new IP address
4. Update `GPU_SERVICE_URL` with new IP
5. SSH in and run GPU service again

## Troubleshooting

**Can't connect to GPU service?**
```bash
# Test from Lambda instance itself
ssh ubuntu@<LAMBDA_IP>
curl localhost:8001/api/health

# Should return: {"status":"healthy",...}
```

**"Invalid API key" error?**
- Make sure the key matches on both sides
- No spaces or typos

**Want to change settings?**
- Duration: 10-20 seconds
- Aspect ratio: 16:9, 9:16, 1:1, 2.39:1
- Motion score: 0.0 (static) to 1.0 (dynamic)

## Cost Estimate

Lambda Labs A100 (40GB): ~$1.10/hour
- Start instance: $0
- Generate 5 videos (30 min): ~$0.55
- Shut down: $0
- **Total: Less than $1 for testing!**

## Next Steps

- [Remote GPU Setup Guide](REMOTE_GPU_SETUP.md) - Detailed setup
- [Security Best Practices](REMOTE_GPU_SETUP.md#security-recommendations)
- [API Documentation](README.md#api-endpoints)
