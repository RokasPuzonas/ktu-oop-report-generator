"""
    Copyright (C) 2021 - Rokas Puzonas <rokas.puz@gmail.com>

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

from math import ceil
from typing import Optional
from fpdf.fpdf import TitleStyle, ToCPlaceholder
from fpdf.outline import OutlineSection
import os
import os.path as path
import subprocess
from subprocess import PIPE
import contextlib
import stat
import sys
from glob import glob
from shutil import copytree, rmtree
from PIL import Image, ImageFont, ImageDraw
from datetime import date
from tempfile import TemporaryDirectory
import re
import time

import fcntl

from .report import Report, ReportSection, Gender, ReportProject
from .pdf import PDF

@contextlib.contextmanager
def pushd(new_dir):
    previous_dir = os.getcwd()
    os.chdir(new_dir)
    yield
    os.chdir(previous_dir)

current_year = date.today().year

class ProjectNotFoundError(FileNotFoundError):
    """
    Given was not pointing to a valid C# project
    """
    pass

# Sort by 2 keys: csharp file type, character count
# 1. A register class is more important than an enum
# 2. A longer file is probably more important also
def key_by_importance(_, filename: str) -> tuple[int, int]:
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

class ReportPDF(PDF):
    report: Report

    title_label: str = "{level} {title}"
    problem_label: str = "{level} Darbo užduotis"
    project_label: str = "{level} Programos tekstas"
    tests_label: str = "{level} Pradiniai duomenys ir rezultatai"
    test_label: str = "{level} {test_name} Testas"
    lecturers_comment_label: str = "{level} Dėstytojo pastabos"
    file_label: str = "{filename}:"
    console_label: str = "Konsolės išvestis:"
    image_numbering_label = "{index} pav. Konsolės išvestis"

    console_font_file: str = "fonts/consolas.ttf"
    console_background: str = "#000000"
    console_foreground: str = "#FFFFFF"
    console_font_size: int = 24
    console_left_padding: int = 10
    console_right_padding: int = 10
    console_top_padding: int = 10
    console_bottom_padding: int = 10

    builld_arguments: list[str] = ["--no-dependencies", "--nologo", "/nowarn:netsdk1138"]

    project_files_sort = key_by_importance

    syntax_highlighting_theme: str = "vs"

    max_toc_level: int = 1
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

    def __init__(self, report: Report = None) -> None:
        super().__init__("portrait", "cm", "A4")
        self.total_sections = 0

        self.add_font("times-new-roman", "", "fonts/times-new-roman.ttf", True)
        self.add_font("times-new-roman", "B", "fonts/times-new-roman-bold.ttf", True)
        self.add_font("times-new-roman", "I", "fonts/times-new-roman-italic.ttf", True)
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
            level0 = TitleStyle("arial", "B", 14, l_margin=self.l_margin+1.5, t_margin=0, b_margin=0.35), # type: ignore
            level1 = TitleStyle("arial", "B", 12, l_margin=self.l_margin+2.5, t_margin=0.15, b_margin=0.35), # type: ignore
            level2 = TitleStyle("arial", "B", 12, l_margin=self.l_margin+3.5, t_margin=0.25, b_margin=0.35), # type: ignore
        )

        if report != None:
            self.add_title_page(report)
            self.add_toc_page(report)
            for section in report.sections:
                project_root = None
                if section.project:
                    project_root = self.determine_project_root(section.project)
                    if not project_root:
                        raise ProjectNotFoundError(f"Could not determine project root from '{section.project}'")

                tests_folder = None
                if report.tests_folder and project_root:
                    tests_folder = path.join(project_root, report.tests_folder)

                self.add_section(
                        title = section.title,
                        problem = section.problem,
                        project_root = project_root,
                        tests_folder = tests_folder
                    )

    @staticmethod
    def generate(report: Report, output: str):
        """
        Convenience method for generating a PDF based on a report and saving it
        """
        ReportPDF(report).output(output)

    @staticmethod
    def _get_people_from_report(report: Report) -> list[tuple[str, str]]:
        people = []
        if report.student.gender == Gender.MALE:
            people.append((report.student.name, "Studentas"))
        else:
            people.append((report.student.name, "Studentė"))

        if report.lecturer.gender == Gender.MALE:
            people.append((report.lecturer.name, "Dėstytojas"))
        else:
            people.append((report.lecturer.name, "Dėstytoja"))
        return people

    def add_title_page(self, report: Report) -> None:
        """
        Add title page by getting needed information from a report
        """
        self.add_page()

        # Top part
        self.set_y(self.t_margin + 0.5 + 12/self.k)
        if self.university_icon:
            self.image(self.university_icon, w=1.78, h=2.04, centered=True)
        else:
            self.ln(2.04)

        self.set_font("times-new-roman", "B", 12)
        if self.university_name:
            self.cell(0, self.font_size*1.5, txt=self.university_name, align="C", ln=True) # type: ignore
        else:
            self.ln(self.font_size*1.5) # type: ignore

        self.set_font("times-new-roman", "", 12)
        if self.faculty_name:
            self.cell(0, txt=self.faculty_name, align="C", ln=True)
        else:
            self.ln(self.font_size)

        # Middle part (title)
        self.ln(self.font_size*15)

        self.set_font("times-new-roman", "B", 18)
        self.cell(0, txt=report.title, align="C", ln=True)
        
        self.set_font("times-new-roman", "", 14)
        if self.sub_title:
            self.cell(0, txt=self.sub_title, align="C", ln=True)
        else:
            self.ln(self.font_size)

        # Student name and professort name section
        self.ln(self.font_size*4)

        width = self.get_page_width()

        # Seperator
        y = self.get_y()
        self.set_draw_color(*self.title_page_seperator_color)
        self.line(width/2+self.font_size, y, width-self.r_margin, y) # type: ignore
        self.ln(self.font_size*2)

        people = self._get_people_from_report(report)
        for i in range(len(people)):
            name, proffesion = people[i]

            self.set_font("times-new-roman", "B", 12)
            self.cell(x=width/2 + self.font_size, w=width/2, txt=name, align="L", ln=True) # type: ignore
            self.ln(self.font_size)

            self.set_font("times-new-roman", "", 12)
            self.cell(x=width/2 + self.font_size, w=width/2, txt=proffesion, align="L", ln=True) # type: ignore
            self.ln(self.font_size*3)

        # Seperator
        y = self.get_y()
        self.set_draw_color(*self.title_page_seperator_color)
        self.line(width/2+self.font_size, y, width-self.r_margin, y) # type: ignore

        # Footer
        self.set_font("times-new-roman", "B", 12)
        self.set_y(-self.font_size*2-self.b_margin) # type: ignore
        self.cell(0, txt=self.title_page_footer, align="C")

    @staticmethod
    def determine_project_root(project: str) -> Optional[str]:
        """
        Extract project root folder. If given path points to a .csproj file, return the directory it's in.
        """
        if path.isfile(project) and project.endswith(".csproj"):
            return path.dirname(project)
        elif path.isdir(project) and len(glob(path.join(project, "*.csproj"))) > 0:
            return project

    @staticmethod
    def is_project_root(project_root: str) -> bool:
        """
        Returns true if given directory contains a .csproj file
        """
        return path.isdir(project_root) and len(glob(path.join(project_root, "*.csproj"))) > 0
    
    @staticmethod
    def list_project_files(project_root: str) -> list[str]:
        """
        Retrieve a list of source code files from given C# project root directory.
        """
        assert ReportPDF.is_project_root(project_root), "Expected to receive path of root project folder"
        files = []

        # Collect all files
        for filename in glob(f"{project_root}/**/*.cs", recursive=True):
            relpath = filename[len(project_root)+1:]
            if not relpath.startswith("obj") and not relpath.startswith("bin"):
                files.append(filename)

        return files

    @contextlib.contextmanager
    def render_labeled(
            self,
            label: str,
            label_family: str = None,
            label_style: str = None,
            label_size: int = None
        ):
        """
        Render label above block
        """
        self.set_font(label_family, label_style, label_size)
        self.cell(txt=label, ln=True)
        self.ln()
        yield
        self.ln()

    def render_file(
            self,
            content: str,
            label: str,
            style_name: Optional[str] = None,
            language: Optional[str] = None
        ):
        """
        Render a file's contents to the page, with optional syntax highlighting
        """
        with self.render_labeled(label, "times-new-roman", "", 12):
            self.set_font("courier-new", "", 10)
            self.write(txt=content, language=language, style_name=style_name)
            self.ln()

    def render_project_files(self, project_root: str):
        """
        Render source code files from C# project given it's root directory.
        """
        assert ReportPDF.is_project_root(project_root), "Expected to receive path of root project folder"

        project_files = self.list_project_files(project_root)
        project_files.sort(key=self.project_files_sort)
        for filename in project_files:
            content = None
            with open(filename, "r", encoding="utf-8-sig") as f:
                content = f.read().strip()

            relpath = path.relpath(filename, project_root)
            self.render_file(
                    content,
                    self.file_label.format(filename=relpath),
                    self.syntax_highlighting_theme,
                    "csharp"
                )

    @staticmethod
    def find_executable(directory: str) -> Optional[str]:
        """
        Find file which is executable in directory. Or try guess which file should
        be the executable by .dll ending.
        """
        # Try searching for a file which is marked as executable
        for filename in glob(path.join(directory, "*")):
            if os.access(filename, os.X_OK):
                return filename

        # If this is some older .NET version if it isin't marked, find .dll file
        # And mark it as executable
        possible_executables = glob(path.join(directory, "*.dll"))
        if len(possible_executables) > 0:
            executable = possible_executables[0]
            os.chmod(executable, stat.S_IEXEC | stat.S_IREAD | stat.S_IWRITE)
            return executable

    @staticmethod
    def remove_all_except(directory: str, ignored_file: str):
        """
        Clear all files, except specifies one
        """
        for item in glob(path.join(directory, "*")):
            if not path.samefile(item, ignored_file):
                if path.isfile(item):
                    os.remove(item)
                elif path.isdir(item):
                    rmtree(item)
    
    def build_project(self, project_root: str, output_directory: str) -> Optional[str]:
        """
        Build C# project using dotnet cli and output it to given directory
        """
        cmd = ["dotnet", "build", project_root, "-o", output_directory, *self.builld_arguments]
        process = subprocess.run(cmd, shell=False)

        # If failed to compile
        if process.returncode != 0:
            print(process.stderr)
            return None

        executable = ReportPDF.find_executable(output_directory)
        if not executable:
            return None

        return executable

    @staticmethod
    def has_subfolders(directory: str) -> bool:
        """
        Return true, if given folder has subfolders
        """
        if path.isdir(directory):
            for item in os.listdir(directory):
                if path.isdir(path.join(directory, item)):
                    return True
        return False

    @staticmethod
    def list_subfolders(directory: str) -> list[str]:
        """
        Returns a list of the immidiate sub folders in directory
        """
        subfolders = []
        for item in os.listdir(directory):
            full_path = path.join(directory, item)
            if path.isdir(full_path):
                subfolders.append(full_path)
        return subfolders

    def render_tests(self, executable: str, tests_folder: str):
        """
        Render test cases to the page
        """
        assert ReportPDF.has_subfolders(tests_folder), "Expected tests folder, to have subfolders"
        assert os.access(executable, os.X_OK), "Excpected to be able to run executable, insufficient permissions"

        test_folders = ReportPDF.list_subfolders(tests_folder)
        test_folders.sort()
        for i in range(len(test_folders)):
            test_folder = test_folders[i]
            test_name = path.relpath(test_folder, tests_folder)
            with self.section_block(self.test_label, test_index = i + 1, test_name = test_name):
                self.render_test(executable, test_folder)

    def create_console_image(self, text: str):
        """
        Render text to image
        """
        font = ImageFont.truetype(self.console_font_file, self.console_font_size)
        w, h = font.getsize_multiline(text)

        bg = self.hex_to_rgb(self.console_background)
        fg = self.hex_to_rgb(self.console_foreground)

        lp = self.console_left_padding
        rp = self.console_right_padding
        tp = self.console_top_padding
        bp = self.console_bottom_padding
        image = Image.new("RGB", (w + lp + rp, h + tp + bp), bg)
        draw = ImageDraw.Draw(image)
        draw.text((lp, tp), text, fill=fg, font=font)

        return image

    @staticmethod
    def run_test(executable: str, test_folder: str):
        assert os.access(executable, os.X_OK), "Excpected to be able to run executable, insufficient permissions"
        assert path.isdir(test_folder), "Failed to verify that given test folder is a folder"

        working_directory = path.dirname(executable)

        # Remove unnecessary files generated by cli
        ReportPDF.remove_all_except(working_directory, executable)

        # copy current test files
        copytree(test_folder, working_directory, dirs_exist_ok=True)

        # Check if stdin is given
        stdin_lines = []
        stdin_file = path.join(working_directory, "stdin.txt")
        if path.isfile(stdin_file):
            with open(stdin_file, "r") as f:
                stdin_lines = f.read().strip().splitlines()
            os.remove(stdin_file)

        # Run program
        # TODO: Add better error handling when executable crashes
        with pushd(working_directory):
            proc = subprocess.Popen(["./"+path.basename(executable)], bufsize=0, shell=False, universal_newlines=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)

            # TODO: Refactor it's cross-platform.
            # This so it dosen't use the fcntl library, because it's posix only.
            # Available options to consider: threads, pexpect library.
            if proc.stdout:
                fcntl.fcntl(proc.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)

            # TODO: Refactor reading of stdout so it's not relying on timings
            # from time.sleep(0.1), because if the calculations of the executable
            # take a long time this system will break.
            stdout = ""
            if proc.stdin:
                for line in stdin_lines:
                    if proc.poll() is not None:
                        break

                    time.sleep(0.1)
                    if proc.stdout:
                        try:
                            stdout += proc.stdout.read()
                        except IOError:
                            pass
                    proc.stdin.write(line + "\n")
                    proc.stdin.flush()
                    stdout += line + "\n"

            proc.wait()
            if proc.stdout:
                try:
                    stdout += proc.stdout.read()
                except IOError:
                    pass

            return proc.returncode, stdout

    def render_test(self, executable: str, test_folder: str):
        """
        Render test case to the page
        """
        assert os.access(executable, os.X_OK), "Excpected to be able to run executable, insufficient permissions"
        assert path.isdir(test_folder), "Failed to verify that given test folder is a folder"

        # Run program
        errcode, stdout = ReportPDF.run_test(executable, test_folder)

        working_directory = path.dirname(executable)

        # Collect used test files
        files_to_render = []
        for root, _, files in os.walk(working_directory, topdown=True):
            for file in files:
                fullpath = path.join(root, file)
                if not path.samefile(fullpath, executable):
                    files_to_render.append(fullpath)

        # Sort by creation time
        files_to_render.sort(key=lambda file: os.stat(file).st_ctime)

        for file in files_to_render:
            relpath = path.relpath(file, working_directory)
            content = None
            with open(file, "r", encoding="utf-8-sig") as f:
                content = f.read().strip()
            self.unbreakable(self.render_file, content, self.file_label.format(filename=relpath))
        
        # Render console output
        console_output = stdout.strip()
        if len(console_output) > 0:
            console_image = self.create_console_image(console_output)

            # TODO: REFACTOR THIS GARBAGE!!!
            # Use a ContextManager instead
            def render():
                with self.render_labeled(self.console_label, "times-new-roman", "", 12):
                    self.image(console_image, w=self.epw, numbered=self.image_numbering_label)
            self.unbreakable(render)

    def add_section(
            self,
            title: str,
            problem: Optional[str] = None,
            project_root: Optional[str] = None,
            lecturers_comment: Optional[str] = None,
            tests_folder: Optional[str] = None
        ) -> None:
        """
        Render a section from a report to the page. This will render:
        * Problem text
        * Project files
        * Run and render test cases
        * Lecturers notes
        """
        if project_root:
            assert ReportPDF.is_project_root(project_root), "Expected to receive path of root project folder"

        build_directory = None
        executable = None
        if project_root and tests_folder and ReportPDF.has_subfolders(tests_folder):
            build_directory = TemporaryDirectory()
            executable = self.build_project(project_root, build_directory.name)
            assert executable != None, "Failed to build project"

        self.add_page()

        with self.section_block(self.title_label, title=title):
            with self.section_block(self.problem_label):
                if problem:
                    self.set_font("times-new-roman", "", 12)
                    self.write_basic_markdown(problem)
                    self.ln()

            with self.section_block(self.project_label):
                if project_root:
                    self.render_project_files(project_root)

            with self.section_block(self.tests_label):
                if tests_folder and executable:
                    self.render_tests(executable, tests_folder)

            with self.section_block(self.lecturers_comment_label):
                if lecturers_comment:
                    self.set_font("times-new-roman", "", 12)
                    self.write_basic_markdown(lecturers_comment)

        if build_directory:
            build_directory.cleanup()

    def render_page_number(self) -> None:
        """
        Render page number at the bottom of the current page
        """
        self.set_font("times-new-roman", "", 12)
        self.set_y(-self.font_size-self.b_margin) # type: ignore
        self.cell(0, txt=str(self.page_no()), align="R")

    def footer(self) -> None:
        if self.page_no() > 1:
            self.render_page_number()

    def add_toc_page(self, report: Report):
        """
        Add table of contents to page
        """
        toc_height = self.get_effective_toc_height(report.sections)
        # Adjust for title that is at the top of the page
        eph = self.eph - (0.5 + 12/self.k)
        toc_height += 12/self.k

        def render_toc(*vargs):
            self.render_toc(*vargs)

        pages = max(1, ceil(toc_height / eph))
        self.insert_toc_placeholder(render_toc, pages)

        # Adjust starting page, because it's a bug
        # When the function creates a new placeholder page, it should start with
        # it, not the one before it.
        placeholder = self._toc_placeholder
        self._toc_placeholder = ToCPlaceholder(
            placeholder.render_function, placeholder.start_page+1, placeholder.y, placeholder.pages
        )

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

            # Only render up to the specified number of levels levels
            if level > self.max_toc_level: continue

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
        """
        Estimate how much space the table of contents is gonna take up
        """
        section_text_height = 14/self.k
        subsection_text_height = 12/self.k
        margins = self.toc_section_spacing_above + self.toc_section_spacing_below
        height = 0

        for section in sections:
            height += section_text_height + margins
            height += 4 * (subsection_text_height + margins)

            # If each test will be shown in toc, it will need more space
            if isinstance(section.project, ReportProject) and self.max_toc_level > 1:
                height += len(section.project.test_folders) * (subsection_text_height + margins)

        return height

