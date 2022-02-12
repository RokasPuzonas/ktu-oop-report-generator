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

from dataclasses import dataclass, field
from typing import Union
from enum import Enum

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"

@dataclass
class Person:
    name: str
    gender: Gender

@dataclass
class Report:
    title: str

    student: Union[Person, list[Person]]
    lecturer: Person

    sections: list[dict] = field(default_factory=list)

    tests_folder: str = field(default="tests")

    def __str__(self) -> str:
        return f"Report[{self.title}]"
