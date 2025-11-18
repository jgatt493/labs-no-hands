import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from logger import logger


class CommandAction(BaseModel):
    """Defines a command and its actions"""

    id: str
    triggers: List[str] = []  # Empty by default for context commands
    action: str
    feedback: Optional[str] = None
    # Action-specific fields
    coordinates: Optional[List[int]] = None  # For click actions (default)
    app_coordinates: Optional[Dict[str, List[int]]] = None  # For context-aware click actions
    keys: Optional[Any] = None  # For keystroke actions - can be List[str] or Dict for context_press
    app: Optional[str] = None  # For launch/focus actions
    text: Optional[str] = None  # For type actions
    button: Optional[str] = None  # For click actions
    mode: Optional[str] = None  # For mode actions
    direction: Optional[str] = None  # For move_cursor actions
    distance: Optional[int] = None  # For move_cursor actions
    shell: Optional[str] = None  # For shell/command actions
    primary_trigger: Optional[str] = None  # For context commands (e.g., "open", "start", "stop")
    apps: Optional[Dict[str, Any]] = None  # For context command app mappings (open context)
    modes: Optional[Dict[str, Any]] = None  # For context command mode mappings (start/stop context)
    state_update: Optional[str] = None  # For context commands: "set_app:{appname}" or "set_mode:{modename}"


class AppConfig(BaseModel):
    """Application configuration"""

    deepgram_model: str = "nova-2"
    interim_results: bool = True
    punctuate: bool = True
    endpointing: bool = True
    confidence_threshold: float = 0.75
    match_threshold: float = 0.80
    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 4096
    enable_feedback: bool = True
    feedback_type: str = "visual"  # visual, audio, or both


class CommandConfig:
    """Load and manage command configuration"""

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.app_config: Optional[AppConfig] = None
        self.commands: List[CommandAction] = []
        self._load()

    def _load(self):
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, "r") as f:
                data = yaml.safe_load(f)

            # Parse app config
            if "config" in data:
                self.app_config = AppConfig(**data["config"])
            else:
                self.app_config = AppConfig()

            # Parse commands
            if "commands" in data:
                for cmd_data in data["commands"]:
                    try:
                        cmd = CommandAction(**cmd_data)
                        self.commands.append(cmd)
                    except Exception as e:
                        logger.error(
                            f"Error parsing command '{cmd_data.get('id')}': {e}"
                        )

            logger.info(
                f"Loaded {len(self.commands)} commands from {self.config_path}"
            )

        except Exception as e:
            logger.error(f"Error loading config from {self.config_path}: {e}")
            raise

    def reload(self):
        """Reload configuration from file"""
        self._load()
        logger.info("Configuration reloaded")

    def get_command(self, command_id: str) -> Optional[CommandAction]:
        """Get command by ID"""
        for cmd in self.commands:
            if cmd.id == command_id:
                return cmd
        return None

    def get_all_triggers(self) -> Dict[str, str]:
        """Get mapping of all triggers to command IDs"""
        triggers = {}
        for cmd in self.commands:
            for trigger in cmd.triggers:
                triggers[trigger.lower()] = cmd.id
        return triggers

