import os
import pickle
from os import path

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


class BrowserManager:
    """TODO: implement"""

    def __init__(self):
        self.options = self._configure_driver_options()
        self.browser = None

    def __enter__(self):
        self.browser = self.start_browser
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_browser()

    @staticmethod
    def _configure_driver_options():
        """Configure ChromeOptions for the webdriver."""
        option_arguments = [
            # "--headless=new",
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

    @property
    def start_browser(self):
        """Start the web driver (remote or local)."""
        try:
            if os.environ.get("DOCKER", False):
                self.browser = webdriver.Remote(
                    command_executor="http://172.0.0.2:4444",
                    options=self.options,
                )
            else:
                self.browser = webdriver.Chrome(options=self.options)
            return self.browser
        except WebDriverException as error:
            config.logger.error(
                "Error starting the web browser: %s", str(error)
            )
            raise error

    def close_browser(self):
        """Close the web browser."""
        try:
            if self.browser:
                self.browser.close()
                config.logger.info("Browser closed")
        except WebDriverException as e:
            config.logger.error("Error closing the web browser: %s", str(e))


class StravaAuthorization:
    """TODO: implement"""

    BASE_URL = "https://www.strava.com"  # TDOD: edit this

    def __init__(self, browser: webdriver, email: str, password: str):
        self.email = email
        self.password = password
        self.browser = browser
        self.cookie_manager = CookieManager(email)

    def authorize(self):
        """TODO: Implement"""
        self.open_sign_in_page()
        cookies = self.cookie_manager.read_cookie()  # Try to read cookies

        if cookies is not None and self.check_apply_cookies(cookies):
            config.logger.info("Cookie file found and applied.")
        else:
            config.logger.warning(
                "Invalid cookies! Authorization failed. "
                "Authentication will be attempted using a login and password"
            )
            self.cookie_manager.remove_cookie()
            self.login(self.email, self.password)

    def check_apply_cookies(self, cookies: list[dict[str, str]]) -> bool:
        """Check if a cookie has been applied"""
        self.add_cookies(cookies)
        self.browser.refresh()
        check = self.check_element(
            (By.CLASS_NAME, "btn-signup"), timeout=1, until_not=True
        )
        return check

    def check_alert_msg(self) -> bool:
        """Check if the alert"""
        return self.check_element((By.CLASS_NAME, "alert-message"))

    def login(self, username: str, password: str):
        """Sign in to the Strava"""
        self.input_email(username)
        self.input_password(password)
        self.click_submit_login()

        if self.check_alert_msg():
            raise AuthorizationFailureException(
                "The username or password did not match."
            )

        config.logger.info("Authorization successful.")
        self.cookie_manager.save_cookie(self.browser.get_cookies())

    def check_element(
        self, by_element: tuple, timeout: int = 0, until_not: bool = False
    ) -> bool:
        """Check if an element is present on the page."""
        wait = WebDriverWait(self.browser, timeout)
        try:
            if until_not:
                wait.until_not(ec.visibility_of_element_located(by_element))
            else:
                wait.until(ec.visibility_of_element_located(by_element))
        except (TimeoutException, NoSuchElementException):
            return False
        return True

    def wait_element(self, by_element: tuple, timeout: int = 15) -> WebElement:
        """Wait for the element"""
        wait = WebDriverWait(self.browser, timeout)
        try:
            element = wait.until(ec.visibility_of_element_located(by_element))
            return element
        except TimeoutException as e:
            raise TimeoutException("Not found element") from e

    def open_sign_in_page(self):
        """Open browser and go to url"""
        self.browser.get(f"{self.BASE_URL}/login")
        config.logger.info("Open page Login URL: %s", self.browser.current_url)

    def add_cookies(self, cookies: list[dict[str, str]]) -> None:
        """Add cookies to the browser."""
        for cookie in cookies:
            self.browser.add_cookie(cookie)

    def click_submit_login(self):
        """Click Login button submit"""
        self.wait_element((By.ID, "login-button")).click()

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


class StravaLeaderboard:
    """TODO: Implement"""

    BASE_URL = "https://www.strava.com"  # TODO: edit this

    def __init__(self, browser: webdriver):
        self.browser = browser

    def get_this_week_or_last_week_leaders(
        self, club_id: int, last_week=True
    ) -> list:
        """Get the leaders of a club for this or last week."""

        self.open_page_club(club_id)

        if last_week:
            self.click_last_week_button()

        return self.get_data_leaderboard()

    def get_data_leaderboard(self) -> list:
        """Get data leaderboard"""

        leaderboard = []
        table = self.wait_element((By.CLASS_NAME, "dense"))
        tr_contents = table.find_elements(By.TAG_NAME, "tr")[1:]

        for trow in tr_contents:
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
            avatar_large = avatar_medium.replace("medium", "large")

            # Extract text values from 'td' elements and assign them to variables
            (
                rank,
                athlete_name,
                distance,
                activities,
                longest,
                avg_pace,
                elev_gain,
            ) = (td.text for td in trow.find_elements(By.TAG_NAME, "td"))

            athlete_data = {
                "rank": rank,
                "athlete_name": athlete_name,
                "distance": distance,
                "activities": activities,
                "longest": longest,
                "avg_pace": avg_pace,
                "elev_gain": elev_gain,
                "avatar_large": avatar_large,
                "avatar_medium": avatar_medium,
                "link": athlete_url,
            }

            leaderboard.append(athlete_data)

        count_athletes = len(leaderboard)
        config.logger.info(
            "A list of dictionaries with athlete data from the table "
            "has been generated for %s athletes of the club",
            count_athletes,
        )
        return leaderboard

    def wait_element(self, by_element: tuple, timeout: int = 15) -> WebElement:
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
        config.logger.info("Go to last week's leaderboard")

    def open_page_club(self, club_id: int):
        """Open browser and go to url"""
        url = f"{self.BASE_URL}/clubs/{str(club_id)}/leaderboard"
        self.browser.get(url)
        config.logger.info("Open page club URL: %s", self.browser.current_url)


class CookieManager:
    """CookieManager is a utility class for managing user-specific cookies."""

    def __init__(self, email: str):
        self.email = email
        self.filename = f"{self.email.split('@')[0]}.cookies"
        self.file_path = path.join(config.BASE_DIR, f"cookies/{self.filename}")

    def save_cookie(self, cookies):
        """Save cookies to a file."""
        with open(self.file_path, "wb") as cookie_file:
            pickle.dump(cookies, cookie_file)
            config.logger.info("Cookie file is saved.")

    def read_cookie(self):
        """Read cookies from a file."""
        if os.path.exists(self.file_path):
            with open(self.file_path, "rb") as cookie_file:
                cookies = pickle.load(cookie_file)
                return cookies
        return None

    def remove_cookie(self):
        """Remove cookies."""
        if os.path.exists(self.file_path):
            config.logger.warning("Delete the file with invalid cookies.")
            os.remove(self.file_path)


def main():
    with BrowserManager() as browser_manager:
        browser = browser_manager.start_browser
        authorization = StravaAuthorization(
            browser,
            config.env(str("EMAIL")),
            config.env.str("PASSWD"),
        )
        leaderboard = StravaLeaderboard(browser)
        try:
            authorization.authorize()
            athletes = leaderboard.get_this_week_or_last_week_leaders(
                config.env.int("CLUB_ID")
            )
        except Exception as e:
            config.logger.error("An error occurred: %s", str(e))

    # print(athletes)


if __name__ == "__main__":
    main()
