# Restart Script Guide

Single command to kill all Python processes and restart the service fresh.

## Quick Start

### On Your Local Machine (Windows)

```cmd
restart.bat --gpu-url http://your-lambda-ip:8001
```

Or set environment variable once:
```cmd
set GPU_SERVICE_URL=http://your-lambda-ip:8001
set GPU_API_KEY=your-secret-key
restart.bat
```

### On Your Local Machine (Linux/Mac)

```bash
./restart.sh --local --gpu-url http://your-lambda-ip:8001
```

Or with environment variables:
```bash
export GPU_SERVICE_URL=http://your-lambda-ip:8001
export GPU_API_KEY=your-secret-key
./restart.sh
```

### On Lambda GPU Instance

```bash
./restart.sh --gpu-service --api-key your-secret-key
```

## What It Does

1. **Kills all Python processes**
   - Stops any running backend/frontend/GPU service
   - Force kills if needed
   - Clean slate every time

2. **Auto-detects configuration**
   - Checks for GPU_SERVICE_URL (local mode)
   - Checks for OPENSORA_PATH (GPU service mode)
   - Uses command line args if provided

3. **Starts the appropriate service**
   - Local backend + frontend (if GPU URL provided)
   - GPU service (if on Lambda instance)

## Usage Examples

### Example 1: Local Development

```bash
# First time - specify everything
./restart.sh --local --gpu-url http://192.168.1.100:8001 --api-key my-key-123

# Subsequent restarts - uses saved env vars
./restart.sh
```

### Example 2: Lambda GPU Service

```bash
# On Lambda instance
./restart.sh --gpu-service --api-key my-key-123 --port 8001
```

### Example 3: Change GPU Endpoint

```bash
# Switch to different GPU instance
./restart.sh --local --gpu-url http://new-lambda-ip:8001
```

### Example 4: Environment Variables (Recommended)

Create `.env` file or add to `~/.bashrc`:
```bash
export GPU_SERVICE_URL=http://your-lambda-ip:8001
export GPU_API_KEY=your-secret-key-123
```

Then just run:
```bash
./restart.sh
```

## All Options

```bash
./restart.sh [OPTIONS]

Options:
  --local              Run local backend mode (default if GPU_URL set)
  --gpu-service        Run GPU service mode (for Lambda instance)
  --gpu-url URL        GPU service URL (e.g., http://lambda-ip:8001)
  --api-key KEY        API key for authentication
  --port PORT          Port to run on (default: 8000 local, 8001 GPU)

Examples:
  # Local backend
  ./restart.sh --local --gpu-url http://lambda:8001 --api-key KEY

  # GPU service
  ./restart.sh --gpu-service --api-key KEY --port 8001

  # Auto-detect from environment
  ./restart.sh
```

## Troubleshooting

### "No Python processes running"

This is normal! It means:
- No services were running
- Clean start

### "ERROR: GPU service URL not specified"

You need to either:
1. Use `--gpu-url` flag
2. Set `GPU_SERVICE_URL` environment variable

```bash
# Option 1
./restart.sh --local --gpu-url http://your-ip:8001

# Option 2
export GPU_SERVICE_URL=http://your-ip:8001
./restart.sh
```

### "ERROR: Open-Sora not found"

You're trying to run GPU service mode but Open-Sora isn't installed.

Either:
1. Install Open-Sora: `./lambda_setup.sh`
2. Or use local mode: `./restart.sh --local --gpu-url ...`

### "Port already in use"

The restart script kills all Python processes, so this shouldn't happen.

If it does:
```bash
# Find what's using the port
lsof -i :8000

# Kill it manually
kill <PID>

# Then restart
./restart.sh
```

### Process won't die

Very rare, but if processes are stuck:
```bash
# Force kill everything
pkill -9 python

# Wait a moment
sleep 2

# Restart
./restart.sh
```

## Tips

### 1. Create an Alias

Add to `~/.bashrc` or `~/.zshrc`:
```bash
alias sora-restart='cd ~/sora2 && ./restart.sh'
```

Then just run:
```bash
sora-restart
```

### 2. Run in Background

```bash
# Start in background
nohup ./restart.sh --local --gpu-url http://lambda:8001 > server.log 2>&1 &

# View logs
tail -f server.log

# Stop
pkill -f "python.*backend/main.py"
```

### 3. Auto-restart on Crash

Use `systemd` (Linux) or create a simple loop:
```bash
while true; do
    ./restart.sh --local --gpu-url http://lambda:8001
    echo "Server crashed, restarting in 5 seconds..."
    sleep 5
done
```

### 4. Health Check Before Restart

```bash
# Check if service is responding
curl http://localhost:8000/ || ./restart.sh
```

## Integration with Other Scripts

### Replace Other Run Scripts

Instead of:
```bash
./run_local.sh --gpu-url ...
```

Use:
```bash
./restart.sh --local --gpu-url ...
```

Benefits:
- Always starts fresh
- No "port already in use" errors
- Clean state

### Cron Job for Auto-restart

Restart every day at 4 AM:
```bash
# Edit crontab
crontab -e

# Add line
0 4 * * * cd /path/to/sora2 && ./restart.sh --local --gpu-url http://lambda:8001
```

## Comparison: restart.sh vs Other Scripts

| Feature | restart.sh | run_local.sh | lambda_run.sh |
|---------|------------|--------------|---------------|
| Kills old processes | ✅ Yes | ❌ No | ❌ No |
| Auto-detects mode | ✅ Yes | ❌ No | ❌ No |
| Works on Windows | ✅ Yes | ❌ No | ❌ No |
| Single command | ✅ Yes | ⚠️ Need to kill first | ⚠️ Need to kill first |
| Safe restart | ✅ Yes | ⚠️ May conflict | ⚠️ May conflict |

**Recommendation:** Use `restart.sh` for development and production!
