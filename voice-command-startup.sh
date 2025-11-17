#!/bin/bash
# Voice Command macOS - Startup Script with Device Detection
# This script is called by the Launch Agent on login
# It waits for the Jabra device to be connected, then starts the voice listener

PROJECT_DIR="/Users/jeremygatt/Projects/voice-command-mac"
VENV_DIR="$PROJECT_DIR/venv"
LOG_FILE="$HOME/.voice-command/logs/startup.log"
ERROR_LOG="$HOME/.voice-command/logs/errors.log"

# Create log directory
mkdir -p "$(dirname "$LOG_FILE")"

# Log function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a "$ERROR_LOG"
}

log "================================"
log "Voice Command Startup Script"
log "================================"
log "Project directory: $PROJECT_DIR"

# Check if project exists
if [ ! -d "$PROJECT_DIR" ]; then
    error "Project directory not found: $PROJECT_DIR"
    exit 1
fi

# Check if venv exists
if [ ! -d "$VENV_DIR" ]; then
    error "Virtual environment not found at $VENV_DIR"
    exit 1
fi

# Activate virtual environment
log "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Change to project directory
cd "$PROJECT_DIR"

# Run with device detection
log "Starting voice listener with device detection..."
log "Waiting for Jabra device..."

python3 src/main.py run --detect-device >> "$LOG_FILE" 2>> "$ERROR_LOG"

EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    log "Voice listener stopped gracefully"
else
    error "Voice listener exited with code $EXIT_CODE"
fi

log "Startup script complete"
exit $EXIT_CODE

