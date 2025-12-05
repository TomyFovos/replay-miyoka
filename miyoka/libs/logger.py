"""
Enhanced logging module with log rotation and Discord notification support.
"""
import logging
from logging import Logger
from logging.handlers import RotatingFileHandler
import os
from typing import Optional
from pythonjsonlogger import jsonlogger

from miyoka.libs.discord_notifier import DiscordHandler, DiscordConfig


# Default formatter
formatter = jsonlogger.JsonFormatter()


def setup_logger(
    name: str,
    dir_path: str,
    file_name: str,
    clear_everytime: bool,
    file_output: bool,
    standard_output: bool,
    level: int = logging.INFO,
    # New options for rotation
    max_bytes: int = 10 * 1024 * 1024,  # 10MB default
    backup_count: int = 5,
    # Discord notification options
    discord_webhook_url: Optional[str] = None,
    discord_min_level: int = logging.WARNING,
    discord_mention_on_error: bool = False,
) -> Logger:
    """
    Set up a logger with optional file rotation and Discord notifications.
    
    Args:
        name: Logger name
        dir_path: Directory path for log files
        file_name: Log file name
        clear_everytime: If True, clear log file on startup (ignored if rotation enabled)
        file_output: Enable file output
        standard_output: Enable console output
        level: Minimum log level
        max_bytes: Maximum size of each log file (for rotation)
        backup_count: Number of backup files to keep
        discord_webhook_url: Discord webhook URL for notifications
        discord_min_level: Minimum level for Discord notifications
        discord_mention_on_error: Mention @everyone on ERROR+
        
    Returns:
        Configured Logger instance
    """
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    log_path = os.path.join(dir_path, file_name)

    # Only clear if not using rotation (rotation handles old files automatically)
    if os.path.exists(log_path) and clear_everytime and backup_count == 0:
        os.remove(log_path)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    if file_output:
        if backup_count > 0:
            # Use rotating file handler
            fh = RotatingFileHandler(
                log_path,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
        else:
            # Use standard file handler
            fh = logging.FileHandler(log_path, encoding='utf-8')
        
        fh.setFormatter(formatter)
        fh.setLevel(level)
        logger.addHandler(fh)

    if standard_output:
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        ch.setLevel(level)
        logger.addHandler(ch)
    
    # Add Discord handler if configured
    if discord_webhook_url:
        discord_config = DiscordConfig(
            webhook_url=discord_webhook_url,
            enabled=True,
            min_level=discord_min_level,
            mention_on_error=discord_mention_on_error,
        )
        discord_handler = DiscordHandler(config=discord_config)
        discord_handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(discord_handler)

    return logger


def get_log_level(level_name: str) -> int:
    """
    Convert log level name to logging level constant.
    
    Args:
        level_name: Level name (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Logging level constant
    """
    levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "WARN": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return levels.get(level_name.upper(), logging.INFO)
