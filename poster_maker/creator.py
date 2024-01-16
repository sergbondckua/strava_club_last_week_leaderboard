from __future__ import annotations

import re
import ssl
from io import BytesIO

import aiohttp
import certifi
from PIL import Image, ImageDraw
from pilmoji import Pilmoji

import config
from poster_maker.font_manager import FontManager


class AthleteRankPosterGenerator:
    """A class for generating posters with athlete rank information."""

    RESOURCES_DIR = config.BASE_DIR / "poster_maker/resources"
    BACKGROUND_IMAGE_PATH = RESOURCES_DIR / "images/background.png"
    BACKGROUND_2_IMAGE_PATH = RESOURCES_DIR / "images/background_2.png"
    CUP_PATH = RESOURCES_DIR / "images/cup.png"
    LOGO_PATH = RESOURCES_DIR / "images/logo.png"
    STRAVA_PATH = RESOURCES_DIR / "images/strava.png"
    HEAD_ICONS_POSITION_Y = 410
    AVATAR_SMALL_SIZE = 60
    AVATAR_LARGE_SIZE = 124
    AVATAR_SMALL_POSITION_X = 20
    AVATARS_TOP3_POSITIONS = ((258, 28), (130, 55), (385, 60))
    DISTANCE_POSITION_X = 450
    NAME_POSITION_X = 85
    ROW_POSITION_Y = 17
    RANK_POSITION_X = 15

    def __init__(self):
        self.logger = config.logger
        self.session = None
        self.font_utils = FontManager()
        self.method_calls = 0

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

        self.method_calls += 1
        self.logger.info(
            "Generation of poster #%s has begun...", self.method_calls
        )
        if not head_icons:
            shift = 50
            poster = Image.open(self.BACKGROUND_2_IMAGE_PATH)
        else:
            shift = self.HEAD_ICONS_POSITION_Y
            poster = Image.open(self.BACKGROUND_IMAGE_PATH)
            # self._add_logos_and_icons(poster)

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
            # emoji_text.text(
            #     (self.RANK_POSITION_X, self.ROW_POSITION_Y + shift),
            #     text=f"{rank}.",
            #     fill="#1b0f13",
            #     font=self.font_utils.font,
            # )

            emoji_text.text(
                (self.NAME_POSITION_X, self.ROW_POSITION_Y + shift),
                text=f"{rank}. {name}",
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

            shift += 59

        self.logger.info("Poster #%s is complete.", self.method_calls)
        return poster
