from typing import Optional, Tuple, Dict
import re
from fuzzywuzzy import fuzz
from logger import logger
from commands.config import CommandConfig, CommandAction
from commands.context_parser import ContextAwareParser

# Try to load semantic similarity model
try:
    from sentence_transformers import SentenceTransformer, util
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False
    logger.warning("sentence-transformers not available - using fuzzy matching fallback")


class CommandParser:
    """Parse voice transcripts into commands"""

    def __init__(self, config: CommandConfig):
        self.config = config
        
        # Initialize context-aware parser
        self.context_parser = ContextAwareParser(config)
        
        # Initialize semantic model if available
        self.semantic_model = None
        self.trigger_embeddings = {}  # Cache embeddings
        
        if SEMANTIC_AVAILABLE:
            try:
                logger.info("Loading semantic similarity model...")
                self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
                self._build_trigger_embeddings()
                logger.info("✓ Semantic model loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load semantic model: {e}")
                self.semantic_model = None

    def _build_trigger_embeddings(self):
        """Pre-compute embeddings for all triggers"""
        if not self.semantic_model:
            return
        
        try:
            all_triggers = []
            
            for cmd in self.config.commands:
                for trigger in cmd.triggers:
                    all_triggers.append(trigger)
            
            # Encode all triggers at once (efficient batch)
            embeddings = self.semantic_model.encode(all_triggers, convert_to_tensor=True)
            
            # Store embeddings
            for trigger, embedding in zip(all_triggers, embeddings):
                self.trigger_embeddings[trigger] = embedding
            
            logger.debug(f"Built embeddings for {len(all_triggers)} triggers")
        except Exception as e:
            logger.error(f"Error building embeddings: {e}")

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalize text: lowercase, strip whitespace, remove punctuation"""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    

    def parse(self, transcript: str, mode: str = "normal") -> Optional[Tuple[CommandAction, float]]:
        """
        Parse transcript using 4-path execution model:
        1. Context-aware parsing (keywords: open/start/stop/close)
        2. Semantic similarity matching
        3. Fuzzy matching fallback
        
        Mode filtering happens via context commands and command definitions.
        """
        if not transcript or not transcript.strip():
            return None

        transcript_clean = self._normalize_text(transcript)
        
        # PATH 1: Try context-aware parser (handles keywords + mode filtering)
        logger.debug(f"Trying context-aware parser for: '{transcript}'")
        context_result = self.context_parser.parse_context(transcript, mode)
        if context_result:
            cmd, score = context_result
            logger.info(f"✅ Matched: {cmd.id} (context-aware, score: {score:.2f})")
            return cmd, score
        logger.debug(f"No context match for: '{transcript}' - trying semantic/fuzzy")
        
        # Normal mode matching - Use semantic similarity if available
        best_match = None
        best_score = 0.0

        if self.semantic_model and self.trigger_embeddings:
            # Semantic matching (more robust)
            try:
                # Encode the transcript
                transcript_embedding = self.semantic_model.encode(transcript, convert_to_tensor=True)
                
                # Compare against all trigger embeddings
                for cmd in self.config.commands:
                    for trigger in cmd.triggers:
                        if trigger in self.trigger_embeddings:
                            trigger_embedding = self.trigger_embeddings[trigger]
                            # Calculate cosine similarity (0-1 range)
                            similarity = util.pytorch_cos_sim(
                                transcript_embedding, trigger_embedding
                            )[0][0].item()
                            
                            if (
                                similarity > best_score
                                and similarity >= self.config.app_config.match_threshold
                            ):
                                best_match = cmd
                                best_score = similarity
                
                if best_match:
                    logger.info(
                        f"✅ Matched: {best_match.id} (semantic score: {best_score:.2f})"
                    )
                    return best_match, best_score
            except Exception as e:
                logger.warning(f"Semantic matching failed: {e}, falling back to fuzzy matching")
        
        # Fallback to fuzzy matching (if semantic not available or failed)
        best_match = None
        best_score = 0.0
        
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
                f"✅ Matched: {best_match.id} (fuzzy score: {best_score:.2f})"
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

