import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from logger import logger

# Load environment variables
dotenv_path = Path(__file__).parent.parent / "dotenv"
load_dotenv(dotenv_path=str(dotenv_path))


def get_env(key: str, default: str = None) -> str:
    """Get environment variable with fallback"""
    value = os.getenv(key, default)
    if value is None:
        logger.error(f"Required environment variable not set: {key}")
        sys.exit(1)
    return value


def get_config_path() -> Path:
    """Get path to commands.yaml configuration file"""
    config_path = os.getenv("CONFIG_PATH", "./config/commands.yaml")
    path = Path(config_path)

    if not path.is_absolute():
        path = Path(__file__).parent.parent / path

    if not path.exists():
        logger.error(f"Configuration file not found: {path}")
        sys.exit(1)

    return path


def get_app_support_dir() -> Path:
    """Get application support directory"""
    app_dir = Path.home() / ".voice-command"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir

