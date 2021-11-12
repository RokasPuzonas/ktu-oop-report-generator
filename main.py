#!/usr/bin/env python
from fpdf import FPDF
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
import inspect
import click
import sys
from datetime import date
import toml

class Gender(Enum):
    MALE = 1
    FEMALE = 2

@dataclass
class ReportSection:
    title: str

    problem: Optional[str] = None
    project_location: Optional[str] = None
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

class PDFReport(FPDF):
    report: Report

    def __init__(self, report: Report) -> None:
        super().__init__("portrait", "cm", "A4")
        self.report = report

        self.add_page()
        self.set_font("times")
        self.cell(4, 1, "Hello, World!")

def from_dict_to_dataclass(cls, data):
    return cls(
        **{
            key: (data[key] if val.default == val.empty else data.get(key, val.default))
            for key, val in inspect.signature(cls).parameters.items()
        }
    )

def read_report_from_toml(filename: str) -> Report:
    parsed_toml = toml.load(filename)

    if isinstance(parsed_toml["student_gender"], str):
        gender = parsed_toml["student_gender"].upper()
        try:
            parsed_toml["student_gender"] = Gender[gender]
        except KeyError:
            pass

    if isinstance(parsed_toml["professor_gender"], str):
        gender = parsed_toml["professor_gender"].upper()
        try:
            parsed_toml["professor_gender"] = Gender[gender]
        except KeyError:
            pass

    if isinstance(parsed_toml["sections"], list):
        sections = parsed_toml["sections"]
        for i in range(len(sections)):
            sections[i] = from_dict_to_dataclass(ReportSection, sections[i])

    return from_dict_to_dataclass(Report, parsed_toml)

@click.command()
@click.argument("input", type=click.Path(exists=True, readable=True, dir_okay=False))
@click.argument("output", type=click.Path(writable=True, dir_okay=False))
def main(input: str, output: str):
    report = None
    try:
        report = read_report_from_toml(input)
    except TypeError as e:
        click.echo(click.style(f"Field error in input file ({input}):", fg="red"))
        click.echo(click.style(e, fg="red"))
        sys.exit(1)
    except toml.TomlDecodeError as e:
        click.echo(click.style(f"Failed to decode input file ({input}):", fg="red"))
        click.echo(click.style(e, fg="red"))
        sys.exit(1)

    pdf = PDFReport(report)
    pdf.output(output)

if __name__ == "__main__":
    main()

