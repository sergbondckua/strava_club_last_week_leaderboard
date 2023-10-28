from __future__ import annotations

import logging
import re
import ssl
from os import path
from pathlib import Path

import asyncio
from io import BytesIO
import certifi
from PIL import Image, ImageDraw, ImageFont

import aiohttp
from fontTools.ttLib import TTFont

from pilmoji import Pilmoji

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


class PosterAthletes:
    """A class for generating posters with athlete rank information."""

    BASE_DIR = Path(__file__).resolve().parent
    RESOURCES_DIR = BASE_DIR / "resources"
    BACKGROUND_IMAGE_PATH = RESOURCES_DIR / "images/background.png"
    BACKGROUND_2_IMAGE_PATH = RESOURCES_DIR / "images/background_2.png"
    CUP_PATH = RESOURCES_DIR / "images/cup.png"
    LOGO_PATH = RESOURCES_DIR / "images/logo.png"
    STRAVA_PATH = RESOURCES_DIR / "images/strava.png"
    HEAD_ICONS_POSITION_Y = 362
    AVATAR_SMALL_SIZE = 60
    AVATAR_LARGE_SIZE = 124
    AVATAR_SMALL_POSITION_X = 70
    AVATARS_TOP3_POSITIONS = ((258, 28), (130, 55), (385, 60))
    DISTANCE_POSITION_X = 450
    NAME_POSITION_X = 140
    ROW_POSITION_Y = 20
    RANK_POSITION_X = 20

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session = None
        self.font_utils = FontManager()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        """Closing the client session when shutting down."""
        await self.session.close()

    def _get_session(self):
        if self.session is None:
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            self.session = aiohttp.ClientSession(connector=connector)
        return self.session

    async def _load_user_avatar(self, avatar_url: str) -> Image.Image | None:
        try:
            async with self._get_session().get(avatar_url) as response:
                response.raise_for_status()  # Checking for successful response status
                image_bytes = await response.read()
                return Image.open(BytesIO(image_bytes))
        except aiohttp.ClientError as e:
            self.logger.error("Error loading avatar: %s", e)
            return None

    async def _make_circular_avatar(
        self,
        avatar_url: str,
        border_color: str = "#fff",
        border_width: int = 1,
        size=None,
    ) -> Image.Image:
        source_img = await self._load_user_avatar(avatar_url)

        if source_img is not None:
            avatar = source_img.resize((size, size)) if size else source_img
            size = min(avatar.size)
            mask = Image.new("L", (size, size), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, size, size), fill=255)

            avatar = avatar.crop((0, 0, size, size))
            avatar.putalpha(mask)

            draw = ImageDraw.Draw(avatar)
            draw.ellipse(
                (0, 0, size, size), outline=border_color, width=border_width
            )

            return avatar
        self.logger.error("Image not found: url=%s incorrect", avatar_url)
        return Image.new(
            "RGBA", (60, 60), (255, 255, 255, 0)
        )  # Return a transparent image on error

    def _add_logos_and_icons(self, image: Image.Image) -> None:
        logo = Image.open(self.LOGO_PATH)
        strava = Image.open(self.STRAVA_PATH)
        cup = Image.open(self.CUP_PATH)

        image.paste(cup, (130, 150), cup)
        image.paste(logo, (5, 5), logo)
        image.paste(strava, (538, 0), strava)

        # Add text
        Pilmoji(image).text((538, 240), "🔟\n🔝", font=self.font_utils.font)

    async def generate_poster(
        self, athletes: list[dict], head_icons: bool = False
    ) -> Image.Image:
        """
        Generate a poster image with athlete information.
        """

        self.logger.info("Generating poster started...")
        if not head_icons:
            shift = 20
            poster = Image.open(self.BACKGROUND_2_IMAGE_PATH)
        else:
            shift = self.HEAD_ICONS_POSITION_Y
            poster = Image.open(self.BACKGROUND_IMAGE_PATH)
            self._add_logos_and_icons(poster)

        emoji_text = Pilmoji(poster)

        for athlete in athletes:
            rank = athlete["rank"]
            long_name = athlete["athlete_name"]
            name = (
                long_name if len(long_name) <= 18 else f"{long_name[:16]}..."
            )
            distance = athlete["distance"]
            avatar_url = athlete["avatar_large"]
            avatar_small = await self._make_circular_avatar(
                avatar_url=avatar_url,
                size=self.AVATAR_SMALL_SIZE,
            )

            if head_icons and int(rank) in range(1, 4):
                avatar_top_3 = await self._make_circular_avatar(
                    avatar_url=avatar_url,
                    size=self.AVATAR_LARGE_SIZE,
                )
                poster.paste(
                    avatar_top_3,
                    self.AVATARS_TOP3_POSITIONS[int(rank) - 1],
                    avatar_top_3,
                )

            poster.paste(
                avatar_small,
                (self.AVATAR_SMALL_POSITION_X, shift),
                avatar_small,
            )

            # Drawing text on an image
            emoji_text.text(
                (self.RANK_POSITION_X, self.ROW_POSITION_Y + shift),
                text=f"{rank}.",
                fill="#1b0f13",
                font=self.font_utils.font,
            )

            emoji_text.text(
                (self.NAME_POSITION_X, self.ROW_POSITION_Y + shift),
                text=name,
                fill="#1b0f13",
                font=await self.font_utils.set_font(
                    re.search(r"\w", name).group(0)
                ),
            )

            emoji_text.text(
                (self.DISTANCE_POSITION_X, self.ROW_POSITION_Y + shift),
                text=f"🔸 {distance}",
                fill="#1b0f13",
                font=self.font_utils.font,
            )

            shift += 62

        self.logger.info("Poster complete.")
        return poster


class PosterSaver:
    """Save poster to disk."""

    OUTPUT_FOLDER = "out_posters"

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.output_dir = Path(self.OUTPUT_FOLDER)

    async def save_poster(self, poster: Image.Image, filename: str):
        """
        Save the generated poster image to a file.
        """

        output_file = self.output_dir / filename
        with output_file.open("wb") as f:
            poster.save(f, "PNG")
        poster.close()  # Explicitly close the image

    async def clear_output_folder(self):
        """Clear the folder."""
        folder_path = self.output_dir.resolve()
        for file in folder_path.glob("*"):
            if file.is_file():
                file.unlink()
        self.logger.info("The folder has been cleared.")


class FontManager:
    """A FontManager class for managing fonts."""

    FONT_DIR = Path(__file__).resolve().parent / "resources/fonts"
    DEFAULT_FONT = path.join(FONT_DIR, "Ubuntu-Regular.ttf")
    FONT_SIZE = 30

    async def set_font(self, symbol: str) -> ImageFont.FreeTypeFont:
        """Set the font_manager to a given symbol"""

        symbol_unicode = ord(symbol)
        ttf = TTFont(self.DEFAULT_FONT)

        if self.is_symbol_in_font(symbol_unicode, ttf):
            return ImageFont.truetype(self.DEFAULT_FONT, size=self.FONT_SIZE)

        fonts_list = self.get_font_list()

        for font in fonts_list:
            ttf = TTFont(path.join(self.FONT_DIR, font))

            if self.is_symbol_in_font(symbol_unicode, ttf):
                return ImageFont.truetype(
                    path.join(self.FONT_DIR, font),
                    size=self.FONT_SIZE,
                )

        return ImageFont.truetype(self.DEFAULT_FONT, size=self.FONT_SIZE)

    @staticmethod
    def is_symbol_in_font(symbol_unicode: ord, font: TTFont) -> bool:
        """
        Checks if a Unicode symbol exists in the specified font.

        :param symbol_unicode: The Unicode symbol as a ord().
        :param font: The TTFont object representing the font.
        :return: True if the symbol exists in the font, otherwise False.
        """
        return any(
            char_map.isUnicode() and symbol_unicode in char_map.cmap
            for char_map in font["cmap"].tables
        )

    def get_font_list(self) -> list[Path]:
        """Get a list of font files in the specified directory."""

        font_dir = Path(self.FONT_DIR).resolve()
        fonts_list = [file for file in font_dir.glob("*") if file.is_file()]
        return fonts_list

    @property
    def font(self) -> ImageFont.FreeTypeFont:
        """Get the font_manager for text in the poster."""
        return ImageFont.truetype(self.DEFAULT_FONT, size=self.FONT_SIZE)
