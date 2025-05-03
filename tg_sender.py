import os
from datetime import datetime, timedelta
from typing import List, Union

from aiogram import Bot, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile, InputMediaPhoto

import config
from config import format_and_translate_date, bot
from sender.album_sender import PosterAlbumSender


class TelegramSender(PosterAlbumSender):
    """
    Class to send images to Telegram Chat.
    Posteralbumsender descendant that provides methods for preparation and sending
    media groups of images with signatures to the said chat.
    """

    CLUB_ID = config.env.str("CLUB_ID")

    def __init__(self):
        self.bot: Bot = bot
        self.logger = config.logger

    @property
    def get_caption(self) -> str:
        """ Get caption for the first image in the album. """
        strava_club_id = self.CLUB_ID

        # Forming a link to Strava Club
        strava_url = (
            f"<a href='https://www.strava.com/clubs/{strava_club_id}'>StravaClub</a>"
            if strava_club_id
            else "<a href='https://www.strava.com/'>Strava</a>"
        )

        # Translation text
        text = "Підсумок {week}-го тижня бігу ({month}, {year})"
        last_week_date = datetime.now() - timedelta(weeks=1)
        description = config.translate.gettext(text).format(
            **format_and_translate_date(last_week_date)
        )
        tag_month = last_week_date.strftime("%B").lower()

        # Final caption
        caption = (
            f"📊 <b>{description}</b>\n\n"
            f"#{tag_month} | #лідери_тижня | {strava_url}"
        )

        return caption

    async def get_media_group(self) -> List[InputMediaPhoto]:
        """
        Get a list of InputMediaPhoto objects from the IMAGE_PATH directory.
        """
        image_files = sorted(self.get_image_files())
        media_group = []

        for i, image_file in enumerate(image_files):
            # Get the caption for the first image
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
        """Send an album of images to a Telegram chat."""
        self.logger.info("Початок відправки альбому до чату %s...", chat_id)

        try:
            async with self.bot as bot:

                # Send a chat action
                await bot.send_chat_action(
                    chat_id=chat_id, action="upload_photo"
                )

                # Get a list of InputMediaPhoto objects
                media = await self.get_media_group()
                if not media:
                    self.logger.warning("No media to send.")
                    return

                # Send the album
                await bot.send_media_group(chat_id=chat_id, media=media)
                self.logger.info(
                    "Successfully sent album to chat %s", chat_id
                )

        except Exception as e:
            self.logger.error("Error sending album: %s", str(e))
            raise
