#!/bin/bash

################################################################################
# Complete GPU Instance Setup Script for Open-Sora Video Generation Service
# Run this on a fresh Lambda Labs or other GPU instance to set up everything
################################################################################

set -e

echo "=========================================="
echo "🚀 Open-Sora GPU Instance Complete Setup"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
OPENSORA_PATH="${OPENSORA_PATH:-$HOME/Open-Sora}"
PROJECT_DIR="$HOME/sora2"
SERVICE_PORT="${GPU_SERVICE_PORT:-8001}"

################################################################################
# Step 1: Install Lambda Labs Guest Agent
################################################################################
echo -e "${BLUE}[1/8] Installing Lambda Labs Guest Agent...${NC}"
if curl -L https://lambdalabs-guest-agent.s3.us-west-2.amazonaws.com/scripts/install.sh | sudo bash 2>/dev/null; then
    echo -e "${GREEN}✅ Lambda Labs Guest Agent installed${NC}"
else
    echo -e "${YELLOW}⚠️  Lambda Labs Guest Agent installation failed (OK if not on Lambda Labs)${NC}"
fi
echo ""

################################################################################
# Step 2: Update system packages
################################################################################
echo -e "${BLUE}[2/8] Updating system packages...${NC}"
sudo apt-get update -qq
sudo apt-get install -y -qq git curl wget ffmpeg python3-pip python3-venv > /dev/null
echo -e "${GREEN}✅ System packages updated${NC}"
echo ""

################################################################################
# Step 3: Check Python and GPU
################################################################################
echo -e "${BLUE}[3/8] Checking Python version...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✅ Python $PYTHON_VERSION${NC}"

echo -e "${BLUE}Checking GPU...${NC}"
if command -v nvidia-smi &> /dev/null; then
    GPU_INFO=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | head -n1)
    echo -e "${GREEN}✅ GPU: $GPU_INFO${NC}"
else
    echo -e "${RED}❌ No GPU detected! This service requires CUDA GPU.${NC}"
    exit 1
fi
echo ""

################################################################################
# Step 4: Clone and install Open-Sora
################################################################################
echo -e "${BLUE}[4/8] Setting up Open-Sora...${NC}"

if [ -d "$OPENSORA_PATH" ]; then
    echo -e "${YELLOW}⚠️  Open-Sora already exists at $OPENSORA_PATH${NC}"
    echo -e "${YELLOW}Updating repository...${NC}"
    cd "$OPENSORA_PATH"
    git pull
else
    echo -e "${YELLOW}Cloning Open-Sora repository...${NC}"
    git clone https://github.com/hpcaitech/Open-Sora.git "$OPENSORA_PATH"
    cd "$OPENSORA_PATH"
fi

echo -e "${YELLOW}Installing Open-Sora dependencies...${NC}"
pip install -v . -q
pip install xformers==0.0.27.post2 --index-url https://download.pytorch.org/whl/cu121 -q
pip install flash-attn --no-build-isolation -q

echo -e "${GREEN}✅ Open-Sora installed at $OPENSORA_PATH${NC}"
echo ""

################################################################################
# Step 5: Clone video generation service
################################################################################
echo -e "${BLUE}[5/8] Setting up video generation service...${NC}"

if [ -d "$PROJECT_DIR" ]; then
    echo -e "${YELLOW}⚠️  Service already exists at $PROJECT_DIR${NC}"
    cd "$PROJECT_DIR"
    git pull
else
    cd "$HOME"
    git clone https://github.com/Blurjp/sora2.git "$PROJECT_DIR"
    cd "$PROJECT_DIR"
fi

echo -e "${YELLOW}Installing service dependencies...${NC}"
pip install -r requirements.txt -q

# Create directories
mkdir -p outputs temp gpu_service/outputs gpu_service/temp

echo -e "${GREEN}✅ Service installed at $PROJECT_DIR${NC}"
echo ""

################################################################################
# Step 6: Fix Open-Sora configuration automatically
################################################################################
echo -e "${BLUE}[6/8] Optimizing Open-Sora configuration for quality...${NC}"

CONFIG_FILE="$OPENSORA_PATH/configs/diffusion/inference/256px.py"

if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}❌ Config file not found: $CONFIG_FILE${NC}"
    exit 1
fi

# Backup original config
BACKUP_FILE="$CONFIG_FILE.backup_$(date +%s)"
cp "$CONFIG_FILE" "$BACKUP_FILE"
echo -e "${YELLOW}Backup created: $(basename $BACKUP_FILE)${NC}"

# Apply all quality optimizations
python3 << 'PYTHON_SCRIPT'
import re

config_file = "$CONFIG_FILE"
with open(config_file.replace("$OPENSORA_PATH", "$OPENSORA_PATH"), 'r') as f:
    content = f.read()

original = content
fixes = []

# Fix 1: FPS (match generation rate)
if re.search(r'fps_save\s*=\s*([0-9]+)', content):
    old = re.search(r'fps_save\s*=\s*([0-9]+)', content).group(1)
    if int(old) != 8:
        content = re.sub(r'fps_save\s*=\s*[0-9]+', 'fps_save=8', content)
        fixes.append(f"fps_save: {old} → 8")

# Fix 2: Image guidance (STRONG face preservation)
if re.search(r'guidance_img\s*=\s*([0-9.]+)', content):
    old = re.search(r'guidance_img\s*=\s*([0-9.]+)', content).group(1)
    if float(old) != 3.5:
        content = re.sub(r'guidance_img\s*=\s*[0-9.]+', 'guidance_img=3.5', content)
        fixes.append(f"guidance_img: {old} → 3.5 (STRONG face preservation)")

# Fix 3: Text guidance (VERY strong prompt adherence)
if re.search(r'(?<!_)guidance\s*=\s*([0-9.]+)', content):
    old = re.search(r'(?<!_)guidance\s*=\s*([0-9.]+)', content).group(1)
    if float(old) != 12.0:
        content = re.sub(r'(?<!_)guidance\s*=\s*[0-9.]+', 'guidance=12.0', content)
        fixes.append(f"guidance: {old} → 12.0 (VERY strong prompt)")

# Fix 4: Quality steps (MAXIMUM quality)
if re.search(r'num_steps\s*=\s*([0-9]+)', content):
    old = re.search(r'num_steps\s*=\s*([0-9]+)', content).group(1)
    if int(old) < 120:
        content = re.sub(r'num_steps\s*=\s*[0-9]+', 'num_steps=120', content)
        fixes.append(f"num_steps: {old} → 120 (MAXIMUM quality)")

# Fix 5: Disable VAE tiling (prevent face distortion)
if 'use_spatial_tiling' in content:
    if re.search(r'use_spatial_tiling\s*=\s*True', content):
        content = re.sub(r'use_spatial_tiling\s*=\s*True', 'use_spatial_tiling=False', content)
        fixes.append("use_spatial_tiling: True → False")

if 'use_temporal_tiling' in content:
    if re.search(r'use_temporal_tiling\s*=\s*True', content):
        content = re.sub(r'use_temporal_tiling\s*=\s*True', 'use_temporal_tiling=False', content)
        fixes.append("use_temporal_tiling: True → False")

# Fix 6: Disable guidance oscillation
if 'text_osci' in content:
    if re.search(r'text_osci\s*=\s*True', content):
        content = re.sub(r'text_osci\s*=\s*True', 'text_osci=False', content)
        fixes.append("text_osci: True → False")

if 'image_osci' in content:
    if re.search(r'image_osci\s*=\s*True', content):
        content = re.sub(r'image_osci\s*=\s*True', 'image_osci=False', content)
        fixes.append("image_osci: True → False")

if content != original:
    with open(config_file.replace("$OPENSORA_PATH", "$OPENSORA_PATH"), 'w') as f:
        f.write(content)
    print("Applied fixes:", ", ".join(fixes))
else:
    print("Config already optimized")
PYTHON_SCRIPT

# Actually run the Python fix
cat > /tmp/fix_config.py << 'EOF'
import re
import os

config_file = os.path.expanduser(os.environ.get('CONFIG_FILE'))
with open(config_file, 'r') as f:
    content = f.read()

original = content
fixes = []

# Fix 1: FPS
match = re.search(r'fps_save\s*=\s*([0-9]+)', content)
if match and int(match.group(1)) != 8:
    old = match.group(1)
    content = re.sub(r'fps_save\s*=\s*[0-9]+', 'fps_save=8', content)
    fixes.append(f"fps_save: {old} → 8")

# Fix 2: Image guidance
match = re.search(r'guidance_img\s*=\s*([0-9.]+)', content)
if match and float(match.group(1)) != 3.5:
    old = match.group(1)
    content = re.sub(r'guidance_img\s*=\s*[0-9.]+', 'guidance_img=3.5', content)
    fixes.append(f"guidance_img: {old} → 3.5")

# Fix 3: Text guidance
match = re.search(r'(?<!_)guidance\s*=\s*([0-9.]+)', content)
if match and float(match.group(1)) != 12.0:
    old = match.group(1)
    content = re.sub(r'(?<!_)guidance\s*=\s*[0-9.]+', 'guidance=12.0', content)
    fixes.append(f"guidance: {old} → 12.0")

# Fix 4: Quality steps
match = re.search(r'num_steps\s*=\s*([0-9]+)', content)
if match and int(match.group(1)) < 120:
    old = match.group(1)
    content = re.sub(r'num_steps\s*=\s*[0-9]+', 'num_steps=120', content)
    fixes.append(f"num_steps: {old} → 120")

# Fix 5: Disable VAE tiling
if re.search(r'use_spatial_tiling\s*=\s*True', content):
    content = re.sub(r'use_spatial_tiling\s*=\s*True', 'use_spatial_tiling=False', content)
    fixes.append("use_spatial_tiling disabled")

if re.search(r'use_temporal_tiling\s*=\s*True', content):
    content = re.sub(r'use_temporal_tiling\s*=\s*True', 'use_temporal_tiling=False', content)
    fixes.append("use_temporal_tiling disabled")

# Fix 6: Disable guidance oscillation
if re.search(r'text_osci\s*=\s*True', content):
    content = re.sub(r'text_osci\s*=\s*True', 'text_osci=False', content)
    fixes.append("text_osci disabled")

if re.search(r'image_osci\s*=\s*True', content):
    content = re.sub(r'image_osci\s*=\s*True', 'image_osci=False', content)
    fixes.append("image_osci disabled")

if content != original:
    with open(config_file, 'w') as f:
        f.write(content)
    for fix in fixes:
        print(f"   ✓ {fix}")
else:
    print("   ✓ Config already optimized")
EOF

export CONFIG_FILE="$CONFIG_FILE"
python3 /tmp/fix_config.py
rm /tmp/fix_config.py

echo -e "${GREEN}✅ Configuration optimized for maximum quality${NC}"
echo ""

################################################################################
# Step 7: Set environment variables
################################################################################
echo -e "${BLUE}[7/8] Setting environment variables...${NC}"

# Create .env file for GPU service
cat > "$PROJECT_DIR/.env" << EOF
# Open-Sora Configuration
OPENSORA_PATH=$OPENSORA_PATH

# GPU Service Configuration
HOST=0.0.0.0
PORT=$SERVICE_PORT

# Quality Settings (optimized for faces and prompt following)
DEFAULT_NUM_STEPS=120
DEFAULT_GUIDANCE=12.0
DEFAULT_GUIDANCE_IMG=3.5

# Optional: Set GPU API key for authentication
# GPU_API_KEY=your-secret-key-here
EOF

echo -e "${GREEN}✅ Environment configured${NC}"
echo ""

################################################################################
# Step 8: Create systemd service (optional but recommended)
################################################################################
echo -e "${BLUE}[8/8] Setting up systemd service...${NC}"

sudo tee /etc/systemd/system/opensora-gpu.service > /dev/null << EOF
[Unit]
Description=Open-Sora GPU Video Generation Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin"
Environment="OPENSORA_PATH=$OPENSORA_PATH"
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=/usr/bin/python3 -m gpu_service.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable opensora-gpu.service

echo -e "${GREEN}✅ Systemd service created${NC}"
echo ""

################################################################################
# Complete!
################################################################################
echo -e "${GREEN}=========================================="
echo "✅ Setup Complete!"
echo "==========================================${NC}"
echo ""
echo -e "${BLUE}📋 Summary:${NC}"
echo "  • Open-Sora installed: $OPENSORA_PATH"
echo "  • Service installed: $PROJECT_DIR"
echo "  • Configuration optimized for MAXIMUM quality"
echo "  • GPU Service port: $SERVICE_PORT"
echo ""
echo -e "${BLUE}🚀 To start the service:${NC}"
echo ""
echo "  Option 1 - Direct run:"
echo -e "    ${YELLOW}cd $PROJECT_DIR${NC}"
echo -e "    ${YELLOW}python3 -m gpu_service.main${NC}"
echo ""
echo "  Option 2 - Using systemd (recommended):"
echo -e "    ${YELLOW}sudo systemctl start opensora-gpu${NC}"
echo -e "    ${YELLOW}sudo systemctl status opensora-gpu${NC}"
echo ""
echo "  View logs:"
echo -e "    ${YELLOW}sudo journalctl -u opensora-gpu -f${NC}"
echo ""
echo -e "${BLUE}🔧 Service will be available at:${NC}"
echo "  http://$(hostname -I | awk '{print $1}'):$SERVICE_PORT"
echo ""
echo -e "${BLUE}📊 Quality Settings (optimized):${NC}"
echo "  • Quality Steps: 120 (MAXIMUM)"
echo "  • Prompt Strength: 12.0 (VERY STRONG)"
echo "  • Image Influence: 3.5 (STRONG face preservation)"
echo ""
echo -e "${YELLOW}💡 Tip: Use 'sudo systemctl enable opensora-gpu' to start on boot${NC}"
echo ""
