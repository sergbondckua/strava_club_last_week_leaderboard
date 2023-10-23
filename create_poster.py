import logging
from os import path
from pathlib import Path

import requests
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps
from pilmoji import Pilmoji

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


class AthletesPoster:
    """Create poster"""

    def __init__(self, athletes):
        self.logger = logging.getLogger(__name__)
        self.base_dir = Path(__file__).resolve().parent
        self.athletes = athletes
        self.image = Image.open(
            path.join(self.base_dir, "resources/images/background.png")
        )
        self.font = ImageFont.truetype(
            path.join(self.base_dir, "resources/fonts/Ubuntu-Regular.ttf"),
            size=30,
        )
        self.draw = ImageDraw.Draw(self.image)
        self.emoji_text = Pilmoji(self.image)
        self.x = 20
        self.y = 362

    def create_head_poster(self, filename):
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

        for athlete in self.athletes:
            rank = athlete["rank"]
            name = athlete["athlete_name"]
            distance = athlete["distance"]
            avatar_url = athlete["avatar_large"]
            avatar_image = Image.open(
                requests.get(avatar_url, stream=True, timeout=5).raw
            )
            self.image.paste(avatar_image, (self.x, self.y))

            # Рисуем текст на изображении
            self.emoji_text.text(
                (self.x, self.y),
                f"{rank} {name} {distance}",
                fill="#1b0f13",
                font=self.font,
            )

        self.image.save(filename)


if __name__ == "__main__":
    athletes_data = [
        {
            "rank": "1",
            "athlete_name": "Евгений Степко",
            "distance": "108.3 km",
            "activities": "6",
            "longest": "25.4 km",
            "avg_pace": "5:07 /km",
            "elev_gain": "430 m",
            "avatar_large": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/37620439/11064752/4/large.jpg",
            "avatar_medium": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/37620439/11064752/4/medium.jpg",
            "link": "https://www.strava.com/athletes/37620439",
        },
        {
            "rank": "2",
            "athlete_name": "Андрій Прядко",
            "distance": "104.4 km",
            "activities": "6",
            "longest": "59.0 km",
            "avg_pace": "10:36 /km",
            "elev_gain": "4,341 m",
            "avatar_large": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/44626735/12516485/22/large.jpg",
            "avatar_medium": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/44626735/12516485/22/medium.jpg",
            "link": "https://www.strava.com/athletes/44626735",
        },
    ]  # Вставьте сюда данные атлетов
    output_filename = "athletes.png"
    athlete_image = AthletesPoster(athletes_data[:1])
    athlete_image.create_round_image_with_border().show()
    # athlete_image.create_head_poster(output_filename)
