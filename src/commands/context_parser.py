"""
Context-Aware Command Parser

Enables commands like:
  "open chrome"      → Launches Chrome
  "open ide"         → Launches Cursor (alias for IDE)
  "open toggle focus" → IGNORED (no valid alias)
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
            if cmd.action.lower() == "context_open":
                # This is a context group command
                context_key = cmd.primary_trigger
                
                # Build app map for this context
                apps = {}
                for app_name, app_config in cmd.apps.items():
                    # Store each trigger as a key pointing to the app
                    for trigger in app_config.triggers:
                        apps[trigger.lower()] = {
                            "app_name": app_name,
                            "app": app_config.app,
                            "action": app_config.action,
                            "feedback": app_config.feedback,
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
                f"Valid: {list(apps.keys())}"
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

    def should_use_context(self, primary: str) -> bool:
        """Check if a primary word is a context command"""
        return primary in self.context_map

