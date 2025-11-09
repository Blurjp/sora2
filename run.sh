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

# Start the service
python3 backend/main.py
