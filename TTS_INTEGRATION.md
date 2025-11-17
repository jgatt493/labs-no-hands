# Deepgram TTS Integration Guide

When you're ready to add audio feedback via Deepgram Text-to-Speech, use this guide.

## Overview

The voice command app will support audio feedback when a command is executed, saying confirmation like:
- "Opened files panel"
- "Copied to clipboard"
- "Launching Chrome"

## Integration Points

### 1. Add TTS Client (`src/deepgram/tts_client.py`)

```python
import asyncio
from deepgram import DeepgramClient, PrerecordedOptions

class DeepgramTTSClient:
    def __init__(self, api_key: str, voice_model: str = "aura-2-odysseus-en"):
        self.client = DeepgramClient(api_key=api_key)
        self.voice_model = voice_model
    
    async def speak(self, text: str) -> bytes:
        """Convert text to speech and return audio bytes"""
        options = PrerecordedOptions(
            model=self.voice_model,
            encoding="linear16",
            sample_rate=16000,
        )
        
        response = await self.client.speak.v("1").stream(
            {"text": text}, options=options
        )
        
        return response.stream.getvalue()
```

### 2. Add Playback (`src/audio/player.py`)

```python
import pyaudio
import numpy as np

class AudioPlayer:
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.p = pyaudio.PyAudio()
    
    async def play(self, audio_bytes: bytes):
        """Play audio bytes"""
        stream = self.p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            output=True,
        )
        
        stream.write(audio_bytes)
        stream.stop_stream()
        stream.close()
```

### 3. Update Command Executor (`src/commands/executor.py`)

```python
from deepgram.tts_client import DeepgramTTSClient
from audio.player import AudioPlayer

class CommandExecutor:
    def __init__(self, tts_client=None, player=None):
        self.tts_client = tts_client
        self.player = player
    
    async def execute(self, command: CommandAction) -> bool:
        # ... existing execution code ...
        
        # Add feedback
        if command.feedback and self.tts_client and self.player:
            try:
                audio = await self.tts_client.speak(command.feedback)
                await self.player.play(audio)
            except Exception as e:
                logger.error(f"TTS playback error: {e}")
        
        return True
```

### 4. Update Main App (`src/main.py`)

```python
class VoiceCommandApp:
    async def initialize(self):
        # ... existing code ...
        
        # Initialize TTS
        if os.getenv("ENABLE_TTS", "false").lower() == "true":
            self.tts_client = DeepgramTTSClient(
                api_key=get_env("DEEPGRAM_API_KEY"),
                voice_model=os.getenv("TTS_VOICE_MODEL", "aura-2-odysseus-en")
            )
            self.audio_player = AudioPlayer()
            
            # Update executor
            self.executor = CommandExecutor(
                tts_client=self.tts_client,
                player=self.audio_player
            )
```

### 5. Update Configuration (`dotenv`)

```
# Enable TTS feedback
ENABLE_TTS=true

# TTS voice model (optional)
TTS_VOICE_MODEL=aura-2-odysseus-en
```

### 6. Update Config YAML (`config/commands.yaml`)

```yaml
config:
  enable_feedback: true
  feedback_type: "audio"  # visual, audio, or both
```

## Available Deepgram Voices

Some popular voice models:

- `aura-asteria-en` - Female, natural
- `aura-luna-en` - Female, warm
- `aura-stella-en` - Female, expressive
- `aura-athena-en` - Female, professional
- `aura-hades-en` - Male, deep
- `aura-zeus-en` - Male, powerful
- `aura-arcas-en` - Male, friendly
- `aura-orpheus-en` - Male, melodic
- `aura-helios-en` - Male, energetic

[See all Deepgram voices](https://developers.deepgram.com/reference/text-to-speech)

## Implementation Steps

1. **Install updated dependencies:**
   ```bash
   pip install deepgram-sdk>=3.0.0
   ```

2. **Create TTS files:**
   - `src/deepgram/tts_client.py` - TTS client
   - `src/audio/player.py` - Audio playback

3. **Update existing files:**
   - Modify `src/commands/executor.py`
   - Modify `src/main.py`
   - Update `dotenv` with TTS settings
   - Update `config/commands.yaml`

4. **Test TTS:**
   ```bash
   # Run with TTS enabled
   ENABLE_TTS=true python3 src/main.py run
   ```

## Error Handling

Wrap TTS in try-catch to handle:
- Network errors (Deepgram API unavailable)
- Audio device errors (speaker not available)
- Rate limiting (too many simultaneous requests)

The app should continue functioning if TTS fails (graceful degradation).

## Performance Considerations

- **Latency**: TTS adds 200-500ms to command execution
- **Cost**: Each TTS request counts toward Deepgram quota
- **Network**: Requires stable internet connection

## Alternative: Local Feedback

If you want instant feedback without TTS:

```python
# Use system sounds
import os
os.system("afplay /System/Library/Sounds/Glass.aiff")

# Or use text-to-speech visualization in logs
logger.info(f"🎤 {command.feedback}")
```

## Next Steps

When ready to implement TTS:
1. Copy the code snippets above
2. Create the new files
3. Update existing files
4. Test with `ENABLE_TTS=true`
5. Configure voice model in dotenv

The integration is designed to be non-breaking - the app works perfectly without TTS.

---

**Ready when you are!** Reach out when you want to add audio feedback. 🎙️

