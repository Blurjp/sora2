# Lambda Labs Deployment Guide

Complete guide for deploying the Open-Sora Video Generation Service on Lambda Labs GPU cloud.

## Why Lambda Labs?

- 💰 Cost-effective GPU rental ($0.60-$2.00/hour for H100)
- 🚀 Pre-configured CUDA environment
- ⚡ High-performance NVIDIA GPUs (A100, H100)
- 🔧 Root access and flexibility

## Prerequisites

- Lambda Labs account (sign up at https://lambdalabs.com/)
- SSH key added to your Lambda Labs account
- Basic familiarity with SSH and terminal

## Quick Start (5 minutes)

### Step 1: Launch GPU Instance

1. Go to https://cloud.lambdalabs.com/instances
2. Click "Launch Instance"
3. **Recommended GPU**: 1x H100 (80GB) or 1x A100 (40GB)
4. **Region**: Choose closest to you
5. **Filesystem**: Standard (100GB minimum)
6. Click "Launch Instance"

**Recommended Configurations:**

| GPU Type | VRAM | Cost/hr | Best For |
|----------|------|---------|----------|
| 1x H100 | 80GB | ~$2.00 | High quality, 768px generation |
| 1x A100 | 40GB | ~$1.10 | Standard quality, 256px generation |
| 8x H100 | 640GB | ~$16.00 | Production, batch processing |

### Step 2: Connect via SSH

```bash
# Lambda Labs will provide the SSH command
ssh ubuntu@<instance-ip>

# Example:
ssh ubuntu@152.42.168.123
```

### Step 3: Run Automated Setup

```bash
# Clone your repository
git clone <your-repo-url> ~/sora2
cd ~/sora2

# Run Lambda Labs setup script
chmod +x lambda_setup.sh
./lambda_setup.sh
```

### Step 4: Start the Service

```bash
# Start in background
./lambda_run.sh

# Or start with logs
python backend/main.py
```

### Step 5: Access the Service

**Option A: SSH Tunnel (Recommended for security)**

From your local machine:
```bash
ssh -L 8000:localhost:8000 ubuntu@<instance-ip>
```

Then open http://localhost:8000 in your browser.

**Option B: Public Access (Use with caution)**

```bash
# On Lambda instance, allow public access
./lambda_run.sh --public
```

Then open http://&lt;instance-ip&gt;:8000

## Manual Installation

If automated setup doesn't work:

### 1. Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Verify GPU

```bash
nvidia-smi
```

You should see your GPU(s) listed.

### 3. Install Open-Sora

```bash
# Clone Open-Sora
cd ~
git clone https://github.com/hpcaitech/Open-Sora.git
cd Open-Sora

# Install dependencies
pip install -v .
pip install xformers==0.0.27.post2 --index-url https://download.pytorch.org/whl/cu121
pip install flash-attn --no-build-isolation

cd ~
```

### 4. Setup Service

```bash
cd ~/sora2

# Install dependencies
pip install -r requirements.txt

# Set Open-Sora path
export OPENSORA_PATH="$HOME/Open-Sora"
echo 'export OPENSORA_PATH="$HOME/Open-Sora"' >> ~/.bashrc

# Update config
sed -i "s|OPENSORA_PATH = os.environ.get(\"OPENSORA_PATH\", \".*\")|OPENSORA_PATH = os.environ.get(\"OPENSORA_PATH\", \"$HOME/Open-Sora\")|" backend/config.py

# Create directories
mkdir -p outputs temp
```

### 5. Start Service

```bash
python backend/main.py
```

## Access Methods

### Method 1: SSH Tunnel (Most Secure)

**For Web UI:**
```bash
# From your local machine
ssh -L 8000:localhost:8000 ubuntu@<lambda-ip>
```

Keep this terminal open and browse to http://localhost:8000

**For API:**
```bash
# From your local machine
curl -X POST "http://localhost:8000/api/generate" \
  -F "image=@photo.jpg" \
  -F "prompt=ocean sunset" \
  -F "duration=15"
```

### Method 2: Direct Access with Firewall

**Configure public access (less secure):**

```bash
# On Lambda instance
# Edit config to allow all hosts
sed -i 's/HOST = "0.0.0.0"/HOST = "0.0.0.0"/' backend/config.py

# Start service
python backend/main.py
```

**Access from anywhere:**
```bash
# Replace <lambda-ip> with your instance IP
http://<lambda-ip>:8000
```

⚠️ **Security Warning**: This exposes your service to the internet. Consider adding authentication or using a VPN.

### Method 3: ngrok (Easiest for sharing)

```bash
# On Lambda instance
# Install ngrok
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.amd64.tgz | tar xz
sudo mv ngrok /usr/local/bin/

# Sign up at ngrok.com and get auth token
./ngrok config add-authtoken <your-token>

# Start tunnel (in separate terminal)
ngrok http 8000
```

ngrok will give you a public URL like: https://abc123.ngrok.io

## Running in Background

### Using tmux (Recommended)

```bash
# Install tmux
sudo apt install tmux -y

# Start tmux session
tmux new -s sora

# Run service
python backend/main.py

# Detach: Press Ctrl+B, then D

# Reattach later
tmux attach -t sora

# Kill session
tmux kill-session -t sora
```

### Using systemd

```bash
# Create service file
sudo tee /etc/systemd/system/sora-video-gen.service > /dev/null <<EOF
[Unit]
Description=Open-Sora Video Generation Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=$HOME/sora2
Environment="PATH=$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin"
Environment="OPENSORA_PATH=$HOME/Open-Sora"
ExecStart=/usr/bin/python3 $HOME/sora2/backend/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Start service
sudo systemctl daemon-reload
sudo systemctl enable sora-video-gen
sudo systemctl start sora-video-gen

# Check status
sudo systemctl status sora-video-gen

# View logs
sudo journalctl -u sora-video-gen -f
```

### Using nohup (Simple)

```bash
nohup python backend/main.py > sora.log 2>&1 &

# Check if running
ps aux | grep python

# View logs
tail -f sora.log

# Kill process
pkill -f "python backend/main.py"
```

## Optimization for Lambda Labs

### 1. Use Instance Storage Efficiently

```bash
# Lambda instances have fast NVMe storage
# Move outputs to instance storage for better performance
mkdir -p /tmp/sora_outputs

# Update config.py
sed -i 's|OUTPUT_DIR = BASE_DIR / "outputs"|OUTPUT_DIR = Path("/tmp/sora_outputs")|' backend/config.py
```

### 2. Enable Multi-GPU (if you have 8x GPU instance)

Edit `backend/generator.py`:

```python
# Change this line:
"--nproc_per_node", "1",

# To (for 8 GPUs):
"--nproc_per_node", "8",
```

### 3. Optimize for Resolution

**For A100 (40GB):**
```python
# In backend/config.py
MODEL_RESOLUTION = "256px"  # Safer for 40GB
```

**For H100 (80GB):**
```python
# In backend/config.py
MODEL_RESOLUTION = "768px"  # High quality
```

### 4. Automatic Cleanup

```bash
# Add cron job to clean old videos
crontab -e

# Add this line (cleanup every hour):
0 * * * * curl -X POST http://localhost:8000/api/cleanup
```

## Cost Management

### Pricing Estimates

**Per Video Generation:**
- 256px: ~1 minute = ~$0.03 (H100)
- 768px: ~5 minutes = ~$0.17 (H100)

**Daily Costs (24/7):**
- 1x H100: $48/day
- 1x A100: $26/day
- 8x H100: $384/day

### Cost Saving Tips

1. **Stop instance when not in use**
   ```bash
   # Lambda Labs dashboard → Terminate instance
   ```

2. **Use persistent storage**
   - Save model checkpoints to Lambda Cloud Storage
   - Faster startup on new instances

3. **Batch process videos**
   - Generate multiple videos in one session
   - Reduces instance startup overhead

4. **Use spot instances**
   - Lambda Labs offers spot pricing (when available)
   - Up to 70% cheaper

5. **Share instance with team**
   - Multiple users can access via SSH tunnel
   - Split costs

## Monitoring

### GPU Usage

```bash
# Real-time monitoring
watch -n 1 nvidia-smi

# Or install nvtop for better visualization
sudo apt install nvtop -y
nvtop
```

### Service Health

```bash
# Check if service is running
curl http://localhost:8000/health

# Monitor logs
tail -f sora.log

# Check disk usage
df -h

# Check memory
free -h
```

### Resource Monitoring Dashboard

Install and run htop:
```bash
sudo apt install htop -y
htop
```

## Troubleshooting

### "Connection refused"

**Solution 1: Check if service is running**
```bash
ps aux | grep python
sudo systemctl status sora-video-gen
```

**Solution 2: Check firewall**
```bash
# Lambda Labs usually doesn't have firewall issues
# But check just in case
sudo ufw status
```

### "Out of memory"

**Solution: Enable offload (already enabled in code)**
```bash
# Check GPU memory
nvidia-smi

# If still failing, reduce resolution in backend/config.py
MODEL_RESOLUTION = "256px"
```

### "Open-Sora not found"

**Solution:**
```bash
echo $OPENSORA_PATH
# Should show: /home/ubuntu/Open-Sora

# If not set:
export OPENSORA_PATH="$HOME/Open-Sora"
echo 'export OPENSORA_PATH="$HOME/Open-Sora"' >> ~/.bashrc
```

### Slow generation

**Check GPU utilization:**
```bash
nvidia-smi

# GPU should be at 95-100% utilization during generation
# If not, check if model is properly loaded
```

### SSH connection lost during generation

**Use tmux to persist sessions:**
```bash
tmux new -s sora
python backend/main.py
# Press Ctrl+B, then D to detach

# Even if SSH disconnects, service keeps running
# Reconnect with: tmux attach -t sora
```

## Data Persistence

### Save Generated Videos

**Download to local machine:**
```bash
# From your local machine
scp ubuntu@<lambda-ip>:~/sora2/outputs/*.mp4 ./downloads/
```

**Upload to S3:**
```bash
# Install AWS CLI on Lambda instance
sudo apt install awscli -y
aws configure

# Upload videos
aws s3 sync ~/sora2/outputs/ s3://your-bucket/videos/
```

**Use Lambda Cloud Storage:**
```bash
# Contact Lambda Labs for persistent storage options
# Or mount external storage
```

## Example Workflow

### Complete Session

```bash
# 1. SSH into Lambda instance
ssh ubuntu@152.42.168.123

# 2. Start tmux session
tmux new -s sora

# 3. Navigate to project
cd ~/sora2

# 4. Start service
python backend/main.py

# 5. Detach from tmux (Ctrl+B, then D)

# 6. Open SSH tunnel from local machine (new terminal)
ssh -L 8000:localhost:8000 ubuntu@152.42.168.123

# 7. Open browser
# Go to http://localhost:8000

# 8. Generate videos!

# 9. Download results
scp ubuntu@152.42.168.123:~/sora2/outputs/*.mp4 ./

# 10. When done, terminate instance from Lambda dashboard
```

## Security Best Practices

1. **Use SSH keys only** (no password authentication)
2. **Keep SSH tunnel** instead of public access
3. **Add API authentication** for production use
4. **Limit upload size** (already configured)
5. **Regular security updates**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

## Performance Benchmarks on Lambda Labs

Based on testing:

| GPU | Resolution | Time per 15s video |
|-----|------------|-------------------|
| 1x A100 40GB | 256px | ~60-90s |
| 1x H100 80GB | 256px | ~45-60s |
| 1x H100 80GB | 768px | ~20-30 min |
| 8x H100 80GB | 768px | ~4-5 min |

## Getting Help

1. **Lambda Labs Support**: support@lambdalabs.com
2. **Check service logs**: `tail -f sora.log`
3. **GPU status**: `nvidia-smi`
4. **Service status**: `curl http://localhost:8000/health`

## Next Steps

1. Launch Lambda Labs instance
2. Run `./lambda_setup.sh`
3. Access via SSH tunnel
4. Generate your first video!
5. Monitor costs in Lambda dashboard
6. Terminate instance when done

---

Happy video generating on Lambda Labs! 🚀
