import time
import random
from typing import List, Dict, Tuple

from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver import Keys, ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

import config
from strava.cookie_manager import CookieManager
from strava.exceptions import AuthorizationFailureException
from strava.page_utils import StravaPageUtils


def pause(min_delay: float = 0.5, max_delay: float = 2.0) -> None:
    """
    Pause execution for a random amount of time to simulate human behavior.

    Args:
        min_delay: Minimum delay time in seconds
        max_delay: Maximum delay time in seconds
    """
    time.sleep(random.uniform(min_delay, max_delay))


class HumanInteractionSimulator:
    """Simulate human-like mouse and keyboard interactions to avoid detection."""

    def __init__(self, browser: webdriver.Chrome):
        """
        Initialize the human interaction simulator.

        Args:
            browser: Selenium WebDriver instance
        """
        self.browser = browser

    @staticmethod
    def simulate_human_typing(
        element: WebElement,
        text: str,
        min_delay: float = 0.05,
        max_delay: float = 0.25,
    ) -> None:
        """
        Simulate human-like typing with variable speed.

        Args:
            element: The element to simulate typing on
            text: The text to type
            min_delay: Minimum delay between keystrokes in seconds
            max_delay: Maximum delay between keystrokes in seconds
        """
        element.clear()  # Clear the field first
        for character in text:
            element.send_keys(character)
            time.sleep(random.uniform(min_delay, max_delay))

    def human_like_mouse_move(
        self,
        start_element: WebElement,
        end_element: WebElement,
        click_at_end: bool = True,
    ) -> None:
        """
        Simulate human-like mouse movement with natural trajectory.

        Args:
            start_element: The starting element
            end_element: The target element
            click_at_end: Whether to click the target element at the end
        """
        # Calculate center points of elements
        start_x = (
            start_element.location["x"] + start_element.size["width"] // 2
        )
        start_y = (
            start_element.location["y"] + start_element.size["height"] // 2
        )
        end_x = end_element.location["x"] + end_element.size["width"] // 2
        end_y = end_element.location["y"] + end_element.size["height"] // 2

        # Generate trajectory with random displacements to simulate natural movement
        steps = random.randint(10, 25)
        trajectory = []

        # Create bezier curve-like path with decreasing noise
        for t in [i / steps for i in range(steps + 1)]:
            # Linear interpolation between start and end points
            x = start_x + (end_x - start_x) * t
            y = start_y + (end_y - start_y) * t

            # Add noise that decreases as we approach the target
            noise_factor = 1 - t  # More noise at beginning, less at end
            noise_x = random.randint(-5, 5) * noise_factor
            noise_y = random.randint(-5, 5) * noise_factor

            trajectory.append((x + noise_x, y + noise_y))

        # Execute the movement
        actions = ActionChains(self.browser)
        actions.move_to_element(start_element)

        current_x, current_y = start_x, start_y

        for target_x, target_y in trajectory:
            offset_x = target_x - current_x
            offset_y = target_y - current_y

            actions.move_by_offset(offset_x, offset_y)
            # Variable pause between movements
            actions.pause(random.uniform(0.01, 0.1))

            current_x, current_y = target_x, target_y

        if click_at_end:
            actions.click()

        actions.perform()


class StravaAuthorization(StravaPageUtils):
    """Handles Strava user authentication with improved reliability."""

    # Define locators as class constants for better maintainability
    LOCATORS = {
        "email_field": (By.ID, "desktop-email"),
        "login_button": (By.ID, "desktop-login-button"),
        "use_password_button": (
            By.CSS_SELECTOR,
            "#__next > div > div:nth-child(2) > div.DesktopLayout_desktopLayout__xENAo.LoginSteps_desktopOnly___v27h > div > div > div:nth-child(7)",
        ),
        "password_field": (
            By.XPATH,
            "//*[@id='__next']/div/div[2]/div[2]/div/div/form/div[1]/div[2]/div/input",
        ),
        "submit_password_button": (
            By.XPATH,
            "//*[@id='__next']/div/div[2]/div[2]/div/div/form/div[2]/button",
        ),
        "error_message": (By.CLASS_NAME, "text-subhead"),
        "alert_message": (By.CLASS_NAME, "Alert_alertContent__kla3s"),
        "signup_button": (By.CLASS_NAME, "btn-signup"),
    }

    def __init__(self, browser: webdriver.Chrome, email: str, password: str):
        """
        Initialize the Strava authorization handler.

        Args:
            browser: Selenium WebDriver instance
            email: Strava account email
            password: Strava account password
        """
        super().__init__(browser)
        self.email = email
        self.password = password
        self.browser = browser
        self.cookie_manager = CookieManager(email)
        self.human_simulator = HumanInteractionSimulator(browser)
        self.logger = config.logger

    def authorization(self) -> None:
        """
        Perform user authentication with cookie management.

        First tries to use saved cookies, falls back to username/password if needed.

        Raises:
            AuthorizationFailureException: If authentication fails
        """
        self._open_page(f"{config.BASE_URL}/login")
        cookies = self.cookie_manager.read_cookie()

        if cookies and self._check_apply_cookies(cookies):
            self.logger.info("Cookies have been successfully applied.")
        else:
            self.logger.warning(
                "Invalid cookies! Authorization failed. "
                "Authentication will be attempted using a login and password."
            )
            self.cookie_manager.remove_cookie()
            self._login(self.email, self.password)

    def _login(self, username: str, password: str) -> None:
        """
        Sign in to Strava using username and password.

        Args:
            username: Strava account email
            password: Strava account password

        Raises:
            AuthorizationFailureException: If credentials are invalid
        """
        try:
            # Step 1: Enter email
            email_field = self._wait_element(self.LOCATORS["email_field"])
            self.human_simulator.simulate_human_typing(email_field, username)
            pause(1, 2)

            # Step 2: Submit email
            self._click_element(self.LOCATORS["login_button"])
            pause(2, 3)

            # Check for errors
            self._handle_potential_errors()

            # Step 3: Select password login option
            self._click_element(self.LOCATORS["use_password_button"])
            pause(1, 2)

            # Step 4: Enter password
            password_field = self._wait_element(
                self.LOCATORS["password_field"]
            )
            self.human_simulator.simulate_human_typing(
                password_field, password
            )
            pause(1, 2)

            # Step 5: Submit password
            self._click_element(self.LOCATORS["submit_password_button"])
            pause(3, 5)

            # Final error checks
            self._handle_potential_errors()

            # Save cookies
            self.logger.info("Authorization successful.")
            self.cookie_manager.save_cookie(self.browser.get_cookies())

        except Exception as e:
            self.logger.error(f"Login failed: {str(e)}")
            raise AuthorizationFailureException(
                f"Login process failed: {str(e)}"
            )

    def _check_apply_cookies(self, cookies: List[Dict[str, str]]) -> bool:
        """
        Apply and validate cookies for authentication.

        Args:
            cookies: List of cookie dictionaries to apply

        Returns:
            bool: True if cookies are valid and authentication succeeded
        """
        self._add_cookies(cookies)
        self.browser.refresh()
        return self._check_element(
            self.LOCATORS["signup_button"], until_not=True
        )

    def _check_alert_msg(self) -> bool:
        """
        Check if an alert message is present.

        Returns:
            bool: True if alert message is found
        """
        return self._check_element(self.LOCATORS["alert_message"])

    def _add_cookies(self, cookies: List[Dict[str, str]]) -> None:
        """
        Add cookies to the browser session.

        Args:
            cookies: List of cookie dictionaries to apply
        """
        for cookie in cookies:
            try:
                self.browser.add_cookie(cookie)
            except Exception as e:
                self.logger.warning(f"Failed to add cookie: {str(e)}")

    def _click_element(self, locator: Tuple[str, str]) -> None:
        """
        Wait for an element and click it.

        Args:
            locator: Tuple of locator strategy and value
        """
        element = self._wait_element(locator)
        try:
            element.click()
        except Exception as e:
            self.logger.warning("Failed to click element: %s", str(e))
            # Fallback to JavaScript click if normal click fails
            self.browser.execute_script("arguments[0].click();", element)

    def _handle_potential_errors(self) -> None:
        """
        Check for and handle error messages, with retry logic.

        Raises:
            AuthorizationFailureException: If max retries are exceeded
        """
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            # Check for error message with short timeout
            if self._check_hidden_element(self.LOCATORS["error_message"]):
                self.logger.error("Occurred error detected")

                # Retry login procedure
                self.logger.info(
                    "Retrying authorization (Attempt %d/%d)",
                    retry_count + 1,
                    max_retries,
                )

                # Check if email or password field is present
                if self._check_element(self.LOCATORS["email_field"]):
                    self.logger.info("Retrying login process")
                    self._retry_login_process()
                else:
                    self.logger.info("Retrying password process")
                    self._retry_password_process()

                retry_count += 1
                pause(2, 3)  # Wait before checking again

                if self._check_url_contains("onboarding" or "dashboard"):
                    return

            else:
                # No error found
                self.logger.debug("No error messages detected")
                return

        if retry_count >= max_retries:
            raise AuthorizationFailureException(
                f"Failed to login after {max_retries} attempts"
            )

    def _retry_login_process(self) -> None:
        """
        Retry the login process from the beginning.
        """
        try:
            # Re-enter email
            email_field = self._wait_element(self.LOCATORS["email_field"])
            self.human_simulator.simulate_human_typing(email_field, self.email)
            pause(1, 2)

            # Submit email
            self._click_element(self.LOCATORS["login_button"])
            pause(2, 3)

            # Select password option
            self._click_element(self.LOCATORS["use_password_button"])
            pause(1, 2)

            # Enter password
            self.human_simulator.human_like_mouse_move(
                self._wait_element(self.LOCATORS["submit_password_button"]),
                self._wait_element(self.LOCATORS["password_field"]),
            )
            password_field = self._wait_element(
                self.LOCATORS["password_field"]
            )
            self.human_simulator.simulate_human_typing(
                password_field, self.password
            )
            pause(1, 2)

            # Submit password
            self._click_element(self.LOCATORS["submit_password_button"])
            pause(3, 5)

        except Exception as e:
            self.logger.error("Error during login retry: %s", str(e))

    def _retry_password_process(self) -> None:
        """
        Retry the password process from the beginning.
        """
        try:
            # Enter password
            password_field = self._wait_element(
                (
                    By.XPATH,
                    "//*[@id='__next']/div/div[2]/div[2]/div/div/form/div[1]/div[3]/div/input",
                )
            )
            self.human_simulator.simulate_human_typing(
                password_field, self.password
            )
            pause(1, 2)

            # Submit password
            self._click_element(self.LOCATORS["submit_password_button"])
        except Exception as e:
            self.logger.error("Error during password retry: %s", str(e))
