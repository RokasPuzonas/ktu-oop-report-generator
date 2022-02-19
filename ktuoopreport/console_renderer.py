"""
    Copyright (C) 2022 - Rokas Puzonas <rokas.puz@gmail.com>

    This file is part of KTU OOP Report Generator.

    KTU OOP Report Generator is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    KTU OOP Report Generator is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with KTU OOP Report Generator. If not, see <https://www.gnu.org/licenses/>.
"""
from PIL import Image, ImageFont, ImageDraw

def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    r, g, b = tuple(int(value[i:i+2], 16) for i in (0, 2, 4))
    return (r, g, b)

def render_console(
        text: str,
        font_file: str,
        font_size: int,
        background: str = "#000000",
        foreground: str = "#FFFFFF",
        left_padding: int = 10,
        right_padding: int = 10,
        top_padding: int = 10,
        bottom_padding: int = 10,
    ):

    font = ImageFont.truetype(font_file, font_size)
    text_width, text_height = font.getsize_multiline(text)

    bg = hex_to_rgb(background)
    fg = hex_to_rgb(foreground)

    width = text_width + left_padding + right_padding
    height = text_height + top_padding + bottom_padding
    image = Image.new("RGB", (width, height), bg)

    draw = ImageDraw.Draw(image)
    draw.text((left_padding, top_padding), text, fill=fg, font=font)

    return image
