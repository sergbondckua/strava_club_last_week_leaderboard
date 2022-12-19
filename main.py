"""Start Starava club rate"""
import os

from strava import Strava
from poster import Poster
from sender import SenderTelegram


def main():
    """Main function"""
    my_strava = Strava(email=os.getenv("LOGIN"), password=os.getenv("PASSWD"))
    rank_in_club = my_strava.get_last_week_leaders(club_id=582642)
    Poster(rank_in_club).create_poster()
    send = SenderTelegram(token_bot=os.getenv("TOKEN_BOT"))
    send.telegram_send(os.getenv("CHAT_ID"),
                       language="ukr",
                       strava_club_id=582642)


if __name__ == '__main__':
    main()
