#!/bin/bash
# Quick setup script for Voice Command auto-start

set -e

PROJECT_DIR="/Users/jeremygatt/Projects/voice-command-mac"
PLIST_FILE="$PROJECT_DIR/com.voicecommand.plist"
STARTUP_SCRIPT="$PROJECT_DIR/voice-command-startup.sh"
LAUNCH_AGENT="$HOME/Library/LaunchAgents/com.voicecommand.plist"

echo "================================"
echo "Voice Command Launch Agent Setup"
echo "================================"
echo ""

# Check if project exists
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ Error: Project directory not found at $PROJECT_DIR"
    exit 1
fi

echo "✓ Project directory found"

# Make startup script executable
echo "Making startup script executable..."
chmod +x "$STARTUP_SCRIPT"
echo "✓ Startup script is executable"

# Create log directory
echo "Creating log directory..."
mkdir -p ~/.voice-command/logs
echo "✓ Log directory created"

# Copy plist to LaunchAgents
echo "Installing Launch Agent..."
cp "$PLIST_FILE" "$LAUNCH_AGENT"
echo "✓ Launch Agent copied to ~/Library/LaunchAgents/"

# Unload if already exists
if launchctl list | grep -q "com.voicecommand.listener"; then
    echo "Unloading existing Launch Agent..."
    launchctl unload "$LAUNCH_AGENT" 2>/dev/null || true
    sleep 1
fi

# Load the launch agent
echo "Loading Launch Agent..."
launchctl load "$LAUNCH_AGENT"

# Verify
if launchctl list | grep -q "com.voicecommand.listener"; then
    echo "✓ Launch Agent loaded successfully"
else
    echo "❌ Failed to load Launch Agent"
    exit 1
fi

echo ""
echo "================================"
echo "✅ Setup Complete!"
echo "================================"
echo ""
echo "The voice command listener will now:"
echo "  1. Start automatically on login"
echo "  2. Wait for your Jabra headset"
echo "  3. Begin listening once connected"
echo "  4. Keep running in the background"
echo ""
echo "To monitor startup:"
echo "  tail -f ~/.voice-command/logs/startup.log"
echo ""
echo "To stop the service:"
echo "  launchctl stop com.voicecommand.listener"
echo ""
echo "To unload from auto-start:"
echo "  launchctl unload ~/Library/LaunchAgents/com.voicecommand.plist"
echo ""
echo "For more info, see: SETUP_LAUNCH_AGENT.md"

