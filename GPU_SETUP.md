# 🚀 Complete GPU Instance Setup Guide

**One-command setup for fresh Lambda Labs or other GPU instances**

## 📋 What You Need To Run

On a **fresh GPU instance**, run these commands:

```bash
# 1. Clone the repository
cd ~
git clone https://github.com/Blurjp/sora2.git
cd sora2

# 2. Run the complete setup script (does everything!)
bash gpu_setup.sh
```

**That's it!** ✅

---

## 🔧 What The Script Does Automatically

The `gpu_setup.sh` script handles **EVERYTHING** in a single run:

### 1. **Lambda Labs Guest Agent** ✅
   - Installs Lambda Labs guest agent
   - Required for Lambda Labs instances
   - Safely skips on non-Lambda instances

### 2. **System Dependencies** ✅
   - Updates apt packages
   - Installs: git, curl, wget, ffmpeg, Python tools

### 3. **GPU Verification** ✅
   - Checks for NVIDIA GPU
   - Displays GPU info
   - Exits if no GPU found

### 4. **Open-Sora Installation** ✅
   - Clones Open-Sora repository
   - Installs all dependencies
   - Installs xformers and flash-attention
   - Location: `~/Open-Sora`

### 5. **Service Installation** ✅
   - Clones video generation service
   - Installs service dependencies
   - Creates output directories
   - Location: `~/sora2`

### 6. **Configuration Optimization** ✅
   - Automatically fixes Open-Sora config
   - Sets MAXIMUM quality defaults:
     - **num_steps: 120** (maximum quality)
     - **guidance: 12.0** (very strong prompt adherence)
     - **guidance_img: 3.5** (strong face preservation)
   - Disables VAE tiling (prevents face distortion)
   - Disables guidance oscillation
   - Sets FPS to 8 (correct video duration)

### 7. **Environment Setup** ✅
   - Creates `.env` file with all settings
   - Configures paths and quality parameters

### 8. **Systemd Service** ✅
   - Creates `opensora-gpu` systemd service
   - Auto-restart on failure
   - Enables on boot (optional)

---

## 🎮 Starting The Service

### Option 1: Direct Run (for testing)

```bash
cd ~/sora2
python3 -m gpu_service.main
```

### Option 2: Systemd Service (recommended for production)

```bash
# Start the service
sudo systemctl start opensora-gpu

# Check status
sudo systemctl status opensora-gpu

# View logs
sudo journalctl -u opensora-gpu -f

# Enable auto-start on boot
sudo systemctl enable opensora-gpu

# Stop the service
sudo systemctl stop opensora-gpu
```

---

## 🌐 Accessing The Service

After starting, the GPU service will be available at:

```
http://YOUR_GPU_IP:8001
```

Find your GPU IP:
```bash
hostname -I | awk '{print $1}'
```

---

## 🔒 Security (Optional)

To add API key authentication, edit `.env`:

```bash
nano ~/sora2/.env
```

Add this line:
```
GPU_API_KEY=your-secret-key-here
```

Then restart:
```bash
sudo systemctl restart opensora-gpu
```

---

## 📊 Quality Settings

The script automatically optimizes for **MAXIMUM quality**:

| Parameter | Value | Purpose |
|-----------|-------|---------|
| **Quality Steps** | 120 | 20% more diffusion steps for best quality |
| **Prompt Strength** | 12.0 | Very strong prompt adherence |
| **Image Influence** | 3.5 | Strong face preservation |
| **FPS** | 8 | Correct video duration |
| **VAE Tiling** | Disabled | Prevents face distortion |
| **Guidance Oscillation** | Disabled | Consistent quality |

---

## 🐛 Troubleshooting

### Error: ModuleNotFoundError: No module named 'tensornvme'

**Recommended Fix: Make it Optional**
```bash
cd ~/sora2
git pull
./fix_tensornvme.sh
```

This patches Open-Sora to make tensornvme optional. **TensorNVMe is NOT required** for GPUs with sufficient VRAM (A100/H100/etc). It only provides GPU-to-SSD offloading for systems with very limited VRAM.

**Note:** Installing tensornvme from source has complex dependencies and build issues. The patch solution is simpler and works perfectly for your setup.

Then restart:
```bash
sudo systemctl restart opensora-gpu
```

### Check service status:
```bash
sudo systemctl status opensora-gpu
```

### View logs:
```bash
sudo journalctl -u opensora-gpu -f
```

### Test GPU:
```bash
nvidia-smi
```

### Restart service:
```bash
sudo systemctl restart opensora-gpu
```

### Manually run to see errors:
```bash
cd ~/sora2
python3 -m gpu_service.main
```

---

## 📁 File Locations

| Item | Location |
|------|----------|
| Open-Sora | `~/Open-Sora` |
| Service | `~/sora2` |
| Config | `~/Open-Sora/configs/diffusion/inference/256px.py` |
| Environment | `~/sora2/.env` |
| Outputs | `~/sora2/gpu_service/outputs/` |
| Systemd Service | `/etc/systemd/system/opensora-gpu.service` |

---

## 🔄 Updating The Service

```bash
cd ~/sora2
git pull
sudo systemctl restart opensora-gpu
```

---

## 📞 Backend Integration

Configure your backend to use this GPU service:

```bash
# In backend .env file:
USE_REMOTE_GPU=true
GPU_SERVICE_URL=http://YOUR_GPU_IP:8001
GPU_API_KEY=your-secret-key-here  # if you set one
```

---

## ⏱️ Setup Time

- **Fresh instance**: ~15-20 minutes
- **Existing Open-Sora**: ~5 minutes

---

## ✅ Verification

After setup, verify everything works:

```bash
# 1. Check service is running
sudo systemctl status opensora-gpu

# 2. Check GPU is detected
nvidia-smi

# 3. Test health endpoint
curl http://localhost:8001/api/health

# Should return: {"status":"healthy","gpu_busy":false,...}
```

---

## 💡 Tips

1. **Use systemd** - More reliable than direct run
2. **Enable on boot** - `sudo systemctl enable opensora-gpu`
3. **Monitor logs** - `sudo journalctl -u opensora-gpu -f`
4. **Test locally first** - Run directly to see any errors
5. **Firewall** - Make sure port 8001 is open if accessing remotely

---

**Need help?** Check the logs first, they show detailed error messages!
