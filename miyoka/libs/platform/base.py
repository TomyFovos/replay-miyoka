"""
Abstract base classes for platform-specific implementations.
"""
from abc import ABC, abstractmethod
from typing import Optional, Tuple, List, Any
import numpy as np


class InputController(ABC):
    """Abstract base class for keyboard/mouse input control."""
    
    @abstractmethod
    def press(self, key: str) -> None:
        """Press and release a key.
        
        Args:
            key: Key name (e.g., 'a', 'Tab', 'ESC', 'Enter')
        """
        ...
    
    @abstractmethod
    def key_down(self, key: str) -> None:
        """Press a key down (without releasing).
        
        Args:
            key: Key name
        """
        ...
    
    @abstractmethod
    def key_up(self, key: str) -> None:
        """Release a key.
        
        Args:
            key: Key name
        """
        ...
    
    @abstractmethod
    def write(self, text: str) -> None:
        """Type a string of text.
        
        Args:
            text: Text to type
        """
        ...
    
    @abstractmethod
    def click(self, x: int, y: int, button: str = "left") -> None:
        """Click at the specified position.
        
        Args:
            x: X coordinate
            y: Y coordinate
            button: Mouse button ('left', 'right', 'middle')
        """
        ...
    
    @abstractmethod
    def move_to(self, x: int, y: int) -> None:
        """Move mouse to the specified position.
        
        Args:
            x: X coordinate
            y: Y coordinate
        """
        ...


class ScreenCapture(ABC):
    """Abstract base class for screen capture functionality."""
    
    @abstractmethod
    def initialize(self, monitor_index: int = 0) -> None:
        """Initialize the screen capture.
        
        Args:
            monitor_index: Index of the monitor to capture
        """
        ...
    
    @abstractmethod
    def grab(self, region: Optional[Tuple[int, int, int, int]] = None) -> Optional[np.ndarray]:
        """Capture a frame from the screen.
        
        Args:
            region: Optional tuple (left, top, right, bottom) to capture specific region
            
        Returns:
            Captured frame as numpy array (BGR format), or None if capture failed
        """
        ...
    
    @abstractmethod
    def release(self) -> None:
        """Release resources used by the screen capture."""
        ...


class WindowInfo:
    """Data class for window information."""
    
    def __init__(
        self,
        title: str,
        left: int,
        top: int,
        right: int,
        bottom: int,
        width: int,
        height: int,
        is_active: bool = False,
        handle: Any = None
    ):
        self.title = title
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom
        self.width = width
        self.height = height
        self.is_active = is_active
        self.handle = handle  # Platform-specific window handle


class WindowManager(ABC):
    """Abstract base class for window management."""
    
    @abstractmethod
    def find_window(self, title: str) -> Optional[WindowInfo]:
        """Find a window by its title.
        
        Args:
            title: Window title (partial match)
            
        Returns:
            WindowInfo if found, None otherwise
        """
        ...
    
    @abstractmethod
    def find_windows(self, title: str) -> List[WindowInfo]:
        """Find all windows matching the title.
        
        Args:
            title: Window title (partial match)
            
        Returns:
            List of matching WindowInfo objects
        """
        ...
    
    @abstractmethod
    def activate_window(self, window: WindowInfo) -> bool:
        """Bring window to foreground and give it focus.
        
        Args:
            window: WindowInfo object
            
        Returns:
            True if successful
        """
        ...
    
    @abstractmethod
    def move_window(self, window: WindowInfo, x: int, y: int) -> bool:
        """Move window to specified position.
        
        Args:
            window: WindowInfo object
            x: Target X coordinate
            y: Target Y coordinate
            
        Returns:
            True if successful
        """
        ...
    
    @abstractmethod
    def resize_window(self, window: WindowInfo, width: int, height: int) -> bool:
        """Resize window to specified dimensions.
        
        Args:
            window: WindowInfo object
            width: Target width
            height: Target height
            
        Returns:
            True if successful
        """
        ...
    
    @abstractmethod
    def is_window_active(self, window: WindowInfo) -> bool:
        """Check if window is currently active/focused.
        
        Args:
            window: WindowInfo object
            
        Returns:
            True if window is active
        """
        ...
    
    @abstractmethod
    def get_window_rect(self, window: WindowInfo) -> Tuple[int, int, int, int]:
        """Get current window rectangle.
        
        Args:
            window: WindowInfo object
            
        Returns:
            Tuple (left, top, right, bottom)
        """
        ...


class ProcessManager(ABC):
    """Abstract base class for process management."""
    
    @abstractmethod
    def is_running(self, process_name: str) -> bool:
        """Check if a process is running.
        
        Args:
            process_name: Name of the process (e.g., 'obs64', 'StreetFighter6.exe')
            
        Returns:
            True if process is running
        """
        ...
    
    @abstractmethod
    def start_process(
        self,
        executable: str,
        args: Optional[List[str]] = None,
        wait: bool = False
    ) -> Optional[int]:
        """Start a new process.
        
        Args:
            executable: Path to executable or command
            args: Optional command line arguments
            wait: If True, wait for process to complete
            
        Returns:
            Process ID if started successfully, None otherwise
        """
        ...
    
    @abstractmethod
    def stop_process(self, process_name: str, force: bool = False) -> bool:
        """Stop a running process.
        
        Args:
            process_name: Name of the process
            force: If True, forcefully terminate
            
        Returns:
            True if process was stopped
        """
        ...
    
    @abstractmethod
    def wait_for_process(self, process_name: str, timeout: float = 30.0) -> bool:
        """Wait for a process to start.
        
        Args:
            process_name: Name of the process
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if process started within timeout
        """
        ...


__all__ = [
    "InputController",
    "ScreenCapture",
    "WindowInfo",
    "WindowManager",
    "ProcessManager",
]
