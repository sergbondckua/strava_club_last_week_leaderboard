import os
from datetime import datetime, timedelta
from typing import List, Union

from aiogram import Bot, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile, InputMediaPhoto

import config
from config import format_and_translate_date
from sender.album_sender import PosterAlbumSender


class TelegramSender(PosterAlbumSender):
    """
    Клас для відправки альбому зображень у Telegram чат.
    Нащадок PosterAlbumSender, що надає методи для підготовки та відправки
    медіа-групи зображень із підписами до вказаного чату.
    """

    CLUB_ID = config.env.str("CLUB_ID")

    def __init__(self, bot_token: str):
        """Ініціалізація з бот-токеном"""
        self.bot = Bot(
            token=bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        self.logger = config.logger

    @property
    def get_caption(self) -> str:
        """Генерує підпис для альбому"""
        strava_club_id = self.CLUB_ID

        # Формування посилання на Strava клуб
        strava_url = (
            f"<a href='https://www.strava.com/clubs/{strava_club_id}'>StravaClub</a>"
            if strava_club_id
            else "<a href='https://www.strava.com/'>Strava</a>"
        )

        # Текст з перекладом
        text = "Підсумок {week}-го тижня бігу ({month}, {year})"
        last_week_date = datetime.now() - timedelta(weeks=1)
        description = config.translate.gettext(text).format(
            **format_and_translate_date(last_week_date)
        )
        tag_month = last_week_date.strftime("%B").lower()

        # Фінальний підпис
        caption = (
            f"📊 <b>{description}</b>\n\n"
            f"#{tag_month} | #лідери_тижня | {strava_url}"
        )

        return caption

    async def get_media_group(self) -> List[InputMediaPhoto]:
        """
        Створює та повертає список InputMediaPhoto для медіа-групи.
        """
        image_files = sorted(self.get_image_files())
        media_group = []

        for i, image_file in enumerate(image_files):
            # Тільки перше зображення матиме підпис
            caption = self.get_caption if i == 0 else None

            media_group.append(
                InputMediaPhoto(
                    media=FSInputFile(
                        os.path.join(self.IMAGE_PATH, image_file)
                    ),
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                )
            )

        return media_group

    async def send_album_to_telegram(self, chat_id: Union[int, str]) -> None:
        """Надсилає альбом зображень у Telegram чат."""
        self.logger.info("Початок відправки альбому до чату %s...", chat_id)

        try:
            async with self.bot as bot:

                # Показати статус завантаження
                await bot.send_chat_action(
                    chat_id=chat_id, action="upload_photo"
                )

                # Надіслати альбом
                media = await self.get_media_group()
                if not media:
                    self.logger.warning("Не знайдено зображень для відправки")
                    return

                await bot.send_media_group(chat_id=chat_id, media=media)
                self.logger.info(
                    "Альбом успішно надіслано до чату %s", chat_id
                )

        except Exception as e:
            self.logger.error("Помилка при відправці альбому: %s", str(e))
            raise
