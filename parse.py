from __future__ import annotations
import os
import pickle
from os import path

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

# Constants
BASE_URL = "https://www.strava.com"


class AuthorizationFailureException(Exception):
    """Exception raised when authorization fails"""


class BrowserManager:
    """A context manager for managing a Selenium web browser instance."""

    def __init__(self):
        self.options = self._configure_driver_options()
        self.browser = None

    def __enter__(self):
        self.start_browser()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_browser()

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
        except WebDriverException as error:
            config.logger.error(
                "Error starting the web browser: %s", str(error)
            )
            raise error
        return self.browser

    def close_browser(self):
        """Close the web browser."""
        try:
            if self.browser:
                self.browser.quit()
                config.logger.info("Browser closed")
        except WebDriverException as e:
            config.logger.error("Error closing the web browser: %s", str(e))


class StravaAuthorization:
    """Handles Strava user authentication."""

    def __init__(self, browser: webdriver, email: str, password: str):
        self.email = email
        self.password = password
        self.browser = browser
        self.cookie_manager = CookieManager(email)

    def authorization(self):
        """
        Performs user authentication.

        This method opens the login page, attempts to read cookies, and, in case of failure,
        performs authentication using a username and password.
        """
        self._open_sign_in_page()
        cookies = self.cookie_manager.read_cookie()

        if cookies is not None and self._check_apply_cookies(cookies):
            config.logger.info("Cookie file found and applied.")
        else:
            config.logger.warning(
                "Invalid cookies! Authorization failed. "
                "Authentication will be attempted using a login and password"
            )
            self.cookie_manager.remove_cookie()
            self._login(self.email, self.password)

    def _login(self, username: str, password: str):
        """Sign in to the Strava"""
        self._input_email(username)
        self._input_password(password)
        self._click_submit_login()

        if self._check_alert_msg():
            raise AuthorizationFailureException(
                "The username or password did not match."
            )

        config.logger.info("Authorization successful.")
        self.cookie_manager.save_cookie(self.browser.get_cookies())

    def _check_apply_cookies(self, cookies: list[dict[str, str]]) -> bool:
        """Check if a cookie has been applied"""
        self._add_cookies(cookies)
        self.browser.refresh()
        check = self._check_element(
            (By.CLASS_NAME, "btn-signup"), timeout=1, until_not=True
        )
        return check

    def _check_alert_msg(self) -> bool:
        """Check if the alert"""
        return self._check_element((By.CLASS_NAME, "alert-message"))

    def _check_element(
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

    def _wait_element(
        self, by_element: tuple, timeout: int = 15
    ) -> WebElement:
        """Wait for the element"""
        wait = WebDriverWait(self.browser, timeout)
        try:
            element = wait.until(ec.visibility_of_element_located(by_element))
            return element
        except TimeoutException as e:
            raise TimeoutException("Not found element") from e

    def _open_sign_in_page(self):
        """Open browser and go to url"""
        self.browser.get(f"{BASE_URL}/login")
        config.logger.info("Open page Login URL: %s", self.browser.current_url)

    def _add_cookies(self, cookies: list[dict[str, str]]) -> None:
        """Add cookies to the browser."""
        for cookie in cookies:
            self.browser.add_cookie(cookie)

    def _click_submit_login(self):
        """Click Login button submit"""
        self._wait_element((By.ID, "login-button")).click()

    def _input_email(self, email: str):
        """Input email address"""
        field = self._wait_element((By.ID, "email"))
        field.clear()
        field.send_keys(email)

    def _input_password(self, password: str):
        """Input password"""
        field = self._wait_element((By.ID, "password"))
        field.clear()
        field.send_keys(password)


class StravaLeaderboard:
    """A class for interacting with the Strava leaderboard of a club."""

    def __init__(self, browser: webdriver):
        self.browser = browser

    def get_this_week_or_last_week_leaders(
        self, club_id: int, last_week=True
    ) -> list:
        """Get the leaders of a club for this or last week."""

        self._open_page_club(club_id)

        if last_week:
            self._click_last_week_button()

        return self._get_data_leaderboard()

    def _get_data_leaderboard(self) -> list:
        """Get data leaderboard"""

        leaderboard = []
        table = self._wait_element((By.CLASS_NAME, "dense"))
        trows = table.find_elements(By.TAG_NAME, "tr")[1:]

        for trow in trows:
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

    def _wait_element(
        self, by_element: tuple, timeout: int = 15
    ) -> WebElement:
        """Wait for the element"""
        wait = WebDriverWait(self.browser, timeout)
        try:
            element = wait.until(ec.visibility_of_element_located(by_element))
            return element
        except TimeoutException as ex:
            raise TimeoutException("Not found element") from ex

    def _click_last_week_button(self):
        """Click last week button on table"""
        self._wait_element((By.CLASS_NAME, "last-week")).click()
        config.logger.info("Go to last week's leaderboard")

    def _open_page_club(self, club_id: int):
        """Open browser and go to url"""
        url = f"{BASE_URL}/clubs/{str(club_id)}/leaderboard"
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


class StravaLeaderboardRetriever:
    """Retrieves Strava leaderboard data for a given club."""

    def __init__(self, email, password, club_id, last_week: bool = True):
        self.club_id = club_id
        self.last_week = last_week
        self.browser = BrowserManager().start_browser()
        self.auth = StravaAuthorization(self.browser, email, password)
        self.leaderboard = StravaLeaderboard(self.browser)

    def retrieve_leaderboard_data(self) -> list[dict[str, str]] | None:
        """Retrieve leaderboard data for the specified Strava club."""
        try:
            self.auth.authorization()
            leaderboard_data = (
                self.leaderboard.get_this_week_or_last_week_leaders(
                    self.club_id
                )
            )
            return leaderboard_data
        except Exception as e:
            config.logger.error("An error occurred: %s", str(e))
        finally:
            self.browser.quit()
        return None


def main():
    strava = StravaLeaderboardRetriever(
        config.env.str("EMAIL"),
        config.env.str("PASSWD"),
        config.env.int("CLUB_ID"),
    )
    athletes_rank = strava.retrieve_leaderboard_data()
    print(athletes_rank)  # for debugging
    return athletes_rank


if __name__ == "__main__":
    main()
