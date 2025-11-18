#!/bin/bash

# Voice Command macOS - Restart Script
# Simple script to restart the voice command app

PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "🛑 Stopping existing voice command app..."
pkill -f "python3 src/main.py" 2>/dev/null || true

echo "⏳ Waiting 2 seconds..."
sleep 2

echo "🚀 Starting voice command app..."
cd "$PROJECT_DIR"
source venv/bin/activate
python3 src/main.py run

