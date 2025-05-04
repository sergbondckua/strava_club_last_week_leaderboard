from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.common import TimeoutException, NoSuchElementException

import config


class StravaPageUtils:
    """
    A base class providing common methods for interacting with the Strava
    web application.
    """

    def __init__(self, browser: webdriver):
        self.browser = browser
        self.wait = WebDriverWait(self.browser, 15)

    def _check_element(
        self, by_element: tuple[str, str], until_not: bool = False
    ) -> bool:
        """Check if an element is present on the page."""
        try:
            if until_not:
                self.wait.until_not(
                    ec.visibility_of_element_located(by_element)
                )
            else:
                self.wait.until(ec.visibility_of_element_located(by_element))
        except (TimeoutException, NoSuchElementException):
            return False
        return True

    def _check_hidden_element(
        self, by_element: tuple[str, str]
    ) -> WebElement | bool:
        """Check if an element is present on the page."""
        try:
            element = self.wait.until(
                ec.presence_of_element_located(by_element)
            )
        except (TimeoutException, NoSuchElementException):
            return False
        return element

    def _wait_element(self, by_element: tuple[str, str]) -> WebElement:
        """Wait for the element"""
        try:
            element = self.wait.until(
                ec.visibility_of_element_located(by_element)
            )
            return element
        except TimeoutException as e:
            raise TimeoutException(f"Not found element {by_element}") from e

    def _check_url_contains(self, by_element: str) -> bool:
        """Check if the URL contains the specified element."""
        try:
            self.wait.until(ec.url_contains(by_element))
        except (TimeoutException, NoSuchElementException):
            return False
        return True

    def _open_page(self, url: str):
        """Open the specified page URL in the browser."""
        self.browser.get(url)
        config.logger.info("Open page URL: %s", self.browser.current_url)
