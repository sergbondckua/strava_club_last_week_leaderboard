"""Sender Telegram to channel/chat"""
import json
import locale
import logging
from os import path
from datetime import datetime, timedelta
from pathlib import Path

import telegram

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


class SenderTelegram:
    """ Send posters on the Telegram channel/chat
    Args:
        :token: The token your Telegram Bot
    Methods:
        :telegram_send: Send to Telegram
    """
    _BASE_DIR = Path(__file__).resolve().parent

    def __init__(self, token_bot: str):
        self.logging = logging.getLogger(__name__)
        self.bot = telegram.Bot(token=token_bot)

    def telegram_send(self, chat_id: str, language=None, strava_club_id=None):
        """Send messages to Telegram
        Args:
            :chat_id: The Telegram chat ID or channel to send
            :language: The language you your chat
            :strava_club_id: The Strava club ID
        """
        self.logging.info("Sending to Telegram channel...")
        # Activity: Typing text
        self.bot.sendChatAction(chat_id=chat_id, action="typing")
        if strava_club_id:
            url = f"<a href='https://www.strava.com/clubs/" \
                  f"{str(strava_club_id)}'>StravaClub</a>"
        else:
            url = "<a href='https://www.strava.com/'>Strava</a>"
        description = (datetime.now() - timedelta(weeks=1)).strftime(
            "Summary of %W-th running week (%B, %Y)")
        if language:
            try:
                with open(path.join(
                        self._BASE_DIR, "resources/lang/package.json"),
                        mode="r",
                        encoding="utf-8") as file:
                    data = json.load(file)
                if lang := data.get(language):
                    locale.setlocale(locale.LC_ALL, lang["name_locale"])
                    description = (
                            datetime.now() - timedelta(weeks=1)).strftime(
                        lang["description"])
            except FileNotFoundError as error:
                self.logging.error(error)
        tag_month = (datetime.now() - timedelta(weeks=1)).strftime("%B")
        media_group = []
        for num in range(1, 3):
            with open(
                    path.join(self._BASE_DIR, f"out_posters/out{num}.png"),
                    "rb") as poster:
                media_group.append(telegram.InputMediaPhoto(
                    poster,
                    parse_mode="html",
                    caption=f"📊 <b>{description}</b>\n\n"
                            f"#{tag_month.lower()} | "
                            f"#leaders_last_week | "
                            f"{url}"
                    if num == 1 else ""
                ))
        self.bot.sendMediaGroup(chat_id=chat_id, media=media_group)
        self.logging.info("Posters have been sent successfully.")
