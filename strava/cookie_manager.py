import os
import json
import config


class CookieManager:
    """CookieManager is a utility class for managing user-specific cookies."""

    def __init__(self, email: str):
        self.email = email
        self.filename = f"{self.email.split('@')[0]}_cookies.json"
        self.file_path = os.path.join(
            config.BASE_DIR, f"cookies/{self.filename}"
        )

        # ensure directory exists
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

    def save_cookie(self, cookies):
        """Save cookies to a JSON file."""
        try:
            with open(self.file_path, "w", encoding="utf-8") as cookie_file:
                json.dump(cookies, cookie_file, indent=2)
                config.logger.info("Cookie JSON file is saved.")
        except Exception as e:
            config.logger.error(f"Failed to save cookie JSON: {e}")

    def read_cookie(self):
        """Read cookies from a JSON file."""
        if os.path.exists(self.file_path):
            try:
                with open(
                    self.file_path, "r", encoding="utf-8"
                ) as cookie_file:
                    cookies = json.load(cookie_file)
                    config.logger.info("Cookie JSON file found. Reading...")
                    return cookies
            except Exception as e:
                config.logger.error(f"Failed to read cookie JSON: {e}")
                return None
        return None

    def remove_cookie(self):
        """Remove cookies."""
        if os.path.exists(self.file_path):
            config.logger.warning("Deleting invalid cookie JSON file.")
            os.remove(self.file_path)