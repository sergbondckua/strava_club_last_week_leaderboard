import time

from selenium import webdriver
from selenium.webdriver.common.by import By

import config
from strava.browser import BrowserManager
from strava.cookie_manager import CookieManager
from strava.exceptions import AuthorizationFailureException
from strava.page_utils import StravaPageUtils


class StravaAuthorization(StravaPageUtils):
    """Handles Strava user authentication."""

    def __init__(self, browser: webdriver.Chrome, email: str, password: str):
        super().__init__(browser)
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
        self._open_page(f"{config.BASE_URL}/login")
        time.sleep(5)
        cookies = self.cookie_manager.read_cookie()

        if cookies is not None and self._check_apply_cookies(cookies):
            config.logger.info("Cookies have been successfully applied.")
        else:
            config.logger.warning(
                "Invalid cookies! Authorization failed. "
                "Authentication will be attempted using a login and password."
            )
            self.cookie_manager.remove_cookie()
            self._login(self.email, self.password)

    def _login(self, username: str, password: str):
        """Sign in to the Strava"""

        self._wait_element((By.ID, "desktop-email")).click()
        self._input_email(username)
        time.sleep(5)
        self._click_submit_login()

        if self._check_element(
            (
                By.XPATH,
                "//*[contains(text(), 'An unexpected error occurred. Please try again.')]",
            ),
            timeout=3,
        ):
            print("yes")
            self._wait_element((By.ID, "desktop-email")).click()
            self._input_email(username)
            self._click_submit_login()
        time.sleep(5)
        self.browser.save_screenshot("login.png")
        self._click_use_password()
        self._input_password(password)
        time.sleep(3)
        self._click_submit_password()

        if self._check_alert_msg():
            raise AuthorizationFailureException(
                "The username or password did not match."
            )

        config.logger.info("Authorization successful.")
        time.sleep(5)
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

    def _add_cookies(self, cookies: list[dict[str, str]]) -> None:
        """Add cookies to the browser."""
        for cookie in cookies:
            self.browser.add_cookie(cookie)

    def _click_submit_login(self):
        """Click Login button submit"""
        self._wait_element((By.ID, "desktop-login-button")).click()

    def _click_use_password(self):
        self._wait_element(
            (
                By.CSS_SELECTOR,
                "#__next > div > div:nth-child(2) > div.DesktopLayout_desktopLayout__xENAo.LoginSteps_desktopOnly___v27h > div > div > div:nth-child(7)",
            )
        ).click()

    def _click_submit_password(self):
        self._wait_element(
            (
                By.XPATH,
                "//*[@id='__next']/div/div[2]/div[2]/div/div/form/div[2]/button",
            )
        ).click()

    def _input_email(self, email: str):
        """Input email address"""
        self._wait_element((By.ID, "desktop-email")).click()
        field = self._wait_element((By.ID, "desktop-email"))
        field.clear()
        field.send_keys(email)

    def _input_password(self, password: str):
        """Input password"""
        field = self._wait_element(
            (
                By.CSS_SELECTOR,
                "#__next > div > div:nth-child(2) > div.DesktopLayout_desktopLayout__xENAo.LoginSteps_desktopOnly___v27h > div > div > form > div.LegacyPasswordForm_passwordInputContainer__VPjgu > div.AuthInput_input__V6C0M > div > input",
            )
        )
        field.clear()
        field.send_keys(password)


if __name__ == "__main__":
    StravaAuthorization(
        BrowserManager().start_browser(), "sergbondckua@gmail.com", "q10101010"
    ).authorization()
