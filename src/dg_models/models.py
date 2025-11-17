from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class Word:
    """Word-level transcription data"""

    word: str
    start: float
    end: float
    confidence: float
    punctuated_word: Optional[str] = None
    speaker: Optional[int] = None


@dataclass
class Alternative:
    """Alternative transcription"""

    transcript: str
    confidence: float
    words: List[Word]
    languages: Optional[List[str]] = None


@dataclass
class Channel:
    """Channel transcription data"""

    alternatives: List[Alternative]


@dataclass
class Metadata:
    """Metadata about transcription"""

    request_id: str
    created: str
    duration: float
    channels: int
    model_info: Optional[Dict[str, Any]] = None


@dataclass
class TranscriptionResult:
    """Complete transcription result"""

    type: str
    is_final: bool
    speech_final: bool
    transcript: str
    confidence: float
    duration: Optional[float] = None
    channel_index: Optional[List[int]] = None

