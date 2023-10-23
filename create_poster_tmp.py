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
    def __init__(self, athletes: list[dict]):
        self.logger = logging.getLogger(__name__)
        self.athletes = athletes
        self.base_dir = Path(__file__).resolve().parent
        self.image = Image.open(
            path.join(self.base_dir, "resources/images/background.png")
        )
        # Создаем клиентскую сессию и TCPConnector в конструкторе
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
        self.connector = aiohttp.TCPConnector(ssl=self.ssl_context)
        self.session = aiohttp.ClientSession(connector=self.connector)

    async def _load_user_avatar(self, avatar_url: str) -> Image.Image | None:
        try:
            async with self.session.get(avatar_url) as response:
                response.raise_for_status()  # Проверка на успешный статус ответа
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
        logo = Image.open(
            path.join(self.base_dir, "resources/images/logo.png")
        )
        strava = Image.open(
            path.join(self.base_dir, "resources/images/strava.png")
        )
        cup = Image.open(path.join(self.base_dir, "resources/images/cup.png"))

        # Add icons and logos
        image.paste(cup, (130, 150), cup)
        image.paste(logo, (5, 5), logo)
        image.paste(strava, (538, 0), strava)

        # Add text
        Pilmoji(image).text((538, 240), "🔟\n🔝", font=self.font)

    @property
    def font(self) -> ImageFont.FreeTypeFont:
        return ImageFont.truetype(
            path.join(self.base_dir, "resources/fonts/Ubuntu-Regular.ttf"),
            size=30,
        )

    async def generate_poster(self, shift: int = 0) -> Image.Image:
        """
        Generate a poster image with athlete information.

        Args:
            shift (int): Vertical position shift for adding multiple athletes (default is 0).

        Returns:
            Image.Image: The generated poster image as a PIL Image.
        """

        self.logger.info("Generating poster started...")
        if shift == 0:
            image = Image.open(
                path.join(self.base_dir, "resources/images/background_2.png")
            )
        else:
            image = self.image
            self._add_logos_and_icons(image)

        emoji_text = Pilmoji(image)

        for athlete in self.athletes:
            rank = athlete["rank"]
            name = athlete["athlete_name"]
            distance = athlete["distance"]
            avatar_url = athlete["avatar_large"]
            avatar_image = await self._make_circular_avatar(
                avatar_url,
                size=60,
            )

            image.paste(avatar_image, (60, shift), avatar_image)

            # Drawing text on an image
            emoji_text.text(
                (20, shift + 20),
                f"{rank}.",
                fill="#1b0f13",
                font=self.font,
            )

            emoji_text.text(
                (140, shift + 20),
                f"{name} 🔸 {distance}",
                fill="#1b0f13",
                font=self.font,
            )

            shift += 62
        await self.close()
        self.logger.info("Poster complete.")
        return image


async def process_image():
    athletes = [
        {
            "rank": "1",
            "athlete_name": "Влад Орлов",
            "distance": "90.2 km",
            "activities": "11",
            "longest": "16.0 km",
            "avg_pace": "5:50 /km",
            "elev_gain": "1,095 m",
            "avatar_large": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/80735219/25672890/6/large.jpg",
            "avatar_medium": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/80735219/25672890/6/medium.jpg",
            "link": "https://www.strava.com/athletes/80735219",
        },
        {
            "rank": "2",
            "athlete_name": "Евгений Степко",
            "distance": "81.0 km",
            "activities": "5",
            "longest": "19.4 km",
            "avg_pace": "4:53 /km",
            "elev_gain": "241 m",
            "avatar_large": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/37620439/11064752/4/large.jpg",
            "avatar_medium": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/37620439/11064752/4/medium.jpg",
            "link": "https://www.strava.com/athletes/37620439",
        },
    ]
    with Strava(email=env.str("EMAIL"), password=env.str("PASSWD")) as strava:
        rank_in_club = strava.get_this_week_or_last_week_leaders(
            env.int("CLUB_ID"),
            True,
        )
    rounded_image = PosterAthletes(rank_in_club[:10])
    poster = await rounded_image.generate_poster(shift=362)
    poster.show()


if __name__ == "__main__":
    asyncio.run(process_image())
