import time
import random

from selenium import webdriver
from selenium.webdriver import Keys, ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

import config
from strava.browser import BrowserManager
from strava.cookie_manager import CookieManager
from strava.exceptions import AuthorizationFailureException
from strava.page_utils import StravaPageUtils


def pause(min_delay: float = 0.5, max_delay: float = 2.0) -> None:
    """Pause execution for a random amount of time."""
    time.sleep(random.uniform(min_delay, max_delay))


class HumanInteractionSimulator:
    """Simulate human-like mouse and keyboard interactions."""

    def __init__(self, browser: webdriver.Chrome):
        self.browser = browser

    @staticmethod
    def simulate_human_typing(
        element: WebElement,
        text: str,
        min_delay: float = 0.05,
        max_delay: float = 0.25,
    ):
        """
        Simulate human-like typing.

        Args:
            element (WebElement): The element to simulate typing on.
            text (str): The text to type.
            min_delay (float, optional): The minimum delay between typing characters. Defaults to 0.05.
            max_delay (float, optional): The maximum delay between typing characters. Defaults to 0.25.
        """
        for character in text:
            element.send_keys(character)
            time.sleep(random.uniform(min_delay, max_delay))  # Pause

    def human_like_mouse_move(
        self,
        start_element: WebElement,
        end_element: WebElement,
        click_at_end: bool = True,
    ):
        """Simulate human-like mouse move.

        Args:
            start_element (WebElement): The start element.
            end_element (WebElement): The end element.
            click_at_end (bool, optional): If True, click at the end element. Defaults to True.
        """

        # initial position center of starting element
        start_x = (
            start_element.location["x"] + start_element.size["width"] // 2
        )
        start_y = (
            start_element.location["y"] + start_element.size["height"] // 2
        )

        # Ultimate position target item center
        end_x = end_element.location["x"] + end_element.size["width"] // 2
        end_y = end_element.location["y"] + end_element.size["height"] // 2

        # Generate a trajectory with random displacements
        steps = random.randint(10, 25)
        trajectory = []
        for t in [i / steps for i in range(steps + 1)]:
            x = start_x + (end_x - start_x) * t
            y = start_y + (end_y - start_y) * t
            noise_x = random.randint(-3, 3) * (1 - t)
            noise_y = random.randint(-3, 3) * (1 - t)
            trajectory.append((x + noise_x, y + noise_y))

        # We simulate mouse movement
        actions = ActionChains(self.browser)
        actions.move_to_element(
            start_element
        )  # We start with the starting item

        current_x, current_y = (
            start_x,
            start_y,
        )  # Keep track of the current position

        for target_x, target_y in trajectory:
            offset_x = target_x - current_x
            offset_y = target_y - current_y

            actions.move_by_offset(offset_x, offset_y)
            actions.pause(random.uniform(0.01, 0.2))

            current_x += offset_x
            current_y += offset_y

        if click_at_end:
            actions.click()

        actions.perform()


class StravaAuthorization(StravaPageUtils):
    """Handles Strava user authentication."""

    def __init__(self, browser: webdriver.Chrome, email: str, password: str):
        super().__init__(browser)
        self.email = email
        self.password = password
        self.browser = browser
        self.cookie_manager = CookieManager(email)
        self.human_simulator = HumanInteractionSimulator(browser)

    def authorization(self):
        """
        Performs user authentication.

        This method opens the login page, tries to read cookies and, in case of refusal,
        Performs authentication using the username and password.
        """
        self._open_page(f"{config.BASE_URL}/login")
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

        self._wait_element((By.ID, "desktop-email"))
        self._input_email(username)  # Enter username
        pause(1, 2)

        self._click_submit_login()  # Click on the "Login" button
        pause(2, 3)

        self._click_use_password()  # Click on the "Use password" button
        pause(1, 2)

        self._input_password(password)  # Enter password
        pause(1, 2)

        self._click_submit_password()  # Click on the "Submit" button
        pause(3, 5)

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
        return self._check_element(
            (By.CLASS_NAME, "Alert_alertContent__kla3s"), timeout=2
        )

    def _add_cookies(self, cookies: list[dict[str, str]]) -> None:
        """Add cookies to the browser."""
        for cookie in cookies:
            self.browser.add_cookie(cookie)

    def _click_submit_login(self):
        """Click Login button submit"""
        self._wait_element((By.ID, "desktop-login-button")).send_keys(
            Keys.ENTER
        )

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
        ).send_keys(Keys.ENTER)

    def _input_email(self, email: str):
        """Input email address"""
        button = self._wait_element((By.TAG_NAME, "button"))
        field = self._wait_element((By.ID, "desktop-email"))
        self.human_simulator.human_like_mouse_move(button, field)
        field.clear()
        self.human_simulator.simulate_human_typing(field, email)

    def _input_password(self, password: str):
        """Input password"""
        li = self._wait_element((By.TAG_NAME, "ul"))
        field = self._wait_element(
            (
                By.XPATH,
                "//*[@id='__next']/div/div[2]/div[2]/div/div/form/div[1]/div[2]/div/input",
            )
        )
        self.human_simulator.human_like_mouse_move(li, field)
        field.clear()
        self.human_simulator.simulate_human_typing(field, password)
