"""Data Parser in Strava Club"""

import pickle
import logging
import time
from os import path, remove
from pathlib import Path
from pprint import pprint

import requests
# Selenium modules
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Chrome driver manager
from webdriver_manager.chrome import ChromeDriverManager

# Custom modules

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO)


class NotClosedException(Exception):
    """Unsuccessful attempt to close the browser"""


class AuthorizationFailureException(Exception):
    """Exception raised when authorization fails"""


class Strava:
    """Connection operations and capabilities
    Attributes:
        :email (str): Login
        :password (str): Password
    Methods:

    """
    _BASE_DIR = Path(__file__).resolve().parent
    _BASE_URL = "https://www.strava.com/"

    def __init__(self, email: str = None, password: str = None):
        self.logging = logging.getLogger(__name__)
        self.password = password
        self.email = email
        self.chromedriver = ChromeDriverManager().install()
        self.browser = self.start_driver()

    def __enter__(self):
        self.start_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.browser.close()
            self.logging.info("Browser closed")
        except NotClosedException as error:
            self.logging.error("Error closing the web browser: %s", error)

    def start_driver(self):
        """Start Chrome webdriver"""
        option_arguments = [
            # "--headless",  # Start Chrome in background mode
            "--hide-scrollbars",
            "start-maximized",  # Opens Chrome in maximize mode
            "--no-sandbox",  # Disable sandbox
            "--disable-blink-features=AutomationControlled",  # To not detected
            "disable-popup-blocking",  # Disables pop-ups displayed on Chrome
        ]
        service = Service(self.chromedriver)  # Service webdriver
        options = Options()  # Options webdriver
        options.add_experimental_option(
            "excludeSwitches", ['enable-automation'])  # Disable info bar
        for argument in option_arguments:
            options.add_argument(argument)
        driver = Chrome(service=service, options=options)
        return driver

    def get_this_week_leaders(self, club_id) -> list:
        """Get the current week leaders"""
        self.open_page_club(club_id)
        if self.email and path.isfile(path.join(
                self._BASE_DIR, f"cookies/{self.email.split('@')[0]}")):
            self.logging.info("Cookie file found. Try authorization.")
            self.read_cookie()
            if not self.check_apply_cookie():
                self.remove_cookie()
        elif self.email and self.password:
            self.click_login_button()
            self.authorization(self.email, self.password)
        return self.get_data_leaderboard()

    def get_last_week_leaders(self, club_id: int) -> list:
        """Get the leaders of a club last week."""
        self.open_page_club(club_id)
        if self.email and path.isfile(path.join(
                self._BASE_DIR, f"cookies/{self.email.split('@')[0]}")):
            self.logging.info("Cookie file found. Try authorization.")
            self.read_cookie()
            if not self.check_apply_cookie():
                self.remove_cookie()
        elif self.email and self.password:
            self.click_login_button()
            self.authorization(self.email, self.password)
        self.click_last_week_button()
        return self.get_data_leaderboard()

    def open_page_club(self, club_id: int):
        """Open browser and go to url"""
        self.browser.get(self._BASE_URL + "clubs/" + str(club_id))
        self.logging.info("Open page club URL: %s", self.browser.current_url)

    def wait_element(self, by_element: tuple, timeout: int = 10) -> WebElement:
        """Wait for the element"""
        wait = WebDriverWait(self.browser, timeout)
        try:
            element = wait.until(ec.visibility_of_element_located(by_element))
            return element
        except TimeoutException as ex:
            raise TimeoutException("Not found element") from ex

    def click_last_week_button(self):
        """Click last week button on table"""
        self.wait_element((By.CLASS_NAME, "last-week")).click()
        self.logging.info("Go to last week's leaderboard")

    def click_login_button(self):
        """Click login button on login page"""
        self.wait_element((By.CLASS_NAME, "btn-login")).click()
        self.logging.info("Open page Login URL: %s", self.browser.current_url)

    def click_submit_login(self):
        """Click Login button submit"""
        self.wait_element((By.ID, "login-button")).click()

    def get_data_leaderboard(self) -> list:
        """Get data leaderboard"""
        leaderboard = []
        table = self.wait_element((By.CLASS_NAME, 'dense'))
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
            lst = [td.text for td in trow.find_elements(By.TAG_NAME, 'td')]

            # List of dict with the athlete's data from the table.
            leaderboard.append(dict(zip(
                ['rank', 'athlete_name', 'distance', 'activities',
                 'longest', 'avg_pace', 'elev_gain'], lst)))

            leaderboard[num]['avatar_large'] = avatar_large
            leaderboard[num]['avatar_medium'] = avatar_medium
            leaderboard[num]['link'] = athlete_url

        self.logging.info(
            "A list of dictionaries with athlete data from the table"
            "has been generated %s athletes of the club",
            len(leaderboard))
        return leaderboard

    def authorization(self, username: str, password: str):
        """Sign in to the Strava"""
        self.input_email(username)
        self.input_password(password)
        self.click_submit_login()
        if self.check_alert_msg():
            raise AuthorizationFailureException(
                "The username or password did not match.")
        self.logging.info("Authorization successful.")
        self.save_cookie()

    def open_sign_in_page(self):
        """Open browser and go to url"""
        self.browser.get(self._BASE_URL + "login")
        self.logging.info("Open page Login URL: %s", self.browser.current_url)

    def input_email(self, email: str):
        """Input email address"""
        field = self.wait_element((By.ID, "email"))
        field.clear()
        field.send_keys(email)

    def input_password(self, password: str):
        """Input password"""
        field = self.wait_element((By.ID, "password"))
        field.clear()
        field.send_keys(password)

    def check_alert_msg(self) -> bool:
        """Check if the alert"""
        wait = WebDriverWait(self.browser, 0)
        try:
            wait.until(ec.visibility_of_element_located(
                (By.CLASS_NAME, "alert-message")))
        except (TimeoutException, NoSuchElementException):
            return False
        return True

    def check_apply_cookie(self) -> bool:
        """Check if a cookie has been applied"""
        try:
            WebDriverWait(self.browser, timeout=1).until_not(ec.visibility_of_element_located((
                By.CLASS_NAME, "btn-login")))
        except (NoSuchElementException, TimeoutException):
            self.logging.warning("Authorization failed.")
        return True

    def save_cookie(self):
        """Get cookies and save to a file"""
        with open(path.join(self._BASE_DIR,
                            f"cookies/{self.email.split('@')[0]}"),
                  "wb") as cookie:
            pickle.dump(self.browser.get_cookies(), cookie)
            self.logging.info("Cookie file is saved.")

    def read_cookie(self):
        """Open the cookie and use it for authorization"""
        with open(path.join(self._BASE_DIR,
                            f"cookies/{self.email.split('@')[0]}"),
                  "rb") as cookie:
            for row in pickle.load(cookie):
                self.browser.add_cookie(row)
        # Require update so that cookies are applied
        self.browser.refresh()

    def remove_cookie(self):
        """Delete invalid cookie"""
        self.logging.warning("Invalid cookies. Delete cookies. Try again.")
        remove(
            path.join(self._BASE_DIR,
                      f"cookies/{self.email.split('@')[0]}"))
        raise ValueError("Invalid cookies. You need username and password.")


class InfoStravaClub:
    """Get information about the Strava Club"""
    auth_url = "https://www.strava.com/oauth/token"

    def __init__(self, club_id):
        self.club_id = club_id
        self.club_url = "https://www.strava.com/api/v3/clubs/" + \
                        str(self.club_id)
        self.headers = dict(Authorization="Bearer " + self.access_token)
        self.params = dict(per_page=200, page=1)

    @property
    def access_token(self):
        """Get access token"""
        payload = {
            'client_id': "***",
            'client_secret': "***",
            'refresh_token': "***",
            'grant_type': "refresh_token",
            'f': 'json'
        }
        res = requests.post(self.auth_url, data=payload, timeout=5)
        access_token = res.json()["access_token"]
        return access_token

    @property
    def get_club_info(self):
        """Get club info"""
        response = requests.get(self.club_url, headers=self.headers, timeout=5)
        return response.json()


if __name__ == "__main__":
    with Strava(email="qqq@gmail.com", password="***") as strava:
        t = strava.get_this_week_leaders(582642)
        # l = strava.get_last_week_leaders(582642)
        print(t)
    # s = InfoStravaClub(582642).get_club_info
    # pprint(s)
