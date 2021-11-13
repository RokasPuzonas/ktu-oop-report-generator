#!/usr/bin/env python
from fpdf import FPDF
from PIL import Image
from enum import Enum
from fpdf.fpdf import ToCPlaceholder
from fpdf.outline import OutlineSection
from typing import Optional
import click
import sys
from datetime import date
from pydantic.error_wrappers import ValidationError
import toml
from pydantic import BaseModel, Field

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"

class ReportSection(BaseModel):
    title: str

    problem: Optional[str]
    project_location: Optional[str]
    professors_notes: Optional[str]

    def __str__(self) -> str:
        return f"ReportSection[{self.title}]"

class Report(BaseModel):
    title: str

    student_name: str
    student_gender: Gender

    professor_name: str
    professor_gender: Gender

    sections: list[ReportSection] = Field(default_factory=list)

    university_name: str = Field(default="Kauno technologijos universitetas")
    faculty_name: str = Field(default="Informatikos fakultetas")
    sub_title: str = Field(default="Laboratorinių darbų ataskaita")
    city_name: str = Field(default="Kaunas")
    year: int = Field(default=date.today().year)

    def __str__(self) -> str:
        return f"Report[{self.student_name}, {self.title}]"

class PDFReport(FPDF):
    university_icon = "university-icon.png"
    toc_max_level = 2
    line_spacing: float = 1.15
    report: Report

    def __init__(self, report: Report) -> None:
        super().__init__("portrait", "cm", "A4")
        self.report = report

        self.add_font("times-new-roman", "", "fonts/times-new-roman.ttf", True)
        self.add_font("times-new-roman", "B", "fonts/times-new-roman-bold.ttf", True)
        self.add_font("arial", "", "fonts/arial.ttf", True)
        self.add_font("arial", "B", "fonts/arial-bold.ttf", True)

        self.set_margins(2.5, 1, 1)
        self.set_auto_page_break(True, 1.5)

        self.add_title_page()
        self.add_toc_page()
        for section in report.sections:
            self.add_section(section)

    def add_title_page(self) -> None:
        self.add_page()

        # Top part
        self.set_y(self.t_margin + 0.5 + 12/self.k)
        self.center_image(self.university_icon, 1.78, 2.04)

        self.set_font("times-new-roman", "B", 12)
        self.cell(0, self.font_size*1.5, txt=self.report.university_name, align="C", ln=True)

        self.set_font("times-new-roman", "", 12)
        self.cell(0, txt=self.report.faculty_name, align="C", ln=True)

        # Middle part (title)
        self.ln(self.font_size*15)

        self.set_font("times-new-roman", "B", 18)
        self.cell(0, txt=self.report.title, align="C", ln=True)
        
        self.set_font("times-new-roman", "", 14)
        self.cell(0, txt=self.report.sub_title, align="C", ln=True)

        # Student name and professort name section
        self.ln(self.font_size*4)

        w = self.get_page_width()

        y = self.get_y()
        self.set_draw_color(212, 175, 55)
        self.line(w/2, y, w-self.r_margin, y)
        self.ln(self.font_size*2)

        self.set_font("times-new-roman", "B", 12)
        self.cell(x=w/2, w=w/2, txt=self.report.student_name, align="L", ln=True)
        self.ln(self.font_size)

        self.set_font("times-new-roman", "", 12)
        if self.report.student_gender == Gender.MALE:
            self.cell(x=w/2, w=w/2, txt="Studentas", align="L", ln=True)
        else:
            self.cell(x=w/2, w=w/2, txt="Studentė", align="L", ln=True)

        self.ln(self.font_size*3)

        self.set_font("times-new-roman", "B", 12)
        self.cell(x=w/2, w=w/2, txt=self.report.professor_name, align="L", ln=True)
        self.ln(self.font_size)

        self.set_font("times-new-roman", "", 12)
        if self.report.professor_gender == Gender.MALE:
            self.cell(x=w/2, w=w/2, txt="Dėstytojas", align="L", ln=True)
        else:
            self.cell(x=w/2, w=w/2, txt="Dėstytoja", align="L", ln=True)
        self.ln(self.font_size)

        y = self.get_y() + self.font_size
        self.set_draw_color(212, 175, 55)
        self.line(w/2, y, w-self.r_margin, y)
        self.ln(self.font_size * self.line_spacing + 3.5)

        # Footer
        self.set_font("times-new-roman", "B", 12)
        self.set_y(-self.font_size*2-self.b_margin)
        self.cell(0, txt=f"{self.report.city_name} {self.report.year}", align="C")

    def add_section(self, section: ReportSection) -> None:
        self.add_page()
        self.set_font("arial", "B", 14)
        self.cell(0, txt=section.title, align="C", ln=True)
        self.start_section(section.title)
        self.start_section("Darbo užduotis", 1)
        self.start_section("Programos tekstas", 1)
        self.start_section("Pradiniai duomenys ir rezultatai", 1)
        self.start_section("1 Testas", 2)
        self.start_section("2 Testas", 2)
        self.start_section("Dėstytojo pastabos", 1)

    def add_toc_page(self):
        self.insert_toc_placeholder(self.render_toc, 2)

        # Adjust starting page, because it's a bug
        # When the function creates a new placeholder page, it should start with
        # it, not the one before it.
        placeholder = self._toc_placeholder
        self._toc_placeholder = ToCPlaceholder(
            placeholder.render_function, placeholder.start_page+1, placeholder.y, placeholder.pages
        )

    # TODO: render_toc could use some refactoring
    def render_toc(self, pdf: FPDF, outline: list[OutlineSection]) -> None:
        pdf.set_y(pdf.t_margin + 0.5 + 12/pdf.k)
        pdf.set_font("times-new-roman", "", 12)
        pdf.cell(0, txt="TURINYS", align="C", ln=True)
        pdf.ln()

        y = pdf.get_y()
        section_numbers = [1, 1, 1, 1]
        for i in range(len(outline)):
            outlineSection = outline[i]
            level = int(outlineSection.level)

            # Only render up to the specified number of levels levels
            if level > self.toc_max_level: continue

            # Reset number prefix if a continuos level has ended
            if i > 0:
                if outline[i-1].level < outlineSection.level:
                    section_numbers[level] = 1
                else:
                    section_numbers[level] += 1

            # Update font
            y += 0.21
            if level == 0:
                pdf.set_font("times-new-roman", "B", 14)
            else:
                pdf.set_font("times-new-roman", "", 12)

            x = pdf.l_margin

            # Indent outline section
            if level > 0:
                x = x+1

            # Do a manual page break
            # TODO: find a better solution for this
            if y + pdf.font_size > pdf.page_break_trigger:
                pdf.page += 1
                y = pdf.t_margin + 0.5 + 12/pdf.k

            # Construct a dot seperated list of section numbers. ex: "1.2.2."
            level_label = ".".join([str(section_numbers[j]) for j in range(level+1)]) + "."
            self.render_toc_section(pdf, x, y, outlineSection, level_label)

            y += pdf.font_size

            y += 0.35

    def render_toc_section(self, pdf: FPDF, x: float, y: float, outlineSection: OutlineSection, level_label: str):
        pdf.text(x, y, f"{level_label} {outlineSection.name} (page {outlineSection.page_number})")

    def add_page_number(self) -> None:
        self.set_font("times-new-roman", "", 12)
        self.set_y(-self.font_size*2-self.b_margin)
        self.cell(0, txt=str(self.page_no()), align="R")

    def footer(self) -> None:
        if self.page_no() > 1:
            self.add_page_number()

    def center_image(self, filename: str, w: float = 0, h: float = 0) -> None:
        if w == 0:
            im = Image.open(filename)
            w = im.size[0]

        self.image(
            filename,
            w = w,
            h = h,
            x = self.l_margin + (self.get_page_width() - self.l_margin - self.r_margin - w)/2
        )

    def get_page_width(self) -> float:
        return self.dw_pt/self.k

    def get_page_height(self) -> float:
        return self.dh_pt/self.k

    def get_page_size(self) -> tuple[float, float]:
        return self.get_page_width(), self.get_page_height()

    def set_line_spacing(self, line_spacing: float) -> None:
        self.line_spacing = line_spacing

    def get_line_spacing(self) -> float:
        return self.line_spacing

    def cell(self, w:float=None, h:float=None, x:float=None, y:float=None, *args, **kwargs) -> None:
        if h is None:
            h = self.font_size * self.line_spacing

        if x and y:
            self.set_xy(x, y)
        elif x:
            self.set_x(x)
        elif y:
            self.set_y(y)

        super().cell(w, h, *args, **kwargs)

@click.command()
@click.argument("input", type=click.Path(exists=True, readable=True, dir_okay=False))
@click.argument("output", type=click.Path(writable=True, dir_okay=False))
def main(input: str, output: str):
    report = None
    try:
        parsed_toml = toml.load(input)
        report = Report(**parsed_toml)
    except ValidationError as e:
        click.echo(click.style(f"Validation error from input file ({input}):", fg="red"))
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

