"""
Application state management

Tracks:
- Current active app (Cursor, Terminal, Chrome, Slack, Spotify, None)
- Current mode (normal, dictation, manual)
"""

from typing import Optional
from logger import logger


class AppState:
    """Manage application state"""

    def __init__(self):
        self.mode: str = "normal"  # normal, dictation, manual
        self.app: Optional[str] = None  # Cursor, Terminal, Chrome, Slack, Spotify

    def set_app(self, app_name: str) -> None:
        """Set the currently active app (called by 'open X' commands)"""
        self.app = app_name
        logger.info(f"📱 Active app: {app_name}")

    def clear_app(self) -> None:
        """Clear the currently active app (called by 'close' commands)"""
        self.app = None
        logger.info("📱 No active app")

    def set_mode(self, mode: str) -> None:
        """Set the current mode"""
        if mode not in ("normal", "dictation", "manual"):
            logger.error(f"Invalid mode: {mode}")
            return

        self.mode = mode
        if mode == "normal":
            logger.info("🔄 Mode: normal")
        elif mode == "dictation":
            logger.info("✍️ Mode: dictation (type freely)")
        elif mode == "manual":
            logger.info("🖱️ Mode: manual (cursor control)")

    def get_app_context(self) -> Optional[str]:
        """Get the current app context for app-scoped commands"""
        return self.app

    def is_mode(self, mode: str) -> bool:
        """Check if in a specific mode"""
        return self.mode == mode

    def has_app(self) -> bool:
        """Check if an app is currently active"""
        return self.app is not None

    def __str__(self) -> str:
        """String representation for logging"""
        app_str = f"app={self.app}" if self.app else "app=None"
        return f"AppState(mode={self.mode}, {app_str})"

    def __repr__(self) -> str:
        return self.__str__()

