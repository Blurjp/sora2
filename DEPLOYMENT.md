# Deployment Guide

This guide covers deployment options for the Open-Sora Video Generation Service.

## Prerequisites

- Linux server with CUDA-compatible GPU
- Docker (optional, for containerized deployment)
- Nginx (optional, for production deployment)
- Domain name (optional)

## Option 1: Local Development

### Quick Start

```bash
# Run setup
chmod +x setup.sh
./setup.sh

# Start service
chmod +x run.sh
./run.sh
```

Access at `http://localhost:8000`

## Option 2: Production Deployment

### 1. System Requirements

**Minimum:**
- GPU: NVIDIA H100/H800 (40GB+ VRAM)
- RAM: 32GB
- Storage: 100GB SSD
- OS: Ubuntu 20.04+

**Recommended:**
- GPU: NVIDIA H100 x8 (for parallel processing)
- RAM: 64GB
- Storage: 500GB SSD

### 2. Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install CUDA drivers
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-keyring_1.0-1_all.deb
sudo dpkg -i cuda-keyring_1.0-1_all.deb
sudo apt-get update
sudo apt-get install -y cuda

# Install Python 3.10
sudo apt install -y python3.10 python3.10-venv python3.10-dev

# Install build tools
sudo apt install -y build-essential git wget
```

### 3. Setup Application

```bash
# Clone repository
git clone <your-repo-url> /opt/sora2
cd /opt/sora2

# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate

# Run setup
./setup.sh
```

### 4. Configure as System Service

Create `/etc/systemd/system/sora-video-gen.service`:

```ini
[Unit]
Description=Open-Sora Video Generation Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/sora2
Environment="PATH=/opt/sora2/venv/bin"
Environment="OPENSORA_PATH=/opt/Open-Sora"
ExecStart=/opt/sora2/venv/bin/python backend/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Start service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable sora-video-gen
sudo systemctl start sora-video-gen
sudo systemctl status sora-video-gen
```

### 5. Setup Nginx Reverse Proxy

Install Nginx:

```bash
sudo apt install -y nginx
```

Create `/etc/nginx/sites-available/sora-video-gen`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts for long video generation
        proxy_read_timeout 600s;
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/sora-video-gen /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 6. Setup SSL (Let's Encrypt)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## Option 3: Docker Deployment

### Dockerfile

```dockerfile
FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04

# Install Python 3.10
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-venv \
    python3-pip \
    git \
    wget \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Clone and install Open-Sora
RUN git clone https://github.com/hpcaitech/Open-Sora.git /opt/Open-Sora
WORKDIR /opt/Open-Sora
RUN pip install -v .
RUN pip install xformers==0.0.27.post2 --index-url https://download.pytorch.org/whl/cu121
RUN pip install flash-attn --no-build-isolation

# Copy application
WORKDIR /app
COPY . .

# Install dependencies
RUN pip install -r requirements.txt

# Set environment variables
ENV OPENSORA_PATH=/opt/Open-Sora
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "backend/main.py"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  sora-video-gen:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./outputs:/app/outputs
      - ./temp:/app/temp
    environment:
      - OPENSORA_PATH=/opt/Open-Sora
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    restart: unless-stopped
```

Build and run:

```bash
docker-compose up -d
```

## Monitoring

### Check Logs

```bash
# Systemd service
sudo journalctl -u sora-video-gen -f

# Docker
docker-compose logs -f
```

### Monitor GPU Usage

```bash
watch -n 1 nvidia-smi
```

### Monitor Disk Space

```bash
df -h
du -sh outputs/
```

## Performance Optimization

### 1. Multi-GPU Setup

Edit `backend/generator.py`:

```python
# Change nproc_per_node to number of GPUs
"--nproc_per_node", "8",  # For 8 GPUs
```

### 2. Memory Optimization

If running out of memory:

```python
# Already enabled in generator.py
"--offload", "True",
```

### 3. Queue Management

Edit `backend/config.py`:

```python
MAX_CONCURRENT_JOBS = 4  # Adjust based on GPU memory
ENABLE_QUEUE = True
```

## Security Considerations

### 1. File Upload Limits

Already configured in `backend/config.py`:

```python
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
```

### 2. Rate Limiting

Install nginx rate limiting:

```nginx
limit_req_zone $binary_remote_addr zone=video_gen:10m rate=10r/m;

location /api/generate {
    limit_req zone=video_gen burst=2;
    # ... rest of config
}
```

### 3. Authentication (Optional)

Add API key authentication in `backend/main.py`:

```python
from fastapi import Header, HTTPException

API_KEY = "your-secret-key"

@app.post("/api/generate")
async def generate_video(
    x_api_key: str = Header(...),
    # ... rest of parameters
):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    # ... rest of function
```

## Troubleshooting

### Out of Memory

- Reduce concurrent jobs
- Enable offload mode
- Use lower resolution (256px instead of 768px)

### Slow Generation

- Use multiple GPUs
- Check GPU utilization with `nvidia-smi`
- Ensure SSD is used for temp files

### Connection Timeout

- Increase nginx timeout values
- Check firewall settings
- Verify GPU is processing

## Backup and Maintenance

### Automated Cleanup

Add cron job:

```bash
0 2 * * * curl -X POST http://localhost:8000/api/cleanup
```

### Database Backup (if you add one)

```bash
0 3 * * * pg_dump video_gen > /backup/video_gen_$(date +\%Y\%m\%d).sql
```

## Scaling

For high traffic:

1. **Load Balancing**: Use multiple instances behind nginx
2. **Queue System**: Implement Redis/RabbitMQ for job queue
3. **Storage**: Use S3/Object storage for generated videos
4. **CDN**: Serve videos through CDN (CloudFlare, AWS CloudFront)

## Support

For issues:
- Check logs first
- Verify GPU is working: `nvidia-smi`
- Check Open-Sora installation
- Review configuration in `backend/config.py`
