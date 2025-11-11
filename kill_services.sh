#!/bin/bash

################################################################################
# Kill All Open-Sora Video Generation Services
# Stops all running backend, GPU service, and inference processes
################################################################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Stopping All Open-Sora Video Generation Services${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"
echo ""

# Track if anything was killed
KILLED_SOMETHING=false

# Function to safely kill processes
kill_processes() {
    local pattern="$1"
    local description="$2"
    local pids=$(ps aux | grep -E "$pattern" | grep -v grep | awk '{print $2}')

    if [ ! -z "$pids" ]; then
        KILLED_SOMETHING=true
        echo -e "${YELLOW}Stopping $description...${NC}"
        for pid in $pids; do
            kill -15 $pid 2>/dev/null && echo "  ✓ Killed PID $pid" || true
        done
        sleep 1

        # Force kill if still running
        for pid in $pids; do
            if kill -0 $pid 2>/dev/null; then
                kill -9 $pid 2>/dev/null && echo "  ✓ Force killed PID $pid" || true
            fi
        done
    fi
}

# 1. Kill systemd services
if systemctl is-active --quiet opensora-gpu 2>/dev/null; then
    echo -e "${YELLOW}Stopping systemd service...${NC}"
    sudo systemctl stop opensora-gpu
    echo "  ✓ Systemd service stopped"
    KILLED_SOMETHING=true
fi

# 2. Kill backend services
kill_processes "python.*backend\.main" "backend services"
kill_processes "python.*backend/main\.py" "backend services"

# 3. Kill GPU services
kill_processes "python.*gpu_service\.main" "GPU services"
kill_processes "python.*gpu_service/main\.py" "GPU services"

# 4. Kill uvicorn processes (FastAPI workers)
kill_processes "uvicorn.*backend" "backend uvicorn workers"
kill_processes "uvicorn.*gpu_service" "GPU service uvicorn workers"

# 5. Kill any processes using our ports
for port in 8000 8001; do
    port_pid=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$port_pid" ]; then
        KILLED_SOMETHING=true
        echo -e "${YELLOW}Freeing port $port...${NC}"
        kill -15 $port_pid 2>/dev/null
        sleep 1
        if kill -0 $port_pid 2>/dev/null; then
            kill -9 $port_pid 2>/dev/null
        fi
        echo "  ✓ Port $port freed (PID: $port_pid)"
    fi
done

# 6. Kill any stray torchrun processes (Open-Sora inference)
kill_processes "torchrun.*inference\.py" "Open-Sora inference processes"

# 7. Kill any remaining Python processes related to sora
kill_processes "python.*sora.*main" "remaining sora services"

echo ""
if [ "$KILLED_SOMETHING" = true ]; then
    echo -e "${GREEN}✓ All services stopped successfully${NC}"
else
    echo -e "${GREEN}✓ No services were running${NC}"
fi
echo ""

# Show remaining Python processes (for verification)
REMAINING=$(ps aux | grep -E "python.*(backend|gpu_service|torchrun)" | grep -v grep)
if [ ! -z "$REMAINING" ]; then
    echo -e "${YELLOW}⚠ Warning: Some processes may still be running:${NC}"
    echo "$REMAINING"
    echo ""
    echo "If you see stuck processes, you can force kill all Python:"
    echo "  pkill -9 python3"
else
    echo -e "${GREEN}✓ Verification: No related processes found${NC}"
fi

echo ""
echo -e "${GREEN}Done!${NC}"
