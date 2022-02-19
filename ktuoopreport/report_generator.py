"""
    Copyright (C) 2022 - Rokas Puzonas <rokas.puz@gmail.com>

    This file is part of KTU OOP Report Generator.

    KTU OOP Report Generator is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    KTU OOP Report Generator is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with KTU OOP Report Generator. If not, see <https://www.gnu.org/licenses/>.
"""

from dataclasses import dataclass
from math import ceil
from fpdf.fpdf import TitleStyle
from fpdf.outline import OutlineSection
import os.path as path
import sys
from datetime import date
from ktuoopreport.sections.class_diagram import ClassDiagramSection

from ktuoopreport.sections.markdown import MarkdownSection
from ktuoopreport.sections.project_source_code import ProjectSourceCodeSection
from ktuoopreport.sections.project_tests import ProjectTestsSection

from .sections import SectionGenerator

from .report import Report, Gender
from .pdf import PDF, FontStyle

current_year = date.today().year

# Sort by 2 keys: csharp file type, character count
# 1. A register class is more important than an enum
# 2. A longer file is probably more important also
def key_by_importance(filename: str) -> tuple[int, int]:
    """
    Returns a tuple with the rating and size of given project file
    """
    rating = 0
    size = path.getsize(filename)
    filename = filename.lower()
    if "program" in filename:
        rating = 10
    elif "register" in filename:
        rating = 8
    elif "container" in filename:
        rating = 6
    return rating, size

ON_POSIX = 'posix' in sys.builtin_module_names

@dataclass
class SectionEntry:
    generator: SectionGenerator
    title: str

class ReportGenerator:
    sections: list[SectionEntry]
    report: Report

    toc_title: str = "TURINYS"

    sub_title: str = "Laboratorinių darbų ataskaita"
    university_name: str = "Kauno technologijos universitetas"
    faculty_name: str = "Informatikos fakultetas"
    university_icon: str = "university-icon.png"
    title_page_footer: str = f"Kaunas {current_year}"
    title_page_seperator_color: tuple[int, int, int] = (212, 175, 55)

    toc_section_spacing_above = 0.21
    toc_section_spacing_below = 0.35

    def __init__(self, sections: list[SectionEntry]) -> None:
        self.sections = sections

        self.total_sections = 0

    def generate(self, report: Report, output: str):
        pdf = self._create_base_pdf()

        self.add_title_page(pdf, report)
        self.add_toc_page(pdf, report)
        for section in report.sections:
            self.add_section(pdf, section, report)

        pdf.save_to_file(output)

    def _create_base_pdf(self) -> PDF:
        pdf = PDF("portrait", "A4")

        pdf.add_font(FontStyle(
            name = "times-new-roman",
            normal_font = "fonts/times-new-roman.ttf",
            bold_font = "fonts/times-new-roman-bold.ttf",
            italic_font = "fonts/times-new-roman-italic.ttf",
            unicode = True
        ))

        pdf.add_font(FontStyle(
            name = "courier-new",
            normal_font = "fonts/courier-new.ttf",
            bold_font = "fonts/courier-new-bold.ttf",
            italic_font = "fonts/courier-new-italic.ttf",
            bold_italic_font = "fonts/courier-new-bold-italic.ttf",
            unicode = True
        ))

        pdf.add_font(FontStyle(
            name = "consolas",
            normal_font = "fonts/consolas.ttf",
            bold_font = "fonts/consolas-bold.ttf",
            italic_font = "fonts/consolas-italic.ttf",
            bold_italic_font = "fonts/consolas-bold-italic.ttf",
            unicode = True
        ))

        pdf.add_font(FontStyle(
            name = "arial",
            normal_font = "fonts/arial.ttf",
            bold_font = "fonts/arial-bold.ttf",
            unicode = True
        ))

        l_margin = 2.5
        pdf.set_margins(l_margin, 1, 1)
        pdf.set_auto_page_break(True, 1.5)

        pdf.set_section_title_styles(
            level0 = TitleStyle("arial", "B", 14, l_margin=l_margin+1.5, t_margin=0, b_margin=0.35), # type: ignore
            level1 = TitleStyle("arial", "B", 12, l_margin=l_margin+2.5, t_margin=0.15, b_margin=0.35), # type: ignore
            level2 = TitleStyle("arial", "B", 12, l_margin=l_margin+3.5, t_margin=0.25, b_margin=0.35), # type: ignore
        )

        def footer() -> None:
            if pdf.page_no() > 1:
                pdf.set_font("times-new-roman", 12)
                pdf.set_text_color(0, 0, 0) # BLACK
                pdf.set_cursor(x=0, y=-pdf.bottom_margin)
                pdf.write(str(pdf.page_no()), w=0, align="R")

        pdf.footer = footer

        return pdf

    def add_toc_page(self, pdf: PDF, report: Report):
        """
        Add table of contents to page
        """
        toc_height = self.get_effective_toc_height(pdf, report.sections)
        # Adjust for title that is at the top of the page
        eph = pdf.eph - (0.5 + pdf.get_font_height(12))
        toc_height += pdf.get_font_height(12)

        def render_toc(*vargs):
            self.render_toc(*vargs)

        pages = max(1, ceil(toc_height / eph))
        pdf.insert_toc_placeholder(render_toc, pages)

    # Used for determining how many pages should be inserted in placeholder
    def get_effective_toc_height(self, pdf: PDF, sections: list[dict]) -> float:
        """
        Estimate how much space the table of contents is gonna take up
        """
        section_text_height = pdf.get_font_height(14)
        subsection_text_height = pdf.get_font_height(12)
        margins = self.toc_section_spacing_above + self.toc_section_spacing_below
        height = 0

        for _ in sections:
            height += section_text_height + margins
            height += len(self.sections) * (subsection_text_height + margins)

        return height

    def render_toc(self, pdf: PDF, outline: list[OutlineSection]) -> None:
        """
        Render table of contents
        """
        page_top_y = pdf.top_margin + 0.5 + pdf.get_font_height(12)
        pdf.set_cursor(y=page_top_y)
        pdf.set_font("times-new-roman", 12)
        pdf.print(self.toc_title, w=0, align="C")
        pdf.newline()

        for i in range(len(outline)):
            outlineSection = outline[i]
            level = int(outlineSection.level)

            # Only render up to 1 level deep
            if level > 1: continue

            # Update font
            if level == 0:
                pdf.set_font("times-new-roman", 14, bold = True)
            else:
                pdf.set_font("times-new-roman", 12)

            # Ensure that text will not be places outside of a page
            h = self.toc_section_spacing_above + pdf.get_font_height()
            pdf.perform_page_break_if_need_be(h)

            # Move cursor where the section label will be placed
            pdf.set_cursor(x=pdf.left_margin)
            pdf.move_cursor(dy=self.toc_section_spacing_above)

            # Indent outline section
            if level > 0:
                pdf.move_cursor(dx=1)

            self.render_toc_section(pdf, outlineSection)

            pdf.move_cursor(dy=pdf.get_font_height())
            pdf.move_cursor(dy=self.toc_section_spacing_below)

    def render_toc_section(self, pdf: PDF, outline: OutlineSection):
        """
        Render a single section from the table of contents
        """
        x = pdf.get_x()

        pdf.write(outline.name)

        text_width = pdf.get_string_width(outline.name)
        page_width = pdf.get_page_width()
        left_over_space = page_width - pdf.right_margin - (x + text_width)

        page_number_width = pdf.get_string_width(str(outline.page_number))
        dot_width = pdf.get_string_width('.')
        needed_dots = round((left_over_space - page_number_width)/dot_width - 0.1)

        page_number_txt = "." * needed_dots + str(outline.page_number)

        pdf.set_cursor(
            x=-pdf.get_string_width(page_number_txt)-pdf.right_margin
        )
        pdf.write(page_number_txt)

    @staticmethod
    def _get_people_from_report(report: Report) -> list[tuple[str, str]]:
        people = []
        if isinstance(report.student, list):
            for student in report.student:
                gender = "Studentas" if student.gender == Gender.MALE else "Studentė"
                people.append((student.name, gender))
        else:
            if report.student.gender == Gender.MALE:
                people.append((report.student.name, "Studentas"))
            else:
                people.append((report.student.name, "Studentė"))

        if report.lecturer.gender == Gender.MALE:
            people.append((report.lecturer.name, "Dėstytojas"))
        else:
            people.append((report.lecturer.name, "Dėstytoja"))
        return people

    def add_title_page(self, pdf: PDF, report: Report) -> None:
        """
        Add title page by getting needed information from a report
        """
        pdf.add_page()

        font_size_pt = 12
        font_height = pdf.get_font_height(font_size_pt)

        pdf.fpdf.set_y(pdf.fpdf.t_margin + 0.5 + 12/pdf.fpdf.k)
        pdf.image(self.university_icon, 1.78, 2.04, centered=True)

        pdf.set_font("times-new-roman", font_size_pt, bold = True)
        pdf.print(self.university_name, w=0, h=font_height*1.5, align="C")

        pdf.set_font("times-new-roman", font_size_pt)
        pdf.print(self.faculty_name, w=0, align="C")

        # Middle part (title)
        pdf.newline(font_height*15)

        pdf.set_font("times-new-roman", 18, bold = True)
        pdf.print(report.title, w=0, align="C")

        pdf.set_font("times-new-roman", 14)
        pdf.print(self.sub_title, w=0, align="C")

        # Student name and professort name section
        font_height = pdf.get_font_height()
        pdf.newline(font_height*4)

        width = pdf.get_page_width()

        # Seperator
        y = pdf.get_y()
        pdf.set_draw_color(self.title_page_seperator_color)
        pdf.line(width/2+font_height, y, width-pdf.right_margin, y)
        pdf.newline(font_height*2)

        people = self._get_people_from_report(report)
        for i in range(len(people)):
            name, lecturer = people[i]

            pdf.set_font("times-new-roman", 12, bold = True)
            pdf.set_cursor(x=width/2 + font_height)
            pdf.print(name, w=width/2, align="L")
            pdf.newline()

            pdf.set_font("times-new-roman", 12)
            pdf.set_cursor(x=width/2 + font_height)
            pdf.print(lecturer, w=width/2, align="L")
            pdf.newline()
            pdf.newline()
            pdf.newline()

        # Seperator
        y = pdf.get_y()
        pdf.set_draw_color(self.title_page_seperator_color)
        pdf.line(width/2+font_height, y, width-pdf.right_margin, y)
        pdf.newline(font_height*2)

        # Footer
        pdf.set_font("times-new-roman", 12, bold = True)
        pdf.set_cursor(y=-font_height*2-pdf.bottom_margin)
        pdf.write(self.title_page_footer, w=0, align="C")

    def add_section(self, pdf: PDF, section: dict, report: Report) -> None:
        title = section["title"]
        assert type(title) == str, "Missing 'title' field in section"

        for entry in self.sections:
            if entry.generator.has_required_fields(section, report):
                entry.generator.assert_fields(section, report)

        pdf.add_page()

        pdf.push_section("{level} {title}", title=title)
        for entry in self.sections:
            pdf.push_section("{level} {title}", title=entry.title)
            if entry.generator.has_required_fields(section, report):
                entry.generator.generate(pdf, section, report)
            else:
                pdf.newline()
                pdf.newline()
                pdf.newline()
            pdf.pop_section()
        pdf.pop_section()

class ReportGenerator1(ReportGenerator):
    def __init__(self) -> None:
        super().__init__(sections=[
            SectionEntry(MarkdownSection("problem"), "Darbo užduotis"),
            SectionEntry(
                ProjectSourceCodeSection(
                    "project", sort_key=key_by_importance,
                    included_files=["*.cs"],
                    excluded_files=["obj/**", "bin/**", "Properties/**"],
                ),
                "Programos tekstas"
            ),
            SectionEntry(ProjectTestsSection("project"), "Pradiniai duomenys ir rezultatai"),
            SectionEntry(MarkdownSection("lecturers_comment"), "Dėstytojo pastabos"),
        ])

class ReportGenerator2(ReportGenerator):
    def __init__(self) -> None:
        super().__init__(sections=[
            SectionEntry(MarkdownSection("problem"), "Darbo užduotis"),
            SectionEntry(MarkdownSection("filler!!!"), "Grafinės vartotojo sąsajos schema"),
            SectionEntry(MarkdownSection("filler!!!"), "Sąsajoje panaudotų komponentų keičiamos savybės"),
            SectionEntry(ClassDiagramSection(
                "project",
                included_files=["*.cs"],
                excluded_files=["obj/**", "bin/**", "Properties/**"],
            ), "Klasių diagrama"),
            SectionEntry(MarkdownSection("guide"), "Programos vartotojo vadovas"),
            SectionEntry(ProjectSourceCodeSection(
                "project", #sort_key=key_by_importance, # TODO: Remake sort key
                included_files=["*.cs", "*.aspx", "*.aspx.cs"],
                excluded_files=["obj/**", "bin/**", "Properties/**"],
            ), "Programos tekstas"),
            SectionEntry(ProjectTestsSection("project"), "Pradiniai duomenys ir rezultatai"),
            SectionEntry(MarkdownSection("lecturers_comment"), "Dėstytojo pastabos"),
        ])
