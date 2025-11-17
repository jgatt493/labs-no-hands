from typing import Optional, Tuple
import re
from fuzzywuzzy import fuzz
from logger import logger
from commands.config import CommandConfig, CommandAction


class CommandParser:
    """Parse voice transcripts into commands"""

    def __init__(self, config: CommandConfig):
        self.config = config
        self.triggers_map = config.get_all_triggers()

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalize text: lowercase, strip whitespace, remove punctuation"""
        # Lowercase and strip
        text = text.lower().strip()
        # Remove punctuation (keep only alphanumeric and spaces)
        text = re.sub(r'[^\w\s]', '', text)
        # Collapse multiple spaces into one
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def parse(self, transcript: str) -> Optional[Tuple[CommandAction, float]]:
        """
        Parse transcript and find matching command.
        Returns (CommandAction, confidence_score) or None if no match.
        Handles variations like "open chrome", "Open Chrome.", "Open Chrome?"
        """
        if not transcript or not transcript.strip():
            return None

        transcript_clean = self._normalize_text(transcript)
        best_match = None
        best_score = 0.0

        # Try to match against all triggers
        for cmd in self.config.commands:
            for trigger in cmd.triggers:
                trigger_clean = self._normalize_text(trigger)

                # Use token_set_ratio for better matching
                score = fuzz.token_set_ratio(
                    transcript_clean, trigger_clean
                ) / 100.0

                if (
                    score > best_score
                    and score >= self.config.app_config.match_threshold
                ):
                    best_match = cmd
                    best_score = score

        if best_match:
            logger.info(
                f"✅ Matched: {best_match.id} (score: {best_score:.2f})"
            )
            return best_match, best_score
        else:
            logger.debug(
                f"No command match for: {transcript} "
                f"(threshold: {self.config.app_config.match_threshold})"
            )
            return None

    def parse_interim(self, transcript: str) -> Optional[Tuple[CommandAction, float]]:
        """
        Parse interim transcription (continuous update).
        More lenient matching for real-time feedback.
        """
        if not transcript or not transcript.strip():
            return None

        transcript_clean = self._normalize_text(transcript)
        best_match = None
        best_score = 0.0

        # More lenient threshold for interim results
        threshold = self.config.app_config.match_threshold - 0.1

        for cmd in self.config.commands:
            for trigger in cmd.triggers:
                trigger_clean = self._normalize_text(trigger)

                # For interim results, use partial_ratio for earlier matches
                score = fuzz.partial_token_set_ratio(
                    transcript_clean, trigger_clean
                ) / 100.0

                if score > best_score and score >= threshold:
                    best_match = cmd
                    best_score = score

        return (best_match, best_score) if best_match else None

