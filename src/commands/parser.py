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
        self.triggers_map = config.get_all_triggers()
        
        # Initialize context-aware parser
        self.context_parser = ContextAwareParser(config)
        
        # Initialize semantic model if available
        self.semantic_model = None
        self.trigger_embeddings = {}  # Cache embeddings
        
        # Mode-specific command mappings for strict matching
        self.mode_commands = {
            "dictation": {
                "enter": ["send"],
                "return": ["send"],
                "stop dictation": ["stop_dictation"],
                "end dictation": ["stop_dictation"],
                "done": ["stop_dictation"],
            },
            "manual": {
                "left": ["move_left"],
                "right": ["move_right"],
                "up": ["move_up"],
                "down": ["move_down"],
                "click": ["click_manual"],
                "stop manual mode": ["stop_manual_mode"],
                "exit manual mode": ["stop_manual_mode"],
                "done": ["stop_manual_mode"],
            },
        }
        
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
    
    def _get_command_by_id(self, command_id: str) -> Optional[CommandAction]:
        """Get a command by its ID"""
        for cmd in self.config.commands:
            if cmd.id == command_id:
                return cmd
        return None
    
    def _try_mode_match(self, transcript_clean: str, mode: str) -> Optional[Tuple[CommandAction, float]]:
        """Try to match using mode-specific strict matching"""
        if mode not in self.mode_commands:
            return None
        
        mode_map = self.mode_commands[mode]
        
        # Check if transcript matches any allowed command in this mode
        if transcript_clean in mode_map:
            command_ids = mode_map[transcript_clean]
            cmd = self._get_command_by_id(command_ids[0])
            if cmd:
                logger.info(f"✅ Matched: {cmd.id} (exact match in {mode} mode)")
                return cmd, 1.0
        
        return None

    def parse(self, transcript: str, mode: str = "normal") -> Optional[Tuple[CommandAction, float]]:
        """
        Parse transcript and find matching command.
        Returns (CommandAction, confidence_score) or None if no match.
        
        Parsing order:
        1. Mode-specific strict matching (dictation, manual)
        2. Context-aware matching (open X, focus X, etc)
        3. Semantic similarity matching
        4. Fuzzy matching fallback
        """
        if not transcript or not transcript.strip():
            return None

        transcript_clean = self._normalize_text(transcript)
        
        # Try mode-specific strict matching first
        mode_result = self._try_mode_match(transcript_clean, mode)
        if mode_result is not None:
            return mode_result
        
        # If in special mode and no match, ignore everything else
        if mode in self.mode_commands:
            logger.debug(f"{mode} mode: ignoring '{transcript}' (not in allowed commands)")
            return None
        
        # Normal mode: Try context-aware parser
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

