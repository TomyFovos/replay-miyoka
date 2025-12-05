"""
Windows-specific platform implementations.
Uses dxcam for screen capture, pygetwindow for window management,
and pydirectinput for input control.
"""
import time
import subprocess
from typing import Optional, Tuple, List, Any
import numpy as np

from miyoka.libs.platform.base import (
    InputController,
    ScreenCapture,
    WindowInfo,
    WindowManager,
    ProcessManager,
)

# Windows-specific imports (conditional)
try:
    import dxcam
    import pygetwindow as gw
    import pydirectinput
    pydirectinput.FAILSAFE = False
    WINDOWS_LIBS_AVAILABLE = True
except (ImportError, NotImplementedError):
    WINDOWS_LIBS_AVAILABLE = False
    dxcam = None
    gw = None
    pydirectinput = None


class WindowsInputController(InputController):
    """Windows input controller using pydirectinput (DirectInput)."""
    
    def __init__(self):
        if not WINDOWS_LIBS_AVAILABLE:
            raise ImportError("pydirectinput is not available. Install with: poetry install --with win")
    
    def press(self, key: str) -> None:
        """Press and release a key."""
        pydirectinput.press(key)
    
    def key_down(self, key: str) -> None:
        """Press a key down."""
        pydirectinput.keyDown(key)
    
    def key_up(self, key: str) -> None:
        """Release a key."""
        pydirectinput.keyUp(key)
    
    def write(self, text: str) -> None:
        """Type a string of text."""
        pydirectinput.write(text)
    
    def click(self, x: int, y: int, button: str = "left") -> None:
        """Click at the specified position."""
        pydirectinput.click(x, y, button=button)
    
    def move_to(self, x: int, y: int) -> None:
        """Move mouse to the specified position."""
        pydirectinput.moveTo(x, y)


class WindowsScreenCapture(ScreenCapture):
    """Windows screen capture using dxcam (DirectX)."""
    
    def __init__(self):
        if not WINDOWS_LIBS_AVAILABLE:
            raise ImportError("dxcam is not available. Install with: poetry install --with win")
        self.camera = None
    
    def initialize(self, monitor_index: int = 0) -> None:
        """Initialize the screen capture."""
        self.camera = dxcam.create(output_idx=monitor_index, output_color="BGR")
    
    def grab(self, region: Optional[Tuple[int, int, int, int]] = None) -> Optional[np.ndarray]:
        """Capture a frame from the screen."""
        if self.camera is None:
            raise RuntimeError("Screen capture not initialized. Call initialize() first.")
        
        try:
            if region:
                return self.camera.grab(region=region)
            else:
                return self.camera.grab()
        except Exception:
            # Fallback to entire screen on error
            return self.camera.grab()
    
    def release(self) -> None:
        """Release resources."""
        if self.camera:
            try:
                self.camera.stop()
            except Exception:
                pass
            self.camera = None


class WindowsWindowManager(WindowManager):
    """Windows window manager using pygetwindow."""
    
    def __init__(self):
        if not WINDOWS_LIBS_AVAILABLE:
            raise ImportError("pygetwindow is not available. Install with: poetry install --with win")
    
    def _to_window_info(self, win) -> WindowInfo:
        """Convert pygetwindow window to WindowInfo."""
        return WindowInfo(
            title=win.title,
            left=win.left,
            top=win.top,
            right=win.right,
            bottom=win.bottom,
            width=win.width,
            height=win.height,
            is_active=win.isActive,
            handle=win
        )
    
    def find_window(self, title: str) -> Optional[WindowInfo]:
        """Find a window by its title."""
        windows = gw.getWindowsWithTitle(title)
        if windows:
            return self._to_window_info(windows[0])
        return None
    
    def find_windows(self, title: str) -> List[WindowInfo]:
        """Find all windows matching the title."""
        windows = gw.getWindowsWithTitle(title)
        return [self._to_window_info(w) for w in windows]
    
    def activate_window(self, window: WindowInfo) -> bool:
        """Bring window to foreground."""
        try:
            window.handle.activate()
            return True
        except Exception:
            return False
    
    def move_window(self, window: WindowInfo, x: int, y: int) -> bool:
        """Move window to specified position."""
        try:
            window.handle.moveTo(x, y)
            return True
        except Exception:
            return False
    
    def resize_window(self, window: WindowInfo, width: int, height: int) -> bool:
        """Resize window."""
        try:
            window.handle.resizeTo(width, height)
            return True
        except Exception:
            return False
    
    def is_window_active(self, window: WindowInfo) -> bool:
        """Check if window is active."""
        try:
            return window.handle.isActive
        except Exception:
            return False
    
    def get_window_rect(self, window: WindowInfo) -> Tuple[int, int, int, int]:
        """Get current window rectangle."""
        try:
            w = window.handle
            return (w.left, w.top, w.right, w.bottom)
        except Exception:
            return (window.left, window.top, window.right, window.bottom)


class WindowsProcessManager(ProcessManager):
    """Windows process manager."""
    
    def is_running(self, process_name: str) -> bool:
        """Check if a process is running."""
        try:
            result = subprocess.run(
                ["tasklist", "/FI", f"IMAGENAME eq {process_name}*"],
                capture_output=True,
                text=True
            )
            return process_name.lower() in result.stdout.lower()
        except Exception:
            return False
    
    def start_process(
        self,
        executable: str,
        args: Optional[List[str]] = None,
        wait: bool = False
    ) -> Optional[int]:
        """Start a new process."""
        try:
            cmd = [executable] + (args or [])
            if wait:
                result = subprocess.run(cmd)
                return result.returncode
            else:
                process = subprocess.Popen(cmd)
                return process.pid
        except Exception:
            return None
    
    def stop_process(self, process_name: str, force: bool = False) -> bool:
        """Stop a running process."""
        try:
            if force:
                subprocess.run(["taskkill", "/F", "/IM", f"{process_name}*"], check=True)
            else:
                subprocess.run(["taskkill", "/IM", f"{process_name}*"], check=True)
            return True
        except Exception:
            return False
    
    def wait_for_process(self, process_name: str, timeout: float = 30.0) -> bool:
        """Wait for a process to start."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.is_running(process_name):
                return True
            time.sleep(0.5)
        return False


__all__ = [
    "WindowsInputController",
    "WindowsScreenCapture",
    "WindowsWindowManager",
    "WindowsProcessManager",
    "WINDOWS_LIBS_AVAILABLE",
]
