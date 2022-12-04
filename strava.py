"""Connection, authorization, parsing to Strava Club"""

import os
import pickle
import time
from pathlib import Path
import logging

# Selenium modules
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# Chrome driver manager
from webdriver_manager.chrome import ChromeDriverManager

from fake_useragent import UserAgent

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
    """
    _BASE_DIR = Path(__file__).resolve().parent
    _CLUB_URL = "https://www.strava.com/clubs/"
    __chromedriver = ChromeDriverManager().install()

    def __init__(self, club_id: int, email: str, password: str):
        self.password = password
        self.email = email
        self.club_id = club_id
        self.logging = logging.getLogger(__name__)
        self.options = Options()  # Options webdriver
        # self.options.add_argument("--headless")  # running in the background
        self.options.add_argument("--no-sandbox")  # Disable sandbox
        self.options.add_argument(
            "--disable-blink-features=AutomationControlled")  # To not detected
        self.options.add_argument(f"userAgent={UserAgent().random}")
        self.browser = Chrome(
            service=Service(self.__chromedriver),
            options=self.options)  # Create a driver object

    @property
    def _authorization(self) -> bool:
        """Authorization on site.
        :return: True if authorization is successful
        """
        try:
            self.browser.get("https://www.strava.com/login")
            self.browser.find_element(By.CLASS_NAME,
                                      "btn-accept-cookie-banner").click()
            # Cookies are found
            if os.path.isfile(os.path.join(
                    self._BASE_DIR,
                    f"cookies/{self.email.split('@')[0]}")):
                self.logging.info("Cookie file found. Try authorization.")
                # Open the cookie and use it for authorization
                with open(os.path.join(self._BASE_DIR,
                                       f"cookies/{self.email.split('@')[0]}"),
                          "rb") as cookie:
                    for row in pickle.load(cookie):
                        self.browser.add_cookie(row)
                # Require update so that cookies are applied
                self.browser.refresh()

                # Check valid or delete file
                if "Log In" in self.browser.title:
                    self.logging.error("Invalid cookies. Delete cookies")
                    os.remove(
                        os.path.join(self._BASE_DIR,
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
                with open(os.path.join(
                        self._BASE_DIR, f"cookies/{self.email.split('@')[0]}"),
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
                self.browser.get(self._CLUB_URL + str(self.club_id))
                # time.sleep(1)
                # Click on the button to show the leaderboard of the last week
                self.browser.find_element(By.CLASS_NAME, "last-week").click()
                self.logging.info("Go to last week's leaderboard")
                # time.sleep(1)
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
                    "has been generated %s athletes", len(last_week_leaders))

                return last_week_leaders
            except TimeoutException as error:
                self.logging.error(error)
            finally:
                self.browser.close()
                self.browser.quit()
        raise AuthorizationFailureException("Authorization failed")


if __name__ == '__main__':
    s = Strava(582642, "login@gmail.com", "******")
    print(s.get_last_week_leaders())
