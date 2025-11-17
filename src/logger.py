import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from colorama import Fore, Style

# Create logs directory
log_dir = Path.home() / ".voice-command" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)

# Log file path
log_file = log_dir / "voice-command.log"


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""

    COLORS = {
        "DEBUG": Fore.CYAN,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.RED + Style.BRIGHT,
    }

    def format(self, record):
        levelname = record.levelname
        color = self.COLORS.get(levelname, "")
        reset = Style.RESET_ALL

        # Format the message
        formatted = super().format(record)

        # Add color for console output
        if hasattr(sys.stderr, "isatty") and sys.stderr.isatty():
            formatted = formatted.replace(
                levelname, f"{color}{levelname}{reset}"
            )

        return formatted


def setup_logger():
    """Setup logging configuration"""
    logger = logging.getLogger("voice_command")

    # Only setup once
    if logger.handlers:
        return logger

    # Determine log level from env
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    # Console handler (colored)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level, logging.INFO))
    console_formatter = ColoredFormatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# Singleton instance
logger = setup_logger()

