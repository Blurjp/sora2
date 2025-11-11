#!/bin/bash

# Run Open-Sora Video Generation Service

# Set Open-Sora path if not already set
if [ -z "$OPENSORA_PATH" ]; then
    export OPENSORA_PATH="${OPENSORA_PATH:-$HOME/Open-Sora}"
fi

echo "Starting Open-Sora Video Generation Service..."
echo "Open-Sora path: $OPENSORA_PATH"
echo ""

# Check if Open-Sora exists
if [ ! -d "$OPENSORA_PATH" ]; then
    echo "Error: Open-Sora not found at $OPENSORA_PATH"
    echo "Please set OPENSORA_PATH environment variable or run setup.sh first"
    exit 1
fi

################################################################################
# Kill any existing Python services
################################################################################
echo "Cleaning up any existing Python services..."

# Function to safely kill processes
kill_processes() {
    local pattern="$1"
    local description="$2"
    local pids=$(ps aux | grep -E "$pattern" | grep -v grep | awk '{print $2}')

    if [ ! -z "$pids" ]; then
        echo "  Stopping $description..."
        for pid in $pids; do
            kill -15 $pid 2>/dev/null && echo "    Killed PID $pid" || true
        done
        sleep 1

        # Force kill if still running
        for pid in $pids; do
            if kill -0 $pid 2>/dev/null; then
                kill -9 $pid 2>/dev/null && echo "    Force killed PID $pid" || true
            fi
        done
    fi
}

# Kill backend services
kill_processes "python.*backend\.main" "backend services"
kill_processes "python.*backend/main\.py" "backend services"

# Kill GPU services
kill_processes "python.*gpu_service\.main" "GPU services"
kill_processes "python.*gpu_service/main\.py" "GPU services"

# Kill uvicorn processes (FastAPI)
kill_processes "uvicorn.*backend" "uvicorn workers"
kill_processes "uvicorn.*gpu_service" "uvicorn workers"

# Kill any Python processes using our ports
for port in 8000 8001; do
    local port_pid=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$port_pid" ]; then
        echo "  Freeing port $port (PID: $port_pid)..."
        kill -15 $port_pid 2>/dev/null && sleep 1
        if kill -0 $port_pid 2>/dev/null; then
            kill -9 $port_pid 2>/dev/null
        fi
        echo "    Port $port freed"
    fi
done

# Kill any stray torchrun processes (Open-Sora inference)
kill_processes "torchrun.*inference\.py" "Open-Sora inference processes"

echo "✓ Cleanup complete"
echo ""

# Start the service
python3 backend/main.py
