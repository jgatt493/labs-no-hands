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
            elif action == "move_cursor":
                return await self._execute_move_cursor(command)
            elif action == "shell":
                return await self._execute_shell(command)
            elif action == "help":
                return await self._execute_help(command)
            else:
                logger.error(f"Unknown action: {action}")
                return False

        except Exception as e:
            logger.error(f"Error executing command '{command.id}': {e}")
            return False

    async def _execute_click(self, command: CommandAction) -> bool:
        """Execute click action - supports app-context coordinates or current cursor position"""
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
        
        # Check if coordinates are [0, 0] which means use current cursor position (for manual mode)
        if coords and len(coords) >= 2 and coords[0] == 0 and coords[1] == 0:
            x, y = self.macos.get_mouse_position()
            logger.info(f"Using current cursor position for click: ({x}, {y})")
        elif not coords or len(coords) < 2:
            logger.error(f"Invalid coordinates for click: {coords}")
            return False
        else:
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

    async def _execute_move_cursor(self, command: CommandAction) -> bool:
        """Execute cursor movement action"""
        direction = getattr(command, 'direction', None)
        distance = getattr(command, 'distance', 15)

        if not direction:
            logger.error("No direction specified for move_cursor action")
            return False

        logger.info(f"Moving cursor {direction} by {distance}px")
        self.macos.move_cursor(direction, distance)

        if command.feedback:
            logger.info(f"Feedback: {command.feedback}")

        self.last_executed = command.id
        return True

    async def _execute_shell(self, command: CommandAction) -> bool:
        """Execute shell command"""
        if not command.shell:
            logger.error("No shell command specified")
            return False

        cmd_str = command.shell
        logger.info(f"Executing shell command: {cmd_str}")

        try:
            # Run shell command asynchronously
            process = await asyncio.create_subprocess_shell(
                cmd_str,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                logger.info(f"Shell command executed successfully")
                if command.feedback:
                    logger.info(f"Feedback: {command.feedback}")
                self.last_executed = command.id
                return True
            else:
                logger.error(f"Shell command failed with code {process.returncode}")
                if stderr:
                    logger.error(f"Error: {stderr.decode()}")
                return False

        except Exception as e:
            logger.error(f"Error executing shell command: {e}")
            return False

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

