import logging
import ssl
from os import path
from pathlib import Path

import certifi
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import aiohttp
import asyncio

from pilmoji import Pilmoji

from main import env
from parsing import Strava

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
    AVATAR_SMALL_POSITION_X = 60
    AVATARS_TOP3_POSITIONS = ((258, 28), (130, 55), (385, 60))
    FONT_SIZE = 30
    NAME_POSITION_X = 140
    NAME_POSITION_Y = 20
    RANK_POSITION_X = 20
    RANK_POSITION_Y = 20

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # self.athletes = athletes
        self.session = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

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
            "RGBA", (16, 16), (255, 255, 255, 0)
        )  # Return a transparent image on error

    async def close(self):
        """Closing the client session when shutting down."""
        await self.session.close()

    def _add_logos_and_icons(self, image: Image.Image) -> None:
        logo = Image.open(self.LOGO_PATH)
        strava = Image.open(self.STRAVA_PATH)
        cup = Image.open(self.CUP_PATH)

        image.paste(cup, (130, 150), cup)
        image.paste(logo, (5, 5), logo)
        image.paste(strava, (538, 0), strava)

        # Add text
        Pilmoji(image).text((538, 240), "🔟\n🔝", font=self.font)

    @property
    def font(self) -> ImageFont.FreeTypeFont:
        """
        Get the font for text in the poster.

        Returns:
            ImageFont.FreeTypeFont: The PIL ImageFont instance.
        """
        return ImageFont.truetype(
            path.join(self.BASE_DIR, "resources/fonts/Ubuntu-Regular.ttf"),
            size=self.FONT_SIZE,
        )

    async def generate_poster(
        self, athletes: list[dict], head_icons: bool = False
    ) -> Image.Image:
        """
        Generate a poster image with athlete information.
        """

        self.logger.info("Generating poster started...")
        if not head_icons:
            shift = 5
            poster = Image.open(self.BACKGROUND_2_IMAGE_PATH)
        else:
            shift = self.HEAD_ICONS_POSITION_Y
            poster = Image.open(self.BACKGROUND_IMAGE_PATH)
            self._add_logos_and_icons(poster)

        emoji_text = Pilmoji(poster)

        for athlete in athletes:
            rank = athlete["rank"]
            name = athlete["athlete_name"]
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
                (self.RANK_POSITION_X, self.RANK_POSITION_Y + shift),
                f"{rank}.",
                fill="#1b0f13",
                font=self.font,
            )

            emoji_text.text(
                (self.NAME_POSITION_X, self.NAME_POSITION_Y + shift),
                f"{name} 🔸 {distance}",
                fill="#1b0f13",
                font=self.font,
            )

            shift += 62

        # await self.close()
        self.logger.info("Poster complete.")

        return poster


async def process_image():
    with Strava(email=env.str("EMAIL"), password=env.str("PASSWD")) as strava:
        athletes_rank = strava.get_this_week_or_last_week_leaders(
            env.int("CLUB_ID"),
            last_week=True,
        )

    async with PosterAthletes() as pa:
        top_10 = athletes_rank[:10]
        remainder = athletes_rank[10:]
        groups = [top_10] + [
            remainder[i:i + 15] for i in range(0, len(remainder), 15)
        ]

        for num, group in enumerate(groups):
            head_icons = True if num == 0 else False
            poster = await pa.generate_poster(group, head_icons)
            poster.show()


if __name__ == "__main__":
    asyncio.run(process_image())
