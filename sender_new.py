import os
from datetime import datetime, timedelta
from os import path
from pathlib import Path

import aiohttp
from aiogram import Bot, types, Dispatcher
from environs import Env

# Read environment variables
env = Env()
env.read_env()


class PhotoAlbumSender:
    """
    This class is responsible for sending a media group of photos to a bot using the given bot token.
    """

    IMAGE_PATH = path.join(Path(__file__).resolve().parent, "out_posters")

    def __init__(self, bot_token: str):
        self.bot = Bot(bot_token, parse_mode=types.ParseMode.HTML)

    async def get_image_files(self) -> list[str]:
        """Get a list the files in the IMAGE_PATH directory."""

        allowed_extensions = (".jpg", ".jpeg", ".png", ".gif")

        image_files = [
            file
            for file in os.listdir(self.IMAGE_PATH)
            if file.lower().endswith(allowed_extensions)
        ]

        return image_files

    @property
    def get_caption(self):
        strava_club_id = env.str("CHAT_ID")

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

    async def send_album_to_telegram(self, chat_id):
        """Send an album of images to a Telegram chat."""

        image_files = await self.get_image_files()
        media_group = types.MediaGroup()

        for num, image_file in enumerate(image_files):
            image_input = types.InputFile(
                path.join(self.IMAGE_PATH, image_file)
            )
            caption = self.get_caption if not num else None

            media_group.attach_photo(
                types.InputMediaPhoto(
                    media=image_input,
                    caption=caption,
                    parse_mode=types.ParseMode.HTML,
                )
            )

        await self.bot.send_media_group(chat_id=chat_id, media=media_group)


async def main():
    sender = PhotoAlbumSender(bot_token=env.str("BOT_TOKEN"))
    await sender.send_album_to_telegram(env.str("CHAT_ID"))


if __name__ == "__main__":
    import asyncio

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
