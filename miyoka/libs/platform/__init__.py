"""
Platform abstraction layer for cross-platform support.
Automatically detects the current platform and provides appropriate implementations.
"""
import platform
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from miyoka.libs.platform.base import (
        InputController,
        ScreenCapture,
        WindowManager,
        ProcessManager,
    )


def get_platform() -> str:
    """Get the current platform identifier."""
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    elif system == "linux":
        return "linux"
    else:
        raise NotImplementedError(f"Unsupported platform: {system}")


def get_input_controller() -> "InputController":
    """Get the appropriate InputController for the current platform."""
    current_platform = get_platform()
    
    if current_platform == "windows":
        from miyoka.libs.platform.windows import WindowsInputController
        return WindowsInputController()
    elif current_platform == "linux":
        from miyoka.libs.platform.linux import LinuxInputController
        return LinuxInputController()


def get_screen_capture() -> "ScreenCapture":
    """Get the appropriate ScreenCapture for the current platform."""
    current_platform = get_platform()
    
    if current_platform == "windows":
        from miyoka.libs.platform.windows import WindowsScreenCapture
        return WindowsScreenCapture()
    elif current_platform == "linux":
        from miyoka.libs.platform.linux import LinuxScreenCapture
        return LinuxScreenCapture()


def get_window_manager() -> "WindowManager":
    """Get the appropriate WindowManager for the current platform."""
    current_platform = get_platform()
    
    if current_platform == "windows":
        from miyoka.libs.platform.windows import WindowsWindowManager
        return WindowsWindowManager()
    elif current_platform == "linux":
        from miyoka.libs.platform.linux import LinuxWindowManager
        return LinuxWindowManager()


def get_process_manager() -> "ProcessManager":
    """Get the appropriate ProcessManager for the current platform."""
    current_platform = get_platform()
    
    if current_platform == "windows":
        from miyoka.libs.platform.windows import WindowsProcessManager
        return WindowsProcessManager()
    elif current_platform == "linux":
        from miyoka.libs.platform.linux import LinuxProcessManager
        return LinuxProcessManager()


__all__ = [
    "get_platform",
    "get_input_controller",
    "get_screen_capture",
    "get_window_manager",
    "get_process_manager",
]
