from environs import Env

from parsing import Strava
# from poster import Poster
# from sender import SenderTelegram

# Read environment variables
env = Env()
env.read_env()


def main():
    """Main function"""

    with Strava(email=env.str("EMAIL"), password=env.str("PASSWD")) as strava:
        rank_in_club = strava.get_this_week_or_last_week_leaders(
            env.int("CLUB_ID"),
            False,
        )
        print(rank_in_club)

    # # Create posters of leaders
    # Poster(rank_in_club).create_poster()
    # # Sending posters via Telegram
    # send = SenderTelegram(token_bot=os.getenv("TOKEN_BOT"))
    # send.telegram_send(
    #     os.getenv("CHAT_ID"), language="en", strava_club_id=1028327
    # )


if __name__ == "__main__":
    main()
