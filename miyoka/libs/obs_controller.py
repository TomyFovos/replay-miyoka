"""
OBS Studio controller using WebSocket API.
Provides cross-platform OBS control without external executables.
"""
import time
from logging import Logger
from typing import Optional
from dataclasses import dataclass


@dataclass
class OBSConfig:
    """OBS WebSocket configuration."""
    host: str = "localhost"
    port: int = 4455
    password: Optional[str] = None  # None for no password
    timeout: float = 10.0


class OBSController:
    """
    OBS Studio controller using obs-websocket protocol.
    
    Requires OBS Studio with WebSocket server enabled:
    Tools > WebSocket Server Settings > Enable WebSocket server
    """
    
    def __init__(self, logger: Logger, config: Optional[OBSConfig] = None):
        self.logger = logger
        self.config = config or OBSConfig()
        self._client = None
        self._connected = False
    
    def _get_client(self):
        """Get or create the WebSocket client."""
        if self._client is None:
            try:
                import obsws_python as obs
                
                if self.config.password:
                    self._client = obs.ReqClient(
                        host=self.config.host,
                        port=self.config.port,
                        password=self.config.password,
                        timeout=self.config.timeout
                    )
                else:
                    self._client = obs.ReqClient(
                        host=self.config.host,
                        port=self.config.port,
                        timeout=self.config.timeout
                    )
                self._connected = True
                self.logger.info(f"Connected to OBS WebSocket at {self.config.host}:{self.config.port}")
            except ImportError:
                raise ImportError(
                    "obsws-python is not installed. Install with: pip install obsws-python"
                )
            except Exception as e:
                self.logger.error(f"Failed to connect to OBS WebSocket: {e}")
                raise ConnectionError(
                    f"Could not connect to OBS WebSocket at {self.config.host}:{self.config.port}. "
                    "Make sure OBS is running and WebSocket server is enabled."
                )
        return self._client
    
    def connect(self) -> bool:
        """
        Connect to OBS WebSocket server.
        
        Returns:
            True if connection successful
        """
        try:
            self._get_client()
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to OBS: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from OBS WebSocket server."""
        if self._client:
            try:
                self._client.base_client.ws.close()
            except Exception:
                pass
            self._client = None
            self._connected = False
            self.logger.info("Disconnected from OBS WebSocket")
    
    def is_connected(self) -> bool:
        """Check if connected to OBS."""
        return self._connected and self._client is not None
    
    def start_recording(self) -> bool:
        """
        Start recording in OBS.
        
        Returns:
            True if recording started successfully
        """
        try:
            client = self._get_client()
            client.start_record()
            self.logger.info("OBS recording started")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start recording: {e}")
            return False
    
    def stop_recording(self) -> Optional[str]:
        """
        Stop recording in OBS.
        
        Returns:
            Path to the recorded file, or None if failed
        """
        try:
            client = self._get_client()
            response = client.stop_record()
            
            # Get the output path from the response
            output_path = getattr(response, 'output_path', None)
            
            if output_path:
                self.logger.info(f"OBS recording stopped. File: {output_path}")
            else:
                self.logger.info("OBS recording stopped")
            
            return output_path
        except Exception as e:
            self.logger.error(f"Failed to stop recording: {e}")
            return None
    
    def pause_recording(self) -> bool:
        """
        Pause recording in OBS.
        
        Returns:
            True if paused successfully
        """
        try:
            client = self._get_client()
            client.pause_record()
            self.logger.info("OBS recording paused")
            return True
        except Exception as e:
            self.logger.error(f"Failed to pause recording: {e}")
            return False
    
    def resume_recording(self) -> bool:
        """
        Resume paused recording in OBS.
        
        Returns:
            True if resumed successfully
        """
        try:
            client = self._get_client()
            client.resume_record()
            self.logger.info("OBS recording resumed")
            return True
        except Exception as e:
            self.logger.error(f"Failed to resume recording: {e}")
            return False
    
    def is_recording(self) -> bool:
        """
        Check if OBS is currently recording.
        
        Returns:
            True if recording is active
        """
        try:
            client = self._get_client()
            status = client.get_record_status()
            return getattr(status, 'output_active', False)
        except Exception as e:
            self.logger.error(f"Failed to get recording status: {e}")
            return False
    
    def get_recording_status(self) -> dict:
        """
        Get detailed recording status.
        
        Returns:
            Dictionary with recording status information
        """
        try:
            client = self._get_client()
            status = client.get_record_status()
            return {
                "active": getattr(status, 'output_active', False),
                "paused": getattr(status, 'output_paused', False),
                "duration": getattr(status, 'output_duration', 0),
                "bytes": getattr(status, 'output_bytes', 0),
            }
        except Exception as e:
            self.logger.error(f"Failed to get recording status: {e}")
            return {"active": False, "paused": False, "duration": 0, "bytes": 0}
    
    def get_version(self) -> Optional[str]:
        """
        Get OBS version.
        
        Returns:
            OBS version string, or None if failed
        """
        try:
            client = self._get_client()
            version = client.get_version()
            return getattr(version, 'obs_version', None)
        except Exception as e:
            self.logger.error(f"Failed to get OBS version: {e}")
            return None
    
    def set_current_scene(self, scene_name: str) -> bool:
        """
        Switch to a specific scene.
        
        Args:
            scene_name: Name of the scene to switch to
            
        Returns:
            True if scene switch successful
        """
        try:
            client = self._get_client()
            client.set_current_program_scene(scene_name)
            self.logger.info(f"Switched to scene: {scene_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to switch scene: {e}")
            return False
    
    def get_scene_list(self) -> list:
        """
        Get list of available scenes.
        
        Returns:
            List of scene names
        """
        try:
            client = self._get_client()
            response = client.get_scene_list()
            scenes = getattr(response, 'scenes', [])
            return [scene.get('sceneName', '') for scene in scenes]
        except Exception as e:
            self.logger.error(f"Failed to get scene list: {e}")
            return []


class OBSProcessController:
    """
    OBS process management for starting/stopping OBS application.
    Works with both Windows and Linux.
    """
    
    def __init__(self, logger: Logger, obs_path: Optional[str] = None):
        self.logger = logger
        self.obs_path = obs_path
        
        # Default paths by platform
        import platform
        if platform.system() == "Windows":
            self.default_obs_path = r"C:\Program Files\obs-studio\bin\64bit\obs64.exe"
            self.process_name = "obs64"
        else:
            self.default_obs_path = "obs"
            self.process_name = "obs"
    
    def _get_process_manager(self):
        """Get the appropriate process manager for the current platform."""
        from miyoka.libs.platform import get_process_manager
        return get_process_manager()
    
    def is_running(self) -> bool:
        """Check if OBS is running."""
        pm = self._get_process_manager()
        return pm.is_running(self.process_name)
    
    def start(self, wait_for_websocket: bool = True, timeout: float = 30.0) -> bool:
        """
        Start OBS application.
        
        Args:
            wait_for_websocket: If True, wait for WebSocket server to be available
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if OBS started successfully
        """
        if self.is_running():
            self.logger.info("OBS is already running")
            return True
        
        obs_path = self.obs_path or self.default_obs_path
        pm = self._get_process_manager()
        
        self.logger.info(f"Starting OBS: {obs_path}")
        
        # Start OBS with arguments to disable shutdown check dialog
        args = ["--disable-shutdown-check"]
        pid = pm.start_process(obs_path, args=args)
        
        if pid is None:
            self.logger.error("Failed to start OBS")
            return False
        
        # Wait for OBS to be fully started
        if not pm.wait_for_process(self.process_name, timeout=timeout):
            self.logger.error("OBS process did not start within timeout")
            return False
        
        # Wait for WebSocket to be available
        if wait_for_websocket:
            self.logger.info("Waiting for OBS WebSocket server...")
            time.sleep(5)  # Give OBS time to initialize WebSocket
        
        self.logger.info("OBS started successfully")
        return True
    
    def stop(self, force: bool = False) -> bool:
        """
        Stop OBS application.
        
        Args:
            force: If True, forcefully terminate
            
        Returns:
            True if OBS stopped successfully
        """
        if not self.is_running():
            self.logger.info("OBS is not running")
            return True
        
        pm = self._get_process_manager()
        
        self.logger.info("Stopping OBS...")
        if pm.stop_process(self.process_name, force=force):
            self.logger.info("OBS stopped successfully")
            return True
        else:
            self.logger.error("Failed to stop OBS")
            return False


__all__ = [
    "OBSConfig",
    "OBSController",
    "OBSProcessController",
]
