"""
Systemd scheduler for automated replay recording.
"""
import os
import subprocess
from pathlib import Path
from typing import Optional


class SystemdScheduler:
    """
    Manages systemd service and timer for scheduled replay recording.
    """
    
    SERVICE_NAME = "miyoka"
    USER_SYSTEMD_DIR = Path.home() / ".config" / "systemd" / "user"
    
    SERVICE_TEMPLATE = """[Unit]
Description=Miyoka Replay Recorder
After=network.target graphical-session.target

[Service]
Type=oneshot
Environment="DISPLAY=:0"
Environment="MIYOKA_CONFIG_PATH={config_path}"
WorkingDirectory={working_dir}
ExecStart={python_path} -m miyoka.cli record --no-launch-game --no-stop-obs

[Install]
WantedBy=default.target
"""
    
    TIMER_TEMPLATE = """[Unit]
Description=Miyoka Replay Recording Timer
Requires={service_name}.service

[Timer]
OnCalendar=*-*-* 00/{interval_hours}:00:00
Persistent=true
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
"""
    
    def __init__(self, config_path: str = "./config.yaml"):
        self.config_path = os.path.abspath(config_path)
        self.working_dir = os.getcwd()
        self.python_path = self._get_python_path()
    
    def _get_python_path(self) -> str:
        """Get the path to the Python interpreter."""
        import sys
        return sys.executable
    
    def _ensure_systemd_dir(self) -> None:
        """Ensure user systemd directory exists."""
        self.USER_SYSTEMD_DIR.mkdir(parents=True, exist_ok=True)
    
    def _get_service_path(self) -> Path:
        """Get path to service file."""
        return self.USER_SYSTEMD_DIR / f"{self.SERVICE_NAME}.service"
    
    def _get_timer_path(self) -> Path:
        """Get path to timer file."""
        return self.USER_SYSTEMD_DIR / f"{self.SERVICE_NAME}.timer"
    
    def _run_systemctl(self, *args) -> bool:
        """Run systemctl command."""
        try:
            result = subprocess.run(
                ["systemctl", "--user"] + list(args),
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def install(self, interval_hours: float = 12.0) -> bool:
        """
        Install systemd service and timer.
        
        Args:
            interval_hours: Interval between recordings in hours
            
        Returns:
            True if installation successful
        """
        self._ensure_systemd_dir()
        
        # Generate service file
        service_content = self.SERVICE_TEMPLATE.format(
            config_path=self.config_path,
            working_dir=self.working_dir,
            python_path=self.python_path,
        )
        
        # Generate timer file
        timer_content = self.TIMER_TEMPLATE.format(
            service_name=self.SERVICE_NAME,
            interval_hours=int(interval_hours),
        )
        
        # Write files
        try:
            self._get_service_path().write_text(service_content)
            self._get_timer_path().write_text(timer_content)
        except Exception as e:
            print(f"Failed to write systemd files: {e}")
            return False
        
        # Reload systemd
        if not self._run_systemctl("daemon-reload"):
            print("Failed to reload systemd daemon")
            return False
        
        # Enable and start timer
        if not self._run_systemctl("enable", f"{self.SERVICE_NAME}.timer"):
            print("Failed to enable timer")
            return False
        
        if not self._run_systemctl("start", f"{self.SERVICE_NAME}.timer"):
            print("Failed to start timer")
            return False
        
        return True
    
    def uninstall(self) -> bool:
        """
        Uninstall systemd service and timer.
        
        Returns:
            True if uninstallation successful
        """
        # Stop and disable timer
        self._run_systemctl("stop", f"{self.SERVICE_NAME}.timer")
        self._run_systemctl("disable", f"{self.SERVICE_NAME}.timer")
        
        # Remove files
        try:
            service_path = self._get_service_path()
            timer_path = self._get_timer_path()
            
            if service_path.exists():
                service_path.unlink()
            if timer_path.exists():
                timer_path.unlink()
        except Exception as e:
            print(f"Failed to remove systemd files: {e}")
            return False
        
        # Reload systemd
        self._run_systemctl("daemon-reload")
        
        return True
    
    def show_status(self) -> None:
        """Show current scheduler status."""
        print("Miyoka Scheduler Status")
        print("=" * 40)
        
        # Check if timer exists
        timer_path = self._get_timer_path()
        if not timer_path.exists():
            print("Status: Not installed")
            print()
            print("To install: miyoka scheduler --install")
            return
        
        print(f"Service file: {self._get_service_path()}")
        print(f"Timer file: {timer_path}")
        print()
        
        # Show timer status
        print("Timer status:")
        subprocess.run(
            ["systemctl", "--user", "status", f"{self.SERVICE_NAME}.timer", "--no-pager"],
            check=False
        )
        
        print()
        print("Next scheduled runs:")
        subprocess.run(
            ["systemctl", "--user", "list-timers", f"{self.SERVICE_NAME}.timer", "--no-pager"],
            check=False
        )
    
    def is_installed(self) -> bool:
        """Check if scheduler is installed."""
        return self._get_timer_path().exists()
    
    def is_active(self) -> bool:
        """Check if scheduler timer is active."""
        result = subprocess.run(
            ["systemctl", "--user", "is-active", f"{self.SERVICE_NAME}.timer"],
            capture_output=True,
            text=True
        )
        return result.stdout.strip() == "active"


__all__ = ["SystemdScheduler"]
