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
from enum import Enum
from dataclasses import dataclass
import math
from PIL import Image, ImageFont, ImageDraw
from math import floor
from typing import Literal, Optional

# TODO: Merge diagrams with the same name into a single one

class VisibilityEnum(Enum):
    Public = 1,
    Private = 2,
    Protected = 3

class ParameterDirection(Enum):
    In = 1,
    Out = 2,
    InOut = 3

@dataclass
class ClassAttribute:
    name: str
    type: str
    visibility: VisibilityEnum
    initial_value: Optional[str]

@dataclass
class ClassMethodParameter:
    name: str
    type: str
    direction: ParameterDirection
    default: Optional[str]

@dataclass
class ClassMethod:
    name: str
    return_type: Optional[str]
    visibility: VisibilityEnum
    parameters: list[ClassMethodParameter]

@dataclass
class ClassDiagram:
    namespace: str
    name: str
    attributes: list[ClassAttribute]
    methods: list[ClassMethod]

    def __str__(self) -> str:
        return f"ClassDiagram({self.namespace}.{self.name})"

@dataclass
class EnumDiagram:
    namespace: str
    name: str
    values: list[str]

    def __str__(self) -> str:
        return f"EnumDiagram({self.namespace}.{self.name})"


"""
def merge_same_diagrams(diagrams: list[EnumDiagram | ClassDiagram]):
    grouped_diagrams = {}

    for diagram in diagrams:
        full_name = f"{diagram.namespace}.{diagram.name}"
        if full_name not in grouped_diagrams:
            grouped_diagrams[full_name] = []
        grouped_diagrams[full_name].append(diagram)

    # print(diagrams)
"""

def stringify_visibility(visibility: VisibilityEnum) -> str:
    if visibility == VisibilityEnum.Protected:
        return "#"
    elif visibility == VisibilityEnum.Public:
        return "+"
    elif visibility == VisibilityEnum.Private:
        return "-"

def stringify_class_attributes(attributes: list[ClassAttribute]) -> list[str]:
    attribute_lines = []

    for attr in attributes:
        attr_line = ""

        attr_line += stringify_visibility(attr.visibility)
        attr_line += " " + attr.name
        attr_line += ": " + attr.type
        if attr.initial_value:
            attr_line += " = " + attr.initial_value

        attribute_lines.append(attr_line)

    return attribute_lines

def stringify_class_parameters(parameters: list[ClassMethodParameter]) -> str:
    stringified_parameters = []
    for param in parameters:
        param_str = ""
        if param.direction == ParameterDirection.In:
            param_str += "in"
        elif param.direction == ParameterDirection.Out:
            param_str += "out"
        elif param.direction == ParameterDirection.InOut:
            param_str += "inout"

        param_str += " " + param.name
        param_str += ": " + param.type
        if param.default:
            param_str += " = " + param.default
        stringified_parameters.append(param_str)
    return ", ".join(stringified_parameters)

def stringify_class_methods(methods: list[ClassMethod]) -> list[str]:
    method_lines = []

    for method in methods:
        method_line = ""

        method_line += stringify_visibility(method.visibility)
        parameters = stringify_class_parameters(method.parameters)
        method_line += f" {method.name}({parameters})"
        if method.return_type and method.return_type != "void":
            method_line += ": " + method.return_type

        method_lines.append(method_line)

    return method_lines

def render_diagram_sections(
        sections: list[list[str]],
        font_file: str,
        font_size: int,
        background: str,
        foreground: str,
        padding: int,
        border_width: int,
        border_color: str,
        line_spacing: float
    ) -> Image.Image:

    font = ImageFont.truetype(font_file, font_size)

    max_line_width = 0
    for section in sections:
        if len(section) > 0:
            max_line_width = max(max_line_width, max(font.getlength(s) for s in section))

    total_line_amount = sum(max(len(section), 1) for section in sections)

    line_height = font_size * line_spacing
    total_width = 2*border_width + 2*padding + floor(max_line_width)
    total_height = 2*border_width + \
                   floor(total_line_amount*line_height - len(sections)*(font_size*(line_spacing-1))) + \
                   len(sections)*(border_width+2*padding)

    # Create image and start drawing
    image = Image.new("RGB", (total_width, total_height), background)

    draw = ImageDraw.Draw(image)
    # Create a cursor, so it is easier to track where things need to be drawn next
    cx = border_width + padding # Cursor x coordinate
    cy = border_width + padding # Cursor y coordinate

    # Draw borders
    draw.rectangle((0, 0, total_width, total_height), outline=border_color, width=border_width)

    # For each section...
    for i in range(len(sections)):
        section = sections[i]

        # Draw all of it's entries line by line and...
        for line in range(len(section)):
            pos = (cx, cy+line*line_height)
            draw.text(pos, section[line], fill=foreground, font=font)

        cy += padding + max(len(section), 1)*line_height + border_width/2 - (font_size*(line_spacing-1))

        # IF this isin't the last section, draw a seperating line
        if i != len(sections)-1:
            draw.line([(0, cy), (total_width-1, cy)], border_color, border_width)

        cy += padding + border_width/2

    return image

def render_class_diagram(
        diagram: ClassDiagram,
        font_file: str,
        font_size: int,
        background: str = "#FFFFFF",
        foreground: str = "#000000",
        padding: int = 10,
        border_width: int = 5,
        border_color: str = "#000000",
        line_spacing: float = 1.20
    ) -> Image.Image:
    sections = []

    sections.append([diagram.name])
    sections.append(stringify_class_attributes(diagram.attributes))
    sections.append(stringify_class_methods(diagram.methods))

    return render_diagram_sections(
        sections,
        font_file, font_size, background, foreground, padding, border_width,
        border_color, line_spacing
    )

def render_enum_diagram(
        diagram: EnumDiagram,
        font_file: str,
        font_size: int,
        background: str = "#FFFFFF",
        foreground: str = "#000000",
        padding: int = 10,
        border_width: int = 5,
        border_color: str = "#000000",
        line_spacing: float = 1.20
    ) -> Image.Image:
    sections = []

    sections.append([diagram.name])
    values_section = []
    for value in diagram.values:
        values_section.append(f"+ {value}")
    sections.append(values_section)

    return render_diagram_sections(
        sections,
        font_file, font_size, background, foreground, padding, border_width,
        border_color, line_spacing
    )

def place_images_into_square(
        images: list[Image.Image],
        spacing: int,
        sort_key,
        cut: Literal["vertical"]|Literal["horizontal"] = "vertical",
        reverse_cut: bool = False
    ) -> tuple[list[tuple[float, float, Image.Image]], float, float]:
    images.sort(key=sort_key, reverse=True)

    available_areas = [(0.0, 0.0, math.inf, math.inf)]
    image_positions: list[tuple[float, float, Image.Image]] = []
    packed_width = 0.0
    packed_height = 0.0

    for image in images:
        best_area_index = -1
        best_area_ratio = 0

        # Find which available area is most sutable for image to be placed in,
        # so that the packed images would be in a square
        for i in range(len(available_areas)):
            area = available_areas[i]
            area_width = area[2] - area[0]
            area_height = area[3] - area[1]
            if image.width <= area_width and image.height <= area_height:
                possible_packed_width = max(area[0] + image.width, packed_width)
                possible_packed_height = max(area[1] + image.height, packed_height)
                possible_ratio = possible_packed_width / possible_packed_height
                if best_area_index == -1 or abs(1-possible_ratio) < abs(1-best_area_ratio):
                    best_area_ratio = possible_ratio
                    best_area_index = i

        assert best_area_index > -1

        # When a sutable area has been found, save a position where the image
        # would be placed, and cut up the area so the next image placement
        # don't overlap already placed image
        left, top, right, bottom = available_areas.pop(best_area_index)
        image_positions.append((left, top, image))

        packed_width = max(left + image.width, packed_width)
        packed_height = max(top + image.height, packed_height)

        new_area_1 = None
        new_area_2 = None
        if cut == "vertical":
            new_area_1 = (left+image.width+spacing, top, right, bottom)
            new_area_2 = (left, top+image.height+spacing, left + image.width, bottom)
        else:
            new_area_1 = (left, top+image.height + spacing, right, bottom)
            new_area_2 = (left + image.width + spacing, top, right, top + image.height)

        if reverse_cut:
            available_areas.append(new_area_1)
            available_areas.append(new_area_2)
        else:
            available_areas.append(new_area_2)
            available_areas.append(new_area_1)

    return (image_positions, packed_width, packed_height)

def find_best_image_placements_in_square(images: list[Image.Image], spacing: int) -> tuple[list[tuple[float, float, Image.Image]], float, float]:
    possible_sort_keys = [
        lambda image: image.height*image.width,
        lambda image: image.height,
        lambda image: image.width
    ]

    best_image_positions = []
    best_width = 0.0
    best_height = 1.0

    for sort_key in possible_sort_keys:
        for cut in ("vertical", "horizontal"):
            for reverse_cut in (False, True):
                image_positions, width, height = place_images_into_square(
                    images,
                    spacing,
                    sort_key,
                    cut, # type: ignore
                    reverse_cut
                )

                ratio = width/height
                best_ratio = best_width/best_height

                if best_image_positions == None or abs(1-ratio) < abs(1-best_ratio):
                    best_image_positions = image_positions
                    best_width = width
                    best_height = height

    return (best_image_positions, best_width, best_height)

# Because the area into which there images are being packed is unbounded,
# I picked a criteria so that it tries to create a packed image which is as
# close a square as possible.
def pack_images(images: list[Image.Image], background: str, spacing: int=0) -> Image.Image:
    image_positions, width, height = find_best_image_placements_in_square(images, spacing)

    packed_image = Image.new("RGB", (int(width), int(height)), background)

    for x, y, image in image_positions:
        packed_image.paste(image, (int(x), int(y)))

    return packed_image

def render_diagrams(
        diagrams: list[ClassDiagram | EnumDiagram],
        font_file: str,
        font_size: int,
        background: str = "#FFFFFF",
        foreground: str = "#000000",
        diagram_padding: int = 10,
        border_width: int = 5,
        border_color: str = "#000000",
        line_spacing: float = 1.20,
        diagram_spacing: int = 25
    ) -> Image.Image:
    rendered_diagrams: list[Image.Image] = []
    for diagram in diagrams:
        renderer = None
        if isinstance(diagram, ClassDiagram):
            renderer = render_class_diagram
        elif isinstance(diagram, EnumDiagram):
            renderer = render_enum_diagram
        else:
            continue

        rendered_diagrams.append(renderer(diagram, # type: ignore
            font_file, font_size, background, foreground, diagram_padding, border_width,
            border_color, line_spacing
        ))

    return pack_images(rendered_diagrams, background, diagram_spacing)
