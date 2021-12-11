"""
    Copyright (C) 2021 - Rokas Puzonas <rokas.puz@gmail.com>

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
from typing import Optional, Union
from enum import Enum
from datetime import date

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"

@dataclass
class ReportProject:
    location: str
    program_files: list[str]
    test_folders: list[str]

@dataclass
class ReportSection:
    title: str

    problem: Optional[str] = None
    project: Optional[Union[str, ReportProject]] = None
    professors_notes: Optional[str] = None

    def __str__(self) -> str:
        return f"ReportSection[{self.title}]"

@dataclass
class Report:
    title: str

    student_name: str
    student_gender: Gender

    professor_name: str
    professor_gender: Gender

    sections: list[ReportSection] = field(default_factory=list)

    tests_folder: str = field(default="tests")

    university_name: str = field(default="Kauno technologijos universitetas")
    faculty_name: str = field(default="Informatikos fakultetas")
    sub_title: str = field(default="Laboratorinių darbų ataskaita")
    city_name: str = field(default="Kaunas")
    year: int = field(default=date.today().year)

    def __str__(self) -> str:
        return f"Report[{self.student_name}, {self.title}]"

