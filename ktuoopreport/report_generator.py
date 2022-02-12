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
from fpdf.fpdf import TitleStyle, ToCPlaceholder
from fpdf.outline import OutlineSection
import os.path as path
import sys
from datetime import date

from ktuoopreport.sections.markdown import MarkdownSection
from ktuoopreport.sections.project_source_code import ProjectSourceCodeSection
from ktuoopreport.sections.project_tests import ProjectTestsSection

from .sections import SectionGenerator

from .report import Report, Gender
from .pdf import PDF


current_year = date.today().year

class ProjectNotFoundError(FileNotFoundError):
    """
    Given was not pointing to a valid C# project
    """
    pass

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

    numbering_font_family = "times-new-roman"
    numbering_font_style = "I"
    numbering_font_size = 12

    def __init__(self, sections: list[SectionEntry]) -> None:
        self.sections = sections

        self.total_sections = 0

    def generate(self, report: Report, output: str):
        pdf = self._create_base_pdf()

        self.add_title_page(pdf, report)
        self.add_toc_page(pdf, report)
        for section in report.sections:
            self.add_section(pdf, section, report)
#             project_root = None
#             if section.project:
#                 project_root = self.determine_project_root(section.project)
#                 if not project_root:
#                     raise ProjectNotFoundError(f"Could not determine project root from '{section.project}'")
#
#             tests_folder = None
#             if report.tests_folder and project_root:
#                 tests_folder = path.join(project_root, report.tests_folder)
#
            # self.add_section(pdf, section, report)
                    # title = section.title,
                    # problem = section.problem,
                    # lecturers_comment = section.lecturers_comment,
                    # project_root = project_root,
                    # tests_folder = tests_folder
                # )

        pdf.output(output)

    def _create_base_pdf(self) -> PDF:
        pdf = PDF("portrait", "cm", "A4")

        pdf.add_font("times-new-roman", "", "fonts/times-new-roman.ttf", True)
        pdf.add_font("times-new-roman", "B", "fonts/times-new-roman-bold.ttf", True)
        pdf.add_font("times-new-roman", "I", "fonts/times-new-roman-italic.ttf", True)
        pdf.add_font("courier-new", "", "fonts/courier-new.ttf", True)
        pdf.add_font("courier-new", "B", "fonts/courier-new-bold.ttf", True)
        pdf.add_font("courier-new", "I", "fonts/courier-new-italic.ttf", True)
        pdf.add_font("courier-new", "BI", "fonts/courier-new-bold-italic.ttf", True)
        pdf.add_font("consolas", "", "fonts/consolas.ttf", True)
        pdf.add_font("consolas", "B", "fonts/consolas-bold.ttf", True)
        pdf.add_font("consolas", "I", "fonts/consolas-italic.ttf", True)
        pdf.add_font("consolas", "BI", "fonts/consolas-bold-italic.ttf", True)
        pdf.add_font("arial", "", "fonts/arial.ttf", True)
        pdf.add_font("arial", "B", "fonts/arial-bold.ttf", True)

        pdf.set_margins(2.5, 1, 1)
        pdf.set_auto_page_break(True, 1.5)

        pdf.set_section_title_styles(
            level0 = TitleStyle("arial", "B", 14, l_margin=pdf.l_margin+1.5, t_margin=0, b_margin=0.35), # type: ignore
            level1 = TitleStyle("arial", "B", 12, l_margin=pdf.l_margin+2.5, t_margin=0.15, b_margin=0.35), # type: ignore
            level2 = TitleStyle("arial", "B", 12, l_margin=pdf.l_margin+3.5, t_margin=0.25, b_margin=0.35), # type: ignore
        )

        return pdf

    def add_toc_page(self, pdf: PDF, report: Report):
        """
        Add table of contents to page
        """
        toc_height = self.get_effective_toc_height(pdf, report.sections)
        # Adjust for title that is at the top of the page
        eph = pdf.eph - (0.5 + 12/pdf.k)
        toc_height += 12/pdf.k

        def render_toc(*vargs):
            self.render_toc(*vargs)

        pages = max(1, ceil(toc_height / eph))
        pdf.insert_toc_placeholder(render_toc, pages)

        # Adjust starting page, because it's a bug
        # When the function creates a new placeholder page, it should start with
        # it, not the one before it.
        placeholder = pdf._toc_placeholder
        assert placeholder
        pdf._toc_placeholder = ToCPlaceholder(
            placeholder.render_function, placeholder.start_page+1, placeholder.y, placeholder.pages
        )

    # Used for determining how many pages should be inserted in placeholder
    def get_effective_toc_height(self, pdf: PDF, sections: list[dict]) -> float:
        """
        Estimate how much space the table of contents is gonna take up
        """
        section_text_height = 14/pdf.k
        subsection_text_height = 12/pdf.k
        margins = self.toc_section_spacing_above + self.toc_section_spacing_below
        height = 0

        for _ in sections:
            height += section_text_height + margins
            height += 4 * (subsection_text_height + margins)

        return height

    # TODO: render_toc could use some refactoring
    def render_toc(self, pdf: PDF, outline: list[OutlineSection]) -> None:
        """
        Render table of contents
        """
        page_top_y = pdf.t_margin + 0.5 + 12/pdf.k
        pdf.set_y(page_top_y)
        pdf.set_font("times-new-roman", "", 12)
        pdf.cell(0, txt=self.toc_title, align="C", ln=True)
        pdf.ln()

        y = pdf.get_y()
        for i in range(len(outline)):
            outlineSection = outline[i]
            level = int(outlineSection.level)

            # Only render up to 1 level deep
            if level > 1: continue

            # Update font
            y += self.toc_section_spacing_above
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
                y = page_top_y

            self.render_toc_section(pdf, x, y, outlineSection)

            y += pdf.font_size
            y += self.toc_section_spacing_below

    def render_toc_section(self, pdf: PDF, x: float, y: float, outlineSection: OutlineSection):
        """
        Render a single section from the table of contents
        """
        txt = outlineSection.name

        pdf.text(x, y, txt)

        txt_width = pdf.get_string_width(txt, True)
        page_width = pdf.get_page_width()
        left_over_space = page_width - x - pdf.r_margin - txt_width
        page_number_width = pdf.get_string_width(str(outlineSection.page_number))
        dot_width = pdf.get_string_width('.')
        needed_dots = round((left_over_space - page_number_width)/dot_width - 0.1)
        page_number_txt = "." * needed_dots + str(outlineSection.page_number)

        pdf.text(
            page_width-pdf.get_string_width(page_number_txt)-pdf.r_margin,
            y,
            txt=page_number_txt
        )

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

        # Top part
        pdf.set_y(pdf.t_margin + 0.5 + 12/pdf.k)
        if self.university_icon:
            pdf.image(self.university_icon, w=1.78, h=2.04, centered=True)
        else:
            pdf.ln(2.04)

        pdf.set_font("times-new-roman", "B", 12)
        if self.university_name:
            pdf.cell(0, pdf.font_size*1.5, txt=self.university_name, align="C", ln=True) # type: ignore
        else:
            pdf.ln(pdf.font_size*1.5) # type: ignore

        pdf.set_font("times-new-roman", "", 12)
        if self.faculty_name:
            pdf.cell(0, txt=self.faculty_name, align="C", ln=True)
        else:
            pdf.ln(pdf.font_size)

        # Middle part (title)
        pdf.ln(pdf.font_size*15)

        pdf.set_font("times-new-roman", "B", 18)
        pdf.cell(0, txt=report.title, align="C", ln=True)

        pdf.set_font("times-new-roman", "", 14)
        if self.sub_title:
            pdf.cell(0, txt=self.sub_title, align="C", ln=True)
        else:
            pdf.ln(pdf.font_size)

        # Student name and professort name section
        pdf.ln(pdf.font_size*4)

        width = pdf.get_page_width()

        # Seperator
        y = pdf.get_y()
        pdf.set_draw_color(*self.title_page_seperator_color)
        pdf.line(width/2+pdf.font_size, y, width-pdf.r_margin, y) # type: ignore
        pdf.ln(pdf.font_size*2)

        people = self._get_people_from_report(report)
        for i in range(len(people)):
            name, proffesion = people[i]

            pdf.set_font("times-new-roman", "B", 12)
            pdf.cell(x=width/2 + pdf.font_size, w=width/2, txt=name, align="L", ln=True) # type: ignore
            pdf.ln(pdf.font_size)

            pdf.set_font("times-new-roman", "", 12)
            pdf.cell(x=width/2 + pdf.font_size, w=width/2, txt=proffesion, align="L", ln=True) # type: ignore
            pdf.ln(pdf.font_size*3)

        # Seperator
        y = pdf.get_y()
        pdf.set_draw_color(*self.title_page_seperator_color)
        pdf.line(width/2+pdf.font_size, y, width-pdf.r_margin, y) # type: ignore

        # Footer
        pdf.set_font("times-new-roman", "B", 12)
        pdf.set_y(-pdf.font_size*2-pdf.b_margin) # type: ignore
        pdf.cell(0, txt=self.title_page_footer, align="C")

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
            pdf.pop_section()
        pdf.pop_section()

class ReportS1Generator(ReportGenerator):
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
