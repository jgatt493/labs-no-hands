"""
Context-Aware Command Parser

Enables commands like:
  "open chrome"        → Launches Chrome
  "open ide"           → Launches Cursor (alias for IDE)
  "open toggle focus"  → IGNORED (no valid alias)
  "start dictation"    → Enters dictation mode
  "stop manual"        → Exits manual mode
"""

from typing import Optional, Tuple
from logger import logger
from commands.config import CommandAction


class ContextAwareParser:
    """Parse commands using first-word context matching"""

    def __init__(self, config):
        self.config = config
        self._build_context_map()

    def _build_context_map(self):
        """Build a map of context groups from config"""
        self.context_map = {}

        for cmd in self.config.commands:
            action = cmd.action.lower()
            
            if action == "context_open":
                # App launch context (e.g., "open chrome")
                context_key = cmd.primary_trigger
                
                # Build app map for this context
                items = {}
                if cmd.apps:
                    for app_name, app_config in cmd.apps.items():
                        # Store each trigger as a key pointing to the app
                        for trigger in app_config.get("triggers", []):
                            items[trigger.lower()] = {
                                "name": app_name,
                                "app": app_config.get("app"),
                                "action": app_config.get("action"),
                                "feedback": app_config.get("feedback"),
                            }
                
                self.context_map[context_key] = {
                    "cmd": cmd,
                    "type": "app",
                    "items": items,
                }
            
            elif action == "context_mode":
                # Mode change context (e.g., "start dictation", "stop manual")
                context_key = cmd.primary_trigger
                
                # Build mode map for this context
                items = {}
                if cmd.modes:
                    for mode_name, mode_config in cmd.modes.items():
                        # Store each trigger as a key pointing to the mode
                        for trigger in mode_config.get("triggers", []):
                            items[trigger.lower()] = {
                                "name": mode_name,
                                "mode": mode_config.get("mode"),
                                "action": mode_config.get("action"),
                                "feedback": mode_config.get("feedback"),
                            }
                
                self.context_map[context_key] = {
                    "cmd": cmd,
                    "type": "mode",
                    "items": items,
                }
            
            elif action == "context_close":
                # App close context (e.g., "close cursor")
                context_key = cmd.primary_trigger
                
                # Build app map for this context
                items = {}
                if cmd.apps:
                    for app_name, app_config in cmd.apps.items():
                        # Store each trigger as a key pointing to the app
                        for trigger in app_config.get("triggers", []):
                            items[trigger.lower()] = {
                                "name": app_name,
                                "app": app_config.get("app"),
                                "action": app_config.get("action"),
                                "feedback": app_config.get("feedback"),
                            }
                
                self.context_map[context_key] = {
                    "cmd": cmd,
                    "type": "app",
                    "items": items,
                }
            
            elif action == "context_press":
                # Key press context (e.g., "press escape", "press space")
                context_key = cmd.primary_trigger
                
                # Build key map for this context
                items = {}
                if cmd.keys:
                    for key_name, key_config in cmd.keys.items():
                        # Store each trigger as a key pointing to the key
                        for trigger in key_config.get("triggers", []):
                            items[trigger.lower()] = {
                                "name": key_name,
                                "key": key_config.get("key"),
                                "feedback": key_config.get("feedback"),
                            }
                
                self.context_map[context_key] = {
                    "cmd": cmd,
                    "type": "key",
                    "items": items,
                }
            
            elif action in ("context_minimize", "context_maximize", "context_toggle"):
                # App minimize/maximize/toggle context (e.g., "minimize cursor", "maximize chrome", "toggle terminal")
                context_key = cmd.primary_trigger
                
                # Build app map for this context
                items = {}
                if cmd.apps:
                    for app_name, app_config in cmd.apps.items():
                        # Store each trigger as a key pointing to the app
                        for trigger in app_config.get("triggers", []):
                            items[trigger.lower()] = {
                                "name": app_name,
                                "app": app_config.get("app"),
                                "feedback": app_config.get("feedback"),
                                "keys": app_config.get("keys"),  # For toggle context
                            }
                
                self.context_map[context_key] = {
                    "cmd": cmd,
                    "type": action,  # "context_minimize", "context_maximize", or "context_toggle"
                    "items": items,
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
            "start dictation" → enters dictation mode (1.0 confidence)
            "open toggle focus" → None (toggle focus not valid alias)
            "open" → None (no alias provided)
        """
        if not transcript or not transcript.strip():
            return None

        # Normalize the transcript first (remove punctuation, lowercase, etc)
        import re
        transcript_normalized = transcript.lower().strip()
        transcript_normalized = re.sub(r'[^\w\s]', '', transcript_normalized)  # Remove punctuation
        transcript_normalized = re.sub(r'\s+', ' ', transcript_normalized)  # Collapse spaces
        
        words = transcript_normalized.split()

        if len(words) < 2:
            # Need at least primary word + alias
            return None

        primary = words[0]
        alias = words[1]

        # Check if this context exists
        if primary not in self.context_map:
            return None

        context = self.context_map[primary]
        items = context["items"]
        context_type = context["type"]

        # Check if alias exists in this context
        if alias not in items:
            logger.debug(
                f"Context '{primary}': alias '{alias}' not found. "
                f"Valid: {list(items.keys())}"
            )
            return None

        # Found valid alias!
        item_config = items[alias]
        logger.info(
            f"✅ Context match: '{primary}' + '{alias}' → {item_config['name']}"
        )

        # Create a synthetic command to return
        # Determine what fields to set based on context type
        if context_type == "app":
            # For app contexts, track which app and include state update
            app_name = item_config["app"]
            cmd = CommandAction(
                id=f"context_{primary}_{alias}",
                triggers=[transcript],
                action=item_config["action"],
                app=app_name,
                feedback=item_config["feedback"],
                state_update=f"set_app:{app_name}",  # Update app state
            )
        elif context_type == "mode":
            # For mode contexts, track which mode and include state update
            mode_name = item_config["mode"]
            cmd = CommandAction(
                id=f"context_{primary}_{alias}",
                triggers=[transcript],
                action=item_config["action"],
                mode=mode_name,
                feedback=item_config["feedback"],
                state_update=f"set_mode:{mode_name}",  # Update mode state
            )
        elif context_type == "key":
            # For key contexts, execute keystroke
            key = item_config["key"]
            cmd = CommandAction(
                id=f"context_{primary}_{alias}",
                triggers=[transcript],
                action="keystroke",
                keys=[key],
                feedback=item_config["feedback"],
            )
        elif context_type == "context_minimize":
            # For minimize context, minimize app and clear app state
            app_name = item_config["app"]
            cmd = CommandAction(
                id=f"context_{primary}_{alias}",
                triggers=[transcript],
                action="minimize",
                app=app_name,
                feedback=item_config["feedback"],
                state_update="clear_app",  # Clear opened app state after minimize
            )
        elif context_type == "context_maximize":
            # For maximize context, maximize app and keep app state
            app_name = item_config["app"]
            cmd = CommandAction(
                id=f"context_{primary}_{alias}",
                triggers=[transcript],
                action="maximize",
                app=app_name,
                feedback=item_config["feedback"],
                state_update=f"set_app:{app_name}",  # Keep app as selected
            )
        elif context_type == "context_toggle":
            # For toggle context, execute app-specific toggle (terminal, chat, project)
            # Item config has "keys" field with keystroke to send
            cmd = CommandAction(
                id=f"context_{primary}_{alias}",
                triggers=[transcript],
                action="keystroke",
                keys=item_config.get("keys", []),
                feedback=item_config["feedback"],
            )
        else:
            return None

        return cmd, 1.0  # Perfect match confidence

    def should_use_context(self, primary: str) -> bool:
        """Check if a primary word is a context command"""
        return primary in self.context_map
