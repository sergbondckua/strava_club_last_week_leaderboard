import asyncio
from datetime import datetime, timedelta

import config
from parse import StravaLeaderboardRetriever
from poster import PosterAthletesCollector
from poster_maker.creator import AthleteRankPosterGenerator
from tg_sender import TelegramSender


async def get_season_config(poster_generator: AthleteRankPosterGenerator):
    """Set season-specific configurations for the poster generator."""

    month: int = (datetime.now() - timedelta(weeks=1)).month

    background_dir = (
        config.BASE_DIR / "poster_maker/resources/images/poster_bgrnd"
    )
    background_images = {
        "winter": "winter.jpg",
        "spring": "spring.jpg",
        "summer": "summer.jpg",
        "autumn": "autumn.jpg",
        "other": "other.jpg",
        "other_winter": "other_winter.jpg",
    }

    # Dictionary with information about seasons and corresponding settings
    season_configs = {
        (1, 2, 12): (
            "winter",
            "other_winter",
            ((263, 43), (130, 123), (400, 123)),
        ),
        (3, 4, 5): ("spring", "other", ((253, 105), (80, 112), (425, 112))),
        (6, 7, 8): ("summer", "other", ((265, 40), (130, 123), (400, 123))),
        (9, 10, 11): ("autumn", "other", ((263, 98), (85, 60), (450, 65))),
    }

    # Determining the season based on the current month
    for months, settings in season_configs.items():
        if month in months:
            poster_generator.BACKGROUND_IMAGE_PATH = (
                background_dir / background_images[settings[0]]
            )
            poster_generator.BACKGROUND_2_IMAGE_PATH = (
                background_dir / background_images[settings[1]]
            )
            poster_generator.AVATARS_TOP3_POSITIONS = settings[2]
            break


async def main():
    """Main function"""

    # Get Athletes data
    strava = StravaLeaderboardRetriever(
        config.env.str("EMAIL"),
        config.env.str("PASSWD"),
        config.env.int("CLUB_ID"),
    )
    athletes_rank = strava.retrieve_leaderboard_data()

    # Check if data was retrieved
    if athletes_rank is None:
        config.logger.error("Failed to retrieve leaderboard data")
        return

    # Generate and save posters
    poster = PosterAthletesCollector(athletes_rank)

    # Apply settings according to the seasons
    await get_season_config(poster.poster_generator)
    await poster.create_and_save_posters()

    # Sending posters via Telegram
    send = TelegramSender(bot_token=config.env.str("BOT_TOKEN"))
    await send.send_album_to_telegram(config.env.int("CHAT_ID"))


if __name__ == "__main__":
    asyncio.run(main())
