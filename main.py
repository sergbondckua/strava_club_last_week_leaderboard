import asyncio

import config
from parse import StravaLeaderboardRetriever
from poster import PosterAthletesCollector
from tg_sender import TelegramSender


async def main():
    """Main function"""

    # Get Athletes data
    strava = StravaLeaderboardRetriever(
        config.env.str("EMAIL"),
        config.env.str("PASSWD"),
        config.env.int("CLUB_ID"),
    )
    athletes_rank = strava.retrieve_leaderboard_data()

    # Generate and save posters
    poster = PosterAthletesCollector(athletes_rank)
    await poster.create_and_save_posters()

    # Sending posters via Telegram
    send = TelegramSender(bot_token=config.env.str("BOT_TOKEN"))
    await send.send_album_to_telegram(config.env.int("CHAT_ID"))


if __name__ == "__main__":
    asyncio.run(main())
