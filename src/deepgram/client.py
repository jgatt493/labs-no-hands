import asyncio
from typing import Callable, Optional
from logger import logger

# Use absolute imports to avoid conflict with local deepgram package
import sys
sys.path.insert(0, '/Users/jeremygatt/Projects/voice-command-mac/venv/lib/python3.9/site-packages')

from deepgram.models import TranscriptionResult
from utils import get_env

# Import from installed deepgram SDK, not local package
try:
    from deepgram import AsyncDeepgramClient
except ImportError as e:
    from deepgram_sdk import AsyncDeepgramClient  # Fallback

# Restore path
sys.path.pop(0)


class DeepgramClient:
    """Deepgram streaming client using official SDK"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "nova-3",
        interim_results: bool = True,
        punctuate: bool = True,
        endpointing: bool = True,
    ):
        self.api_key = api_key or get_env("DEEPGRAM_API_KEY")
        self.model = model
        self.interim_results = interim_results
        self.punctuate = punctuate
        self.endpointing = endpointing
        self.ws = None
        self.connected = False

    async def connect(
        self, on_transcript: Callable[[TranscriptionResult], None]
    ):
        """Connect to Deepgram and stream audio"""
        try:
            logger.info(f"🔌 Connecting to Deepgram with {self.model}...")
            
            # Create async Deepgram client
            client = AsyncDeepgramClient(api_key=self.api_key)
            
            # Create live streaming options
            options = {
                "model": self.model,
                "interim_results": self.interim_results,
                "punctuate": self.punctuate,
                "endpointing": self.endpointing,
                "encoding": "linear16",
                "sample_rate": 16000,
            }
            
            # Create WebSocket connection for live streaming
            self.ws = await client.listen.v1.live(options)
            self.connected = True
            logger.info("✅ Connected to Deepgram WebSocket")
            
            # Listen for results
            await self._listen(on_transcript)

        except asyncio.CancelledError:
            logger.info("Deepgram connection cancelled")
        except Exception as e:
            logger.error(f"❌ Deepgram connection error: {e}")
            raise
        finally:
            self.connected = False
            logger.info("Deepgram connection closed")

    async def send_audio(self, audio_data: bytes):
        """Send audio chunk to Deepgram (non-blocking)"""
        if self.ws and self.connected:
            try:
                await self.ws.send(audio_data)
                # Log every 50 chunks
                if not hasattr(self, '_audio_chunk_count'):
                    self._audio_chunk_count = 0
                self._audio_chunk_count += 1
                if self._audio_chunk_count % 50 == 0:
                    logger.info(f"🔊 {self._audio_chunk_count} chunks sent")
            except Exception as e:
                logger.error(f"❌ Error sending audio: {e}")

    async def _listen(
        self, on_transcript: Callable[[TranscriptionResult], None]
    ):
        """Listen for transcription results from Deepgram"""
        try:
            async for message in self.ws:
                try:
                    # Check if this is a transcription result
                    if hasattr(message, 'type'):
                        msg_type = message.type

                        if msg_type == "Results":
                            # Extract transcription from results
                            if (hasattr(message, 'channel') and 
                                hasattr(message.channel, 'alternatives') and
                                message.channel.alternatives):
                                
                                alt = message.channel.alternatives[0]
                                transcript = alt.transcript if hasattr(alt, 'transcript') else ""
                                confidence = alt.confidence if hasattr(alt, 'confidence') else 0.0
                                
                                if transcript:
                                    status = "✅ FINAL" if message.is_final else "🔄 interim"
                                    logger.info(
                                        f"{status} | {transcript} "
                                        f"[{confidence:.2f}]"
                                    )
                                    
                                    # Create result object for command processor
                                    result = TranscriptionResult(
                                        type="Results",
                                        is_final=message.is_final,
                                        speech_final=getattr(message, 'speech_final', False),
                                        transcript=transcript,
                                        confidence=confidence,
                                        duration=None,
                                        channel_index=0,
                                    )
                                    await on_transcript(result)

                        elif msg_type == "SpeechStarted":
                            logger.info("🎤 Speech detected")

                        elif msg_type == "UtteranceEnd":
                            logger.info("⏹️ Utterance end")

                except Exception as e:
                    logger.error(f"❌ Error processing message: {e}")

        except asyncio.CancelledError:
            logger.info("Listening cancelled")
        except Exception as e:
            logger.error(f"❌ Error in listen loop: {e}")

    async def close(self):
        """Close the connection"""
        try:
            if self.ws:
                await self.ws.finish()
        except Exception as e:
            logger.debug(f"Error closing connection: {e}")
        self.connected = False
