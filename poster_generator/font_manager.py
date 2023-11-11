import os
from pathlib import Path

from PIL import ImageFont
from fontTools.ttLib import TTFont

import config


class FontManager:
    """A FontManager class for managing fonts."""

    FONT_DIR = config.BASE_DIR / "poster_generator/resources/fonts"
    DEFAULT_FONT = os.path.join(FONT_DIR, "Ubuntu-Regular.ttf")
    FONT_SIZE = 30

    async def set_font(self, symbol: str) -> ImageFont.FreeTypeFont:
        """Set the font_manager to a given symbol"""
        symbol_unicode = ord(symbol)
        ttf = TTFont(self.DEFAULT_FONT)

        if self.is_symbol_in_font(symbol_unicode, ttf):
            return ImageFont.truetype(self.DEFAULT_FONT, size=self.FONT_SIZE)

        fonts = self.get_font_list()

        for font in fonts:
            ttf = TTFont(os.path.join(self.FONT_DIR, font))

            if self.is_symbol_in_font(symbol_unicode, ttf):
                return ImageFont.truetype(
                    os.path.join(self.FONT_DIR, font),
                    size=self.FONT_SIZE,
                )

        return ImageFont.truetype(self.DEFAULT_FONT, size=self.FONT_SIZE)

    @staticmethod
    def is_symbol_in_font(symbol_unicode: ord, font: TTFont) -> bool:
        """
        Checks if a Unicode symbol exists in the specified font.

        :param symbol_unicode: The Unicode symbol as ord().
        :param font: The TTFont object representing the font.
        :return: True if the symbol exists in the font, otherwise False.
        """
        return any(
            char_map.isUnicode() and symbol_unicode in char_map.cmap
            for char_map in font["cmap"].tables
        )

    def get_font_list(self) -> list[Path]:
        """Get a list of font files in the specified directory."""
        font_dir = Path(self.FONT_DIR).resolve()
        fonts_list = [file for file in font_dir.glob("*") if file.is_file()]
        return fonts_list

    @property
    def font(self) -> ImageFont.FreeTypeFont:
        """Get the font_manager for text in the poster."""
        return ImageFont.truetype(self.DEFAULT_FONT, size=self.FONT_SIZE)
