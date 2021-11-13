#!/usr/bin/env python
import click
import sys
from pydantic.decorator import validate_arguments
from pydantic.error_wrappers import ValidationError
import toml

from oopgen import Report, PDFGenerator

@click.command()
@click.argument("input", type=click.Path(exists=True, readable=True, dir_okay=False))
@click.argument("output", type=click.Path(writable=True, dir_okay=False))
def main(input: str, output: str):
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

    pdf = PDFGenerator(report)
    pdf.output(output)

if __name__ == "__main__":
    main()

