import ssl
import certifi
from PIL import Image, ImageDraw
from io import BytesIO
import aiohttp
import asyncio


class CreatePosterAthletes:
    def __init__(self, athletes: list[dict]):
        self.athletes = athletes
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
    ) -> Image.Image:
        avatar = await self._load_user_avatar(avatar_url)
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
        {
            "rank": "3",
            "athlete_name": "Yevhenii Kukhol 🇺🇦",
            "distance": "63.2 km",
            "activities": "9",
            "longest": "12.3 km",
            "avg_pace": "5:04 /km",
            "elev_gain": "272 m",
            "avatar_large": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/64522338/18318527/2/large.jpg",
            "avatar_medium": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/64522338/18318527/2/medium.jpg",
            "link": "https://www.strava.com/athletes/64522338",
        },
        {
            "rank": "4",
            "athlete_name": "Оля Моргун🇺🇦",
            "distance": "52.7 km",
            "activities": "4",
            "longest": "16.1 km",
            "avg_pace": "6:15 /km",
            "elev_gain": "895 m",
            "avatar_large": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/31197384/13320843/3/large.jpg",
            "avatar_medium": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/31197384/13320843/3/medium.jpg",
            "link": "https://www.strava.com/athletes/31197384",
        },
        {
            "rank": "5",
            "athlete_name": "Руслан Тищенко",
            "distance": "46.0 km",
            "activities": "2",
            "longest": "30.0 km",
            "avg_pace": "5:27 /km",
            "elev_gain": "349 m",
            "avatar_large": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/30094594/9033194/7/large.jpg",
            "avatar_medium": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/30094594/9033194/7/medium.jpg",
            "link": "https://www.strava.com/athletes/30094594",
        },
    ]
    image_url = "https://dgalywyr863hv.cloudfront.net/pictures/athletes/37620439/11064752/4/large.jpg"
    rounded_image = CreatePosterAthletes(athletes)
    avatar = await rounded_image._make_circular_avatar(image_url)
    avatar.show()


if __name__ == "__main__":
    asyncio.run(process_image())
