# Voice Command macOS

A lightweight voice command application for macOS that listens to your voice and executes keyboard/mouse commands or launches applications.

**Features:**
- 🎙️ Real-time voice recognition via Deepgram
- ⚡ Low-latency command matching with fuzzy logic
- ⌨️ Keyboard shortcuts, mouse clicks, app launching
- 🔧 Easy YAML-based command configuration
- 🚀 Runs as a background daemon
- 🔐 Privacy-focused (local processing)

## Quick Start

### Prerequisites
- macOS 10.15+
- Python 3.10+
- Deepgram API key

### Installation

1. **Clone/setup the project:**
```bash
cd /Users/jeremygatt/Projects/voice-command-mac
python -m venv venv
source venv/bin/activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment:**
```bash
cp .env.example .env
# Edit .env and add your DEEPGRAM_API_KEY
nano .env
```

4. **Grant microphone permission:**
```bash
# Run once to grant microphone access
python src/main.py --check-permissions
```

### Running

**Development (foreground):**
```bash
python src/main.py run
```

**As daemon (background):**
```bash
python src/main.py daemon start
python src/main.py daemon stop
python src/main.py daemon status
```

**Auto-start on login:**
```bash
python src/main.py daemon install
# Uninstall with: python src/main.py daemon uninstall
```

## Configuration

Edit `config/commands.yaml` to add/modify voice commands:

```yaml
commands:
  - id: "focus_chat"
    triggers:
      - "focus chat"
      - "click on chat"
    action: click
    coordinates: [640, 400]
    feedback: "Focusing chat window"

  - id: "open_files"
    triggers:
      - "open files"
    action: keystroke
    keys: ["cmd", "b"]
    feedback: "Opening files panel"
```

## Command Types

### Click (Mouse)
```yaml
action: click
coordinates: [x, y]      # Pixel coordinates
button: "left"           # left, right, middle (optional)
```

### Keystroke
```yaml
action: keystroke
keys: ["cmd", "b"]       # Key combinations
```

### Launch App
```yaml
action: launch
app: "Google Chrome"     # App name from /Applications
```

### Type Text
```yaml
action: type
text: "Hello world"      # Text to type
```

## Logs

View real-time logs:
```bash
tail -f ~/.voice-command/logs/voice-command.log
```

## Troubleshooting

**Microphone not recognized:**
```bash
python src/main.py --check-audio
```

**Commands not matching:**
- Lower the `match_threshold` in `config/commands.yaml`
- Check logs for transcription output
- Test with: `python src/main.py --test-transcript "your text"`

**Deepgram connection issues:**
- Verify `DEEPGRAM_API_KEY` in `.env`
- Check internet connection
- Run `python src/main.py --test-deepgram`

## Advanced

### Enable interim results (lower latency):
In `config/commands.yaml`:
```yaml
config:
  interim_results: true
  endpointing: 100  # ms to wait before finalizing
```

### Custom feedback sounds:
In `config/commands.yaml`:
```yaml
commands:
  - id: "example"
    triggers: ["example"]
    action: keystroke
    keys: ["cmd", "c"]
    feedback_sound: "/path/to/sound.mp3"
```

## Development

### Project structure:
```
src/
├── main.py              # Entry point & CLI
├── daemon.py            # Daemon management
├── audio/               # Audio capture
├── deepgram/            # Deepgram integration
├── commands/            # Command processing
├── automation/          # macOS automation
└── logger.py            # Logging
```

### Run tests:
```bash
python -m pytest tests/
```

## License

MIT

