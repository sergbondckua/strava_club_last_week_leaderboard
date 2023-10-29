import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

from aiogram import Bot, types
from environs import Env

# Read environment variables
env = Env()
env.read_env()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


class PosterAlbumSender:
    """
    This class is responsible for sending a media group of photos to a bot.
    """

    IMAGE_PATH = os.path.join(Path(__file__).resolve().parent, "out_posters")
    CLUB_ID = env.str("CLUB_ID")

    def __init__(self, bot_token: str):
        self.logger = logging.getLogger(__name__)
        self.bot = Bot(bot_token, parse_mode=types.ParseMode.HTML)

    def get_image_files(self) -> list[str]:
        """Get a list the files in the IMAGE_PATH directory."""

        allowed_extensions = (".jpg", ".jpeg", ".png", ".gif")
        image_files = [
            file
            for file in os.listdir(self.IMAGE_PATH)
            if file.lower().endswith(allowed_extensions)
        ]

        return image_files

    @property
    def get_caption(self) -> str:
        strava_club_id = self.CLUB_ID

        strava_url = (
            f"<a href='https://www.strava.com/clubs/{strava_club_id}'>StravaClub</a>"
            if strava_club_id
            else "<a href='https://www.strava.com/'>Strava</a>"
        )

        last_week_date = datetime.now() - timedelta(weeks=1)
        description = last_week_date.strftime(
            "Summary of %W-th running week (%B, %Y)"
        )
        tag_month = last_week_date.strftime("%B").lower()

        caption = (
            f"📊 <b>{description}</b>\n\n"
            f"#{tag_month} | #leaders_last_week | {strava_url}"
        )

        return caption

    def get_media_group(self) -> types.MediaGroup:
        """
        Creates and returns a MediaGroup object based on images located in the specified folder.
        """

        image_files = self.get_image_files()
        media_group = types.MediaGroup()

        for num, image_file in enumerate(image_files):
            print(image_file)
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

        self.logger.info("Sending to Telegram channel %s...", chat_id)
        await self.bot.send_chat_action(
            chat_id=chat_id, action=types.ChatActions.UPLOAD_PHOTO
        )
        media = self.get_media_group()
        await self.bot.send_media_group(chat_id=chat_id, media=media)
        self.logger.info("Album have been sent successfully.")


async def main():
    sender = PosterAlbumSender(bot_token=env.str("BOT_TOKEN"))
    await sender.send_album_to_telegram(env.str("CHAT_ID"))


if __name__ == "__main__":
    import asyncio

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
