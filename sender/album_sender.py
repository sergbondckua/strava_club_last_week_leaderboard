import os

import config


class PosterAlbumSender:
    """
    This class is responsible for sending a media group of photos to a bot.
    """

    IMAGE_PATH = config.BASE_DIR / "out_posters"

    def get_image_files(self) -> list[str]:
        """Get a list the files in the IMAGE_PATH directory."""
        allowed_extensions = (".jpg", ".jpeg", ".png", ".gif")
        image_files = [
            file
            for file in os.listdir(self.IMAGE_PATH)
            if file.lower().endswith(allowed_extensions)
        ]

        return image_files
