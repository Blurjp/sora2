#!/bin/bash

################################################################################
# Complete GPU Instance Setup Script for WAN 2.2 Video Generation Service
# Run this on a fresh Lambda Labs or other GPU instance to set up everything
################################################################################

set -e

echo "=========================================="
echo "WAN 2.2 GPU Instance Complete Setup"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="$HOME/sora2"
SERVICE_PORT="${GPU_SERVICE_PORT:-8001}"

# WAN Model Configuration
# Default to I2V-A14B for H100/A100 GPUs (80GB VRAM)
# Use TI2V-5B for consumer GPUs like RTX 4090 (24GB VRAM)
WAN_MODEL_ID="${WAN_MODEL_ID:-Wan-AI/Wan2.2-I2V-A14B-Diffusers}"

################################################################################
# Step 1: Install Lambda Labs Guest Agent
################################################################################
echo -e "${BLUE}[1/6] Installing Lambda Labs Guest Agent...${NC}"
if curl -L https://lambdalabs-guest-agent.s3.us-west-2.amazonaws.com/scripts/install.sh | sudo bash 2>/dev/null; then
    echo -e "${GREEN}Guest Agent installed${NC}"
else
    echo -e "${YELLOW}Guest Agent installation failed (OK if not on Lambda Labs)${NC}"
fi
echo ""

################################################################################
# Step 2: Update system packages
################################################################################
echo -e "${BLUE}[2/6] Updating system packages...${NC}"
sudo apt-get update -qq
sudo apt-get install -y -qq git curl wget ffmpeg python3-pip python3-venv > /dev/null
echo -e "${GREEN}System packages updated${NC}"
echo ""

################################################################################
# Step 3: Check Python and GPU
################################################################################
echo -e "${BLUE}[3/6] Checking Python version...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}Python $PYTHON_VERSION${NC}"

echo -e "${BLUE}Checking GPU...${NC}"
if command -v nvidia-smi &> /dev/null; then
    GPU_INFO=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | head -n1)
    GPU_MEM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -n1)
    echo -e "${GREEN}GPU: $GPU_INFO${NC}"

    # Recommend model based on VRAM
    if [ "$GPU_MEM" -lt 30000 ]; then
        echo -e "${YELLOW}Detected <30GB VRAM. Recommending TI2V-5B model (24GB required)${NC}"
        RECOMMENDED_MODEL="Wan-AI/Wan2.2-TI2V-5B-Diffusers"
    else
        echo -e "${GREEN}Detected 80GB+ VRAM. Using I2V-A14B model for best quality${NC}"
        RECOMMENDED_MODEL="Wan-AI/Wan2.2-I2V-A14B-Diffusers"
    fi
else
    echo -e "${RED}No GPU detected! This service requires CUDA GPU.${NC}"
    exit 1
fi
echo ""

################################################################################
# Step 4: Clone and install service
################################################################################
echo -e "${BLUE}[4/6] Setting up WAN 2.2 video generation service...${NC}"

if [ -d "$PROJECT_DIR" ]; then
    echo -e "${YELLOW}Service already exists at $PROJECT_DIR${NC}"
    cd "$PROJECT_DIR"
    git pull
else
    cd "$HOME"
    git clone https://github.com/Blurjp/sora2.git "$PROJECT_DIR"
    cd "$PROJECT_DIR"
fi

echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install -r requirements.txt -q

# Install additional dependencies for WAN
echo -e "${YELLOW}Installing WAN 2.2 dependencies...${NC}"
pip install torch>=2.4.0 -q
pip install diffusers>=0.32.0 transformers>=4.45.0 accelerate>=0.34.0 -q
pip install sentencepiece imageio imageio-ffmpeg -q

# Create directories
mkdir -p outputs temp gpu_service/outputs gpu_service/temp

echo -e "${GREEN}Service installed at $PROJECT_DIR${NC}"
echo ""

################################################################################
# Step 5: Set environment variables
################################################################################
echo -e "${BLUE}[5/6] Setting environment variables...${NC}"

# Create .env file for GPU service
cat > "$PROJECT_DIR/.env" << EOF
# WAN 2.2 Configuration
WAN_MODEL_ID=${RECOMMENDED_MODEL:-$WAN_MODEL_ID}
WAN_MODEL_VARIANT=720P
WAN_WIDTH=1280
WAN_HEIGHT=720

# GPU Service Configuration
HOST=0.0.0.0
PORT=$SERVICE_PORT

# Quality Settings
DEFAULT_NUM_STEPS=40
DEFAULT_GUIDANCE=5.0
DEFAULT_GUIDANCE_IMG=3.5

# Memory Optimization
WAN_ENABLE_MODEL_CPU_OFFLOAD=false
WAN_ENABLE_VAE_SLICING=true
WAN_ENABLE_VAE_TILING=false
WAN_TORCH_DTYPE=bfloat16

# Performance Settings
PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
TORCH_CUDNN_V8_API_ENABLED=1
CUDA_LAUNCH_BLOCKING=0
CUDNN_BENCHMARK=1
TORCH_ALLOW_TF32=1

# Optional: Set GPU API key for authentication
# GPU_API_KEY=your-secret-key-here
EOF

echo -e "${GREEN}Environment configured${NC}"
echo ""

################################################################################
# Step 6: Create systemd service
################################################################################
echo -e "${BLUE}[6/6] Setting up systemd service...${NC}"

sudo tee /etc/systemd/system/wan-gpu.service > /dev/null << EOF
[Unit]
Description=WAN 2.2 GPU Video Generation Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=/usr/bin/python3 -m gpu_service.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable wan-gpu.service

echo -e "${GREEN}Systemd service created${NC}"
echo ""

################################################################################
# Complete!
################################################################################
echo -e "${GREEN}=========================================="
echo "Setup Complete!"
echo "==========================================${NC}"
echo ""
echo -e "${BLUE}Summary:${NC}"
echo "  - Service installed: $PROJECT_DIR"
echo "  - Model: ${RECOMMENDED_MODEL:-$WAN_MODEL_ID}"
echo "  - GPU Service port: $SERVICE_PORT"
echo ""
echo -e "${BLUE}To start the service:${NC}"
echo ""
echo "  Option 1 - Direct run:"
echo -e "    ${YELLOW}cd $PROJECT_DIR${NC}"
echo -e "    ${YELLOW}python3 -m gpu_service.main${NC}"
echo ""
echo "  Option 2 - Using systemd (recommended):"
echo -e "    ${YELLOW}sudo systemctl start wan-gpu${NC}"
echo -e "    ${YELLOW}sudo systemctl status wan-gpu${NC}"
echo ""
echo "  View logs:"
echo -e "    ${YELLOW}sudo journalctl -u wan-gpu -f${NC}"
echo ""
echo -e "${BLUE}Service will be available at:${NC}"
echo "  http://$(hostname -I | awk '{print $1}'):$SERVICE_PORT"
echo ""
echo -e "${BLUE}WAN 2.2 Model Info:${NC}"
if [[ "${RECOMMENDED_MODEL:-$WAN_MODEL_ID}" == *"TI2V-5B"* ]]; then
    echo "  - Model: TI2V-5B (5B parameters)"
    echo "  - VRAM: ~24GB required"
    echo "  - Resolution: 1280x704 (720P)"
    echo "  - Best for: RTX 4090, consumer GPUs"
else
    echo "  - Model: I2V-A14B (14B parameters, MoE)"
    echo "  - VRAM: ~80GB required"
    echo "  - Resolution: 1280x720 (720P)"
    echo "  - Best for: H100, A100, enterprise GPUs"
fi
echo ""
echo -e "${YELLOW}First run will download the model (~30-60GB) from HuggingFace${NC}"
echo ""
echo -e "${YELLOW}Tip: Use 'sudo systemctl enable wan-gpu' to start on boot${NC}"
echo ""
echo -e "${YELLOW}Monitor GPU: watch -n 1 nvidia-smi${NC}"
echo ""
