import asyncio

from environs import Env

from create_poster import PosterAthletes, PosterSaver
from parsing import Strava


# from sender import SenderTelegram

# Read environment variables
env = Env()
env.read_env()


async def main():
    """Main function"""

    with Strava(email=env.str("EMAIL"), password=env.str("PASSWD")) as strava:
        athletes_rank = strava.get_this_week_or_last_week_leaders(
            env.int("CLUB_ID"),
            last_week=True,
        )

    async with PosterAthletes() as pa:
        top_10 = athletes_rank[:10]
        remainder = athletes_rank[10:25]
        tag = len(remainder) - (len(remainder) % 15)
        groups = [top_10] + [remainder[i : i + 15] for i in range(0, tag, 15)]
        poster_saver = PosterSaver()
        await poster_saver.clear_output_folder()

        for num, group in enumerate(groups):
            head_icons = num == 0
            filename = f"out{num + 1}.png"
            poster = await pa.generate_poster(group, head_icons)
            await poster_saver.save_poster(poster, filename)

    # # Sending posters via Telegram
    # send = SenderTelegram(token_bot=os.getenv("TOKEN_BOT"))
    # send.telegram_send(
    #     os.getenv("CHAT_ID"), language="en", strava_club_id=1028327
    # )


if __name__ == "__main__":
    asyncio.run(main())
