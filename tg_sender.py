import os
from datetime import datetime, timedelta

from aiogram import types, Bot

import config
from config import format_and_translate_date
from sender.album_sender import PosterAlbumSender


class TelegramSender(PosterAlbumSender):
    """
    A class for sending an album of images to a Telegram chat.

    This class inherits from PosterAlbumSender and provides methods to prepare and send a media group
    of images with captions to a specified Telegram chat.
    """

    def __init__(self, bot_token: str):
        self.logger = config.logger
        self.bot = Bot(bot_token, parse_mode=types.ParseMode.HTML)

    @property
    def get_caption(self) -> str:
        strava_club_id = self.CLUB_ID

        strava_url = (
            f"<a href='https://www.strava.com/clubs/{strava_club_id}'>StravaClub</a>"
            if strava_club_id
            else "<a href='https://www.strava.com/'>Strava</a>"
        )

        text = "Summary of {week}-th running week ({month}, {year})"
        last_week_date = datetime.now() - timedelta(weeks=1)
        description = config.translate.gettext(text).format(
            **format_and_translate_date(last_week_date)
        )
        tag_month = last_week_date.strftime("%B").lower()

        caption = (
            f"📊 <b>{description}</b>\n\n"
            f"#{tag_month} | #leaders_last_week | {strava_url}"
        )

        return caption

    async def get_media_group(self) -> types.MediaGroup:
        """
        Creates and returns a MediaGroup object based on images located in the specified folder.
        """
        image_files = sorted(self.get_image_files())
        media_group = types.MediaGroup()

        for num, image_file in enumerate(image_files):
            image_input = types.InputFile(
                os.path.join(self.IMAGE_PATH, image_file)
            )
            caption = self.get_caption if not num else None

            media_group.attach_photo(
                types.InputMediaPhoto(
                    media=image_input,
                    caption=caption,
                    parse_mode=types.ParseMode.HTML,
                )
            )

        return media_group

    async def send_album_to_telegram(self, chat_id):
        """Send an album of images to a Telegram chat."""
        self.logger.info("Sending to Telegram channel %s ...", chat_id)
        session = await self.bot.get_session()
        await self.bot.send_chat_action(
            chat_id=chat_id, action=types.ChatActions.UPLOAD_PHOTO
        )
        media = await self.get_media_group()
        await self.bot.send_media_group(chat_id=chat_id, media=media)
        await session.close()
        self.logger.info("Album have been sent successfully.")
