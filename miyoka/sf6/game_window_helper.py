import cv2 as cv
from miyoka.libs.game_window_helper import GameWindowHelper as GameWindowHelperBase
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
        roi = (260, 90, 100, 25)

        (x, y, width, height) = roi
        cropped_image = image[y : y + height, x : x + width]

        self.save_image(cropped_image, f"last_images/identify_replay_id/image.jpeg")

        name = self.detect_text(f"last_images/identify_replay_id/image.jpeg")

        return urllib.parse.quote_plus(name)
