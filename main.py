#!/usr/bin/env python
from fpdf import FPDF
import click

class Report:
    pass

class ReportStyle:
    pass

class ReportGenerator:
    pass

@click.command()
@click.argument("output")
def main(output: str):
    pdf = FPDF("portrait", "mm", "A4")
    pdf.add_page()
    pdf.set_font("times")
    pdf.cell(40, 10, "Hello, World!")
    pdf.output(output)

if __name__ == "__main__":
    main()

