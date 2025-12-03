import cv2 as cv
from miyoka.libs.game_window_helper import GameWindowHelper as GameWindowHelperBase
from datetime import datetime
import urllib.parse


class GameWindowHelper(GameWindowHelperBase):
    def templates_dir(self, dir):
        return f"miyoka/sf6/templates/{self.normalized_screen_width}x{self.normalized_screen_height}/{self.screen_language}/{dir}"

    def switch_to_original_language(self):
        self.change_language(self.extra["original_language"])

    def get_original_quality(self):
        return self.extra["original_quality"]

    def get_original_display_mode(self):
        return self.extra["original_display_mode"]

    def get_original_language(self):
        return self.extra["original_language"]

    def identify_screen(self, image):
        self.save_image(image, f"last_images/identify_screen/screen.jpeg")

        screen, _ = self.identify_in_screen(
            image, self.templates_dir("screens"), threthold=0.85
        )

        return screen

    def is_replay_options_exist(self, image):
        roi = (326, 704, 635, 100)

        (x, y, width, height) = roi
        cropped_image = image[y : y + height, x : x + width]

        self.save_image(
            cropped_image, f"last_images/is_replay_options_exist/image.jpeg"
        )

        option, _ = self.identify_in_screen(
            cropped_image, self.templates_dir("replay_options")
        )

        print(f"option: {option}")
        return option != ""

    def is_replay_options_in_round_exist(self, image):
        roi = (326, 704, 635, 100)

        (x, y, width, height) = roi
        cropped_image = image[y : y + height, x : x + width]

        self.save_image(
            cropped_image, f"last_images/is_replay_options_in_round_exist/image.jpeg"
        )

        option, _ = self.identify_in_screen(
            cropped_image, self.templates_dir("replay_options_in_round"), threthold=0.85
        )

        print(f"option: {option}")
        return option != ""

    def is_replay_started(self, image):
        roi = (605, 174, 76, 57)

        (x, y, width, height) = roi
        cropped_image = image[y : y + height, x : x + width]

        self.save_image(cropped_image, f"last_images/is_paused/image.jpeg")

        tmp, _ = self.identify_in_screen(
            cropped_image, self.templates_dir("replay_center"), threthold=0.7
        )

        return tmp == "play"

    def identify_in_screen(self, image, template_dir, threthold=0.75):
        if not isinstance(image, list):
            image = [image]

        detected = ""
        highest = 0
        roi = None

        for img in image:
            img_gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

            for template_file in self.all_templates(template_dir):
                template = cv.imread(
                    template_dir + "/" + template_file, cv.IMREAD_GRAYSCALE
                )
                name = template_file.replace(".jpeg", "").split("_")[0]
                score, roi = self.detect(img_gray, template)

                if (score > threthold) and (score > highest):
                    highest = score
                    detected = name
                    roi = roi

        return detected, roi

    def identify_replay_id(self, image):
        roi = (273, 123, 90, 23)

        (x, y, width, height) = roi
        cropped_image = image[y : y + height, x : x + width]

        self.save_image(cropped_image, f"last_images/identify_replay_id/image.jpeg")

        name = self.detect_text(f"last_images/identify_replay_id/image.jpeg")

        return urllib.parse.quote_plus(name)

    def identify_played_at(self, image):
        roi = (858, 108, 120, 20)

        (x, y, width, height) = roi
        cropped_image = image[y : y + height, x : x + width]

        self.save_image(cropped_image, f"last_images/identify_played_at/image.jpeg")

        detected_played_at = self.detect_text(
            f"last_images/identify_played_at/image.jpeg"
        )

        try:
            played_at = detected_played_at.replace("-", "").strip()
            played_at = datetime.strptime(played_at, "%m/%d/%Y %H:%M")
        except Exception as e:
            self.logger.error(
                f"failed to identify played_at. detected_played_at: {detected_played_at}"
            )
            played_at = None

        return played_at

    def identify_result(self, image, player):
        p1_roi = (458, 315, 82, 29)

        if player == "p1":
            roi = p1_roi
        elif player == "p2":
            roi = self.mirror_p2_roi_from(p1_roi)

        (x, y, width, height) = roi
        cropped_image = image[y : y + height, x : x + width]

        self.save_image(cropped_image, f"last_images/summary_results/{player}.jpeg")

        tmp, _ = self.identify_in_screen(
            cropped_image, self.templates_dir("summary_results"), threthold=0.7
        )

        if not tmp:
            self.logger.error(f"failed to identify results for {player}")
            raise ValueError()

        return tmp

    def identify_mode(self, image, player):
        if player == "p1":
            roi = (200, 200, 30, 30)
        elif player == "p2":
            roi = (933, 200, 30, 30)

        (x, y, width, height) = roi
        cropped_image = image[y : y + height, x : x + width]

        self.save_image(cropped_image, f"last_images/summary_modes/{player}.jpeg")

        mode, _ = self.identify_in_screen(
            cropped_image, self.templates_dir("summary_modes"), threthold=0.70
        )

        if not mode:
            self.logger.error(f"failed to identify mode for {player}")
            raise ValueError()

        return mode

    def identify_rank(self, image, player):
        p1_roi = (250, 182, 72, 45)

        if player == "p1":
            roi = p1_roi
        elif player == "p2":
            roi = self.mirror_p2_roi_from(p1_roi)

        (x, y, width, height) = roi
        cropped_image = image[y : y + height, x : x + width]

        self.save_image(cropped_image, f"last_images/summary_ranks/{player}.jpeg")

        rank, _ = self.identify_in_screen(
            cropped_image, self.templates_dir("summary_ranks"), threthold=0.8
        )

        return rank

    def identify_player_name(self, image, player):
        if player == "p1":
            roi = (189, 241, 211, 23)
        elif player == "p2":
            roi = (921, 241, 211, 23)

        (x, y, width, height) = roi
        cropped_image = image[y : y + height, x : x + width]

        self.save_image(
            cropped_image, f"last_images/summary_player_names/{player}.jpeg"
        )
        player_name = self.detect_text(
            f"last_images/summary_player_names/{player}.jpeg"
        )
        return player_name

    def identify_mr(self, image, player):
        if player == "p1":
            roi = (325, 202, 65, 20)
        elif player == "p2":
            roi = (1062, 202, 65, 20)

        (x, y, width, height) = roi
        cropped_image = image[y : y + height, x : x + width]

        self.save_image(cropped_image, f"last_images/summary_mrs/{player}.jpeg")

        mr_str = self.detect_text(f"last_images/summary_mrs/{player}.jpeg")
        mr_str = mr_str.replace("MR", "").strip()

        if not mr_str.isdecimal():
            return None

        return int(mr_str)

    def identify_lp(self, image, player):
        if player == "p1":
            roi = (325, 205, 65, 21)
        elif player == "p2":
            roi = (1062, 205, 65, 21)

        (x, y, width, height) = roi
        cropped_image = image[y : y + height, x : x + width]

        self.save_image(cropped_image, f"last_images/summary_lps/{player}.jpeg")

        lp_str = self.detect_text(f"last_images/summary_lps/{player}.jpeg")
        lp_str = lp_str.replace("LP", "").strip()

        if not lp_str.isdecimal():
            return None

        return int(lp_str)

    def identify_character(self, image, player):
        p1_roi = (430, 175, 135, 140)

        if player == "p1":
            roi = p1_roi
        elif player == "p2":
            roi = self.mirror_p2_roi_from(p1_roi)

        (x, y, width, height) = roi
        cropped_image = image[y : y + height, x : x + width]
        cropped_image_mirror = cv.flip(cropped_image, 1)

        self.save_image(cropped_image, f"last_images/summary_characters/{player}.jpeg")

        character, _ = self.identify_in_screen(
            [cropped_image, cropped_image_mirror],
            self.templates_dir("summary_characters"),
            threthold=0.7,
        )

        if not character:
            self.logger.error(f"failed to identify character for {player}")
            return "unknown"

        return character

    def identify_round_results(self, image, player):
        p1_rois = [
            (590, 201, 40, 25),  # r1
            (590, 223, 40, 25),  # r2
            (590, 253, 40, 25),  # r3
        ]

        if player == "p1":
            rois = p1_rois
        elif player == "p2":
            rois = [self.mirror_p2_roi_from(p1_roi) for p1_roi in p1_rois]

        ret = []

        for i, roi in enumerate(rois):
            (x, y, width, height) = roi
            cropped_image = image[y : y + height, x : x + width]
            cropped_image_mirror = cv.flip(cropped_image, 1)

            self.save_image(
                cropped_image, f"last_images/summary_round_wins/{player}-r{i}.jpeg"
            )

            round_win, _ = self.identify_in_screen(
                [cropped_image, cropped_image_mirror],
                self.templates_dir("summary_round_wins"),
                threthold=0.7,
            )

            if not round_win:
                self.logger.error(f"failed to identify round_win for {player}")
                raise ValueError()

            ret.append(round_win)

        return ret
