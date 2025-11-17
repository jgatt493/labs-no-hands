import asyncio
import subprocess
from typing import Optional
from logger import logger
from commands.config import CommandAction
from automation.macos_control import MacOSControl


class CommandExecutor:
    """Execute commands via macOS automation"""

    def __init__(self, config=None):
        self.macos = MacOSControl()
        self.last_executed = None
        self.config = config

    async def execute(self, command: CommandAction) -> bool:
        """Execute a command"""
        try:
            action = command.action.lower()

            if action == "click":
                return await self._execute_click(command)
            elif action == "keystroke":
                return await self._execute_keystroke(command)
            elif action == "launch":
                return await self._execute_launch(command)
            elif action == "focus":
                return await self._execute_focus(command)
            elif action == "type":
                return await self._execute_type(command)
            elif action == "mode":
                return await self._execute_mode(command)
            elif action == "help":
                return await self._execute_help(command)
            else:
                logger.error(f"Unknown action: {action}")
                return False

        except Exception as e:
            logger.error(f"Error executing command '{command.id}': {e}")
            return False

    async def _execute_click(self, command: CommandAction) -> bool:
        """Execute click action - supports app-context coordinates"""
        # Determine which coordinates to use
        coords = None
        
        # If app_coordinates mapping exists, try to use app-specific coords
        if command.app_coordinates:
            active_app = self.macos.get_active_app()
            logger.info(f"Checking app-specific coordinates for: {active_app}")
            coords = command.app_coordinates.get(active_app)
            if coords:
                logger.info(f"Using app-specific coordinates for {active_app}")
        
        # Fall back to default coordinates
        if not coords:
            coords = command.coordinates
        
        if not coords or len(coords) < 2:
            logger.error(f"Invalid coordinates for click: {coords}")
            return False

        x, y = coords[0], coords[1]
        button = command.button or "left"

        logger.info(f"Executing click at ({x}, {y}) with button {button}")
        self.macos.click(x, y, button=button)

        if command.feedback:
            logger.info(f"Feedback: {command.feedback}")

        self.last_executed = command.id
        return True

    async def _execute_keystroke(self, command: CommandAction) -> bool:
        """Execute keystroke action"""
        if not command.keys or len(command.keys) == 0:
            logger.error(f"Invalid keys for keystroke: {command.keys}")
            return False

        keys = command.keys
        logger.info(f"Executing keystroke: {'+'.join(keys)}")
        self.macos.keystroke(keys)

        if command.feedback:
            logger.info(f"Feedback: {command.feedback}")

        self.last_executed = command.id
        return True

    async def _execute_launch(self, command: CommandAction) -> bool:
        """Execute launch action"""
        if not command.app:
            logger.error("No app specified for launch action")
            return False

        app_name = command.app
        logger.info(f"Launching application: {app_name}")

        try:
            # Use open command to launch app
            subprocess.run(
                ["open", "-a", app_name],
                check=True,
                capture_output=True,
            )

            if command.feedback:
                logger.info(f"Feedback: {command.feedback}")

            self.last_executed = command.id
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to launch {app_name}: {e}")
            return False

    async def _execute_focus(self, command: CommandAction) -> bool:
        """Execute focus action - bring app to foreground"""
        if not command.app:
            logger.error("No app specified for focus action")
            return False

        app_name = command.app
        logger.info(f"Focusing application: {app_name}")

        try:
            # Use open with -a and --activate to focus the app
            subprocess.run(
                ["open", "-a", app_name, "--activate"],
                check=True,
                capture_output=True,
            )

            if command.feedback:
                logger.info(f"Feedback: {command.feedback}")

            self.last_executed = command.id
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to focus {app_name}: {e}")
            return False

    async def _execute_type(self, command: CommandAction) -> bool:
        """Execute type action"""
        if not command.text:
            logger.error("No text specified for type action")
            return False

        text = command.text
        logger.info(f"Typing text: {text}")
        self.macos.type_text(text)

        if command.feedback:
            logger.info(f"Feedback: {command.feedback}")

        self.last_executed = command.id
        return True

    async def _execute_mode(self, command: CommandAction) -> bool:
        """Execute mode change action - returns true to indicate mode change"""
        mode = getattr(command, 'mode', None)
        if not mode:
            logger.error("No mode specified for mode action")
            return False

        logger.info(f"Mode changed to: {mode}")
        
        if command.feedback:
            logger.info(f"Feedback: {command.feedback}")

        self.last_executed = command.id
        return True

    async def _execute_help(self, command: CommandAction) -> bool:
        """Execute help action - display all available commands"""
        if not self.config:
            logger.error("No config available for help")
            return False

        logger.info("=" * 80)
        logger.info("📚 AVAILABLE COMMANDS")
        logger.info("=" * 80)

        for cmd in self.config.commands:
            triggers_str = " | ".join(cmd.triggers)
            logger.info(f"  💬 {triggers_str}")
            logger.info(f"     Action: {cmd.action}")
            if cmd.feedback:
                logger.info(f"     Feedback: {cmd.feedback}")

        logger.info("=" * 80)
        
        if command.feedback:
            logger.info(f"Feedback: {command.feedback}")

        self.last_executed = command.id
        return True

