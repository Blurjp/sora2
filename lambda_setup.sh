#!/bin/bash

################################################################################
# Open-Sora Video Generation Service - Lambda Labs Setup Script
#
# This script automates the installation on Lambda Labs GPU instances
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Lambda Labs defaults
LAMBDA_HOME="/home/ubuntu"
OPENSORA_PATH="$LAMBDA_HOME/Open-Sora"
PROJECT_PATH="$LAMBDA_HOME/sora2"

echo -e "${BLUE}"
echo "================================================================"
echo "   Open-Sora Video Generator - Lambda Labs Setup"
echo "   Automated installation for Lambda Labs GPU instances"
echo "================================================================"
echo -e "${NC}"
echo ""

# Function to print section headers
print_section() {
    echo -e "\n${BLUE}>>> $1${NC}\n"
}

# Function to print success messages
print_success() {
    echo -e "${GREEN}[OK] $1${NC}"
}

# Function to print warnings
print_warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Function to print errors
print_error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

# Check if running on Lambda Labs
print_section "Checking Environment"

if [[ $(hostname) == *"lambda"* ]] || [[ -d "/home/ubuntu" ]]; then
    print_success "Lambda Labs environment detected"
else
    print_warning "This script is optimized for Lambda Labs instances"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Install bc early (needed for GPU memory calculation)
print_section "Installing Basic Dependencies"

sudo apt update > /dev/null 2>&1
sudo apt install -y bc > /dev/null 2>&1
print_success "Basic dependencies installed"

# Check GPU
print_section "Checking GPU"

if command -v nvidia-smi &> /dev/null; then
    GPU_COUNT=$(nvidia-smi --list-gpus | wc -l)
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -n1)
    GPU_MEMORY_RAW=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -n1)

    print_success "GPU detected: $GPU_NAME"
    print_success "GPU count: $GPU_COUNT"
    print_success "GPU memory: ${GPU_MEMORY_RAW} MiB"

    # Convert MiB to GB (divide by 1024 with proper rounding)
    # Add 512 MiB before dividing to round up properly (40536 MiB -> 40 GB)
    MEMORY_GB=$(echo "scale=0; ($GPU_MEMORY_RAW + 512) / 1024" | bc)

    print_success "GPU memory: ${MEMORY_GB} GB"

    # Check if suitable for Open-Sora
    if [ "$MEMORY_GB" -lt 40 ]; then
        print_error "GPU has less than 40GB memory. Open-Sora requires at least 40GB."
        print_warning "Generation may fail or be very slow."
    fi
else
    print_error "No GPU detected! Open-Sora requires CUDA-compatible GPU."
    exit 1
fi

# Check CUDA
print_section "Checking CUDA"

if command -v nvcc &> /dev/null; then
    CUDA_VERSION=$(nvcc --version | grep "release" | awk '{print $5}' | cut -d',' -f1)
    print_success "CUDA version: $CUDA_VERSION"
else
    print_warning "CUDA compiler not found, but runtime may still work"
fi

# Update system
print_section "Updating System Packages"

sudo apt update > /dev/null 2>&1
print_success "Package list updated"

# Install system dependencies
print_section "Installing System Dependencies"

sudo apt install -y \
    build-essential \
    git \
    wget \
    curl \
    tmux \
    htop \
    bc \
    > /dev/null 2>&1

# Try to install nvtop (may not be available on all systems)
sudo apt install -y nvtop > /dev/null 2>&1 || print_warning "nvtop not available"

print_success "System dependencies installed"

# Check Python
print_section "Checking Python"

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
print_success "Python version: $PYTHON_VERSION"

REQUIRED_VERSION="3.10"
if [[ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]]; then
    print_error "Python 3.10+ required. Found: $PYTHON_VERSION"

    print_section "Installing Python 3.10"
    sudo apt install -y python3.10 python3.10-venv python3.10-dev
    sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1
    print_success "Python 3.10 installed"
fi

# Upgrade pip
print_section "Upgrading pip"

python3 -m pip install --upgrade pip > /dev/null 2>&1
print_success "pip upgraded"

# Install PyTorch (if not already installed)
print_section "Checking PyTorch"

if python3 -c "import torch" 2>/dev/null; then
    TORCH_VERSION=$(python3 -c "import torch; print(torch.__version__)")
    print_success "PyTorch already installed: $TORCH_VERSION"
else
    print_section "Installing PyTorch"
    pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
    print_success "PyTorch installed"
fi

# Install Open-Sora
print_section "Installing Open-Sora"

if [ -d "$OPENSORA_PATH" ]; then
    print_warning "Open-Sora directory already exists at $OPENSORA_PATH"
    read -p "Reinstall? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$OPENSORA_PATH"
    else
        print_success "Using existing Open-Sora installation"
        SKIP_OPENSORA=true
    fi
fi

if [ "$SKIP_OPENSORA" != "true" ]; then
    echo "Cloning Open-Sora repository..."
    git clone https://github.com/hpcaitech/Open-Sora.git "$OPENSORA_PATH"
    print_success "Open-Sora cloned"

    cd "$OPENSORA_PATH"

    echo "Installing Open-Sora dependencies (this may take 5-10 minutes)..."
    pip install -v . > /tmp/opensora_install.log 2>&1
    print_success "Open-Sora base package installed"

    echo "Installing xformers..."
    pip install xformers==0.0.27.post2 --index-url https://download.pytorch.org/whl/cu121 > /tmp/xformers_install.log 2>&1
    print_success "xformers installed"

    echo "Installing flash-attn (this may take a few minutes)..."
    pip install flash-attn --no-build-isolation > /tmp/flash_attn_install.log 2>&1
    print_success "flash-attn installed"

    print_success "Open-Sora installation complete"
fi

# Fix compatibility issues (always run, even if Open-Sora was already installed)
print_section "Fixing Python Library Compatibility"

echo "Ensuring PyTorch is installed for tensornvme build..."
if ! python3 -c "import torch" 2>/dev/null; then
    echo "Installing PyTorch..."
    pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 > /tmp/torch_install_compat.log 2>&1
    print_success "PyTorch installed"
else
    print_success "PyTorch already available"
fi

echo "Upgrading rich library..."
pip install --upgrade rich > /tmp/rich_install.log 2>&1
print_success "rich library upgraded"

echo "Downgrading numpy to 1.x for compatibility..."
pip install "numpy<2" > /tmp/numpy_install.log 2>&1
print_success "numpy downgraded to 1.x"

echo "Installing tensornvme for checkpoint loading..."
# First, uninstall any broken partial installation
pip uninstall -y tensornvme > /dev/null 2>&1

# Install build dependencies
sudo apt install -y liburing-dev libaio-dev > /dev/null 2>&1

# Export PYTHONPATH to ensure torch is visible during build
export PYTHONPATH="$HOME/.local/lib/python3.10/site-packages:$PYTHONPATH"

# Install with --no-build-isolation so it can see torch
pip install --no-build-isolation tensornvme > /tmp/tensornvme_install.log 2>&1
if [ $? -eq 0 ]; then
    # Source bashrc if it was modified
    source ~/.bashrc 2>/dev/null || true
    # Verify installation
    if python3 -c "from tensornvme.async_file_io import AsyncFileWriter" 2>/dev/null; then
        print_success "tensornvme installed and verified"
    else
        print_warning "tensornvme installed but verification failed"
        print_warning "Open-Sora may work without it or download it at runtime"
    fi
else
    print_error "tensornvme installation failed"
    tail -20 /tmp/tensornvme_install.log
    print_warning "Continuing anyway - Open-Sora may work without it"
fi

# Setup service
print_section "Setting up Video Generation Service"

# Determine project path
if [ -d "$PROJECT_PATH" ]; then
    cd "$PROJECT_PATH"
else
    # If running from a different location
    cd "$(dirname "$0")"
    PROJECT_PATH=$(pwd)
fi

print_success "Project path: $PROJECT_PATH"

# Install service dependencies
echo "Installing service dependencies..."
pip install -r requirements.txt > /tmp/service_install.log 2>&1
print_success "Service dependencies installed"

# Set environment variable
export OPENSORA_PATH="$OPENSORA_PATH"
if ! grep -q "OPENSORA_PATH" ~/.bashrc; then
    echo "export OPENSORA_PATH=\"$OPENSORA_PATH\"" >> ~/.bashrc
    print_success "OPENSORA_PATH added to ~/.bashrc"
fi

# Store GPU count
if ! grep -q "GPU_COUNT" ~/.bashrc; then
    echo "export GPU_COUNT=$GPU_COUNT" >> ~/.bashrc
fi

# Update config.py
print_section "Configuring Service"

sed -i "s|OPENSORA_PATH = os.environ.get(\"OPENSORA_PATH\", \".*\")|OPENSORA_PATH = os.environ.get(\"OPENSORA_PATH\", \"$OPENSORA_PATH\")|" backend/config.py
print_success "Configuration updated"

# Set resolution based on GPU memory (using properly converted GB value)
if [ "$MEMORY_GB" -ge 80 ]; then
    sed -i 's/MODEL_RESOLUTION = "256px"/MODEL_RESOLUTION = "768px"/' backend/config.py
    print_success "Configured for high-quality 768px generation (80GB+ VRAM)"
elif [ "$MEMORY_GB" -ge 40 ]; then
    # Keep default 256px
    print_success "Configured for standard 256px generation (40-79GB VRAM)"
else
    print_warning "GPU has limited memory ($MEMORY_GB GB). Generation may be slow or fail."
fi

# Create directories
mkdir -p outputs temp
print_success "Output directories created"

# Test installation
print_section "Testing Installation"

echo "Testing Python imports..."
python3 -c "import torch; import fastapi; print('Torch version:', torch.__version__); print('CUDA available:', torch.cuda.is_available())" 2>&1

if [ $? -eq 0 ]; then
    print_success "Python environment is working"
else
    print_error "Python environment test failed"
fi

echo "Verifying critical dependencies..."
DEPS_OK=true

# Check numpy version
NUMPY_VERSION=$(python3 -c "import numpy; print(numpy.__version__)" 2>/dev/null)
if [[ $NUMPY_VERSION == 1.* ]]; then
    print_success "NumPy version correct: $NUMPY_VERSION"
else
    print_error "NumPy version wrong: $NUMPY_VERSION (should be 1.x)"
    DEPS_OK=false
fi

# Check rich
if python3 -c "from rich.progress import MofNCompleteColumn" 2>/dev/null; then
    print_success "rich library verified"
else
    print_error "rich library missing or outdated"
    DEPS_OK=false
fi

# Check tensornvme
if python3 -c "from tensornvme.async_file_io import AsyncFileWriter" 2>/dev/null; then
    print_success "tensornvme verified"
else
    print_warning "tensornvme not working (may still work without it)"
fi

if [ "$DEPS_OK" = false ]; then
    print_error "Some dependencies have issues. Try running ./lambda_setup.sh again."
fi

# Setup complete
echo ""
echo -e "${GREEN}"
echo "================================================================"
echo "                 Setup Complete!"
echo "================================================================"
echo -e "${NC}"
echo ""
echo -e "${BLUE}Installation Summary:${NC}"
echo "  GPU: $GPU_NAME ($GPU_COUNT x ${MEMORY_GB}GB)"
echo "  Python: $PYTHON_VERSION"
echo "  Open-Sora: $OPENSORA_PATH"
echo "  Project: $PROJECT_PATH"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo ""
echo "1. Start the service:"
echo -e "   ${YELLOW}./lambda_run.sh${NC}"
echo ""
echo "2. Access via SSH tunnel (from your local machine):"
echo -e "   ${YELLOW}ssh -L 8000:localhost:8000 ubuntu@<instance-ip>${NC}"
echo -e "   Then open: ${YELLOW}http://localhost:8000${NC}"
echo ""
echo "3. Run in background with tmux:"
echo -e "   ${YELLOW}tmux new -s sora${NC}"
echo -e "   ${YELLOW}./lambda_run.sh${NC}"
echo -e "   Press Ctrl+B, then D to detach"
echo ""
echo -e "${BLUE}Useful Commands:${NC}"
echo "  Monitor GPU: ${YELLOW}watch -n 1 nvidia-smi${NC}"
echo "  Check health: ${YELLOW}curl http://localhost:8000/health${NC}"
echo ""
print_success "Ready to generate videos!"
echo ""
