# Lambda Labs Quick Start - 5 Minutes to Your First Video

Super quick guide to get started on Lambda Labs.

## Step 1: Launch Instance (2 min)

1. Go to https://cloud.lambdalabs.com/instances
2. Click **"Launch Instance"**
3. Select GPU:
   - **Budget**: 1x A100 (40GB) - $1.10/hr → Use 256px
   - **Quality**: 1x H100 (80GB) - $2.00/hr → Use 768px
4. Click **"Launch Instance"**

## Step 2: Connect & Setup (2 min)

```bash
# SSH into your instance (Lambda provides the command)
ssh ubuntu@<instance-ip>

# Clone your repository
git clone <your-repo-url> ~/sora2
cd ~/sora2

# Run automated setup
chmod +x lambda_setup.sh lambda_run.sh
./lambda_setup.sh
```

Setup installs:
- ✅ Open-Sora 2.0
- ✅ All dependencies
- ✅ GPU optimization
- ✅ Service configuration

## Step 3: Start Service (30 sec)

```bash
# Option A: Run with tmux (recommended - survives disconnects)
tmux new -s sora
./lambda_run.sh
# Press Ctrl+B, then D to detach

# Option B: Run directly (for testing)
./lambda_run.sh
```

## Step 4: Access Service (30 sec)

**On your local machine (new terminal):**

```bash
# Open SSH tunnel
ssh -L 8000:localhost:8000 ubuntu@<instance-ip>
```

**In your browser:**
```
http://localhost:8000
```

## Generate Your First Video!

1. Upload an image
2. Enter prompt: "ocean waves crashing on beach at sunset"
3. Set duration: 15 seconds
4. Click "Generate Video"
5. Wait 1-5 minutes
6. Download your video!

## Quick Commands

```bash
# Monitor GPU
watch -n 1 nvidia-smi

# Check service health
curl http://localhost:8000/health

# View logs (if using tmux)
tmux attach -t sora

# Download all generated videos to your local machine
scp -r ubuntu@<instance-ip>:~/sora2/outputs/*.mp4 ./
```

## Cost Tracking

| GPU | Resolution | Time/Video | Cost/Video |
|-----|------------|------------|------------|
| A100 | 256px | 1 min | $0.02 |
| H100 | 256px | 1 min | $0.03 |
| H100 | 768px | 5 min | $0.17 |

## When You're Done

```bash
# Download your videos first!
scp -r ubuntu@<instance-ip>:~/sora2/outputs/*.mp4 ./

# Then terminate instance in Lambda dashboard to stop billing
```

## Troubleshooting

**Service won't start?**
```bash
# Check if Open-Sora is installed
ls ~/Open-Sora

# Check GPU
nvidia-smi

# Re-run setup
./lambda_setup.sh
```

**Can't access web UI?**
```bash
# Make sure SSH tunnel is running
ssh -L 8000:localhost:8000 ubuntu@<instance-ip>

# Keep this terminal open!
```

**Out of memory?**
```bash
# Edit backend/config.py
nano backend/config.py

# Change line:
MODEL_RESOLUTION = "256px"  # Instead of 768px
```

## Pro Tips

1. **Use tmux** - Your service survives SSH disconnects
2. **Monitor GPU** - `watch nvidia-smi` in another terminal
3. **Download videos** - Don't lose them when instance terminates
4. **Batch processing** - Generate multiple videos before terminating
5. **Set alerts** - Lambda dashboard can notify you of costs

## Full Documentation

- Complete guide: `cat LAMBDA_LABS.md`
- API docs: http://localhost:8000/docs
- General guide: `cat README.md`

---

**Ready to generate! 🎬**

Total time: ~5 minutes
Cost to try: ~$0.10 (generate 3-4 test videos)
