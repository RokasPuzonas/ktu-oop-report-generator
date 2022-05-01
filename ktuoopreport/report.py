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

    def __str__(self) -> str:
        return f"Report[{self.title}]"
