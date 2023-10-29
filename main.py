import asyncio

import config
from create_poster import PosterAthletes, PosterSaver
from parsing import Strava
from sender_new import TelegramSender


async def main():
    """Main function"""

    with Strava(
        email=config.env.str("EMAIL"), password=config.env.str("PASSWD")
    ) as strava:
        athletes_rank = strava.get_this_week_or_last_week_leaders(
            config.env.int("CLUB_ID"),
            last_week=True,
        )

    async with PosterAthletes() as pa:
        top_10 = athletes_rank[:10]
        remainder = athletes_rank[10:40]
        tag = len(remainder) - (len(remainder) % 15)
        groups = [top_10] + [remainder[i : i + 15] for i in range(0, tag, 15)]
        poster_saver = PosterSaver()
        await poster_saver.clear_output_folder()

        for num, group in enumerate(groups):
            head_icons = num == 0
            filename = f"out{num + 1}.png"
            poster = await pa.generate_poster(group, head_icons)
            await poster_saver.save_poster(poster, filename)

    # Sending posters via Telegram
    send = TelegramSender(bot_token=config.env.str("BOT_TOKEN"))
    await send.send_album_to_telegram(config.env.int("CHAT_ID"))


if __name__ == "__main__":
    asyncio.run(main())
