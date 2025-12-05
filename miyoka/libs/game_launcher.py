"""
Game launcher for starting and managing game processes.
Supports both direct execution and Steam launch methods.
"""
import time
import platform
from logging import Logger
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum


class LaunchMethod(Enum):
    """Game launch method."""
    DIRECT = "direct"  # Direct executable launch
    STEAM = "steam"    # Launch via Steam


@dataclass
class GameLaunchConfig:
    """Game launch configuration."""
    method: LaunchMethod = LaunchMethod.DIRECT
    
    # Direct launch settings
    exe_path: Optional[str] = None
    exe_args: list = field(default_factory=list)
    working_directory: Optional[str] = None
    
    # Steam launch settings
    steam_app_id: Optional[str] = None
    
    # Common settings
    window_title: str = ""  # Window title to wait for
    startup_wait_seconds: float = 30.0
    process_name: Optional[str] = None  # Process name to monitor


# Default configurations for supported games
GAME_CONFIGS = {
    "sf6": GameLaunchConfig(
        method=LaunchMethod.DIRECT,
        steam_app_id="1364780",
        window_title="Street Fighter 6",
        process_name="StreetFighter6",
        startup_wait_seconds=60.0,
    ),
}


class GameLauncher:
    """
    Game launcher supporting both direct and Steam launch methods.
    """
    
    def __init__(self, logger: Logger, config: Optional[GameLaunchConfig] = None):
        self.logger = logger
        self.config = config or GameLaunchConfig()
        self._system = platform.system().lower()
    
    def _get_process_manager(self):
        """Get the appropriate process manager for the current platform."""
        from miyoka.libs.platform import get_process_manager
        return get_process_manager()
    
    def _get_window_manager(self):
        """Get the appropriate window manager for the current platform."""
        from miyoka.libs.platform import get_window_manager
        return get_window_manager()
    
    def _get_steam_command(self) -> str:
        """Get the Steam command for the current platform."""
        if self._system == "windows":
            return "steam"
        else:
            # Linux - try flatpak first, then native
            import shutil
            if shutil.which("flatpak"):
                # Check if Steam is installed via flatpak
                import subprocess
                result = subprocess.run(
                    ["flatpak", "list", "--app"],
                    capture_output=True, text=True
                )
                if "com.valvesoftware.Steam" in result.stdout:
                    return "flatpak run com.valvesoftware.Steam"
            
            return "steam"
    
    def is_running(self) -> bool:
        """Check if the game is currently running."""
        pm = self._get_process_manager()
        
        if self.config.process_name:
            return pm.is_running(self.config.process_name)
        
        # Fallback: check by window title
        wm = self._get_window_manager()
        window = wm.find_window(self.config.window_title)
        return window is not None
    
    def launch(self) -> bool:
        """
        Launch the game using the configured method.
        
        Returns:
            True if game launched successfully
        """
        if self.is_running():
            self.logger.info(f"Game is already running: {self.config.window_title}")
            return True
        
        if self.config.method == LaunchMethod.STEAM:
            return self._launch_via_steam()
        else:
            return self._launch_direct()
    
    def _launch_direct(self) -> bool:
        """Launch game directly via executable."""
        if not self.config.exe_path:
            self.logger.error("exe_path not configured for direct launch")
            return False
        
        pm = self._get_process_manager()
        
        self.logger.info(f"Launching game directly: {self.config.exe_path}")
        
        # Build command with arguments
        args = list(self.config.exe_args) if self.config.exe_args else []
        
        pid = pm.start_process(self.config.exe_path, args=args)
        
        if pid is None:
            self.logger.error("Failed to start game process")
            return False
        
        # Wait for game window to appear
        return self._wait_for_game_window()
    
    def _launch_via_steam(self) -> bool:
        """Launch game via Steam."""
        if not self.config.steam_app_id:
            self.logger.error("steam_app_id not configured for Steam launch")
            return False
        
        pm = self._get_process_manager()
        steam_cmd = self._get_steam_command()
        
        # Build Steam URL
        steam_url = f"steam://rungameid/{self.config.steam_app_id}"
        
        self.logger.info(f"Launching game via Steam: {steam_url}")
        
        # On Linux, we might need to handle the steam command differently
        if self._system == "linux":
            if "flatpak" in steam_cmd:
                # Flatpak Steam
                import subprocess
                subprocess.Popen(
                    ["flatpak", "run", "com.valvesoftware.Steam", steam_url],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
            else:
                # Native Steam
                import subprocess
                subprocess.Popen(
                    ["steam", steam_url],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
        else:
            # Windows - use start command
            import subprocess
            subprocess.Popen(
                ["cmd", "/c", "start", "", steam_url],
                shell=True
            )
        
        # Wait for game window to appear
        return self._wait_for_game_window()
    
    def _wait_for_game_window(self) -> bool:
        """Wait for the game window to appear."""
        if not self.config.window_title:
            self.logger.warning("window_title not configured, skipping window wait")
            return True
        
        wm = self._get_window_manager()
        timeout = self.config.startup_wait_seconds
        
        self.logger.info(f"Waiting for game window: {self.config.window_title} (timeout: {timeout}s)")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            window = wm.find_window(self.config.window_title)
            if window:
                self.logger.info(f"Game window found: {window.title}")
                return True
            time.sleep(1.0)
        
        self.logger.error(f"Game window not found within {timeout} seconds")
        return False
    
    def terminate(self, force: bool = False) -> bool:
        """
        Terminate the game process.
        
        Args:
            force: If True, forcefully terminate
            
        Returns:
            True if game terminated successfully
        """
        if not self.is_running():
            self.logger.info("Game is not running")
            return True
        
        pm = self._get_process_manager()
        
        if self.config.process_name:
            self.logger.info(f"Terminating game: {self.config.process_name}")
            return pm.stop_process(self.config.process_name, force=force)
        
        self.logger.error("process_name not configured, cannot terminate")
        return False
    
    def focus(self) -> bool:
        """
        Bring the game window to foreground.
        
        Returns:
            True if window focused successfully
        """
        if not self.config.window_title:
            self.logger.error("window_title not configured")
            return False
        
        wm = self._get_window_manager()
        window = wm.find_window(self.config.window_title)
        
        if window:
            return wm.activate_window(window)
        
        self.logger.error(f"Game window not found: {self.config.window_title}")
        return False
    
    def move_to_origin(self) -> bool:
        """
        Move game window to (0, 0) position.
        
        Returns:
            True if window moved successfully
        """
        if not self.config.window_title:
            self.logger.error("window_title not configured")
            return False
        
        wm = self._get_window_manager()
        window = wm.find_window(self.config.window_title)
        
        if window:
            return wm.move_window(window, 0, 0)
        
        self.logger.error(f"Game window not found: {self.config.window_title}")
        return False


def create_game_launcher(
    logger: Logger,
    game_name: str,
    method: Optional[str] = None,
    exe_path: Optional[str] = None,
    steam_app_id: Optional[str] = None,
    **kwargs
) -> GameLauncher:
    """
    Factory function to create a GameLauncher with appropriate configuration.
    
    Args:
        logger: Logger instance
        game_name: Name of the game (e.g., 'sf6')
        method: Launch method ('direct' or 'steam'), default is 'direct'
        exe_path: Path to game executable (for direct launch)
        steam_app_id: Steam App ID (for Steam launch)
        **kwargs: Additional configuration options
        
    Returns:
        Configured GameLauncher instance
    """
    # Start with default config for the game
    if game_name in GAME_CONFIGS:
        config = GAME_CONFIGS[game_name]
        # Create a copy to avoid modifying the default
        config = GameLaunchConfig(
            method=config.method,
            exe_path=config.exe_path,
            exe_args=list(config.exe_args),
            working_directory=config.working_directory,
            steam_app_id=config.steam_app_id,
            window_title=config.window_title,
            startup_wait_seconds=config.startup_wait_seconds,
            process_name=config.process_name,
        )
    else:
        config = GameLaunchConfig()
    
    # Override with provided values
    if method:
        config.method = LaunchMethod(method)
    if exe_path:
        config.exe_path = exe_path
    if steam_app_id:
        config.steam_app_id = steam_app_id
    
    # Apply any additional kwargs
    for key, value in kwargs.items():
        if hasattr(config, key) and value is not None:
            setattr(config, key, value)
    
    return GameLauncher(logger, config)


__all__ = [
    "LaunchMethod",
    "GameLaunchConfig",
    "GameLauncher",
    "create_game_launcher",
    "GAME_CONFIGS",
]
