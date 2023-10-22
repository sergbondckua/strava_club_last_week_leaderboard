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

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


class CreatePosterAthletes:
    def __init__(self, athletes: list[dict]):
        self.logger = logging.getLogger(__name__)
        self.athletes = athletes
        self.base_dir = Path(__file__).resolve().parent
        self.image = Image.open(
            path.join(self.base_dir, "resources/images/background.png")
        )
        self.font = ImageFont.truetype(
            path.join(self.base_dir, "resources/fonts/Ubuntu-Regular.ttf"),
            size=30,
        )
        self.draw = ImageDraw.Draw(self.image)
        self.emoji_text = Pilmoji(self.image)
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
            print(f"Error loading avatar: {str(e)}")
            return None

    async def _make_circular_avatar(
        self,
        avatar_url: str,
        border_color: str = "#fff",
        border_width: int = 2,
        size: int = 60,
    ) -> Image.Image:
        open_url = await self._load_user_avatar(avatar_url)
        avatar = open_url.resize((size, size))
        if avatar is not None:
            size = min(avatar.size)
            mask = Image.new("L", (size, size), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, size, size), fill=255)

            avatar = avatar.crop((0, 0, size, size))
            avatar.putalpha(mask)

            # Draw a circular border directly on the avatar image
            draw = ImageDraw.Draw(avatar)
            draw.ellipse(
                (0, 0, size, size), outline=border_color, width=border_width
            )

            return avatar
        raise ValueError("Image not found")

    def close(self):
        # Закрытие клиентской сессии при завершении работы
        self.session.close()

    def cap_poster(self):
        logo = Image.open(
            path.join(self.base_dir, "resources/images/logo.png")
        )
        strava = Image.open(
            path.join(self.base_dir, "resources/images/strava.png")
        )
        cup = Image.open(path.join(self.base_dir, "resources/images/cup.png"))

        # Icons on the "out" background
        self.image.paste(cup, (130, 150), cup)
        self.image.paste(logo, (5, 5), logo)
        self.image.paste(strava, (538, 0), strava)

        self.emoji_text.text((538, 240), "🔟\n🔝", font=self.font)
        return self.image

    async def poster(self):
        for athlete in self.athletes:
            rank = athlete["rank"]
            name = athlete["athlete_name"]
            distance = athlete["distance"]
            avatar_url = athlete["avatar_large"]
            avatar_image = await self._make_circular_avatar(avatar_url)
            self.image.paste(avatar_image, (20, 362))

            # Рисуем текст на изображении
            self.emoji_text.text(
                (20, 362),
                f"{rank} {name} {distance}",
                fill="#1b0f13",
                font=self.font,
            )


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
    image_url = "https://dgalywyr863hv.cloudfront.net/pictures/athletes/37620439/11064752/4/large.jpg"
    rounded_image = CreatePosterAthletes(athletes[:1])
    avatar = await rounded_image._make_circular_avatar(image_url)
    poster = rounded_image.cap_poster()
    await rounded_image.poster()
    poster.show()
    avatar.show()


if __name__ == "__main__":
    asyncio.run(process_image())
