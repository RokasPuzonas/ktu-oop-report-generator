#!/usr/bin/env python
import click
import sys
import toml
import os.path as path
from enum import Enum

from dacite.core import from_dict
from dacite.config import Config

from ktuoopreport import Report, ReportPDF, Gender, Person, ReportSection

# TODO: Create a full report by just having a git repository url ant the configurations filename
# TODO: Clear old build files, before rebuilding project.
# TODO: Add support for loading program descriptions from individual README files
# TODO: Support loading project from git urls

def read_report_toml(filename: str) -> Report:
    report = None
    try:
        parsed_toml = toml.load(filename)
        report = from_dict(
                data_class = Report,
                data = parsed_toml, # type: ignore
                config = Config(cast = [Enum])
        )
    except toml.TomlDecodeError as e:
        click.echo(click.style(f"Failed to decode input file ({filename}):", fg="red"))
        click.echo(click.style(str(e), fg="red"))
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"Validation error from input file ({filename}):", fg="red"))
        click.echo(click.style(str(e), fg="red"))
        sys.exit(1)

    base_directory = path.dirname(filename)
    for section in report.sections:
        if section.project:
            section.project = path.join(base_directory, section.project)

    return report

@click.command()
@click.argument("input", type=click.Path(exists=True, readable=True, dir_okay=False))
@click.option("-o", "--output", required=False, type=click.Path(writable=True, dir_okay=False))
def main(input: str, output: str):
    if not output:
        output = path.splitext(input)[0] + ".pdf"

    # Beware this method is devious. I can end the program with sys.exit
    report = read_report_toml(input)

    ReportPDF.generate(report, output)

def example():
    example_report = Report(
        title = "Objektinis programavimas I (P175B118)",
        student = Person("Bobby bob", Gender.MALE),
        lecturer = Person("Alice alison", Gender.FEMALE),
        sections = [
            ReportSection("Introduction to containers"),
            ReportSection("Now let's go to registers"),
            ReportSection("Regex magic"),
            ReportSection("Inheritence")
        ]
    )

    ReportPDF.generate(example_report, "example-report.pdf")

if __name__ == "__main__":
    main()

