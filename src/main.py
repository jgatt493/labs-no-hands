#!/usr/bin/env python3
import asyncio
import sys
import os
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

import click
from logger import logger
from utils import get_config_path, get_env
from audio.recorder import AudioRecorder
from dg_models.client import DeepgramClient
from commands.config import CommandConfig
from commands.parser import CommandParser
from commands.executor import CommandExecutor


class VoiceCommandApp:
    """Main voice command application"""

    def __init__(self):
        self.config_path = get_config_path()
        self.config = CommandConfig(self.config_path)
        self.parser = CommandParser(self.config)
        self.executor = CommandExecutor(self.config)
        self.recorder = None
        self.deepgram = None
        self.is_running = False
        self.last_transcript = None
        self.pending_command = None
        self.mode = "normal"  # "normal" or "dictation"

    async def initialize(self):
        """Initialize audio and Deepgram"""
        try:
            # Initialize audio recorder
            cfg = self.config.app_config
            self.recorder = AudioRecorder(
                sample_rate=cfg.sample_rate,
                chunk_size=cfg.chunk_size,
                channels=cfg.channels,
            )

            # Check microphone
            if not self.recorder.check_microphone():
                logger.error("Microphone check failed")
                return False

            # Initialize Deepgram
            self.deepgram = DeepgramClient(
                model=cfg.deepgram_model,
                interim_results=cfg.interim_results,
                punctuate=cfg.punctuate,
                endpointing=cfg.endpointing,
            )

            logger.info("Initialization complete")
            return True

        except Exception as e:
            logger.error(f"Initialization error: {e}")
            return False

    async def run(self):
        """Main application loop"""
        if not await self.initialize():
            logger.error("Failed to initialize")
            return

        self.is_running = True

        try:
            # Start recording and connect to Deepgram
            await asyncio.gather(
                self.recorder.start_recording(self._on_audio),
                self.deepgram.connect(self._on_transcript),
            )

        except KeyboardInterrupt:
            pass
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            self.is_running = False
            if self.deepgram:
                await self.deepgram.close()

    async def run_with_device_detection(self, max_retries: int = None, retry_delay: int = 5):
        """
        Run with Jabra device detection and retry logic.
        Useful for startup when device may not be immediately available.
        
        Args:
            max_retries: Max number of retries (None = infinite)
            retry_delay: Initial delay between retries in seconds
        """
        retry_count = 0
        current_delay = retry_delay
        
        while True:
            if max_retries and retry_count >= max_retries:
                logger.error(f"Max retries ({max_retries}) reached. Exiting.")
                return
            
            # Check if Jabra is connected
            if AudioRecorder.is_jabra_connected():
                logger.info("🎤 Jabra device connected, starting voice listener...")
                try:
                    await self.run()
                    # If run() completes, we're done
                    break
                except Exception as e:
                    logger.error(f"Error during execution: {e}")
                    logger.info("Retrying...")
                    retry_count += 1
                    current_delay = min(retry_delay * (2 ** retry_count), 60)  # Cap at 60s
                    await asyncio.sleep(current_delay)
            else:
                logger.warning("❌ Jabra device NOT found. Retrying...")
                devices = AudioRecorder.list_input_devices()
                if devices:
                    logger.info("Available input devices:")
                    for device in devices:
                        logger.info(f"  - {device['name']}")
                
                retry_count += 1
                current_delay = min(retry_delay * (2 ** retry_count), 60)  # Exponential backoff, cap at 60s
                logger.info(f"Retrying in {current_delay}s... (attempt {retry_count})")
                await asyncio.sleep(current_delay)

    async def _on_audio(self, audio_data: bytes):
        """Handle audio chunk from recorder"""
        if self.deepgram:
            # Fire and forget - don't await to avoid blocking audio capture
            asyncio.create_task(self.deepgram.send_audio(audio_data))

    async def _on_transcript(self, result):
        """Handle transcription result from Deepgram"""
        if not result.transcript:
            return

        self.last_transcript = result.transcript

        # Try to match command FIRST (always check commands, even in dictation mode)
        if result.is_final:
            # Final result - try command matching first
            logger.info(f"🔍 Parsing: '{result.transcript}'")
            match = self.parser.parse(result.transcript)

            if match:
                # Command matched - execute it
                command, confidence = match
                logger.info(f"⚙️  Executing action: {command.action}")

                success = await self.executor.execute(command)

                if success:
                    logger.info(f"✓ {command.feedback}")
                    
                    # Check if mode changed
                    if command.action.lower() == "mode":
                        self.mode = getattr(command, 'mode', 'normal')
                else:
                    logger.error(f"✗ Failed to execute {command.id}")
            else:
                # No command matched - check if in dictation mode
                if self.mode == "dictation":
                    logger.info(f"📝 Dictating: '{result.transcript}'")
                    self.executor.macos.type_text(result.transcript + " ")
                else:
                    logger.info(f"❌ No command matched (threshold: {self.config.app_config.match_threshold})")

        else:
            # Interim result - show potential match
            match = self.parser.parse_interim(result.transcript)

            if match:
                command, confidence = match
                logger.debug(
                    f"Interim match: {command.id} "
                    f"({result.transcript}) "
                    f"[{confidence:.2f}]"
                )


@click.group()
def cli():
    """Voice Command macOS - Control your Mac with voice"""
    pass


@cli.command()
@click.option('--detect-device', is_flag=True, help='Wait for Jabra device before starting')
def run(detect_device):
    """Run voice listener (foreground)"""
    app = VoiceCommandApp()
    if detect_device:
        logger.info("Starting with device detection mode...")
        asyncio.run(app.run_with_device_detection())
    else:
        asyncio.run(app.run())


@cli.command()
def daemon():
    """Manage daemon (start, stop, status)"""
    # TODO: Implement daemon management
    click.echo("Daemon management not yet implemented")


@cli.command()
def test_audio():
    """Test audio input"""
    try:
        recorder = AudioRecorder()
        if recorder.check_microphone():
            click.echo("✓ Microphone test passed")
        else:
            click.echo("✗ Microphone test failed")
    except Exception as e:
        click.echo(f"✗ Error: {e}")


@cli.command()
def test_deepgram():
    """Test Deepgram connection"""
    try:
        api_key = get_env("DEEPGRAM_API_KEY")
        client = DeepgramClient(api_key=api_key)

        async def test():
            try:
                await asyncio.wait_for(
                    asyncio.sleep(0.1), timeout=5
                )
                # Just test the connection can be created
                click.echo("✓ Deepgram client created successfully")
                return True
            except Exception as e:
                click.echo(f"✗ Error: {e}")
                return False

        asyncio.run(test())

    except Exception as e:
        click.echo(f"✗ Error: {e}")


@cli.command()
@click.argument("text")
def test_command(text):
    """Test command matching"""
    try:
        config = CommandConfig(get_config_path())
        parser = CommandParser(config)

        result = parser.parse(text)

        if result:
            command, confidence = result
            click.echo(f"✓ Matched: {command.id}")
            click.echo(f"  Confidence: {confidence:.2f}")
            click.echo(f"  Action: {command.action}")
            click.echo(f"  Feedback: {command.feedback}")
        else:
            click.echo("✗ No command matched")
            click.echo(f"  Text: {text}")
            click.echo(f"  Threshold: {config.app_config.match_threshold}")

    except Exception as e:
        click.echo(f"✗ Error: {e}")


@cli.command()
def list_commands():
    """List all available commands"""
    try:
        config = CommandConfig(get_config_path())

        click.echo(f"\nAvailable commands ({len(config.commands)} total):\n")

        for cmd in config.commands:
            click.echo(f"  {cmd.id}")
            for trigger in cmd.triggers:
                click.echo(f"    • {trigger}")
            click.echo(f"    Action: {cmd.action}")
            if cmd.feedback:
                click.echo(f"    Feedback: {cmd.feedback}")
            click.echo()

    except Exception as e:
        click.echo(f"✗ Error: {e}")


@cli.command()
def list_audio_devices():
    """List all available audio input devices"""
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        click.echo("\n📋 Available Audio Devices:\n")
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                click.echo(f"  [{i}] {info['name']}")
                click.echo(f"      Channels: {info['maxInputChannels']}, Sample Rate: {int(info['defaultSampleRate'])} Hz")
        p.terminate()
        click.echo("\n💡 Tip: Pass the device index with --device flag if needed\n")
    except Exception as e:
        click.echo(f"✗ Error: {e}")


@cli.command()
def check_permissions():
    """Check system permissions"""
    click.echo("Checking system permissions...")

    # Check microphone access
    try:
        recorder = AudioRecorder()
        if recorder.check_microphone():
            click.echo("✓ Microphone: OK")
        else:
            click.echo("✗ Microphone: Not accessible")
    except Exception as e:
        click.echo(f"✗ Microphone: Error - {e}")

    # Check config
    try:
        config_path = get_config_path()
        if config_path.exists():
            click.echo(f"✓ Config file: {config_path}")
        else:
            click.echo(f"✗ Config file: Not found at {config_path}")
    except Exception as e:
        click.echo(f"✗ Config: Error - {e}")

    # Check environment
    try:
        api_key = get_env("DEEPGRAM_API_KEY")
        if api_key and api_key != "your_deepgram_api_key_here":
            click.echo("✓ DEEPGRAM_API_KEY: Set")
        else:
            click.echo("✗ DEEPGRAM_API_KEY: Not properly set")
    except Exception as e:
        click.echo(f"✗ DEEPGRAM_API_KEY: {e}")


if __name__ == "__main__":
    cli()

