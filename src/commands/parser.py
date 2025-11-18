from typing import Optional, Tuple, Dict
import re
from fuzzywuzzy import fuzz
from logger import logger
from commands.config import CommandConfig, CommandAction

# Try to load semantic similarity model
try:
    from sentence_transformers import SentenceTransformer, util
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False
    logger.warning("sentence-transformers not available - using fuzzy matching fallback")


class ContextAwareParser:
    """Parse commands using first-word context matching"""

    def __init__(self, config):
        self.config = config
        self._build_context_map()

    def _build_context_map(self):
        """Build a map of context groups from config"""
        self.context_map = {}

        for cmd in self.config.commands:
            if cmd.action.lower() == "context_open":
                # This is a context group command
                context_key = cmd.primary_trigger
                
                # Build app map for this context
                apps = {}
                if cmd.apps:
                    for app_name, app_config in cmd.apps.items():
                        # Store each trigger as a key pointing to the app
                        for trigger in app_config.get("triggers", []):
                            apps[trigger.lower()] = {
                                "app_name": app_name,
                                "app": app_config.get("app"),
                                "action": app_config.get("action"),
                                "feedback": app_config.get("feedback"),
                            }
                
                self.context_map[context_key] = {
                    "cmd": cmd,
                    "apps": apps,
                }

        logger.debug(f"Built context map with {len(self.context_map)} contexts")

    def parse_context(
        self, transcript: str, mode: str = "normal"
    ) -> Optional[Tuple[CommandAction, float]]:
        """
        Parse using context-aware matching.

        Returns:
            (CommandAction, confidence) or None if no match

        Examples:
            "open chrome" → launches Chrome (1.0 confidence)
            "open toggle focus" → None (toggle focus not valid alias)
            "open" → None (no alias provided)
        """
        if not transcript or not transcript.strip():
            return None

        words = transcript.lower().strip().split()

        if len(words) < 2:
            # Need at least primary word + alias
            return None

        primary = words[0]
        alias = words[1]

        # Check if this context exists
        if primary not in self.context_map:
            return None

        context = self.context_map[primary]
        apps = context["apps"]

        # Check if alias exists in this context
        if alias not in apps:
            logger.debug(
                f"Context '{primary}': alias '{alias}' not found. "
                f"Valid aliases: {list(apps.keys())}"
            )
            return None

        # Found valid alias!
        app_config = apps[alias]
        logger.info(
            f"✅ Context match: '{primary}' + '{alias}' → {app_config['app_name']}"
        )

        # Create a synthetic command to return
        cmd = CommandAction(
            id=f"context_{primary}_{alias}",
            triggers=[transcript],
            action=app_config["action"],
            app=app_config["app"],
            feedback=app_config["feedback"],
        )

        return cmd, 1.0  # Perfect match confidence


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
        Parse transcript and find matching command.
        Returns (CommandAction, confidence_score) or None if no match.
        Handles variations like "open chrome", "Open Chrome.", "Open Chrome?"
        
        In dictation mode, only exact matches for "enter" and "clear" are allowed.
        In manual mode, only exact matches for "left", "right", "up", "down", "click", and mode commands are allowed.
        """
        if not transcript or not transcript.strip():
            return None

        transcript_clean = self._normalize_text(transcript)
        
        # In dictation mode, ONLY allow "enter" and "stop dictation"
        if mode == "dictation":
            # Only allow these exact commands in dictation mode
            if transcript_clean == "enter" or transcript_clean == "return":
                # Find and return the send command (which handles enter/return)
                for cmd in self.config.commands:
                    if cmd.id == "send":
                        logger.info(f"✅ Matched: {cmd.id} (exact match in dictation mode)")
                        return cmd, 1.0
            elif transcript_clean == "stop dictation" or transcript_clean == "end dictation" or transcript_clean == "done":
                # Allow exit dictation mode commands
                for cmd in self.config.commands:
                    if cmd.id == "stop_dictation":
                        logger.info(f"✅ Matched: {cmd.id} (exact match in dictation mode - exit)")
                        return cmd, 1.0
            
            # In dictation mode, ignore EVERYTHING else - even if it matches a command
            logger.debug(f"Dictation mode: ignoring '{transcript}' (not enter/stop dictation)")
            return None
        
        # In manual mode, only allow movement and click commands
        if mode == "manual":
            # Check for exact direction matches
            if transcript_clean == "left":
                for cmd in self.config.commands:
                    if cmd.id == "move_left":
                        logger.info(f"✅ Matched: {cmd.id} (exact match in manual mode)")
                        return cmd, 1.0
            elif transcript_clean == "right":
                for cmd in self.config.commands:
                    if cmd.id == "move_right":
                        logger.info(f"✅ Matched: {cmd.id} (exact match in manual mode)")
                        return cmd, 1.0
            elif transcript_clean == "up":
                for cmd in self.config.commands:
                    if cmd.id == "move_up":
                        logger.info(f"✅ Matched: {cmd.id} (exact match in manual mode)")
                        return cmd, 1.0
            elif transcript_clean == "down":
                for cmd in self.config.commands:
                    if cmd.id == "move_down":
                        logger.info(f"✅ Matched: {cmd.id} (exact match in manual mode)")
                        return cmd, 1.0
            elif transcript_clean == "click":
                for cmd in self.config.commands:
                    if cmd.id == "click_manual":
                        logger.info(f"✅ Matched: {cmd.id} (exact match in manual mode)")
                        return cmd, 1.0
            # Allow mode change commands (exit manual mode)
            elif transcript_clean == "stop manual mode" or transcript_clean == "exit manual mode" or transcript_clean == "done":
                for cmd in self.config.commands:
                    if cmd.id == "stop_manual_mode":
                        logger.info(f"✅ Matched: {cmd.id} (exact match in manual mode)")
                        return cmd, 1.0
            
            # In manual mode, ignore everything else
            logger.debug(f"Manual mode: ignoring non-command text '{transcript}'")
            return None
        
        # Normal mode: Try context-aware parser first
        context_result = self.context_parser.parse_context(transcript, mode)
        if context_result:
            cmd, score = context_result
            logger.info(f"✅ Matched: {cmd.id} (context-aware, score: {score:.2f})")
            return cmd, score
        
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

