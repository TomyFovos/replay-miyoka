"""SF6 Replay Recorder - Records replays from Street Fighter 6.
Refactored to use platform abstraction layer for cross-platform support.
"""
from logging import Logger
import os
import time
import re
import shutil
import cv2 as cv
from typing import Optional
from datetime import datetime, timezone
from miyoka.libs.utils import cleanup_dir
from miyoka.libs.replay_recorder import ReplayRecorder as ReplayRecorderBase
from miyoka.libs.game_window_helper import WIDTH_1280, HEIGHT_720
from miyoka.libs.platform import get_input_controller
from miyoka.libs.platform.base import InputController
from miyoka.libs.obs_controller import OBSController, OBSConfig
from miyoka.sf6.game_window_helper import (
    GameWindowHelper,
)
import traceback
import threading
import pathlib

__all__ = ["ReplayRecorder"]


class ReplayRecorder(ReplayRecorderBase):
    def __init__(
        self,
        logger: Logger,
        game_window_helper: GameWindowHelper,
        replay_search_players: Optional[list[dict[str, str]]] = None,
        replay_search_replay_ids: Optional[list[str]] = None,
        max_replays_per_run: Optional[int] = None,
        stop_after_duplicate_replays: Optional[int] = None,
        skip_recording: Optional[bool] = None,
        separate_round: Optional[bool] = None,
        local_file_storage_dir: Optional[str] = "replays",
        obs_config: Optional[OBSConfig] = None,
    ):
        super().__init__()

        self.logger = logger
        self.game_window_helper = game_window_helper
        self.replay_search_players = replay_search_players
        self.replay_search_replay_ids = replay_search_replay_ids
        self.max_replays_per_run = max_replays_per_run
        self.stop_after_duplicate_replays = stop_after_duplicate_replays
        self.skip_recording = skip_recording
        self.separate_round = separate_round
        self.local_file_storage_dir = local_file_storage_dir

        self.current_replay_id = None
        self.current_metadata = None
        self.replay_search_user_code = None
        self.replay_search_replay_id = None
        self.replay_rewind_count = 5
        self.in_replay = False
        self.is_recording = False
        self.replay_done = False
        self.round = 0
        self.recorded_replay_count = 0
        self.duplicate_replay_count = 0

        # Initialize platform-specific input controller
        self._input: InputController = get_input_controller()
        
        # Initialize OBS controller
        self._obs = OBSController(logger, obs_config or OBSConfig())

        cleanup_dir("last_images")
        game_window_helper.wait_until_game_launched()
        game_window_helper.wait_until_game_focused()
        game_window_helper.ensure_obs()
        game_window_helper.update_game_window_size()
        game_window_helper.init_camera()

        if game_window_helper.normalized_screen_width != WIDTH_1280:
            raise ValueError(
                f"Window width must be {WIDTH_1280} but currently it's {game_window_helper.normalized_screen_width}. "
                "Please make sure that the Game setting and Windows Display setting have the same size."
            )

        if game_window_helper.normalized_screen_height != HEIGHT_720:
            raise ValueError(
                f"Window height must be {HEIGHT_720} but currently it's {game_window_helper.normalized_screen_height}. "
                "Please make sure that the Game setting and Windows Display setting have the same size."
            )

    def run(self):
        try:
            if self.replay_search_replay_ids is not None:
                for replay_search_replay_id in self.replay_search_replay_ids:
                    self.replay_search_replay_id = replay_search_replay_id
                    self._run()
                    self._exit_from_replay()
            elif self.replay_search_players is not None:
                for replay_search_player in self.replay_search_players:
                    self.replay_search_user_code = str(replay_search_player["id"])
                    self._run()
                    self._exit_from_replay()
        except Exception as e:
            self.logger.error(f"Error: {e} traceback: {traceback.format_exc()}")
            raise e

    def _start_recording(self):
        """Start OBS recording."""
        self.is_recording = True
        
        if self._obs.start_recording():
            self.logger.info("OBS recording started")
        else:
            self.logger.error("Failed to start OBS recording")

    def _stop_recording(self):
        """Stop OBS recording and get the recording path."""
        self.is_recording = False
        
        recording_path = self._obs.stop_recording()
        
        if recording_path:
            self.logger.info(f"OBS recording stopped. File: {recording_path}")
            self.save_replay(recording_path)
        else:
            self.logger.error("Failed to stop recording or get recording path")

    def _process_separate_round_in_replay(self, frame):
        is_replay_options_in_round_exist = (
            self.game_window_helper.is_replay_options_in_round_exist(frame)
        )

        if is_replay_options_in_round_exist and not self.is_recording:
            self._input.press("r")  # Pause
            for _ in range(self.replay_rewind_count):
                self._input.press("z")  # Previous Scene - Rolling back to the beginning of the game.

            # Start recording
            self._start_recording()

            time.sleep(1.0)

            self._input.press("r")  # Resume

        if not is_replay_options_in_round_exist and self.is_recording:
            # Stop recording
            self._stop_recording()

            self.round += 1

    def _run(self):
        g_repeat_mode = False

        while True:
            frame = self.game_window_helper.grab_frame()

            if self.separate_round and self.in_replay:
                self._process_separate_round_in_replay(frame)

            screen = self.game_window_helper.identify_screen(frame)

            self.logger.info(f"screen: {screen}")

            match screen:
                case "TitleScreen":
                    self.in_replay = False
                    g_repeat_mode = False
                    self._input.press("Tab")  # Press Any Button
                case "MainBh":
                    self.in_replay = False
                    g_repeat_mode = False
                    self._input.press("Tab")  # Open menu
                    time.sleep(3)
                case "News":
                    self._input.press("ESC")  # Exit from news
                case "MultiMenuProfile":
                    self._input.press("d")  # Right
                case "MultiMenuCfn":
                    self._input.press("f")  # Enter
                case "CfnPlayers":
                    self._input.press("d")  # Right
                case "CfnClubs":
                    self._input.press("d")  # Right
                case "CfnReplays":
                    self._input.press("f")  # Enter
                    time.sleep(2)
                case "KeywordSearchByPlayerName":
                    self._input.press("s")  # Down in submenu
                case "KeywordSearchByUserCode":
                    if self.replay_search_user_code:
                        self._input.press("f")  # Enter
                    else:
                        self._input.press("s")  # Down in submenu
                case "KeywordSearchByReplayId":
                    if self.replay_search_replay_id:
                        self._input.press("f")  # Enter
                    else:
                        self._input.press("s")  # Down in submenu
                case "DialogUserCode":
                    self._input.press("f")  # Enter the text box
                    time.sleep(2)
                    # Clear existing text before input
                    self._input.key_down("ctrl")
                    self._input.press("a")
                    self._input.key_up("ctrl")
                    self._input.press("delete")
                    self.logger.info(
                        f"Setting user code {self.replay_search_user_code}"
                    )
                    self._input.write(self.replay_search_user_code)
                    self._input.press("Enter")  # Exit the focus from the text box
                    self._input.press("s")  # Down
                    self._input.press("f")  # Enter - Start searching
                case "DialogReplayId":
                    self._input.press("f")  # Enter the text box
                    time.sleep(2)
                    # Clear existing text before input
                    self._input.key_down("ctrl")
                    self._input.press("a")
                    self._input.key_up("ctrl")
                    self._input.press("delete")
                    self.logger.info(
                        f"Setting replay ID {self.replay_search_replay_id}"
                    )
                    self._input.write(self.replay_search_replay_id.lower())
                    self._input.press("Enter")  # Exit the focus from the text box
                    self._input.press("s")  # Down
                    self._input.press("f")  # Enter - Start searching
                case "SearchResults":
                    if self.replay_search_replay_id and self.replay_done:
                        self.logger.info(
                            f"Recorded {self.replay_search_replay_id} replay. Stopping."
                        )
                        return

                    if self.replay_done:
                        time.sleep(2)
                        self._input.press("s")  # Down - Select the next replay
                        self.replay_done = False

                    self._input.press("f")  # Enter - Enter a replay
                case "ReplaySummary":
                    if self.recorded_replay_count >= self.max_replays_per_run:
                        self.logger.info(
                            f"Recorded {self.recorded_replay_count} replays. Stopping."
                        )
                        return

                    if self.duplicate_replay_count >= self.stop_after_duplicate_replays:
                        self.logger.info(
                            f"Already recorded {self.duplicate_replay_count} replays. Stopping."
                        )
                        return

                    self.extract_replay_id(frame)

                    if self.is_replay_exist() or self.skip_recording:
                        self.duplicate_replay_count += 1
                        self._input.press("ESC")  # Exit
                        self.replay_done = True
                        continue

                    self._input.press("f")  # Enter - Start watching replay

                    self.in_replay = True
                    self.round = 1
                    self.recorded_replay_count += 1

                    if self.separate_round:
                        # For showing reply menu and skipping opening
                        g_repeat_mode = True
                        self.is_recording = False
                    else:
                        time.sleep(2.0)
                        # Start recording
                        self._start_recording()
                case "ReplayEndDiaglogPlayAgain":
                    if not self.separate_round:
                        # Stop recording
                        self._stop_recording()

                    self.in_replay = False
                    g_repeat_mode = False
                    self.replay_done = True

                    self._input.press("s")  # Down
                    self._input.press("f")  # Confirm - End replay

                    self.game_window_helper.update_game_window_size()  # Reset the game window size after the analyze.
                case "ErrorCommunication" | "ErrorCommunication2":
                    self._input.press("f")  # OK - Close dialog
                case "ErrorLogin":
                    self._input.press("d")  # To Right
                    self._input.press("f")  # Click No to the offline mode
                case "MainFg":
                    self._input.press("a")  # Left
                case "OptionsLanguageDisplayLanguageEnglish":
                    # From Language settings, navigate back to main menu
                    self._input.press("ESC")  # Exit from language settings
                    time.sleep(1)
                    self._input.press("ESC")  # Exit from options menu
                    time.sleep(1)
                    self._input.press("ESC")  # Exit to main menu
                case "MultiOptions":
                    # Instead of ESC, navigate to Game options to eventually reach CFN
                    self._input.press("f")  # Enter Game options from Multi Options
                    time.sleep(1)
                case "OptionsGame":
                    self._input.press("E")  # Navigate in Game options (1/5)
                    time.sleep(0.5)
                    self._input.press("E")  # Navigate in Game options (2/5)
                    time.sleep(0.5)
                    self._input.press("E")  # Navigate in Game options (3/5)
                    time.sleep(0.5)
                    self._input.press("E")  # Navigate in Game options (4/5)
                    time.sleep(0.5)
                    self._input.press("E")  # Navigate in Game options (5/5)
                    time.sleep(0.5)
                case _:
                    pass

            if g_repeat_mode:
                self._input.press("g")

            time.sleep(0.3)

            if g_repeat_mode:
                self._input.press("g")

    def extract_replay_id(self, frame):
        if self.replay_search_replay_id:
            self.current_replay_id = self.replay_search_replay_id
            return

        current_replay_id = self.game_window_helper.identify_replay_id(frame)
        self.logger.info(f"Current Replay ID: {current_replay_id}")

        self.current_replay_id = current_replay_id

    def is_replay_exist(self) -> bool:
        # リプレイIDが取得できていない場合は存在チェックをスキップ
        if not self.current_replay_id:
            return False

        filename = self._local_replay_file_name()

        if os.path.exists(os.path.join(self._local_replay_dir(), filename)):
            self.logger.warn(f"Replay {filename} already exists")
            return True
            
        return False

    def save_replay_locally(
        self,
        recording_path: str,
        replay_dir: str,
        filename: str,
    ):
        time.sleep(5) # OBS might still be processing the video.
        destination_dir = pathlib.Path(replay_dir)
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination_path = destination_dir.joinpath(filename)

        try:
            shutil.move(recording_path, str(destination_path))
        except Exception as ex:
            self.logger.error(
                f"Failed to move replay from {recording_path} to {destination_path}: {ex}"
            )

    def save_replay(self, recording_path: str):
        # Save to local file storage
        threading.Thread(
            target=self.save_replay_locally,
            kwargs={
                "recording_path": recording_path,
                "replay_dir": self._local_replay_dir(),
                "filename": self._local_replay_file_name(),
            },
        ).start()


    def _local_replay_dir(self):
        base_dir = self.local_file_storage_dir or "replays"

        if not os.path.isabs(base_dir):
            base_dir = os.path.join(os.getcwd(), base_dir)

        player_id = self._get_current_player_id()
        if player_id:
            return os.path.join(base_dir, str(player_id))

        return base_dir

    def _get_current_player_id(self) -> Optional[str]:
        if self.replay_search_user_code:
            return str(self.replay_search_user_code)

        if not self.current_metadata or not self.replay_search_players:
            return None

        p1_name = self.current_metadata.get("p1", {}).get("player_name", "")
        p2_name = self.current_metadata.get("p2", {}).get("player_name", "")

        for player in self.replay_search_players:
            pattern = player.get("pattern")
            player_id = player.get("id")

            if not player_id:
                continue

            if not pattern:
                return str(player_id)

            try:
                if re.search(pattern, p1_name, re.IGNORECASE) or re.search(pattern, p2_name, re.IGNORECASE):
                    return str(player_id)
            except re.error:
                lower_pattern = pattern.lower()
                if lower_pattern in p1_name.lower() or lower_pattern in p2_name.lower():
                    return str(player_id)

        return None
    
    def _local_replay_file_name(self):
        if self.separate_round:
            return f"{self.current_replay_id}_{self.round}.mp4"
        else:
            return f"{self.current_replay_id}.mp4"

    def _exit_from_replay(self):
        # Back to the top screen
        self._input.press("ESC")
        self._input.press("ESC")
        self._input.press("ESC")
        self.recorded_replay_count = 0
        self.duplicate_replay_count = 0
        self.replay_done = False
