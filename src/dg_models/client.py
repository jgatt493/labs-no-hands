import asyncio
import json
import websockets
from typing import Callable, Optional
from logger import logger
from dg_models.models import TranscriptionResult
from utils import get_env


class DeepgramClient:
    """Deepgram streaming client using raw websockets (proven approach)"""

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
        url = self._build_url()

        try:
            logger.info(f"🔌 Connecting to Deepgram...")
            
            # Headers for authorization
            headers = {
                "Authorization": f"Token {self.api_key}"
            }
            
            # Connect with 20 second timeout for handshake
            async with websockets.connect(
                url, 
                additional_headers=headers,
                open_timeout=20
            ) as ws:
                self.ws = ws
                self.connected = True
                logger.info("✅ Connected to Deepgram WebSocket")
                
                # Run receiver and keepalive concurrently
                # The receiver will block until connection closes
                await asyncio.gather(
                    self._receiver(on_transcript),
                    self._keepalive(),
                    return_exceptions=True
                )

        except asyncio.CancelledError:
            logger.info("Deepgram connection cancelled")
        except Exception as e:
            logger.error(f"❌ Deepgram connection error: {e}")
            raise
        finally:
            self.connected = False
            logger.info("Deepgram connection closed")

    async def send_audio(self, audio_data: bytes):
        """Send audio chunk to Deepgram"""
        if self.ws and self.connected:
            try:
                await self.ws.send(audio_data)
            except Exception as e:
                logger.error(f"❌ Error sending audio: {e}")

    async def _keepalive(self):
        """Send periodic KeepAlive messages"""
        try:
            while self.connected:
                await asyncio.sleep(5)
                if self.ws and self.connected:
                    try:
                        await self.ws.send(json.dumps({"type": "KeepAlive"}))
                    except Exception as e:
                        logger.error(f"❌ Error sending keepalive: {e}")
                        break
        except asyncio.CancelledError:
            pass

    async def _receiver(
        self, on_transcript: Callable[[TranscriptionResult], None]
    ):
        """Receive and process messages from Deepgram"""
        try:
            async for message in self.ws:
                try:
                    # Handle binary data (audio echo)
                    if isinstance(message, bytes):
                        continue
                    
                    # Parse JSON messages
                    data = json.loads(message)
                    msg_type = data.get("type")

                    if msg_type == "Results":
                        # Only log and process FINAL results
                        if data.get("is_final"):
                            channel = data.get("channel", {})
                            alternatives = channel.get("alternatives", [])

                            if alternatives:
                                alt = alternatives[0]
                                transcript = alt.get("transcript", "")
                                confidence = alt.get("confidence", 0.0)
                                
                                if transcript:
                                    logger.info(f"{transcript}")
                                    
                                    # Create result for command processor
                                    result = TranscriptionResult(
                                        type="Results",
                                        is_final=True,
                                        speech_final=data.get("speech_final", False),
                                        transcript=transcript,
                                        confidence=confidence,
                                        duration=data.get("duration"),
                                        channel_index=data.get("channel_index"),
                                    )
                                    await on_transcript(result)

                except json.JSONDecodeError:
                    pass
                except Exception as e:
                    logger.error(f"❌ Error processing message: {e}")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"❌ Error in receiver: {e}")

    def _build_url(self) -> str:
        """Build Deepgram WebSocket URL"""
        base_url = "wss://api.deepgram.com/v1/listen"

        params = [
            f"model={self.model}",
            f"interim_results={'true' if self.interim_results else 'false'}",
            f"punctuate={'true' if self.punctuate else 'false'}",
            f"endpointing={'true' if self.endpointing else 'false'}",
            "encoding=linear16",
            "sample_rate=16000",
        ]

        return f"{base_url}?{'&'.join(params)}"

    async def close(self):
        """Close the connection"""
        self.connected = False
        if self.ws:
            try:
                await self.ws.close()
            except Exception as e:
                logger.debug(f"Error closing: {e}")
