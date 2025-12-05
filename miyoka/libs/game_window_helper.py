"""
Game window helper for screen capture and window management.
Uses platform abstraction layer for cross-platform support.
"""
import time
import os
import cv2 as cv
import pathlib
from logging import Logger
from typing import Optional
from miyoka.libs.utils import retry
import pytesseract
from PIL import Image

# Platform abstraction imports
from miyoka.libs.platform import (
    get_screen_capture,
    get_window_manager,
    get_process_manager,
)
from miyoka.libs.platform.base import ScreenCapture, WindowManager, WindowInfo

WIDTH_1280 = 1280
WIDTH_1920 = 1920
HEIGHT_720 = 720
HEIGHT_1080 = 1080
DEFAULT_SCREEN_LANGUAGE = "en"


class GameWindowHelper:
    """
    Helper class for game window management and screen capture.
    Supports both Windows and Linux platforms.
    """
    
    def __init__(self, logger: Logger, window_name: str, extra: dict, margin: int = 50):
        self.logger = logger
        self.window_name = window_name
        self.extra = extra
        self.margin = margin
        # Use language from config if available, otherwise fallback to default
        self._screen_language = extra.get("original_language", DEFAULT_SCREEN_LANGUAGE) if extra else DEFAULT_SCREEN_LANGUAGE
        
        # Platform abstraction components (lazy initialization)
        self._screen_capture: Optional[ScreenCapture] = None
        self._window_manager: Optional[WindowManager] = None
        self._current_window: Optional[WindowInfo] = None
        self.current_screen_region = None
        self._current_screen_width = 0
        self._current_screen_height = 0

    def _get_screen_capture(self) -> ScreenCapture:
        """Get or create screen capture instance."""
        if self._screen_capture is None:
            self._screen_capture = get_screen_capture()
        return self._screen_capture
    
    def _get_window_manager(self) -> WindowManager:
        """Get or create window manager instance."""
        if self._window_manager is None:
            self._window_manager = get_window_manager()
        return self._window_manager

    def init_camera(self):
        """Initialize screen capture."""
        screen_capture = self._get_screen_capture()
        screen_capture.initialize(monitor_index=0)

    def grab_frame(self):
        """Capture current frame from screen."""
        screen_capture = self._get_screen_capture()
        frame = None

        if not self.current_screen_region:
            raise ValueError(
                "Region is not set. Please call update_game_window_size() first."
            )

        while True:
            try:
                frame = screen_capture.grab(region=self.current_screen_region)
            except ValueError:
                frame = screen_capture.grab()  # Fallback to entire screen
                self.logger.warning(
                    f"Fallback to entire screen when the window does not fit within the screen. "
                    f"current_screen_region: {self.current_screen_region}"
                )

            if frame is not None:
                break
            else:
                print(f"Frame not found! Grabbing again...")
                time.sleep(0.1)
                continue

        return frame

    def wait_until_game_launched(self):
        """Wait until game window is found."""
        while True:
            try:
                self.get_game_window()
                break
            except Exception:
                print(
                    f"Failed to find the game screen. Please make sure the game is running."
                )
                time.sleep(1)

    def get_game_window(self) -> WindowInfo:
        """Get game window info."""
        wm = self._get_window_manager()
        window = wm.find_window(self.window_name)
        if window is None:
            raise ValueError(f"Window not found: {self.window_name}")
        self._current_window = window
        return window

    def wait_until_game_focused(self):
        """Wait until game window is focused."""
        wm = self._get_window_manager()
        window = self.get_game_window()
        
        try:
            wm.activate_window(window)
            wm.move_window(window, 0, 0)
        except Exception as e:
            self.logger.error(f"Failed to activate window. {e}")

        # Wait for the window to be focused
        max_wait = 10  # seconds
        start_time = time.time()
        while time.time() - start_time < max_wait:
            if wm.is_window_active(window):
                break
            time.sleep(0.1)

    def ensure_obs(self):
        """Ensure OBS is running."""
        wm = self._get_window_manager()
        windows = wm.find_windows("OBS")
        if len(windows) == 0:
            raise ValueError("OBS window not found. Did you start OBS?")

    @property
    def normalized_screen_width(self):
        if (self._current_screen_width > (WIDTH_1280 - self.margin)) and (
            self._current_screen_width < (WIDTH_1280 + self.margin)
        ):
            return WIDTH_1280

        if (self._current_screen_width > (WIDTH_1920 - self.margin)) and (
            self._current_screen_width < (WIDTH_1920 + self.margin)
        ):
            return WIDTH_1920

        self.logger.error(
            f"Unknown screen width. self._current_screen_width: {self._current_screen_width}"
        )
        raise ValueError()

    @property
    def normalized_screen_height(self):
        if (self._current_screen_height > (HEIGHT_720 - self.margin)) and (
            self._current_screen_height < (HEIGHT_720 + self.margin)
        ):
            return HEIGHT_720

        if (self._current_screen_width > (HEIGHT_1080 - self.margin)) and (
            self._current_screen_height < (HEIGHT_1080 + self.margin)
        ):
            return HEIGHT_1080

        self.logger.error(
            f"Unknown screen height. self._current_screen_height: {self._current_screen_height}"
        )
        raise ValueError()

    @property
    def screen_language(self):
        return self._screen_language

    @property
    def current_screen_width(self):
        return self._current_screen_width

    @current_screen_width.setter
    def current_screen_width(self, value):
        self._current_screen_width = value

    @property
    def current_screen_height(self):
        return self._current_screen_height

    @current_screen_height.setter
    def current_screen_height(self, value):
        self._current_screen_height = value

    def change_language(self, language):
        self._screen_language = language

    def update_game_window_size(self):
        """Update game window size and region."""
        wm = self._get_window_manager()
        window = self.get_game_window()
        
        # Get current window rect
        left, top, right, bottom = wm.get_window_rect(window)
        width = right - left
        height = bottom - top
        
        # Adjust for window borders/titlebar to get client area
        # Windows typically adds ~8px border on each side and ~31px titlebar
        # Linux with X11 may have different decoration sizes
        if width > WIDTH_1280 and width < WIDTH_1280 + self.margin:
            border_x = (width - WIDTH_1280) // 2
            left = left + border_x
            right = left + WIDTH_1280
            width = WIDTH_1280
        if height > HEIGHT_720 and height < HEIGHT_720 + self.margin:
            # タイトルバー（上）とボーダー（下）を分けて調整
            total_extra = height - HEIGHT_720
            border_bottom = 8  # 下ボーダーの推定値
            titlebar_top = total_extra - border_bottom
            top = top + titlebar_top
            height = HEIGHT_720
            bottom = top + height
        
        region = (left, top, right, bottom)
        self.logger.info(
            f"top: {top}, left: {left}, right: {right}, bottom: {bottom}, width: {width}, height: {height}"
        )

        self._current_screen_width = width
        self._current_screen_height = height
        self.current_screen_region = region

        return region

    def save_image(self, image, name="screenshot.jpeg"):
        current_dir = pathlib.Path().resolve()
        file_path = current_dir.joinpath(name)
        parent_dir = pathlib.Path(file_path).parent
        parent_dir.mkdir(parents=True, exist_ok=True)
        cv.imwrite(str(file_path), image)

    def all_templates(self, dir):
        template_files = []

        for file in os.listdir(dir):
            if file.endswith(".jpeg"):
                template_files.append(file)

        return template_files

    def detect(self, image, template, method=cv.TM_CCOEFF_NORMED):
        w, h = template.shape[::-1]
        img_h, img_w = image.shape[:2]
        
        # Skip if template is larger than image
        if w > img_w or h > img_h:
            return 0, (0, 0, w, h)
        
        res = cv.matchTemplate(image, template, method)
        min_val, max_val, min_loc, max_loc = cv.minMaxLoc(res)
        (x, y) = max_loc
        return max_val, (x, y, w, h)

    @retry(max_retries=3, delay=2)
    def detect_text(self, path):
        """Detects text in the file using local Tesseract OCR."""

        # 画像をグレースケールで読み込み
        image = cv.imread(path, cv.IMREAD_GRAYSCALE)
        if image is None:
            raise ValueError(f"Failed to load image for OCR: {path}")

        # 簡単な前処理: 二値化でコントラストを上げる
        _, thresh = cv.threshold(
            image, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU
        )

        pil_img = Image.fromarray(thresh)

        # 一行テキスト想定で英数字を優先して読む
        text = pytesseract.image_to_string(
            pil_img,
            lang="eng",
            config="--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789:/-"
        )

        return text.strip()
    
    def release(self):
        """Release resources."""
        if self._screen_capture:
            self._screen_capture.release()
            self._screen_capture = None
