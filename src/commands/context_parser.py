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
            cmd = CommandAction(
                id=f"context_{primary}_{alias}",
                triggers=[transcript],
                action=item_config["action"],
                app=item_config["app"],
                feedback=item_config["feedback"],
            )
        elif context_type == "mode":
            cmd = CommandAction(
                id=f"context_{primary}_{alias}",
                triggers=[transcript],
                action=item_config["action"],
                mode=item_config["mode"],
                feedback=item_config["feedback"],
            )
        else:
            return None

        return cmd, 1.0  # Perfect match confidence

    def should_use_context(self, primary: str) -> bool:
        """Check if a primary word is a context command"""
        return primary in self.context_map
