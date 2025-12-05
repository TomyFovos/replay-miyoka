"""
Linux-specific platform implementations.
Uses xdotool for input control, mss for screen capture,
and python-xlib/ewmh for window management.
"""
import time
import subprocess
import shutil
from typing import Optional, Tuple, List, Any
import numpy as np

from miyoka.libs.platform.base import (
    InputController,
    ScreenCapture,
    WindowInfo,
    WindowManager,
    ProcessManager,
)

# Linux-specific imports (conditional)
try:
    import mss
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False
    mss = None

try:
    from ewmh import EWMH
    from Xlib import X, display
    from Xlib.protocol import event
    XLIB_AVAILABLE = True
except ImportError:
    XLIB_AVAILABLE = False
    EWMH = None
    display = None

# Check if xdotool is available
XDOTOOL_AVAILABLE = shutil.which("xdotool") is not None


class LinuxInputController(InputController):
    """Linux input controller using xdotool (subprocess)."""
    
    # Key name mapping from common names to xdotool names
    KEY_MAP = {
        "Tab": "Tab",
        "ESC": "Escape",
        "Escape": "Escape",
        "Enter": "Return",
        "Return": "Return",
        "ctrl": "ctrl",
        "shift": "shift",
        "alt": "alt",
        "delete": "Delete",
        "backspace": "BackSpace",
        "space": "space",
        "up": "Up",
        "down": "Down",
        "left": "Left",
        "right": "Right",
    }
    
    def __init__(self):
        if not XDOTOOL_AVAILABLE:
            raise RuntimeError("xdotool is not installed. Install with: sudo apt install xdotool")
    
    def _map_key(self, key: str) -> str:
        """Map key name to xdotool key name."""
        return self.KEY_MAP.get(key, key)
    
    def press(self, key: str) -> None:
        """Press and release a key."""
        mapped_key = self._map_key(key)
        subprocess.run(["xdotool", "key", mapped_key], check=False)
    
    def key_down(self, key: str) -> None:
        """Press a key down."""
        mapped_key = self._map_key(key)
        subprocess.run(["xdotool", "keydown", mapped_key], check=False)
    
    def key_up(self, key: str) -> None:
        """Release a key."""
        mapped_key = self._map_key(key)
        subprocess.run(["xdotool", "keyup", mapped_key], check=False)
    
    def write(self, text: str) -> None:
        """Type a string of text."""
        subprocess.run(["xdotool", "type", "--clearmodifiers", text], check=False)
    
    def click(self, x: int, y: int, button: str = "left") -> None:
        """Click at the specified position."""
        button_map = {"left": "1", "middle": "2", "right": "3"}
        btn = button_map.get(button, "1")
        subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", btn], check=False)
    
    def move_to(self, x: int, y: int) -> None:
        """Move mouse to the specified position."""
        subprocess.run(["xdotool", "mousemove", str(x), str(y)], check=False)


class LinuxScreenCapture(ScreenCapture):
    """Linux screen capture using mss."""
    
    def __init__(self):
        if not MSS_AVAILABLE:
            raise ImportError("mss is not available. Install with: pip install mss")
        self.sct = None
        self.monitor_index = 0
    
    def initialize(self, monitor_index: int = 0) -> None:
        """Initialize the screen capture."""
        self.sct = mss.mss()
        self.monitor_index = monitor_index + 1  # mss uses 1-based indexing (0 is all monitors)
    
    def grab(self, region: Optional[Tuple[int, int, int, int]] = None) -> Optional[np.ndarray]:
        """Capture a frame from the screen."""
        if self.sct is None:
            raise RuntimeError("Screen capture not initialized. Call initialize() first.")
        
        try:
            if region:
                left, top, right, bottom = region
                monitor = {
                    "left": left,
                    "top": top,
                    "width": right - left,
                    "height": bottom - top
                }
            else:
                monitor = self.sct.monitors[self.monitor_index]
            
            screenshot = self.sct.grab(monitor)
            # Convert to numpy array (BGRA -> BGR)
            frame = np.array(screenshot)
            return frame[:, :, :3]  # Remove alpha channel
        except Exception:
            return None
    
    def release(self) -> None:
        """Release resources."""
        if self.sct:
            self.sct.close()
            self.sct = None


class LinuxWindowManager(WindowManager):
    """Linux window manager using xdotool and EWMH."""
    
    def __init__(self):
        if not XDOTOOL_AVAILABLE:
            raise RuntimeError("xdotool is not installed. Install with: sudo apt install xdotool")
        
        self.ewmh = None
        if XLIB_AVAILABLE:
            try:
                self.ewmh = EWMH()
            except Exception:
                pass
    
    def _get_window_geometry(self, window_id: str) -> Tuple[int, int, int, int]:
        """Get window geometry using xdotool."""
        try:
            result = subprocess.run(
                ["xdotool", "getwindowgeometry", "--shell", window_id],
                capture_output=True, text=True, check=True
            )
            
            geometry = {}
            for line in result.stdout.strip().split('\n'):
                if '=' in line:
                    key, value = line.split('=')
                    geometry[key] = int(value)
            
            x = geometry.get('X', 0)
            y = geometry.get('Y', 0)
            width = geometry.get('WIDTH', 0)
            height = geometry.get('HEIGHT', 0)
            
            return (x, y, x + width, y + height)
        except Exception:
            return (0, 0, 0, 0)
    
    def _get_active_window_id(self) -> Optional[str]:
        """Get the active window ID."""
        try:
            result = subprocess.run(
                ["xdotool", "getactivewindow"],
                capture_output=True, text=True, check=True
            )
            return result.stdout.strip()
        except Exception:
            return None
    
    def find_window(self, title: str) -> Optional[WindowInfo]:
        """Find a window by its title."""
        try:
            result = subprocess.run(
                ["xdotool", "search", "--name", title],
                capture_output=True, text=True, check=True
            )
            
            window_ids = result.stdout.strip().split('\n')
            if window_ids and window_ids[0]:
                window_id = window_ids[0]
                left, top, right, bottom = self._get_window_geometry(window_id)
                
                # Get window title
                title_result = subprocess.run(
                    ["xdotool", "getwindowname", window_id],
                    capture_output=True, text=True, check=False
                )
                window_title = title_result.stdout.strip() if title_result.returncode == 0 else title
                
                active_id = self._get_active_window_id()
                
                return WindowInfo(
                    title=window_title,
                    left=left,
                    top=top,
                    right=right,
                    bottom=bottom,
                    width=right - left,
                    height=bottom - top,
                    is_active=(window_id == active_id),
                    handle=window_id
                )
        except Exception:
            pass
        return None
    
    def find_windows(self, title: str) -> List[WindowInfo]:
        """Find all windows matching the title."""
        windows = []
        try:
            result = subprocess.run(
                ["xdotool", "search", "--name", title],
                capture_output=True, text=True, check=True
            )
            
            window_ids = result.stdout.strip().split('\n')
            active_id = self._get_active_window_id()
            
            for window_id in window_ids:
                if window_id:
                    left, top, right, bottom = self._get_window_geometry(window_id)
                    
                    title_result = subprocess.run(
                        ["xdotool", "getwindowname", window_id],
                        capture_output=True, text=True, check=False
                    )
                    window_title = title_result.stdout.strip() if title_result.returncode == 0 else title
                    
                    windows.append(WindowInfo(
                        title=window_title,
                        left=left,
                        top=top,
                        right=right,
                        bottom=bottom,
                        width=right - left,
                        height=bottom - top,
                        is_active=(window_id == active_id),
                        handle=window_id
                    ))
        except Exception:
            pass
        return windows
    
    def activate_window(self, window: WindowInfo) -> bool:
        """Bring window to foreground."""
        try:
            subprocess.run(
                ["xdotool", "windowactivate", "--sync", str(window.handle)],
                check=True
            )
            return True
        except Exception:
            return False
    
    def move_window(self, window: WindowInfo, x: int, y: int) -> bool:
        """Move window to specified position."""
        try:
            subprocess.run(
                ["xdotool", "windowmove", str(window.handle), str(x), str(y)],
                check=True
            )
            return True
        except Exception:
            return False
    
    def resize_window(self, window: WindowInfo, width: int, height: int) -> bool:
        """Resize window."""
        try:
            subprocess.run(
                ["xdotool", "windowsize", str(window.handle), str(width), str(height)],
                check=True
            )
            return True
        except Exception:
            return False
    
    def is_window_active(self, window: WindowInfo) -> bool:
        """Check if window is active."""
        active_id = self._get_active_window_id()
        return str(window.handle) == active_id
    
    def get_window_rect(self, window: WindowInfo) -> Tuple[int, int, int, int]:
        """Get current window rectangle."""
        return self._get_window_geometry(str(window.handle))


class LinuxProcessManager(ProcessManager):
    """Linux process manager."""
    
    def is_running(self, process_name: str) -> bool:
        """Check if a process is running."""
        try:
            result = subprocess.run(
                ["pgrep", "-f", process_name],
                capture_output=True, text=True
            )
            return result.returncode == 0
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
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                return process.pid
        except Exception:
            return None
    
    def stop_process(self, process_name: str, force: bool = False) -> bool:
        """Stop a running process."""
        try:
            signal = "-9" if force else "-15"
            subprocess.run(["pkill", signal, "-f", process_name], check=True)
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
    "LinuxInputController",
    "LinuxScreenCapture",
    "LinuxWindowManager",
    "LinuxProcessManager",
    "XDOTOOL_AVAILABLE",
    "MSS_AVAILABLE",
    "XLIB_AVAILABLE",
]
