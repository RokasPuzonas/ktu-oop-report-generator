#!/usr/bin/env python
import click
import sys
import toml
import os.path as path
from enum import Enum

from dacite.core import from_dict
from dacite import Config

from ktuoopreport import Report, ReportPDF

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
                data = parsed_toml,
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

    # ReportPDF.generate(report, output)

    pdf = ReportPDF(report)
    pdf.output(output)


if __name__ == "__main__":
    main()

