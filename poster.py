"""Create a poster with the given leaders"""
import logging
import ssl
from os import path
from pathlib import Path
from urllib.request import urlopen

import certifi
from PIL import (
    Image,
    ImageChops,
    ImageDraw,
    ImageFont
)
from pilmoji import Pilmoji
from fontTools.ttLib import TTFont

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


class Poster:
    """Create a poster with the given leaders"""
    _BASE_DIR = Path(__file__).resolve().parent
    __ubuntu_font = path.join(_BASE_DIR, "resources/fonts/Ubuntu-Regular.ttf")
    __symbol_font = path.join(_BASE_DIR, "resources/fonts/Symbola-AjYx.ttf")

    def __init__(self, leaders: list):
        self.leaders = leaders
        self.logging = logging.getLogger(__name__)
        self.out = Image.open(path.join(
            self._BASE_DIR, "resources/images/background.png"))
        self.out_2 = Image.open(path.join(
            self._BASE_DIR, "resources/images/background_2.png"))
        self.font = ImageFont.truetype(self.__ubuntu_font, size=30)
        # Icons and text on the "out and out_2" background
        self.emoji_text = Pilmoji(self.out)
        self.emoji_text2 = Pilmoji(self.out_2)

    @staticmethod
    def char_in_font(unicode_char: str, font: ImageFont) -> bool:
        """ Checks if the font supports a character in a string,
        if it doesn't support True
        :param unicode_char: the character to check
        :param font: the font to check
        :return: True if the character is in the font, False otherwise
        """
        for cmap in font["cmap"].tables:
            if cmap.isUnicode() and ord(unicode_char) in cmap.cmap:
                return False
        return True

    @staticmethod
    def crop_to_circle(img: Image):
        """ Creates a round photo frame and crops
        to make it round with a border
        :param img: the image to crop
        :return: the cropped image
        """
        big_size = (img.size[0] * 3, img.size[1] * 3)
        mask = Image.new("L", big_size, 0)
        ImageDraw.Draw(mask).ellipse((0, 0) + big_size, fill=255)
        mask = mask.resize(img.size, Image.LANCZOS)
        mask = ImageChops.darker(mask, img.split()[-1])
        img.putalpha(mask)
        border = Image.new("RGBA", big_size, 0)
        ImageDraw.Draw(border).ellipse((0, 0) + big_size,
                                       fill=0, outline="#fff", width=3)
        border = border.resize(img.size, Image.LANCZOS)
        img.paste(border, (0, 0), border)

    def create_poster(self):
        """Create a poster"""
        logo = Image.open(path.join(
            self._BASE_DIR, "resources/images/logo.png"))
        strava = Image.open(path.join(
            self._BASE_DIR, "resources/images/strava.png"))
        cup = Image.open(path.join(
            self._BASE_DIR, "resources/images/cup.png"))
        # Icons on the "out" background
        self.out.paste(cup, (130, 150), cup)
        self.out.paste(logo, (5, 5), logo)
        self.out.paste(strava, (538, 0), strava)

        self.emoji_text.text((538, 240), "🔟\n🔝", font=self.font)
        shift = 362  # Start coordinate of the top 10 list
        shift_2 = 0  # Starting coordinate after top 10 list

        self.logging.info("Posters with the rating of athletes are created")

        for place, sportsmen in enumerate(self.leaders[:26]):
            font = self.font
            # If the characters in the name (string) of the athlete are not
            # supported by the font, we replace it with a font that can do this
            if self.char_in_font(
                    sportsmen.get("athlete_name").split(" ")[1][:1],
                    TTFont(self.__ubuntu_font)):
                font = ImageFont.truetype(self.__symbol_font, size=26)

            # Resize the athlete's avatar to the desired size
            with urlopen(
                    sportsmen.get("avatar_medium"),
                    context=ssl.create_default_context(
                        cafile=certifi.where())) as avatar_medium:
                avatar = Image.open(
                    avatar_medium).convert("RGBA").resize((60, 60))

            with urlopen(
                    sportsmen.get("avatar_large"),
                    context=ssl.create_default_context(
                        cafile=certifi.where())) as avatar_large:
                avatar_top_3 = Image.open(
                    avatar_large).convert("RGBA").resize((124, 124))

            # Making avatars round
            self.crop_to_circle(avatar)
            self.crop_to_circle(avatar_top_3)

            # We form the first image list, TOP10
            if place <= 9:
                if place <= 2:
                    coordinate = ()
                    if place == 0:  # First place
                        coordinate = (258, 28)
                    elif place == 1:  # Second place
                        coordinate = (130, 55)
                    elif place == 2:  # Third place
                        coordinate = (385, 60)
                    self.out.paste(avatar_top_3, coordinate, avatar_top_3)

                self.out.paste(avatar, (60, shift), avatar)
                self.emoji_text.text((20, shift + 20),
                                     f"{sportsmen.get('rank')}.",
                                     font=ImageFont.truetype(
                                         self.__ubuntu_font,
                                         size=30),
                                     fill="#1b0f13"
                                     )

                self.emoji_text.text((140, shift + 20),
                                     f"{sportsmen.get('athlete_name')} 🔸 "
                                     f"{sportsmen.get('distance')}",
                                     font=font,
                                     fill="#1b0f13"
                                     )
                shift += 62
            # We form the first list of images, all the rest
            else:
                self.out_2.paste(avatar, (60, shift_2), avatar)
                self.emoji_text2.text((20, shift_2 + 20),
                                      f"{sportsmen.get('rank')}.",
                                      font=ImageFont.truetype(
                                          self.__ubuntu_font,
                                          size=30),
                                      fill="#1b0f13"
                                      )

                self.emoji_text2.text((140, shift_2 + 20),
                                      f"{sportsmen.get('athlete_name')} 🔸 "
                                      f"{sportsmen.get('distance')}",
                                      font=font,
                                      fill="#1b0f13"
                                      )
                shift_2 += 62
        # Save the created image and close
        self.out.save(path.join(self._BASE_DIR, "out_posters/out1.png"), "PNG")
        self.out.close()
        # Save the created image and close
        self.out_2.save(path.join(self._BASE_DIR, "out_posters/out2.png"), "PNG")
        self.out_2.close()
        self.logging.info("Posters are ready and saved")
