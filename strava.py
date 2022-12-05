"""Connection, authorization, parsing to Strava Club"""

import pickle
import time
from pathlib import Path
import logging
from os import path, remove

# Selenium modules
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# Chrome driver manager
from webdriver_manager.chrome import ChromeDriverManager

from fake_useragent import UserAgent
import poster

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


class AuthorizationFailureException(Exception):
    """Exception raised when authorization fails"""


class Strava:  # pylint: disable=too-few-public-methods
    """Connection operations and capabilities
    Attributes:
        club_id (int): Club ID
        email (str): Login
        password (str): Password
    Methods:
        _authorization -> True if authorization is successful:
        get_last_week_leaders() -> List of last week leaders club:
    """
    _BASE_DIR = Path(__file__).resolve().parent
    _BASE_URL = "https://www.strava.com/"
    __chromedriver = ChromeDriverManager().install()

    def __init__(self, club_id: int, email: str, password: str):
        self.password = password
        self.email = email
        self.club_id = club_id
        self.logging = logging.getLogger(__name__)
        self.service = Service(self.__chromedriver)  # Service webdriver
        self.options = Options()  # Options webdriver
        self.options.add_argument("--headless")  # Running in the background
        self.options.add_argument("--no-sandbox")  # Disable sandbox
        self.options.add_argument(
            "--disable-blink-features=AutomationControlled")  # To not detected
        self.options.add_argument(f"userAgent={UserAgent().random}")
        self.browser = Chrome(service=self.service, options=self.options)

    @property
    def _authorization(self) -> bool:
        """Authorization on site.
        :return: True if authorization is successful
        """
        try:
            self.browser.get(self._BASE_URL + "login")
            self.browser.find_element(By.CLASS_NAME,
                                      "btn-accept-cookie-banner").click()
            # Cookies are found
            if path.isfile(path.join(self._BASE_DIR,
                                     f"cookies/{self.email.split('@')[0]}")):
                self.logging.info("Cookie file found. Try authorization.")
                # Open the cookie and use it for authorization
                with open(path.join(self._BASE_DIR,
                                    f"cookies/{self.email.split('@')[0]}"),
                          "rb") as cookie:
                    for row in pickle.load(cookie):
                        self.browser.add_cookie(row)
                # Require update so that cookies are applied
                self.browser.refresh()

                # Check valid or delete file
                if "Log In" in self.browser.title:
                    self.logging.error("Invalid cookies. Delete cookies")
                    remove(
                        path.join(self._BASE_DIR,
                                  f"cookies/{self.email.split('@')[0]}"))
                else:
                    self.logging.info("Authorization successful!")
                    return True

            # Logging
            self.logging.info("Login page opened.")

            # Enter email
            email_input = self.browser.find_element(By.ID, "email")
            email_input.clear()
            email_input.send_keys(self.email)

            # Enter password
            password_input = self.browser.find_element(By.ID, "password")
            password_input.clear()
            password_input.send_keys(self.password)

            # Click on the email button
            self.browser.find_element(By.ID, "login-button").click()

            if "Log In" not in self.browser.title:
                self.logging.info("Authorization successful!")
                # Get cookies and save to a file
                with open(path.join(self._BASE_DIR,
                                    f"cookies/{self.email.split('@')[0]}"),
                          "wb") as cookie:
                    pickle.dump(self.browser.get_cookies(), cookie)
                    self.logging.info("Cookie file is saved.")
                return True

            self.logging.error(
                self.browser.find_element(By.CLASS_NAME, "alert-message").text)
        except TimeoutException as error:
            self.logging.error(error)
        self.browser.close()
        self.browser.quit()
        return False

    def get_last_week_leaders(self) -> list:
        """Get the last week leaders.
        :return: List of dicts last week leaders
        """
        if self._authorization:
            try:
                self.browser.get(self._BASE_URL + "clubs/" + str(self.club_id))
                time.sleep(0.5)
                # Click on the button to show the leaderboard of the last week
                self.browser.find_element(By.CLASS_NAME, "last-week").click()
                self.logging.info("Go to last week's leaderboard")
                time.sleep(0.5)
                last_week_leaders = []
                lst = []

                table = self.browser.find_element(By.CLASS_NAME, 'dense')
                tr_contents = table.find_elements(By.TAG_NAME, 'tr')

                for num, trow in enumerate(tr_contents[1:]):
                    athlete_url = trow.find_element(
                        By.TAG_NAME, "a").get_attribute("href").strip()
                    avatar_medium = trow.find_element(
                        By.TAG_NAME, "img").get_attribute("src").strip()
                    avatar_large = trow.find_element(
                        By.TAG_NAME, "img"
                    ).get_attribute("src").strip().replace("medium", "large")

                    # Iterate to find 'td' under each 'tr'
                    for tdata in trow.find_elements(By.TAG_NAME, 'td'):
                        # Store the content of each td in lst
                        lst.append(tdata.text)

                    # List of dict with the athlete's data from the table.
                    last_week_leaders.append(dict(zip(
                        ['rank', 'athlete_name', 'distance', 'activities',
                         'longest', 'avg_pace', 'elev_gain'], lst)))

                    last_week_leaders[num]['avatar_large'] = avatar_large
                    last_week_leaders[num]['avatar_medium'] = avatar_medium
                    last_week_leaders[num]['link'] = athlete_url
                    lst = []

                self.logging.info(
                    "A list of dictionaries with athlete data from the table"
                    "has been generated %s athletes of the club %s",
                    len(last_week_leaders), self.get_info_club['name'])

                return last_week_leaders
            except TimeoutException as error:
                self.logging.error(error)
        raise AuthorizationFailureException("Authorization failed")

    @property
    def get_info_club(self) -> dict | None:
        """Get the name of the club.
        :return: Club's name
        """
        url_club = self._BASE_URL + "clubs/" + str(self.club_id)
        try:
            self.browser.get(url_club)
            sport = self.browser.find_element(
                By.CLASS_NAME, "location").find_element(
                By.TAG_NAME, "span").text.strip()
            location = self.browser.find_element(
                By.CLASS_NAME, "location").text.replace(sport, "").strip()
            site = self.browser.find_element(
                By.CLASS_NAME, "text-footnote").text.strip()
            description = self.browser.find_element(
                By.CLASS_NAME, "club-description").text.strip()
            try:
                status = self.browser.find_element(
                    By.CLASS_NAME, "spans11").find_element(
                    By.TAG_NAME, "h1").find_element(
                    By.TAG_NAME, "span").text.strip()
                club_name = self.browser.find_element(
                    By.CLASS_NAME, "spans11").find_element(
                    By.TAG_NAME, "h1").text.replace(status, "").strip()
            except NoSuchElementException:
                club_name = self.browser.find_element(
                    By.CLASS_NAME, "spans11").find_element(
                    By.TAG_NAME, "h1").text.strip()
            return dict(
                name=club_name,
                sport=sport,
                location=location,
                description=description,
                site=site,
                url_club=url_club)
        except TimeoutException as error:
            self.logging.error(error)
        finally:
            self.browser.close()
            self.browser.quit()
        return None


if __name__ == '__main__':
    s = Strava(582642, "sergbondckua@gmail.com", "Q10101010")  # 582642
    d = poster.Poster(s.get_last_week_leaders())
    d.create_poster()
