from math import ceil
from dataclasses import dataclass
from typing import OrderedDict
from fpdf.fpdf import TitleStyle, ToCPlaceholder
from fpdf.outline import OutlineSection
import os
import os.path as path
import subprocess
import contextlib
import stat
from glob import glob
from shutil import copytree, rmtree
from PIL import Image, ImageFont, ImageDraw

from .report import Report, ReportSection, Gender, ReportProject
from .pdf import PDF

@contextlib.contextmanager
def pushd(new_dir):
    previous_dir = os.getcwd()
    os.chdir(new_dir)
    yield
    os.chdir(previous_dir)

@dataclass
class PDFGeneratorStyle:
    toc_max_level: int = 1

    # Default to Visual Studio theme
    syntax_highlighting_theme: str = "vs"

    console_bg: str = "#000000"
    console_fg: str = "#FFFFFF"
    console_font_file: str = "fonts/consolas.ttf"
    console_font_size: int = 24
    console_horizontal_padding: int = 30
    console_vertical_padding: int = 30

class PDFGenerator(PDF):
    report: Report
    style: PDFGeneratorStyle
    university_icon = "university-icon.png"

    toc_section_spacing_above = 0.21
    toc_section_spacing_below = 0.35

    def __init__(self, report: Report, style: PDFGeneratorStyle = PDFGeneratorStyle()) -> None:
        super().__init__("portrait", "cm", "A4")
        self.report = report
        self.style = style

        self.add_font("times-new-roman", "", "fonts/times-new-roman.ttf", True)
        self.add_font("times-new-roman", "B", "fonts/times-new-roman-bold.ttf", True)
        self.add_font("courier-new", "", "fonts/courier-new.ttf", True)
        self.add_font("courier-new", "B", "fonts/courier-new-bold.ttf", True)
        self.add_font("courier-new", "I", "fonts/courier-new-italic.ttf", True)
        self.add_font("courier-new", "BI", "fonts/courier-new-bold-italic.ttf", True)
        self.add_font("consolas", "", "fonts/consolas.ttf", True)
        self.add_font("consolas", "B", "fonts/consolas-bold.ttf", True)
        self.add_font("consolas", "I", "fonts/consolas-italic.ttf", True)
        self.add_font("consolas", "BI", "fonts/consolas-bold-italic.ttf", True)
        self.add_font("arial", "", "fonts/arial.ttf", True)
        self.add_font("arial", "B", "fonts/arial-bold.ttf", True)

        self.set_margins(2.5, 1, 1)
        self.set_auto_page_break(True, 1.5)

        self.set_section_title_styles(
            level0 = TitleStyle("arial", "B", 14, l_margin=self.l_margin+1.5, t_margin=0, b_margin=0.35),
            level1 = TitleStyle("arial", "B", 12, l_margin=self.l_margin+2.5, t_margin=0.15, b_margin=0.35),
            level2 = TitleStyle("arial", "B", 12, l_margin=self.l_margin+3.5, t_margin=0.25, b_margin=0.35),
        )

        self.add_title_page()
        self.add_toc_page()
        for i in range(len(report.sections)):
            self.add_section(i)

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

    def add_section(self, index: int) -> None:
        section = self.report.sections[index]
        project = section.project
        index += 1
        self.add_page()
        self.start_section(f"{index}. {section.title}")

        self.start_section(f"{index}.1. Darbo užduotis", 1)
        if section.problem:
            self.set_font("times-new-roman", "", 12)
            self.write_basic_markdown(section.problem)
            self.ln()

        # TODO: order files by importance
        self.start_section(f"{index}.2. Programos tekstas", 1)
        if isinstance(project, ReportProject):
            self.render_csharp_files(project.program_files, project.location)

        self.start_section(f"{index}.3. Pradiniai duomenys ir rezultatai", 1)
        if isinstance(project, ReportProject) and len(project.test_folders) > 0:
            if self.compile_project(project.location):
                executable = self.find_project_executable(project.location)
                os.chmod(executable, stat.S_IEXEC | stat.S_IREAD | stat.S_IWRITE)
                for i in range(len(project.test_folders)):
                    self.start_section(f"{index}.3.{i+1}. {i+1} Testas", 2)
                    self.render_test(executable, project.test_folders[i])

        self.start_section(f"{index}.4. Dėstytojo pastabos", 1)
        if section.professors_notes:
            self.set_font("times-new-roman", "", 12)
            self.write_basic_markdown(section.professors_notes)

    @staticmethod
    def compile_project(location: str) -> bool:
        with pushd(location):
            process = subprocess.run(["dotnet", "build"], shell=False)
            return process.returncode == 0

    @staticmethod
    def find_project_executable(project_location: str) -> str:
        return glob(path.join(project_location, "bin/Debug/**/*.dll"))[0]

    @staticmethod
    def clear_all_except(target_location: str, target_file: str):
        for item in glob(path.join(target_location, "*")):
            if not path.samefile(item, target_file):
                if path.isfile(item):
                    os.remove(item)
                elif path.isdir(item):
                    rmtree(item)

    def create_console_image(self, text: str):
        font_file = path.realpath(self.style.console_font_file)
        font_size = self.style.console_font_size
        font = ImageFont.truetype(font_file, font_size)
        w, h = font.getsize_multiline(text)

        h_padding = self.style.console_horizontal_padding
        v_padding = self.style.console_vertical_padding
        bg = self.hex_to_rgb(self.style.console_bg)
        fg = self.hex_to_rgb(self.style.console_fg)
        image = Image.new("RGB", (w+h_padding, h+v_padding), bg)
        draw = ImageDraw.Draw(image)
        draw.text((h_padding/2, v_padding/2), text, fill=fg, font=font)

        return image

    # Will always output created files from the program after input files
    def render_test(self, executable: str, test_folder: str):
        executable_dir = path.dirname(executable)
        self.clear_all_except(executable_dir, executable)

        # copy current test files
        copytree(test_folder, executable_dir, dirs_exist_ok=True)

        # Used for storing which files will need to be shown
        # Files created by the test will always be after the input files
        used_testing_files = OrderedDict()

        # Record which files are inputs
        for root, _, files in os.walk(test_folder, topdown=True):
            for file in files:
                relpath = path.join(root, file)
                used_testing_files[relpath] = None

        # Run program
        process = None
        command = "./"+path.basename(executable)
        with pushd(executable_dir):
            process = subprocess.run([command], shell=False, capture_output=True)

        # Record which files are outputs
        for root, _, files in os.walk(test_folder, topdown=True):
            for file in files:
                relpath = path.join(root, file)
                used_testing_files[relpath] = None

        # Render used test files
        theme = self.style.syntax_highlighting_theme
        for file in used_testing_files.keys():
            # Ignore executable
            if path.samefile(file, executable): continue

            relpath = path.relpath(file, test_folder)
            self.render_file(file, f"{relpath}:", theme, "c#")

        with self.render_labaled("Konsolė:", "times-new-roman", "", 12):
            console_output = process.stdout.decode("UTF-8").strip()
            console_image = self.create_console_image(console_output)
            self.image(console_image, w=self.epw)

    def render_csharp_files(self, files: list[str], root_path: str):
        for filename in files:
            label = f"{path.relpath(filename, root_path)}:"
            self.render_file(filename, label, self.style.syntax_highlighting_theme, "c#")

    @contextlib.contextmanager
    def render_labaled(self, label: str, label_family: str = None, label_style: str = None, label_size: int = None):
        self.ln()
        self.set_font(label_family, label_style, label_size)
        self.cell(txt=label, ln=True)
        self.ln()
        yield
        self.ln()

    def render_file(self, filename: str, label: str, style_name: str, language: str = None):
        syntax_highlighting = (language or filename, style_name)

        with self.render_labaled(label, "times-new-roman", "", 12):
            self.set_font("courier-new", "", 10)
            with open(filename, "r", encoding='utf-8-sig') as f:
                contents = f.read().strip()
                self.write(txt=contents, syntax_highlighting=syntax_highlighting)

    def add_toc_page(self):
        toc_height = self.get_effective_toc_height(self.report.sections)
        # Adjust for title that is at the top of the page
        eph = self.eph - (0.5 + 12/self.k)
        toc_height += 12/self.k

        pages = max(1, ceil(toc_height / eph))
        self.insert_toc_placeholder(self.render_toc, pages)

        # Adjust starting page, because it's a bug
        # When the function creates a new placeholder page, it should start with
        # it, not the one before it.
        placeholder = self._toc_placeholder
        self._toc_placeholder = ToCPlaceholder(
            placeholder.render_function, placeholder.start_page+1, placeholder.y, placeholder.pages
        )

    # TODO: render_toc could use some refactoring
    def render_toc(self, pdf: PDF, outline: list[OutlineSection]) -> None:
        page_top_y = pdf.t_margin + 0.5 + 12/pdf.k
        pdf.set_y(page_top_y)
        pdf.set_font("times-new-roman", "", 12)
        pdf.cell(0, txt="TURINYS", align="C", ln=True)
        pdf.ln()

        y = pdf.get_y()
        for i in range(len(outline)):
            outlineSection = outline[i]
            level = int(outlineSection.level)

            # Only render up to the specified number of levels levels
            if level > self.style.toc_max_level: continue

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
        txt = outlineSection.name

        pdf.text(x, y, txt)

        txt_width = self.get_string_width(txt, True)
        page_width = self.get_page_width()
        left_over_space = page_width - x - self.r_margin - txt_width
        page_number_width = self.get_string_width(str(outlineSection.page_number))
        dot_width = self.get_string_width('.')
        needed_dots = round((left_over_space - page_number_width)/dot_width - 0.1)
        page_number_txt = "." * needed_dots + str(outlineSection.page_number)

        pdf.text(
            page_width-self.get_string_width(page_number_txt)-self.r_margin,
            y,
            txt=page_number_txt
        )

    # Used for determining how many pages should be inserted in placeholder
    def get_effective_toc_height(self, sections: list[ReportSection]) -> float:
        section_text_height = 14/self.k
        subsection_text_height = 12/self.k
        margins = self.toc_section_spacing_above + self.toc_section_spacing_below
        height = 0

        for section in sections:
            height += section_text_height + margins
            height += 4 * (subsection_text_height + margins)

            # If each test will be shown in toc, it will need more space
            if isinstance(section.project, ReportProject) and self.style.toc_max_level > 1:
                height += len(section.project.test_folders) * (subsection_text_height + margins)

        return height

    def render_page_number(self) -> None:
        self.set_font("times-new-roman", "", 12)
        self.set_y(-self.font_size-self.b_margin)
        self.cell(0, txt=str(self.page_no()), align="R")

    def footer(self) -> None:
        if self.page_no() > 1:
            self.render_page_number()


