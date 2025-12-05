"""
Discord notification handler for logging.
Sends log messages to Discord webhook based on log level.
"""
import json
import logging
import urllib.request
from datetime import datetime
from typing import Optional
from dataclasses import dataclass
from enum import IntEnum


class NotificationLevel(IntEnum):
    """Log levels that trigger Discord notifications."""
    DEBUG = logging.DEBUG      # 10
    INFO = logging.INFO        # 20
    WARNING = logging.WARNING  # 30
    ERROR = logging.ERROR      # 40
    CRITICAL = logging.CRITICAL  # 50


@dataclass
class DiscordConfig:
    """Discord notification configuration."""
    webhook_url: Optional[str] = None
    enabled: bool = True
    min_level: int = logging.WARNING  # Minimum level to send notifications
    username: str = "Miyoka Bot"
    avatar_url: Optional[str] = None
    mention_on_error: bool = False  # Mention @everyone on ERROR+
    mention_role_id: Optional[str] = None  # Role ID to mention on ERROR+


class DiscordHandler(logging.Handler):
    """
    Logging handler that sends messages to Discord webhook.
    """
    
    # Color codes for Discord embeds (decimal)
    COLORS = {
        logging.DEBUG: 8421504,     # Gray
        logging.INFO: 3447003,      # Blue
        logging.WARNING: 16776960,  # Yellow
        logging.ERROR: 15158332,    # Red
        logging.CRITICAL: 10038562, # Dark Red
    }
    
    # Emoji prefixes
    EMOJIS = {
        logging.DEBUG: "🔍",
        logging.INFO: "ℹ️",
        logging.WARNING: "⚠️",
        logging.ERROR: "❌",
        logging.CRITICAL: "🚨",
    }
    
    def __init__(self, config: Optional[DiscordConfig] = None):
        super().__init__()
        self.config = config or DiscordConfig()
        
        if self.config.min_level:
            self.setLevel(self.config.min_level)
    
    def emit(self, record: logging.LogRecord) -> None:
        """Send log record to Discord."""
        if not self.config.enabled or not self.config.webhook_url:
            return
        
        if record.levelno < self.config.min_level:
            return
        
        try:
            self._send_to_discord(record)
        except Exception:
            # Don't raise exceptions from logging handler
            self.handleError(record)
    
    def _send_to_discord(self, record: logging.LogRecord) -> None:
        """Send formatted message to Discord webhook."""
        # Build embed
        color = self.COLORS.get(record.levelno, 8421504)
        emoji = self.EMOJIS.get(record.levelno, "📋")
        
        # Format message
        message = self.format(record) if self.formatter else record.getMessage()
        
        # Truncate if too long (Discord limit is 4096 for embed description)
        if len(message) > 4000:
            message = message[:4000] + "... (truncated)"
        
        # Build embed object
        embed = {
            "title": f"{emoji} {record.levelname}",
            "description": f"```\n{message}\n```",
            "color": color,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {
                "text": f"{record.name} | {record.filename}:{record.lineno}"
            }
        }
        
        # Build payload
        payload = {
            "username": self.config.username,
            "embeds": [embed]
        }
        
        if self.config.avatar_url:
            payload["avatar_url"] = self.config.avatar_url
        
        # Add mentions for ERROR and above
        if record.levelno >= logging.ERROR:
            content_parts = []
            if self.config.mention_on_error:
                content_parts.append("@everyone")
            if self.config.mention_role_id:
                content_parts.append(f"<@&{self.config.mention_role_id}>")
            if content_parts:
                payload["content"] = " ".join(content_parts)
        
        # Send to Discord
        self._post_webhook(payload)
    
    def _post_webhook(self, payload: dict) -> None:
        """Post payload to Discord webhook."""
        data = json.dumps(payload).encode("utf-8")
        
        req = urllib.request.Request(
            self.config.webhook_url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Miyoka/1.0"
            }
        )
        
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                pass  # Success
        except urllib.error.HTTPError as e:
            if e.code == 429:  # Rate limited
                # Could implement retry logic here
                pass
            raise


class DiscordNotifier:
    """
    Simple Discord notifier for sending standalone messages.
    """
    
    def __init__(self, config: Optional[DiscordConfig] = None):
        self.config = config or DiscordConfig()
    
    def send(
        self,
        message: str,
        title: Optional[str] = None,
        level: int = logging.INFO,
        fields: Optional[dict] = None
    ) -> bool:
        """
        Send a notification to Discord.
        
        Args:
            message: Message content
            title: Optional title for the embed
            level: Log level (affects color)
            fields: Optional dict of field name -> value
            
        Returns:
            True if sent successfully
        """
        if not self.config.enabled or not self.config.webhook_url:
            return False
        
        color = DiscordHandler.COLORS.get(level, 8421504)
        emoji = DiscordHandler.EMOJIS.get(level, "📋")
        
        embed = {
            "description": message,
            "color": color,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if title:
            embed["title"] = f"{emoji} {title}"
        
        if fields:
            embed["fields"] = [
                {"name": k, "value": str(v), "inline": True}
                for k, v in fields.items()
            ]
        
        payload = {
            "username": self.config.username,
            "embeds": [embed]
        }
        
        if self.config.avatar_url:
            payload["avatar_url"] = self.config.avatar_url
        
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self.config.webhook_url,
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Miyoka/1.0"
                }
            )
            with urllib.request.urlopen(req, timeout=10):
                return True
        except Exception:
            return False
    
    def send_success(self, message: str, title: str = "Success") -> bool:
        """Send a success notification."""
        return self.send(message, title=title, level=logging.INFO)
    
    def send_warning(self, message: str, title: str = "Warning") -> bool:
        """Send a warning notification."""
        return self.send(message, title=title, level=logging.WARNING)
    
    def send_error(self, message: str, title: str = "Error") -> bool:
        """Send an error notification."""
        return self.send(message, title=title, level=logging.ERROR)
    
    def send_recording_complete(
        self,
        replay_count: int,
        duration_minutes: float,
        player_id: Optional[str] = None
    ) -> bool:
        """Send recording completion notification."""
        fields = {
            "Replays Recorded": str(replay_count),
            "Duration": f"{duration_minutes:.1f} min",
        }
        if player_id:
            fields["Player ID"] = player_id
        
        return self.send(
            message="Replay recording session completed successfully.",
            title="Recording Complete",
            level=logging.INFO,
            fields=fields
        )
    
    def send_recording_error(self, error_message: str) -> bool:
        """Send recording error notification."""
        return self.send(
            message=f"An error occurred during replay recording:\n```\n{error_message}\n```",
            title="Recording Error",
            level=logging.ERROR
        )


__all__ = [
    "NotificationLevel",
    "DiscordConfig",
    "DiscordHandler",
    "DiscordNotifier",
]
