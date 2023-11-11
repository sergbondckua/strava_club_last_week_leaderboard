from pathlib import Path

from PIL import Image

import config


class PosterSaver:
    """Save poster to disk."""

    OUTPUT_FOLDER = config.BASE_DIR / "out_posters"

    def __init__(self):
        self.logger = config.logger
        self.output_dir = Path(self.OUTPUT_FOLDER)

    async def save_poster(self, poster: Image.Image, filename: str):
        """Save the generated poster image to a file."""
        output_file = self.output_dir / filename
        with output_file.open("wb") as f:
            poster.save(f, "PNG")
        poster.close()  # Explicitly close the image

    async def clear_output_folder(self):
        """Clear the folder."""
        folder_path = self.output_dir.resolve()
        for file in folder_path.glob("*"):
            if file.is_file():
                file.unlink()
        self.logger.info("The folder has been cleared.")