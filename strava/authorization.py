import time
import random

from selenium import webdriver
from selenium.webdriver import Keys, ActionChains
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

    @staticmethod
    def simulate_human_typing(element, text, min_delay=0.05, max_delay=0.25):
        """
        Імітує людсько-подібне набивання з випадковими затримками між клавішами
        """
        for character in text:
            element.send_keys(character)
            # Випадкова затримка між клавішами
            time.sleep(random.uniform(min_delay, max_delay))

    def human_like_mouse_move(self, start_element, end_element):
        """ Імітує рух миші з випадковими зміщеннями """

        # Початкова позиція (центр стартового елемента)
        start_x = (
            start_element.location["x"] + start_element.size["width"] // 2
        )
        start_y = (
            start_element.location["y"] + start_element.size["height"] // 2
        )

        # Кінцева позиція (центр цільового елемента)
        end_x = end_element.location["x"] + end_element.size["width"] // 2
        end_y = end_element.location["y"] + end_element.size["height"] // 2

        # Генеруємо траєкторію з випадковими зміщеннями
        steps = random.randint(20, 30)
        trajectory = []
        for t in [i / steps for i in range(steps + 1)]:
            x = start_x + (end_x - start_x) * t
            y = start_y + (end_y - start_y) * t
            noise_x = random.randint(-3, 3) * (1 - t)
            noise_y = random.randint(-3, 3) * (1 - t)
            trajectory.append((x + noise_x, y + noise_y))

        # Імітуємо рух миші
        actions = ActionChains(self.browser)
        actions.move_to_element(
            start_element
        )  # Починаємо зі стартового елемента

        current_x, current_y = start_x, start_y  # Відстежуємо поточну позицію

        for target_x, target_y in trajectory:
            offset_x = target_x - current_x
            offset_y = target_y - current_y

            actions.move_by_offset(offset_x, offset_y)
            actions.pause(random.uniform(0.01, 0.2))

            current_x += offset_x
            current_y += offset_y

        actions.click().perform()  # Клік у кінці (опціонально)

    def authorization(self):
        """
        Виконує автентифікацію користувача.

        Цей метод відкриває сторінку входу, намагається прочитати файли cookie та, у разі відмови,
        виконує аутентифікацію за допомогою імені користувача та пароля.
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

        self._input_email(username)  # Введення ім'я користувача
        time.sleep(random.uniform(0.3, 0.7))  # Пауза

        self._click_submit_login()  # Клік на кнопку "Login"
        time.sleep(random.uniform(2, 3))  # Пауза

        self._click_use_password()  # Клік на кнопку "Use password"
        time.sleep(random.uniform(1, 2))  # Пауза

        self._input_password(password)  # Введення пароля
        time.sleep(random.uniform(1, 2))  # Пауза

        self._click_submit_password()  # Клік на кнопку "Submit"
        time.sleep(random.uniform(3, 4))  # Пауза

        if self._check_alert_msg():
            raise AuthorizationFailureException(
                "The username or password did not match."
            )

        config.logger.info("Authorization successful.")
        # time.sleep(5)
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
        return self._check_element((By.CLASS_NAME, "Alert_alertContent__kla3s"))

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
        ).click()

    def _input_email(self, email: str):
        """Input email address"""
        self._wait_element((By.ID, "desktop-email"))
        button = self.browser.find_element(By.TAG_NAME, "button")
        # email_field = self.browser.find_element(By.ID, "desktop-email")
        field = self._wait_element((By.ID, "desktop-email"))
        self.human_like_mouse_move(button, field)
        field.clear()
        # field.send_keys(email)
        self.simulate_human_typing(field, email)

    def _input_password(self, password: str):
        """Input password"""
        field = self._wait_element(
            (
                By.XPATH,
                "//*[@id='__next']/div/div[2]/div[2]/div/div/form/div[1]/div[2]/div/input",
            )
        )
        field.clear()
        # field.send_keys(password)
        self.simulate_human_typing(field, password)
