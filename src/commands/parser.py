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
        
        # App-specific command loading
        self.app_commands = {}  # Cache of loaded app configs
        self.current_app_config = None  # Currently loaded app config
        self.app_trigger_embeddings = {}  # App-specific embeddings cache
        
        # Initialize semantic model if available
        self.semantic_model = None
        self.trigger_embeddings = {}  # Cache embeddings for global commands
        
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

    def load_app_commands(self, app_name: str) -> bool:
        """Load app-specific commands for an app"""
        if not app_name:
            self.current_app_config = None
            self.app_trigger_embeddings = {}
            return False
        
        # Check if already loaded
        if app_name in self.app_commands:
            self.current_app_config = self.app_commands[app_name]
            logger.debug(f"Using cached app commands for: {app_name}")
            return True
        
        # Try to load app-specific config
        try:
            from pathlib import Path
            app_config_path = Path(__file__).parent.parent.parent / "config" / "app_commands" / f"{app_name.lower()}.yaml"
            
            if app_config_path.exists():
                app_config = CommandConfig(app_config_path)
                self.app_commands[app_name] = app_config
                self.current_app_config = app_config
                
                # Build embeddings for app commands if semantic model available
                if self.semantic_model:
                    self._build_app_trigger_embeddings(app_name)
                
                logger.info(f"✅ Loaded app commands for: {app_name} ({len(app_config.commands)} commands)")
                return True
            else:
                logger.debug(f"No app-specific config found for: {app_name}")
                self.current_app_config = None
                return False
        except Exception as e:
            logger.warning(f"Error loading app commands for {app_name}: {e}")
            self.current_app_config = None
            return False
    
    def _build_app_trigger_embeddings(self, app_name: str):
        """Build embeddings for app-specific triggers"""
        if not self.semantic_model or app_name not in self.app_commands:
            return
        
        try:
            app_config = self.app_commands[app_name]
            all_triggers = []
            
            for cmd in app_config.commands:
                for trigger in cmd.triggers:
                    all_triggers.append(trigger)
            
            if all_triggers:
                embeddings = self.semantic_model.encode(all_triggers, convert_to_tensor=True)
                
                self.app_trigger_embeddings[app_name] = {}
                for trigger, embedding in zip(all_triggers, embeddings):
                    self.app_trigger_embeddings[app_name][trigger] = embedding
                
                logger.debug(f"Built embeddings for {len(all_triggers)} app triggers ({app_name})")
        except Exception as e:
            logger.error(f"Error building app embeddings for {app_name}: {e}")
    
    def _parse_app_commands(self, transcript: str, transcript_clean: str, app_name: str) -> Optional[Tuple[CommandAction, float]]:
        """Parse against app-specific commands"""
        if not self.current_app_config:
            return None
        
        best_match = None
        best_score = 0.0
        
        # Semantic matching for app commands
        if self.semantic_model and app_name in self.app_trigger_embeddings:
            try:
                transcript_embedding = self.semantic_model.encode(transcript, convert_to_tensor=True)
                
                for cmd in self.current_app_config.commands:
                    for trigger in cmd.triggers:
                        if trigger in self.app_trigger_embeddings[app_name]:
                            trigger_embedding = self.app_trigger_embeddings[app_name][trigger]
                            similarity = util.pytorch_cos_sim(
                                transcript_embedding, trigger_embedding
                            ).item()
                            
                            if similarity > best_score:
                                best_score = similarity
                                best_match = (cmd, similarity)
            except Exception as e:
                logger.debug(f"App semantic matching error: {e}")
        
        # Check semantic match threshold - MUST meet threshold to proceed
        if best_match and best_score >= self.config.app_config.match_threshold:
            cmd, score = best_match
            logger.debug(f"Semantic match passed threshold: {cmd.id} ({best_score:.2f} >= {self.config.app_config.match_threshold})")
            logger.info(f"✅ Matched: {cmd.id} (app-specific, semantic score: {score:.2f})")
            return cmd, score
        elif best_match:
            logger.debug(f"Semantic match below threshold: {best_match[0].id} ({best_score:.2f} < {self.config.app_config.match_threshold}), falling back to fuzzy")
        
        # Fuzzy matching fallback for app commands - reset scores for clean comparison
        best_match = None
        best_score = 0.0
        
        for cmd in self.current_app_config.commands:
            for trigger in cmd.triggers:
                score = fuzz.token_set_ratio(transcript_clean, trigger.lower()) / 100.0
                
                if score >= self.config.app_config.match_threshold:
                    if score > best_score:
                        best_score = score
                        best_match = (cmd, score)
        
        if best_match:
            cmd, score = best_match
            logger.info(f"✅ Matched: {cmd.id} (app-specific, fuzzy score: {score:.2f})")
            return cmd, score
        
        return None

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalize text: lowercase, strip whitespace, remove punctuation"""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _try_press_command(self, transcript: str, transcript_clean: str) -> Optional[Tuple[CommandAction, float]]:
        """Check if this is a 'press' context command (LAYER 1 - highest priority)"""
        words = transcript_clean.split()
        if len(words) < 2 or words[0] != "press":
            return None
        
        # Try context parser for press command
        result = self.context_parser.parse_context(transcript)
        if result and result[0].action == "keystroke":
            return result
        
        return None
    
    def _try_dictation_exact_match(self, transcript: str, transcript_clean: str) -> Optional[Tuple[CommandAction, float]]:
        """Check for exact-match dictation commands (LAYER 2 - in dictation mode only)"""
        # Look for commands that have mode_only="dictation"
        for cmd in self.config.commands:
            if cmd.mode_only != "dictation":
                continue
            
            # For mode-only commands, require exact match of one trigger
            for trigger in cmd.triggers:
                if transcript_clean == trigger.lower():
                    logger.debug(f"Dictation exact match: '{trigger}' → {cmd.id}")
                    return cmd, 1.0
        
        return None

    def parse(self, transcript: str, mode: str = "normal", app: str = None) -> Optional[Tuple[CommandAction, float]]:
        """
        Parse transcript using LAYERED priority system:
        
        LAYER 1 (Always): Press commands (e.g., "press escape")
        LAYER 2 (If in dictation mode): Exact-match dictation commands (e.g., "new line", "select all")
        LAYER 3 (If not in special mode): Context-aware parsing (open/start/stop/close)
        LAYER 4 (Normal/App context): App-specific or global semantic/fuzzy matching
        
        This ensures press commands work anywhere, dictation has strict controls,
        and context/app commands are priority-ordered appropriately.
        """
        if not transcript or not transcript.strip():
            return None

        transcript_clean = self._normalize_text(transcript)
        
        # LAYER 1: Always check for "press" commands first (highest priority)
        logger.debug(f"LAYER 1: Checking for press command in: '{transcript}'")
        press_result = self._try_press_command(transcript, transcript_clean)
        if press_result:
            cmd, score = press_result
            logger.info(f"✅ Matched: {cmd.id} (press command, score: {score:.2f})")
            return cmd, score
        
        # LAYER 2: If in dictation mode, prioritize context commands (for exit) then exact-match dictation
        if mode == "dictation":
            logger.debug(f"LAYER 2a: In dictation mode, checking context commands for mode exit")
            # Context commands like "stop dictation" should work even in dictation mode
            context_result = self.context_parser.parse_context(transcript, mode)
            if context_result:
                cmd, score = context_result
                logger.info(f"✅ Matched: {cmd.id} (dictation context-aware, score: {score:.2f})")
                return cmd, score
            
            logger.debug(f"LAYER 2b: Checking exact-match dictation commands")
            dictation_result = self._try_dictation_exact_match(transcript, transcript_clean)
            if dictation_result:
                cmd, score = dictation_result
                logger.info(f"✅ Matched: {cmd.id} (dictation exact, score: {score:.2f})")
                return cmd, score
            
            # In dictation mode, if no exact match, ignore all other commands (type as text)
            logger.debug(f"Dictation mode: no context or exact match found, typing as text")
            return None
        
        # LAYER 3: Try context-aware parser (handles keywords + app/mode context)
        logger.debug(f"LAYER 3: Trying context-aware parser for: '{transcript}'")
        context_result = self.context_parser.parse_context(transcript, mode)
        if context_result:
            cmd, score = context_result
            logger.info(f"✅ Matched: {cmd.id} (context-aware, score: {score:.2f})")
            return cmd, score
        logger.debug(f"No context match for: '{transcript}'")
        
        # In manual mode, if context match failed, ignore all other commands
        if mode == "manual":
            logger.debug(f"Manual mode: no context match found, ignoring input")
            return None
        
        # LAYER 4: Try app-specific commands (if app is set)
        if app:
            if self.load_app_commands(app):
                logger.debug(f"Trying app-specific commands for: {app}")
                app_result = self._parse_app_commands(transcript, transcript_clean, app)
                if app_result:
                    return app_result
                logger.debug(f"No app-specific match for: {app}")
        
        logger.debug(f"Trying global semantic/fuzzy matching")
        
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

