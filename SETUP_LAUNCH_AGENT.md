# Voice Command macOS - Auto-Start Setup

This guide shows how to set up the voice command listener to automatically start on login.

## **What it does:**

1. ✅ Waits for your Jabra headset to be connected
2. ✅ Automatically starts the voice listener
3. ✅ Keeps running in the background
4. ✅ Restarts if it crashes
5. ✅ Logs all startup activity for debugging

## **Installation Steps:**

### **Step 1: Make the startup script executable**

```bash
chmod +x /Users/jeremygatt/Projects/voice-command-mac/voice-command-startup.sh
```

### **Step 2: Create log directory**

```bash
mkdir -p ~/.voice-command/logs
```

### **Step 3: Install the Launch Agent**

Copy the plist file to the LaunchAgents directory:

```bash
cp /Users/jeremygatt/Projects/voice-command-mac/com.voicecommand.plist ~/Library/LaunchAgents/
```

### **Step 4: Load the Launch Agent**

```bash
launchctl load ~/Library/LaunchAgents/com.voicecommand.plist
```

### **Step 5: Verify it's running**

```bash
launchctl list | grep voicecommand
```

You should see something like:
```
- 0 com.voicecommand.listener
```

---

## **Monitoring & Debugging**

### **View startup logs:**
```bash
tail -f ~/.voice-command/logs/startup.log
```

### **View errors:**
```bash
tail -f ~/.voice-command/logs/errors.log
```

### **View system output:**
```bash
tail -f ~/.voice-command/logs/stdout.log
tail -f ~/.voice-command/logs/stderr.log
```

### **Check if it's running:**
```bash
launchctl list | grep voicecommand
```

### **Stop the service:**
```bash
launchctl stop com.voicecommand.listener
```

### **Start the service:**
```bash
launchctl start com.voicecommand.listener
```

### **Unload the service (remove from auto-start):**
```bash
launchctl unload ~/Library/LaunchAgents/com.voicecommand.plist
```

### **Reload the service (after making changes):**
```bash
launchctl unload ~/Library/LaunchAgents/com.voicecommand.plist
launchctl load ~/Library/LaunchAgents/com.voicecommand.plist
```

---

## **How it works:**

**On Login:**
1. macOS runs the Launch Agent
2. Calls `voice-command-startup.sh`
3. Script activates Python venv
4. Runs `python3 src/main.py run --detect-device`
5. App waits for Jabra device to be connected
6. Once connected, voice listener starts
7. Logs all activity to `~/.voice-command/logs/`

**Retry Logic:**
- Initial retry delay: 5 seconds
- Exponential backoff: 5s, 10s, 20s, 40s, etc (capped at 60s)
- Infinite retries until device is found
- Lists available devices in logs so you can debug

---

## **Troubleshooting:**

### **Service not starting?**
1. Check logs: `tail -f ~/.voice-command/logs/startup.log`
2. Verify plist is correct: `cat ~/Library/LaunchAgents/com.voicecommand.plist`
3. Check file permissions: `ls -la ~/Library/LaunchAgents/com.voicecommand.plist`

### **Jabra not being detected?**
1. Make sure Jabra is actually connected via Bluetooth/USB
2. Check available devices: `python3 src/main.py list-audio-devices`
3. Verify it appears in System Preferences → Sound → Input

### **App keeps crashing?**
1. Check error logs: `tail -f ~/.voice-command/logs/errors.log`
2. Run manually with: `python3 src/main.py run`
3. Check Deepgram API key is set: `echo $DEEPGRAM_API_KEY`

---

## **Quick Start:**

```bash
# One-liner to set everything up:
cd /Users/jeremygatt/Projects/voice-command-mac && \
chmod +x voice-command-startup.sh && \
mkdir -p ~/.voice-command/logs && \
cp com.voicecommand.plist ~/Library/LaunchAgents/ && \
launchctl load ~/Library/LaunchAgents/com.voicecommand.plist

# Verify it's running:
launchctl list | grep voicecommand

# Watch the logs:
tail -f ~/.voice-command/logs/startup.log
```

---

## **What happens when Jabra connects:**

```
[2025-01-17 10:30:15] ================================
[2025-01-17 10:30:15] Voice Command Startup Script
[2025-01-17 10:30:15] ================================
[2025-01-17 10:30:16] Starting voice listener with device detection...
[2025-01-17 10:30:16] Waiting for Jabra device...
[2025-01-17 10:30:20] ❌ Jabra device NOT found. Retrying...
[2025-01-17 10:30:20] Available input devices:
[2025-01-17 10:30:20]   - MacBook Pro Microphone
[2025-01-17 10:30:20] Retrying in 5s... (attempt 1)
[2025-01-17 10:31:25] 🎤 Jabra device connected, starting voice listener...
[2025-01-17 10:31:26] ✅ Connected to Deepgram WebSocket
[2025-01-17 10:31:26] Voice command listener started
```

Perfect! Now you're ready! 🚀

