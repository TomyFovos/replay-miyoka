import time
import os
import cv2 as cv
import pathlib
from logging import Logger
from miyoka.libs.utils import retry
import pytesseract
from PIL import Image

try:
    import dxcam
    import pygetwindow as gw
except (ImportError, NotImplementedError) as e:
    print("WARN: dxcam and pygetwindow are supported in Windows only.")

WIDTH_1280 = 1280
WIDTH_1920 = 1920
HEIGHT_720 = 720
HEIGHT_1080 = 1080
DEFAULT_SCREEN_LANGUAGE = "en"


class GameWindowHelper:
    def __init__(self, logger: Logger, window_name: str, extra: dict, margin: int = 50):
        self.logger = logger
        self.window_name = window_name
        self.extra = extra
        self.margin = margin
        # Use language from config if available, otherwise fallback to default
        self._screen_language = extra.get("original_language", DEFAULT_SCREEN_LANGUAGE) if extra else DEFAULT_SCREEN_LANGUAGE

    def init_camera(self):
        self.camera = dxcam.create(
            output_idx=0, output_color="BGR"
        )  # returns a DXCamera instance on primary monitor

    def grab_frame(self):
        frame = None

        if not self.current_screen_region:
            ValueError(
                "Region is not set. Please call update_game_window_size() first."
            )

        while True:
            try:
                frame = self.camera.grab(region=self.current_screen_region)  # region
            except ValueError:
                frame = (
                    self.camera.grab()
                )  # Fallback to entire screen when the window does not fit within the screen.
                self.logger.warn(
                    f"Fallback to entire screen when the window does not fit within the screen. self.current_screen_region: {self.current_screen_region}"
                )

            if frame is not None:
                break
            else:
                print(f"Frame not found! Grabbing again...")
                time.sleep(0.1)
                continue

        return frame

    def wait_until_game_launched(self):
        # Activate the game window
        while True:
            try:
                self.get_game_window()
                break
            except:
                print(
                    f"Failed to find the game screen. Please make sure the game is running."
                )
                time.sleep(1)

    def get_game_window(self):
        return gw.getWindowsWithTitle(self.window_name)[0]

    def wait_until_game_focused(self):
        game_window = self.get_game_window()
        try:
            game_window.activate()
            game_window.moveTo(0, 0)
        except Exception as e:
            self.logger.error(f"Failed to activate window. {e}")

        # Wait for the window to be focused
        while not game_window.isActive:
            time.sleep(0.1)

    def ensure_obs(self):
        window_list = gw.getWindowsWithTitle("OBS")
        if len(window_list) == 0:
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
        game_window = self.get_game_window()
        top = game_window.top
        left = game_window.left
        right = game_window.right
        bottom = game_window.bottom
        width = game_window.right - game_window.left
        height = game_window.bottom - game_window.top
        
        # Adjust for window borders/titlebar to get client area
        # Windows typically adds ~8px border on each side and ~31px titlebar
        # We normalize to standard resolutions
        if width > WIDTH_1280 and width < WIDTH_1280 + self.margin:
            border_x = (width - WIDTH_1280) // 2
            left = left + border_x
            right = left + WIDTH_1280
            width = WIDTH_1280
        if height > HEIGHT_720 and height < HEIGHT_720 + self.margin:
            titlebar_and_border = height - HEIGHT_720
            top = top + titlebar_and_border
            height = HEIGHT_720
            bottom = top + height
        
        region = (left, top, right, bottom)
        size = (width, height)
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
