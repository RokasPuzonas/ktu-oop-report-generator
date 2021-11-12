#!/usr/bin/env python
from fpdf import FPDF
from PIL import Image
from enum import Enum
from dataclasses import dataclass, field
from fpdf.fpdf import ToCPlaceholder
from fpdf.outline import OutlineSection
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
    university_icon = "university-icon.png"
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
        self.start_section("Dėstytojo pastabos", 1)

    def add_toc_page(self):
        self.insert_toc_placeholder(self.render_toc, 1)

        # Adjust starting page, because it's a bug
        # When the function creates a new placeholder page, it should start with
        # it, not the one before it.
        placeholder = self._toc_placeholder
        self._toc_placeholder = ToCPlaceholder(
            placeholder.render_function, placeholder.start_page+1, placeholder.y, placeholder.pages
        )

    @staticmethod
    def render_toc(pdf: FPDF, outline: list[OutlineSection]) -> None:
        pdf.set_y(pdf.t_margin + 0.5 + 12/pdf.k)
        pdf.set_font("times-new-roman", "", 12)
        pdf.cell(0, txt="TURINYS", align="C", ln=True)

        counters = [1, 1]
        for i in range(len(outline)):
            section = outline[i]
            level = int(section.level)
            if level > 1: continue
            if i > 0:
                if outline[i-1].level == section.level:
                    counters[level] += 1
                elif outline[i-1].level < section.level:
                    counters[level] = 1
                elif outline[i-1].level > section.level:
                    counters[level] += 1
            if level > 0:
                pdf.set_x(pdf.get_x()+1)
            if level == 0:
                pdf.set_font("times-new-roman", "B", 14)
            else:
                pdf.set_font("times-new-roman", "", 12)
            level_label = "".join([f"{counters[j]}." for j in range(level+1)])
            pdf.cell(txt=f'{level_label} {section.name} (page {section.page_number})', ln=1)

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

