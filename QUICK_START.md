# ⚡ Quick Start - Fresh GPU Instance

## 🎯 Exactly What To Run

On a **brand new Lambda Labs or GPU instance**, copy and paste this:

```bash
cd ~ && \
git clone https://github.com/Blurjp/sora2.git && \
cd sora2 && \
bash gpu_setup.sh
```

**Wait 15-20 minutes for setup to complete.**

---

## 🚀 Then Start The Service

```bash
sudo systemctl start opensora-gpu
sudo systemctl status opensora-gpu
```

---

## ✅ Test It Works

```bash
curl http://localhost:8001/api/health
```

Should return:
```json
{"status":"healthy","gpu_busy":false}
```

---

## 🌐 Get Your GPU IP

```bash
hostname -I | awk '{print $1}'
```

Your service is now at: `http://YOUR_IP:8001`

---

## 📝 Configure Backend

On your backend server, set these in `.env`:

```bash
USE_REMOTE_GPU=true
GPU_SERVICE_URL=http://YOUR_GPU_IP:8001
```

---

**That's it! You're done!** ✅

See [GPU_SETUP.md](GPU_SETUP.md) for detailed documentation.
