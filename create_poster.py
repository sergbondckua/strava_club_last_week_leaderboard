import logging
import ssl
from os import path
from pathlib import Path
import aiohttp
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from pilmoji import Pilmoji
import certifi
from main import env
from parsing import Strava


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


class PosterAthletes:
    def __init__(self, athletes: list[dict], image_generator, avatar_loader):
        self.logger = logging.getLogger(__name__)
        self.athletes = athletes
        self.image_generator = image_generator
        self.avatar_loader = avatar_loader
        self.session = None

    def generate_poster(self, shift: int = 0):
        self.logger.info("Generating poster started...")
        if shift == 0:
            poster = self.image_generator.open_background_image_2()
        else:
            poster = self.image_generator.open_background_image()
            self.image_generator.add_logos_and_icons(poster)

        emoji_text = Pilmoji(poster)

        for athlete in self.athletes:
            rank = athlete["rank"]
            name = athlete["athlete_name"]
            distance = athlete["distance"]
            avatar_url = athlete["avatar_large"]
            avatar_small = self.avatar_loader.make_circular_avatar(
                avatar_url=avatar_url,
                size=self.avatar_loader.AVATAR_SMALL_SIZE,
            )

            if int(rank) in range(1, 4):
                avatar_top_3 = self.avatar_loader.make_circular_avatar(
                    avatar_url=avatar_url,
                    size=self.avatar_loader.AVATAR_LARGE_SIZE,
                )
                poster.paste(
                    avatar_top_3,
                    self.avatar_loader.AVATARS_TOP3_POSITIONS[int(rank) - 1],
                    avatar_top_3,
                )

            poster.paste(
                avatar_small,
                (self.avatar_loader.AVATAR_SMALL_POSITION_X, shift),
                avatar_small,
            )

            emoji_text.text(
                (
                    self.avatar_loader.RANK_POSITION_X,
                    self.avatar_loader.RANK_POSITION_Y + shift,
                ),
                f"{rank}.",
                fill="#1b0f13",
                font=self.avatar_loader.font,
            )

            emoji_text.text(
                (
                    self.avatar_loader.NAME_POSITION_X,
                    self.avatar_loader.ROW_POSITION_Y + shift,
                ),
                f"{name} 🔸 {distance}",
                fill="#1b0f13",
                font=self.avatar_loader.font,
            )

            shift += 62

        self.avatar_loader.close()
        self.logger.info("Poster complete.")
        return poster


class ImageGenerator:
    def __init__(self, resources_dir):
        self.resources_dir = resources_dir

    def open_background_image_2(self):
        return Image.open(self.resources_dir / "images/background_2.png")

    def open_background_image(self):
        return Image.open(self.resources_dir / "images/background.png")

    def add_logos_and_icons(self, image):
        logo = Image.open(self.resources_dir / "images/logo.png")
        strava = Image.open(self.resources_dir / "images/strava.png")
        cup = Image.open(self.resources_dir / "images/cup.png")

        image.paste(cup, (130, 150), cup)
        image.paste(logo, (5, 5), logo)
        image.paste(strava, (538, 0), strava)

        Pilmoji(image).text((538, 240), "🔟\n🔝", font=self.font)


class AvatarLoader:
    def __init__(self, session, font, avatars_positions):
        self.session = session
        self.font = font
        self.AVATARS_TOP3_POSITIONS = avatars_positions

    async def _load_user_avatar(self, avatar_url: str) -> Image.Image | None:
        try:
            async with self.session.get(avatar_url) as response:
                response.raise_for_status()
                image_bytes = await response.read()
                return Image.open(BytesIO(image_bytes))
        except aiohttp.ClientError as e:
            self.logger.error("Error loading avatar: %s", e)
            return None

    async def make_circular_avatar(
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
        self.logger.error("Image not found: url=%s incorrect")
        return Image.new("RGBA", (16, 16), (255, 255, 255, 0))

    async def close(self):
        await self.session.close()
