# Installation & Setup Guide

## System Requirements

- **macOS**: 10.15 or later
- **Python**: 3.9 or later
- **Deepgram API**: Free tier account (https://console.deepgram.com)
- **Microphone**: Any audio input device

## Step-by-Step Installation

### 1. Create Virtual Environment

```bash
cd /Users/jeremygatt/Projects/voice-command-mac
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install python-Levenshtein  # Optional but recommended for performance
```

Or use the automated setup script:

```bash
bash setup.sh
```

### 3. Configure API Key

Edit the configuration file:

```bash
nano dotenv
```

Find this line:
```
DEEPGRAM_API_KEY=your_deepgram_api_key_here
```

Replace with your actual Deepgram API key from https://console.deepgram.com/keys

### 4. Grant Microphone Permissions

On first run, macOS will prompt for microphone access. You may need to:

1. Go to **System Preferences** → **Security & Privacy** → **Microphone**
2. Add Terminal (or your shell) to the allowed apps
3. Restart the application

Test microphone access:
```bash
python3 src/main.py test-audio
```

### 5. Test Everything

```bash
# Check all permissions
python3 src/main.py check-permissions

# Test audio input
python3 src/main.py test-audio

# Test Deepgram (requires API key)
python3 src/main.py test-deepgram

# Test command matching
python3 src/main.py test-command "open files"

# List all available commands
python3 src/main.py list-commands
```

## Running the Application

### Foreground (Testing)

```bash
source venv/bin/activate
python3 src/main.py run
```

You should see:
```
23:54:59 | INFO     | Initialization complete
23:54:59 | INFO     | Voice command listener started
```

Now speak commands like:
- "open files"
- "focus chat"
- "copy"
- "paste"

### Background (Daemon)

To run as a background service that starts automatically:

```bash
# Copy daemon configuration
cp launchd/com.voicecommand.daemon.plist ~/Library/LaunchAgents/

# Load it
launchctl load ~/Library/LaunchAgents/com.voicecommand.daemon.plist

# Verify it's running
launchctl list | grep voicecommand
```

To stop:
```bash
launchctl unload ~/Library/LaunchAgents/com.voicecommand.daemon.plist
```

To view logs:
```bash
tail -f ~/.voice-command/logs/voice-command.log
```

## Customizing Commands

Edit `config/commands.yaml` to add or modify voice commands.

Example adding a new command:

```yaml
commands:
  - id: "my_custom_command"
    triggers:
      - "do something"
      - "do the thing"
    action: keystroke
    keys: ["cmd", "shift", "p"]
    feedback: "Executed custom command"
```

### Available Actions

**Click (Mouse)**
```yaml
action: click
coordinates: [x, y]  # Pixel coordinates on screen
button: "left"       # left, right, or middle (optional)
```

**Keystroke**
```yaml
action: keystroke
keys: ["cmd", "b"]   # Modifier + key combinations
```

**Launch App**
```yaml
action: launch
app: "Google Chrome" # App name from /Applications
```

**Type Text**
```yaml
action: type
text: "Hello world"  # Text to type
```

## Troubleshooting

### Microphone Not Recognized

```bash
# Check audio device
python3 src/main.py test-audio

# If it fails, grant Terminal microphone access:
# System Preferences → Security & Privacy → Microphone
```

### Commands Not Matching

1. Check transcription in logs:
```bash
tail -f ~/.voice-command/logs/voice-command.log
```

2. Test the exact text:
```bash
python3 src/main.py test-command "your exact text"
```

3. Lower the match threshold in `config/commands.yaml`:
```yaml
config:
  match_threshold: 0.70  # Default is 0.80 (lower = more lenient)
```

### Deepgram Connection Fails

1. Verify API key is set:
```bash
grep DEEPGRAM dotenv | head -1
```

2. Check internet connection:
```bash
curl -I https://api.deepgram.com
```

3. Test connection:
```bash
python3 src/main.py test-deepgram
```

### Application Crashes or Stops

Check the error log:
```bash
tail -100 ~/.voice-command/logs/voice-command-error.log
```

If running as daemon:
```bash
# Restart it
launchctl unload ~/Library/LaunchAgents/com.voicecommand.daemon.plist
launchctl load ~/Library/LaunchAgents/com.voicecommand.daemon.plist

# Check status
launchctl list | grep voicecommand
```

### Performance Issues

- **High CPU**: Too many interim results. Set `interim_results: false` in config.yaml
- **High memory**: Long audio buffers. Reduce `chunk_size` in config.yaml
- **Slow response**: Network latency. Check Deepgram status

## Getting Help

Check logs for detailed information:
```bash
# Real-time logs
tail -f ~/.voice-command/logs/voice-command.log

# All debug info
LOG_LEVEL=DEBUG python3 src/main.py run
```

## Next Steps

1. **Customize commands** in `config/commands.yaml`
2. **Update coordinates** for "focus_chat" to match your Cursor window
3. **Test extensively** before setting up as daemon
4. **Monitor logs** initially to ensure commands are triggering correctly
5. **Adjust thresholds** based on your speech patterns

Enjoy voice-controlled macOS! 🎙️

