#!/usr/bin/env python
import click
import sys
from pydantic.decorator import validate_arguments
from pydantic.error_wrappers import ValidationError
import toml
import os.path as path
from glob import glob

from oopgen import Report, PDFGenerator
from oopgen.report import ReportProject

# TODO: Create a full report by just having a git repository url ant the configurations filename
# TODO: Clear old build files, before rebuilding project.
# TODO: Add support for loading program descriptions from individual README files
# TODO: Support loading project from git urls
def read_project(location: str, tests_folder: str) -> ReportProject:
    if not path.exists(location):
        raise FileNotFoundError(f"Project '{location}' dosen't exist")

    if path.isfile(location):
        if not location.endswith(".csproj"):
            raise FileNotFoundError(f"'{location}' is not a project file ending with .csproj")
        location = path.dirname(location)
    elif path.isdir(location) and len(glob(path.join(location, "*.csproj"))) == 0:
        raise FileNotFoundError(f"Project directory '{location}' dosen't contain project file")

    test_folders: list[str] = []
    tests_location = path.join(location, tests_folder)
    if path.isdir(tests_location):
        for test_folder in glob(path.join(tests_location, "*")):
            if path.isdir(test_folder):
                test_folders.append(test_folder)

    program_files = glob(path.join(location, "*.cs"))
    return ReportProject(location, program_files, test_folders)


@click.command()
@click.argument("input", type=click.Path(exists=True, readable=True, dir_okay=False))
@click.option("-o", "--output", required=False, type=click.Path(writable=True, dir_okay=False))
def main(input: str, output: str):
    if not output:
        output = path.splitext(input)[0] + ".pdf"

    PydanticReport = validate_arguments(Report)
    report = None
    try:
        parsed_toml = toml.load(input)
        report = PydanticReport(**parsed_toml)
    except ValidationError as e:
        click.echo(click.style(f"Validation error from input file ({input}):", fg="red"))
        click.echo(click.style(e, fg="red"))
        sys.exit(1)
    except toml.TomlDecodeError as e:
        click.echo(click.style(f"Failed to decode input file ({input}):", fg="red"))
        click.echo(click.style(e, fg="red"))
        sys.exit(1)

    try:
        for section in report.sections:
            if isinstance(section.project, str):
                location = section.project
                if not path.isabs(location):
                    inputdir = path.dirname(path.abspath(input))
                    location = path.join(inputdir, location)
                section.project = read_project(location, report.tests_folder)
    except FileNotFoundError as e:
        click.echo(click.style(f"Failed to read project ({input}):", fg="red"))
        click.echo(click.style(e, fg="red"))
        sys.exit(1)


    pdf = PDFGenerator(report)
    pdf.output(output)

if __name__ == "__main__":
    main()

