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
    tests: list[list[str]]

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

    university_name: str = field(default="Kauno technologijos universitetas")
    faculty_name: str = field(default="Informatikos fakultetas")
    sub_title: str = field(default="Laboratorinių darbų ataskaita")
    city_name: str = field(default="Kaunas")
    year: int = field(default=date.today().year)

    def __str__(self) -> str:
        return f"Report[{self.student_name}, {self.title}]"

