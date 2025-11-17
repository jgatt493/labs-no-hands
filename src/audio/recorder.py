import pyaudio
import asyncio
from typing import Callable
from logger import logger


class AudioRecorder:
    """Records audio from microphone using PyAudio callback pattern"""

    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_size: int = 4096,
        channels: int = 1,
    ):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.is_recording = False

        # PyAudio setup
        self.p = pyaudio.PyAudio()

        # Find default input device
        self.device_index = self._find_input_device()
        if self.device_index is None:
            logger.error("No audio input device found")
            raise RuntimeError("No audio input device found")

        self.stream = None
        self.audio_queue = asyncio.Queue()

    def _find_input_device(self) -> int:
        """Find the default audio input device"""
        try:
            default_device = self.p.get_default_input_device_info()
            logger.info(
                f"Using audio device: {default_device['name']} "
                f"(channels: {default_device['maxInputChannels']})"
            )
            return default_device["index"]
        except Exception as e:
            logger.error(f"Error finding audio device: {e}")
            return None

    @staticmethod
    def is_jabra_connected() -> bool:
        """Check if Jabra headset is connected"""
        try:
            p = pyaudio.PyAudio()
            for i in range(p.get_device_count()):
                device_info = p.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    device_name = device_info['name'].lower()
                    if 'jabra' in device_name:
                        logger.info(f"✅ Jabra device found: {device_info['name']}")
                        p.terminate()
                        return True
            p.terminate()
            return False
        except Exception as e:
            logger.error(f"Error checking for Jabra: {e}")
            return False

    @staticmethod
    def list_input_devices() -> list:
        """List all available input devices"""
        try:
            p = pyaudio.PyAudio()
            devices = []
            for i in range(p.get_device_count()):
                device_info = p.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    devices.append({
                        'index': i,
                        'name': device_info['name'],
                        'channels': device_info['maxInputChannels']
                    })
            p.terminate()
            return devices
        except Exception as e:
            logger.error(f"Error listing devices: {e}")
            return []

    def _mic_callback(self, in_data, frame_count, time_info, status_flag):
        """PyAudio callback that puts audio into async queue"""
        if status_flag:
            logger.debug(f"Audio callback status: {status_flag}")
        
        # Put audio data into the queue (non-blocking)
        try:
            self.audio_queue.put_nowait(in_data)
        except asyncio.QueueFull:
            logger.warning("Audio queue full, dropping frame")
        
        return (in_data, pyaudio.paContinue)

    async def start_recording(self, callback: Callable[[bytes], None]):
        """Start recording and stream audio chunks"""
        try:
            # Open stream with callback
            self.stream = self.p.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._mic_callback,
            )

            self.is_recording = True
            self.stream.start_stream()

            # Main loop: read from queue and send to callback
            chunk_count = 0
            while self.is_recording and self.stream.is_active():
                try:
                    # Wait for audio from queue (with timeout)
                    audio_data = await asyncio.wait_for(
                        self.audio_queue.get(), 
                        timeout=1.0
                    )
                    
                    if audio_data:
                        chunk_count += 1
                        
                        # Send to callback
                        await callback(audio_data)
                        
                except asyncio.TimeoutError:
                    # Queue timeout is normal - just means no audio yet
                    continue
                except Exception as e:
                    logger.error(f"Error processing audio: {e}")
                    break

        except Exception as e:
            logger.error(f"Error in recording: {e}")
            raise
        finally:
            await self.stop_recording()

    async def stop_recording(self):
        """Stop recording and close stream"""
        self.is_recording = False
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception as e:
                logger.error(f"Error stopping stream: {e}")
        if self.p:
            try:
                self.p.terminate()
            except Exception as e:
                logger.error(f"Error terminating PyAudio: {e}")

    def check_microphone(self) -> bool:
        """Check if microphone is accessible"""
        try:
            test_stream = self.p.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.chunk_size,
            )
            test_stream.close()
            logger.info("Microphone check: OK")
            return True
        except Exception as e:
            logger.error(f"Microphone check failed: {e}")
            return False

    def __del__(self):
        """Cleanup PyAudio resources"""
        try:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
        except Exception:
            pass
        try:
            if self.p:
                self.p.terminate()
        except Exception:
            pass
