import asyncio
import os
import pickle
from os import path, remove
from pathlib import Path
import requests

# Selenium modules
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
)

import config


class NotClosedException(Exception):
    """Unsuccessful attempt to close the browser"""


class AuthorizationFailureException(Exception):
    """Exception raised when authorization fails"""


class Strava:
    """Class to interact with Strava"""

    BASE_DIR = Path(__file__).resolve().parent
    BASE_URL = "https://www.strava.com/"

    def __init__(self, email=None, password=None):
        self.email = email
        self.password = password
        self.logger = config.logger
        self.options = self._configure_driver_options()
        self.service = webdriver.ChromeService()
        self.browser = None

    @staticmethod
    def _configure_driver_options():
        """Configure ChromeOptions for the webdriver."""

        option_arguments = [
            "--headless=new",
            "--hide-scrollbars",
            "start-maximized",
            "--no-sandbox",
            "--disable-blink-features=AutomationControlled",
            "disable-popup-blocking",
        ]

        options = webdriver.ChromeOptions()
        options.add_experimental_option(
            "excludeSwitches", ["enable-automation"]
        )

        for argument in option_arguments:
            options.add_argument(argument)

        return options

    def start_driver(self):
        """Start the web driver (remote or local)."""

        try:
            if os.environ.get("DOCKER", False):
                self.browser = webdriver.Remote(
                    command_executor="http://172.0.0.2:4444",
                    options=self.options,
                )
            else:
                self.browser = webdriver.Chrome(
                    service=self.service,
                    options=self.options,
                )

            return self.browser
        except WebDriverException as error:
            self.logger.error("Error starting the web browser: %s", str(error))
            raise error

    def close_browser(self):
        """Close the web browser."""

        try:
            if self.browser:
                self.browser.close()
                self.logger.info("Browser closed")
        except WebDriverException as e:
            self.logger.error("Error closing the web browser: %s", str(e))

    def __enter__(self):
        self.browser = self.start_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_browser()

    def _handle_authorization(self):
        if self.email and path.isfile(
            path.join(self.BASE_DIR, f"cookies/{self.email.split('@')[0]}")
        ):
            self.logger.info("Cookie file found. Try authorization.")
            self.read_cookie()
            if not self.check_apply_cookie():
                self.remove_cookie()
        elif self.email and self.password:
            self.click_login_button()
            self.authorization(self.email, self.password)

    def get_this_week_or_last_week_leaders(
        self, club_id: int, last_week=True
    ) -> list:
        """Get the leaders of a club for this or last week."""

        self.open_page_club(club_id)
        self._handle_authorization()

        if last_week:
            self.click_last_week_button()

        return self.get_data_leaderboard()

    def open_page_club(self, club_id: int):
        """Open browser and go to url"""

        self.browser.get(
            self.BASE_URL + "clubs/" + str(club_id) + "/leaderboard"
        )
        self.logger.info("Open page club URL: %s", self.browser.current_url)

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
        self.logger.info("Go to last week's leaderboard")

    def click_login_button(self):
        """Click login button on login page"""

        self.wait_element((By.CLASS_NAME, "btn-login")).click()
        self.logger.info("Open page Login URL: %s", self.browser.current_url)

    def click_submit_login(self):
        """Click Login button submit"""

        self.wait_element((By.ID, "login-button")).click()

    def get_data_leaderboard(self) -> list:
        """Get data leaderboard"""

        leaderboard = []
        table = self.wait_element((By.CLASS_NAME, "dense"))
        tr_contents = table.find_elements(By.TAG_NAME, "tr")
        for num, trow in enumerate(tr_contents[1:]):
            athlete_url = (
                trow.find_element(By.TAG_NAME, "a")
                .get_attribute("href")
                .strip()
            )
            avatar_medium = (
                trow.find_element(By.TAG_NAME, "img")
                .get_attribute("src")
                .strip()
            )
            avatar_large = (
                trow.find_element(By.TAG_NAME, "img")
                .get_attribute("src")
                .strip()
                .replace("medium", "large")
            )

            # Iterate to find 'td' under each 'tr'
            lst = [td.text for td in trow.find_elements(By.TAG_NAME, "td")]

            # List of dict with the athlete's data from the table.
            leaderboard.append(
                dict(
                    zip(
                        [
                            "rank",
                            "athlete_name",
                            "distance",
                            "activities",
                            "longest",
                            "avg_pace",
                            "elev_gain",
                        ],
                        lst,
                    )
                )
            )

            leaderboard[num]["avatar_large"] = avatar_large
            leaderboard[num]["avatar_medium"] = avatar_medium
            leaderboard[num]["link"] = athlete_url

        self.logger.info(
            "A list of dictionaries with athlete data from the table"
            "has been generated %s athletes of the club",
            len(leaderboard),
        )
        return leaderboard

    def authorization(self, username: str, password: str):
        """Sign in to the Strava"""

        self.input_email(username)
        self.input_password(password)
        self.click_submit_login()

        if self.check_alert_msg():
            raise AuthorizationFailureException(
                "The username or password did not match."
            )

        self.logger.info("Authorization successful.")
        self.save_cookie()

    def open_sign_in_page(self):
        """Open browser and go to url"""

        self.browser.get(self.BASE_URL + "login")
        self.logger.info("Open page Login URL: %s", self.browser.current_url)

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
            wait.until(
                ec.visibility_of_element_located(
                    (By.CLASS_NAME, "alert-message")
                )
            )
        except (TimeoutException, NoSuchElementException):
            return False
        return True

    def check_apply_cookie(self) -> bool:
        """Check if a cookie has been applied"""

        try:
            WebDriverWait(self.browser, timeout=1).until_not(
                ec.visibility_of_element_located((By.CLASS_NAME, "btn-login"))
            )
        except (NoSuchElementException, TimeoutException):
            self.logger.warning("Authorization failed.")
        return True

    def save_cookie(self):
        """Get cookies and save to a file"""

        with open(
            path.join(self.BASE_DIR, f"cookies/{self.email.split('@')[0]}"),
            "wb",
        ) as cookie:
            pickle.dump(self.browser.get_cookies(), cookie)
            self.logger.info("Cookie file is saved.")

    def read_cookie(self):
        """Open the cookie and use it for authorization"""

        with open(
            path.join(self.BASE_DIR, f"cookies/{self.email.split('@')[0]}"),
            "rb",
        ) as cookie:
            for row in pickle.load(cookie):
                self.browser.add_cookie(row)
        # Require update so that cookies are applied
        self.browser.refresh()

    def remove_cookie(self):
        """Delete invalid cookie"""

        self.logger.warning("Invalid cookies. Delete cookies. Try again.")
        remove(path.join(self.BASE_DIR, f"cookies/{self.email.split('@')[0]}"))
        raise ValueError("Invalid cookies. You need username and password.")


class InfoStravaClub:
    """Get information about the Strava Club"""

    auth_url = "https://www.strava.com/oauth/token"

    def __init__(self, club_id):
        self.club_id = club_id
        self.club_url = "https://www.strava.com/api/v3/clubs/" + str(
            self.club_id
        )
        self.headers = {"Authorization": "Bearer " + self.access_token}
        self.params = {"per_page": 200, "page": 1}

    @property
    def access_token(self):
        """Get access token"""
        payload = {
            "client_id": "***",
            "client_secret": "***",
            "refresh_token": "***",
            "grant_type": "refresh_token",
            "f": "json",
        }
        res = requests.post(self.auth_url, data=payload, timeout=5)
        access_token = res.json()["access_token"]
        return access_token

    @property
    def get_club_info(self):
        """Get club info"""
        response = requests.get(self.club_url, headers=self.headers, timeout=5)
        return response.json()
