# Lambda Labs API Management Guide

Complete guide to managing Lambda GPU instances programmatically.

## Setup

### 1. Your API Key

Your Lambda Labs API key:
```
secret_sora2_3e1296ff401d44c5b476387cda212173.PmVHz6bzECPi06mihPABbHObqOo5RiBs
```

**⚠️ Keep this secure!** Already saved to `.env` file.

### 2. Install Requirements

```bash
# jq for JSON parsing (if not installed)
# Ubuntu/Debian
sudo apt-get install jq

# Mac
brew install jq

# Windows (WSL or Git Bash)
# Download from https://stedolan.github.io/jq/
```

### 3. Verify Setup

```bash
./lambda_manager.sh list
```

Should show your instances (or empty if none running).

## Quick Start Workflow

### Complete End-to-End Setup (5 commands)

```bash
# 1. See available GPU types and prices
./lambda_manager.sh types

# 2. Launch an A100 instance
./lambda_manager.sh launch gpu_1x_a100

# 3. Wait 2-3 minutes, then check status
./lambda_manager.sh list

# 4. Automatic setup (installs everything and starts GPU service)
./lambda_manager.sh setup <instance-id>

# 5. Start your local backend
./restart.sh
```

Done! Open http://localhost:8000

## Commands Reference

### List Instances

```bash
# See all your instances
./lambda_manager.sh list

# Alias
./lambda_manager.sh ls
```

Example output:
```
INSTANCE ID              TYPE                 STATUS          IP ADDRESS
-----------              ----                 ------          ----------
0xa1b2c3d4e5f6          gpu_1x_a100          active          123.45.67.89
```

### List Available GPU Types

```bash
./lambda_manager.sh types
```

Example output:
```
TYPE                           PRICE/HR        DESCRIPTION
----                           --------        -----------
gpu_1x_a100                    $1.10          NVIDIA A100 (40 GB)
gpu_1x_a10                     $0.60          NVIDIA A10 (24 GB)
gpu_1x_h100_pcie               $2.49          NVIDIA H100 PCIe (80 GB)
```

### Launch Instance

```bash
# Basic launch (recommended)
./lambda_manager.sh launch gpu_1x_a100

# With custom region
./lambda_manager.sh launch gpu_1x_a100 us-east-1

# With custom name
./lambda_manager.sh launch gpu_1x_a100 us-west-1 my-sora-gpu
```

**Available regions:**
- `us-west-1` (California) - Default
- `us-east-1` (Virginia)
- `us-south-1` (Texas)
- `europe-central-1` (Germany)

### Get Instance Info

```bash
# Detailed info for specific instance
./lambda_manager.sh info <instance-id>

# Quick status (same as list)
./lambda_manager.sh status
```

### SSH Into Instance

```bash
./lambda_manager.sh ssh <instance-id>
```

### Setup GPU Service (Automated!)

```bash
# Auto-setup everything
./lambda_manager.sh setup <instance-id>

# With custom API key
./lambda_manager.sh setup <instance-id> my-custom-key-123
```

This will:
1. Clone the repo
2. Run `lambda_setup.sh`
3. Install Open-Sora
4. Start GPU service in tmux
5. Display connection info

### Terminate Instance

```bash
./lambda_manager.sh terminate <instance-id>

# Alias
./lambda_manager.sh stop <instance-id>
```

**Warning:** This is permanent! Make sure to save any data first.

## Complete Workflow Examples

### Example 1: First Time Setup

```bash
# 1. See what's available
./lambda_manager.sh types

# 2. Launch A100 (best price/performance)
./lambda_manager.sh launch gpu_1x_a100

# Output: Instance ID: 0x1234567890abcdef

# 3. Wait 2-3 minutes, check if ready
./lambda_manager.sh list

# 4. Auto-setup GPU service
./lambda_manager.sh setup 0x1234567890abcdef sora-gpu-2025

# Output:
#   GPU_SERVICE_URL=http://123.45.67.89:8001
#   GPU_API_KEY=sora-gpu-2025

# 5. Update .env automatically (script does this)
# Or manually:
# echo "GPU_SERVICE_URL=http://123.45.67.89:8001" >> .env
# echo "GPU_API_KEY=sora-gpu-2025" >> .env

# 6. Start local backend
./restart.sh

# 7. Open browser
# http://localhost:8000
```

### Example 2: Using Existing Instance

```bash
# 1. Check your instances
./lambda_manager.sh list

# 2. Get IP address
./lambda_manager.sh info 0x1234567890abcdef

# 3. SSH and start GPU service manually
./lambda_manager.sh ssh 0x1234567890abcdef
# On instance:
cd ~/sora2
./lambda_run_gpu_service.sh --api-key sora-gpu-2025
# Press Ctrl+B then D to detach from tmux

# 4. Update .env with IP
# GPU_SERVICE_URL=http://<ip>:8001

# 5. Restart local backend
./restart.sh
```

### Example 3: Cost Optimization

```bash
# Morning: Launch instance
./lambda_manager.sh launch gpu_1x_a10  # Cheaper option
INSTANCE_ID=$(./lambda_manager.sh list | tail -1 | awk '{print $1}')

# Setup
sleep 180  # Wait 3 minutes
./lambda_manager.sh setup $INSTANCE_ID

# Work on your videos
./restart.sh
# Generate videos...

# Evening: Shut down to save money
./lambda_manager.sh terminate $INSTANCE_ID
```

**Cost:** A10 @ $0.60/hr × 8 hours = $4.80/day

### Example 4: Multiple Regions (Availability)

```bash
# Try west coast first
./lambda_manager.sh launch gpu_1x_a100 us-west-1

# If not available, try east coast
./lambda_manager.sh launch gpu_1x_a100 us-east-1

# Or Europe
./lambda_manager.sh launch gpu_1x_a100 europe-central-1
```

## Advanced Usage

### Manual API Calls

If you need more control:

```bash
# Set API key
export LAMBDA_API_KEY='secret_sora2_...'

# List instances
curl -u "${LAMBDA_API_KEY}:" https://cloud.lambdalabs.com/api/v1/instances | jq

# Get specific instance
curl -u "${LAMBDA_API_KEY}:" https://cloud.lambdalabs.com/api/v1/instances/<id> | jq

# Launch instance
curl -u "${LAMBDA_API_KEY}:" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "region_name": "us-west-1",
    "instance_type_name": "gpu_1x_a100",
    "ssh_key_names": [],
    "quantity": 1
  }' \
  https://cloud.lambdalabs.com/api/v1/instance-operations/launch | jq
```

### Environment Variables

```bash
# .env file (recommended)
LAMBDA_API_KEY=secret_sora2_...
GPU_SERVICE_URL=http://instance-ip:8001
GPU_API_KEY=sora-gpu-2025

# Or export directly
export LAMBDA_API_KEY='secret_sora2_...'
export GPU_SERVICE_URL='http://123.45.67.89:8001'
export GPU_API_KEY='sora-gpu-2025'
```

### Automation Scripts

**Auto-launch and setup:**
```bash
#!/bin/bash
# auto_setup.sh

# Launch instance
RESPONSE=$(./lambda_manager.sh launch gpu_1x_a100)
INSTANCE_ID=$(echo "$RESPONSE" | grep "Instance ID:" | awk '{print $3}')

echo "Waiting for instance to boot..."
sleep 180

# Setup GPU service
./lambda_manager.sh setup $INSTANCE_ID sora-gpu-2025

# Start local backend
./restart.sh
```

**Daily shutdown:**
```bash
# Cron job to auto-shutdown at midnight
0 0 * * * cd /path/to/sora2 && ./lambda_manager.sh terminate $(./lambda_manager.sh list | tail -1 | awk '{print $1}')
```

## Troubleshooting

### "LAMBDA_API_KEY not set"

```bash
# Check .env file exists
cat .env

# If not, create it
echo 'LAMBDA_API_KEY=secret_sora2_...' > .env

# Or export directly
export LAMBDA_API_KEY='secret_sora2_...'
```

### "jq: command not found"

```bash
# Install jq
sudo apt-get install jq  # Ubuntu/Debian
brew install jq          # Mac
```

### "No instances available"

Lambda Labs sometimes runs out of capacity. Try:
1. Different GPU type (A10 instead of A100)
2. Different region
3. Wait and try again later

### Instance stuck in "booting" status

Normal! Takes 2-3 minutes. Check again:
```bash
./lambda_manager.sh list
```

### Can't SSH into instance

Wait for status to be "active":
```bash
./lambda_manager.sh list
# Wait until STATUS shows "active"
```

### Setup script fails

SSH in manually and run setup:
```bash
./lambda_manager.sh ssh <instance-id>

# On instance:
cd ~
git clone https://github.com/YOUR_USERNAME/sora2.git
cd sora2
./lambda_setup.sh
./lambda_run_gpu_service.sh --api-key sora-gpu-2025
```

## Cost Management

### Price Comparison

| GPU Type | VRAM | Price/Hr | Best For |
|----------|------|----------|----------|
| A10 | 24GB | $0.60 | Testing, short videos |
| A100 | 40GB | $1.10 | Production, best value |
| H100 | 80GB | $2.49 | Maximum quality |

### Cost Calculation

```bash
# Example: 20 videos, 2 min each = 40 minutes
# A100 @ $1.10/hr × 0.67 hr = $0.74
# vs AWS p4d.24xlarge @ $32.77/hr × 0.67 hr = $21.95

# Savings: 96% cheaper!
```

### Tips to Save Money

1. **Shut down when not using**
   ```bash
   ./lambda_manager.sh terminate <instance-id>
   ```

2. **Use cheaper GPUs for testing**
   ```bash
   ./lambda_manager.sh launch gpu_1x_a10  # $0.60/hr
   ```

3. **Batch your generations**
   - Generate multiple videos in one session
   - Shut down when done

4. **Set reminders**
   - Phone alarm to remind you to shut down
   - Or use cron jobs (see Automation above)

## Next Steps

- [Quick Start Guide](QUICKSTART_REMOTE.md) - Get started in 5 minutes
- [Remote GPU Setup](REMOTE_GPU_SETUP.md) - Detailed architecture
- [Restart Guide](RESTART_GUIDE.md) - Using the restart script

## API Reference

Official Lambda Labs API docs:
https://cloud.lambdalabs.com/api/v1/docs
