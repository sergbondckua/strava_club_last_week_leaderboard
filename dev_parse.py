import asyncio
import os
import pickle
from os import path
from pathlib import Path


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
    """ TODO: implement"""

    def __init__(self):
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
                self.browser = webdriver.Chrome(
                    service=self.service,
                    options=self.options,
                )
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

    BASE_URL = "https://www.strava.com"

    def __init__(self, browser_manager, email, password):
        self.email = email
        self.password = password
        self.browser = browser_manager.start_browser
        self.cookie_manager = CookieManager(email)

    def authorize(self):
        """
        TODO: Implement
        """
        self.open_sign_in_page()
        cookies = self.cookie_manager.read_cookie()  # Try to read cookies
        if cookies is not None and self.check_apply_cookies(cookies):
            config.logger.info("Cookie file found and applied.")
        elif self.email and self.password:
            self.authorization_process(self.email, self.password)

    def check_apply_cookies(self, cookies: list[dict[str, str]]) -> bool:
        """Check if a cookie has been applied"""
        for cookie in cookies:
            self.browser.add_cookie(cookie)
        self.browser.refresh()

        try:
            WebDriverWait(self.browser, timeout=1).until_not(
                ec.visibility_of_element_located((By.CLASS_NAME, "btn-signup"))
            )
        except (NoSuchElementException, TimeoutException):
            config.logger.warning(
                "Invalid cookies! Authorization failed. "
                "Authentication will be attempted using a login and password"
            )
            return False
        return True

    def open_sign_in_page(self):
        """Open browser and go to url"""
        self.browser.get(f"{self.BASE_URL}/login")
        config.logger.info("Open page Login URL: %s", self.browser.current_url)

    def authorization_process(self, username: str, password: str):
        """Sign in to the Strava"""
        self.input_email(username)
        self.input_password(password)
        self.click_submit_login()

        if self.check_alert_msg():
            self.cookie_manager.remove_cookie()
            raise AuthorizationFailureException(
                "The username or password did not match."
            )

        config.logger.info("Authorization successful.")
        self.cookie_manager.save_cookie(self.browser.get_cookies())

    def wait_element(self, by_element: tuple, timeout: int = 15) -> WebElement:
        """Wait for the element"""
        wait = WebDriverWait(self.browser, timeout)
        try:
            element = wait.until(ec.visibility_of_element_located(by_element))
            return element
        except TimeoutException as ex:
            raise TimeoutException("Not found element") from ex

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


class CookieManager:
    """
    CookieManager is a utility class for managing user-specific cookies.
    """

    def __init__(self, email):
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
        """Remove invalid cookies."""
        if os.path.exists(self.file_path):
            config.logger.warning("Delete the file with invalid cookies.")
            os.remove(self.file_path)


def main():
    browser_manager = BrowserManager()
    authorization = StravaAuthorization(
        browser_manager,
        config.env(str("EMAIL")),
        config.env.str("PASSWD"),
    )
    try:
        authorization.authorize()
    except Exception as e:
        print("An error occurred:", str(e))
    finally:
        browser_manager.close_browser()


if __name__ == "__main__":
    main()
