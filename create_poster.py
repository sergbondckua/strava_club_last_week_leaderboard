import logging
from os import path
from pathlib import Path

import requests
from PIL import Image, ImageChops, ImageDraw, ImageFont
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
        {
            "rank": "3",
            "athlete_name": "Yevhenii Kukhol 🇺🇦",
            "distance": "92.0 km",
            "activities": "11",
            "longest": "17.7 km",
            "avg_pace": "5:13 /km",
            "elev_gain": "1,489 m",
            "avatar_large": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/64522338/18318527/2/large.jpg",
            "avatar_medium": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/64522338/18318527/2/medium.jpg",
            "link": "https://www.strava.com/athletes/64522338",
        },
        {
            "rank": "4",
            "athlete_name": "Влад 🇺🇦",
            "distance": "57.8 km",
            "activities": "4",
            "longest": "18.1 km",
            "avg_pace": "5:31 /km",
            "elev_gain": "209 m",
            "avatar_large": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/94984713/24934843/2/large.jpg",
            "avatar_medium": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/94984713/24934843/2/medium.jpg",
            "link": "https://www.strava.com/athletes/94984713",
        },
        {
            "rank": "5",
            "athlete_name": "Оля Моргун🇺🇦",
            "distance": "42.1 km",
            "activities": "3",
            "longest": "15.0 km",
            "avg_pace": "6:21 /km",
            "elev_gain": "441 m",
            "avatar_large": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/31197384/13320843/3/large.jpg",
            "avatar_medium": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/31197384/13320843/3/medium.jpg",
            "link": "https://www.strava.com/athletes/31197384",
        },
        {
            "rank": "6",
            "athlete_name": "Сергей Зуев",
            "distance": "41.5 km",
            "activities": "5",
            "longest": "13.2 km",
            "avg_pace": "6:22 /km",
            "elev_gain": "161 m",
            "avatar_large": "https://graph.facebook.com/905358666522374/picture?height=256&width=256",
            "avatar_medium": "https://graph.facebook.com/905358666522374/picture?height=256&width=256",
            "link": "https://www.strava.com/athletes/40853149",
        },
        {
            "rank": "7",
            "athlete_name": "Влад Орлов",
            "distance": "36.1 km",
            "activities": "7",
            "longest": "10.2 km",
            "avg_pace": "4:58 /km",
            "elev_gain": "373 m",
            "avatar_large": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/80735219/25672890/6/large.jpg",
            "avatar_medium": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/80735219/25672890/6/medium.jpg",
            "link": "https://www.strava.com/athletes/80735219",
        },
        {
            "rank": "8",
            "athlete_name": "Сергій Ковба",
            "distance": "31.1 km",
            "activities": "3",
            "longest": "11.9 km",
            "avg_pace": "6:55 /km",
            "elev_gain": "126 m",
            "avatar_large": "https://graph.facebook.com/833300830470358/picture?height=256&width=256",
            "avatar_medium": "https://graph.facebook.com/833300830470358/picture?height=256&width=256",
            "link": "https://www.strava.com/athletes/51586074",
        },
        {
            "rank": "9",
            "athlete_name": "Антон Смірнов",
            "distance": "26.1 km",
            "activities": "3",
            "longest": "10.0 km",
            "avg_pace": "6:03 /km",
            "elev_gain": "130 m",
            "avatar_large": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/108602045/28041303/1/large.jpg",
            "avatar_medium": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/108602045/28041303/1/medium.jpg",
            "link": "https://www.strava.com/athletes/108602045",
        },
        {
            "rank": "10",
            "athlete_name": "Valeria Kamenetska",
            "distance": "24.2 km",
            "activities": "2",
            "longest": "13.4 km",
            "avg_pace": "6:14 /km",
            "elev_gain": "226 m",
            "avatar_large": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/49903015/15504169/7/large.jpg",
            "avatar_medium": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/49903015/15504169/7/medium.jpg",
            "link": "https://www.strava.com/athletes/49903015",
        },
        {
            "rank": "11",
            "athlete_name": "Max Shentsov",
            "distance": "24.0 km",
            "activities": "3",
            "longest": "10.0 km",
            "avg_pace": "6:38 /km",
            "elev_gain": "109 m",
            "avatar_large": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/80233755/19308987/4/large.jpg",
            "avatar_medium": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/80233755/19308987/4/medium.jpg",
            "link": "https://www.strava.com/athletes/80233755",
        },
        {
            "rank": "12",
            "athlete_name": "Світлана Лепетуха",
            "distance": "23.7 km",
            "activities": "4",
            "longest": "7.5 km",
            "avg_pace": "6:54 /km",
            "elev_gain": "86 m",
            "avatar_large": "https://graph.facebook.com/455028262425855/picture?height=256&width=256",
            "avatar_medium": "https://graph.facebook.com/455028262425855/picture?height=256&width=256",
            "link": "https://www.strava.com/athletes/81633083",
        },
        {
            "rank": "13",
            "athlete_name": "Anna Opanasiuk",
            "distance": "22.4 km",
            "activities": "4",
            "longest": "5.7 km",
            "avg_pace": "5:46 /km",
            "elev_gain": "124 m",
            "avatar_large": "https://graph.facebook.com/1801927769824166/picture?height=256&width=256",
            "avatar_medium": "https://graph.facebook.com/1801927769824166/picture?height=256&width=256",
            "link": "https://www.strava.com/athletes/22576692",
        },
        {
            "rank": "14",
            "athlete_name": "Руслан Тищенко",
            "distance": "21.2 km",
            "activities": "1",
            "longest": "21.2 km",
            "avg_pace": "5:44 /km",
            "elev_gain": "141 m",
            "avatar_large": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/30094594/9033194/7/large.jpg",
            "avatar_medium": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/30094594/9033194/7/medium.jpg",
            "link": "https://www.strava.com/athletes/30094594",
        },
        {
            "rank": "15",
            "athlete_name": "Nik Nik 🇺🇦",
            "distance": "19.6 km",
            "activities": "3",
            "longest": "7.6 km",
            "avg_pace": "6:45 /km",
            "elev_gain": "131 m",
            "avatar_large": "https://graph.facebook.com/1045986488888084/picture?height=256&width=256",
            "avatar_medium": "https://graph.facebook.com/1045986488888084/picture?height=256&width=256",
            "link": "https://www.strava.com/athletes/31837621",
        },
        {
            "rank": "16",
            "athlete_name": "Сергей Рассоха",
            "distance": "18.1 km",
            "activities": "2",
            "longest": "15.1 km",
            "avg_pace": "5:47 /km",
            "elev_gain": "586 m",
            "avatar_large": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/41702559/25100910/1/large.jpg",
            "avatar_medium": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/41702559/25100910/1/medium.jpg",
            "link": "https://www.strava.com/athletes/41702559",
        },
        {
            "rank": "17",
            "athlete_name": "Яворська Ганна",
            "distance": "16.3 km",
            "activities": "3",
            "longest": "11.1 km",
            "avg_pace": "7:10 /km",
            "elev_gain": "68 m",
            "avatar_large": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/112297311/26443279/2/large.jpg",
            "avatar_medium": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/112297311/26443279/2/medium.jpg",
            "link": "https://www.strava.com/athletes/112297311",
        },
        {
            "rank": "18",
            "athlete_name": "Юра Казанцев",
            "distance": "12.2 km",
            "activities": "1",
            "longest": "12.2 km",
            "avg_pace": "5:21 /km",
            "elev_gain": "--",
            "avatar_large": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/53930445/24670201/4/large.jpg",
            "avatar_medium": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/53930445/24670201/4/medium.jpg",
            "link": "https://www.strava.com/athletes/53930445",
        },
        {
            "rank": "19",
            "athlete_name": "Юлія Степаненко - Моргун",
            "distance": "12.1 km",
            "activities": "1",
            "longest": "12.1 km",
            "avg_pace": "6:44 /km",
            "elev_gain": "44 m",
            "avatar_large": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/107322300/25399139/1/large.jpg",
            "avatar_medium": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/107322300/25399139/1/medium.jpg",
            "link": "https://www.strava.com/athletes/107322300",
        },
        {
            "rank": "20",
            "athlete_name": "Katya Kryvda",
            "distance": "7.0 km",
            "activities": "1",
            "longest": "7.0 km",
            "avg_pace": "6:22 /km",
            "elev_gain": "18 m",
            "avatar_large": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/44278197/15260206/7/large.jpg",
            "avatar_medium": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/44278197/15260206/7/medium.jpg",
            "link": "https://www.strava.com/athletes/44278197",
        },
        {
            "rank": "21",
            "athlete_name": "Real Vlad",
            "distance": "6.5 km",
            "activities": "2",
            "longest": "5.0 km",
            "avg_pace": "8:40 /km",
            "elev_gain": "13 m",
            "avatar_large": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/42172355/13643414/19/large.jpg",
            "avatar_medium": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/42172355/13643414/19/medium.jpg",
            "link": "https://www.strava.com/athletes/42172355",
        },
        {
            "rank": "22",
            "athlete_name": "Vlad Belichenko",
            "distance": "6.2 km",
            "activities": "1",
            "longest": "6.2 km",
            "avg_pace": "6:52 /km",
            "elev_gain": "313 m",
            "avatar_large": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/42079332/12297439/9/large.jpg",
            "avatar_medium": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/42079332/12297439/9/medium.jpg",
            "link": "https://www.strava.com/athletes/42079332",
        },
        {
            "rank": "23",
            "athlete_name": "KostyantyN Horbenko",
            "distance": "6.0 km",
            "activities": "1",
            "longest": "6.0 km",
            "avg_pace": "6:57 /km",
            "elev_gain": "7 m",
            "avatar_large": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/69686953/17150090/6/large.jpg",
            "avatar_medium": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/69686953/17150090/6/medium.jpg",
            "link": "https://www.strava.com/athletes/69686953",
        },
        {
            "rank": "24",
            "athlete_name": "Tan Kolom",
            "distance": "6.0 km",
            "activities": "1",
            "longest": "6.0 km",
            "avg_pace": "5:49 /km",
            "elev_gain": "25 m",
            "avatar_large": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/45614990/23412540/1/large.jpg",
            "avatar_medium": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/45614990/23412540/1/medium.jpg",
            "link": "https://www.strava.com/athletes/45614990",
        },
        {
            "rank": "25",
            "athlete_name": "Serhii Dratovanyi",
            "distance": "5.5 km",
            "activities": "2",
            "longest": "4.6 km",
            "avg_pace": "6:33 /km",
            "elev_gain": "2 m",
            "avatar_large": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/15836860/18022698/1/large.jpg",
            "avatar_medium": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/15836860/18022698/1/medium.jpg",
            "link": "https://www.strava.com/athletes/15836860",
        },
        {
            "rank": "26",
            "athlete_name": "Anastasia Larionty",
            "distance": "5.0 km",
            "activities": "1",
            "longest": "5.0 km",
            "avg_pace": "12:15 /km",
            "elev_gain": "41 m",
            "avatar_large": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/76042302/18421240/5/large.jpg",
            "avatar_medium": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/76042302/18421240/5/medium.jpg",
            "link": "https://www.strava.com/athletes/76042302",
        },
        {
            "rank": "27",
            "athlete_name": "Игорь Макаренко",
            "distance": "3.0 km",
            "activities": "1",
            "longest": "3.0 km",
            "avg_pace": "5:49 /km",
            "elev_gain": "9 m",
            "avatar_large": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/40002244/13288279/4/large.jpg",
            "avatar_medium": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/40002244/13288279/4/medium.jpg",
            "link": "https://www.strava.com/athletes/40002244",
        },
        {
            "rank": "28",
            "athlete_name": "Zhanna Prysiazhna 💙💛",
            "distance": "0.4 km",
            "activities": "1",
            "longest": "0.4 km",
            "avg_pace": "8:34 /km",
            "elev_gain": "--",
            "avatar_large": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/56333138/15436812/6/large.jpg",
            "avatar_medium": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/56333138/15436812/6/medium.jpg",
            "link": "https://www.strava.com/athletes/56333138",
        },
    ]  # Вставьте сюда данные атлетов
    output_filename = "athletes.png"
    athlete_image = AthletesPoster(athletes_data[:1])
    athlete_image.create_head_poster(output_filename)
