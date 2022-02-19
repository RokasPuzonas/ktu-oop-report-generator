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
from PIL import Image, ImageFont, ImageDraw
from math import ceil, floor
from typing import Optional

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
    line_height = font_size * line_spacing

    font = ImageFont.truetype(font_file, font_size)
    attribute_lines = stringify_class_attributes(diagram.attributes)
    method_lines = stringify_class_methods(diagram.methods)

    # Append empty entry, so there is at least a section for methods and
    # attributes even if there aren't any in the diagram
    if len(attribute_lines) == 0:
        attribute_lines.append("")
    if len(method_lines) == 0:
        method_lines.append("")

    max_line_width = max(
        max(font.getlength(s) for s in attribute_lines),
        max(font.getlength(s) for s in method_lines),
        font.getlength(diagram.name)
    )

    total_width = 2*border_width + 2*padding + floor(max_line_width)

    total_line_amount = len(attribute_lines) + len(method_lines) + 1
    total_height = floor(total_line_amount*line_height + 4*border_width + 6*padding - 3*(font_size*(line_spacing-1)))

    # Create image and start drawing
    image = Image.new("RGB", (total_width, total_height), background)

    draw = ImageDraw.Draw(image)
    # Create a cursor, so it is easier to track where things need to be drawn next
    cx = border_width + padding # Cursor x coordinate
    cy = border_width + padding # Cursor y coordinate

    # Draw borders
    draw.rectangle((0, 0, total_width, total_height), outline=border_color, width=border_width)

    # Draw class name
    draw.text((cx, cy), diagram.name, fill=foreground, font=font)

    # Draw seperator line
    cy += padding + font_size + border_width/2
    draw.line([(0, cy), (total_width-1, cy)], border_color, border_width)

    # Draw attributes
    cy += padding + border_width/2
    for i in range(len(attribute_lines)):
        draw.text((cx, cy+i*line_height), attribute_lines[i], fill=foreground, font=font)

    # Draw seperator line
    cy += padding + len(attribute_lines)*line_height + border_width/2 - (font_size*(line_spacing-1))
    draw.line([(0, cy), (total_width-1, cy)], border_color, border_width)

    # Draw methods
    cy += padding + border_width/2
    for i in range(len(method_lines)):
        draw.text((cx, cy+i*line_height), method_lines[i], fill=foreground, font=font)

    return image

# def render_class_diagrams(diagrams: list[ClassDiagram]) -> Image.Image:
    # image = Image.new("RGB", (100, 100), self.diagram_background)
    # return image
