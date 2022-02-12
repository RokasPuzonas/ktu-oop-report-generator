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
from . import SectionGenerator
from ..pdf import PDF
from ..report import Report
from .. import dotnet
from os import path
import os
from tempfile import TemporaryDirectory
from PIL import Image, ImageFont, ImageDraw

def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    r, g, b = tuple(int(value[i:i+2], 16) for i in (0, 2, 4))
    return (r, g, b)

class ProjectTestsSection(SectionGenerator):
    test_label: str = "{level} {test_name} Testas"
    file_label: str = "{filename}:"
    console_label: str = "Konsolės išvestis:"
    console_numbering_label: str = "{index} pav. Konsolės išvestis"

    builld_arguments: list[str] = ["--no-dependencies", "--nologo", "/nowarn:netsdk1138"]

    console_font_file: str = "fonts/consolas.ttf"
    console_background: str = "#000000"
    console_foreground: str = "#FFFFFF"
    console_font_size: int = 24
    console_left_padding: int = 10
    console_right_padding: int = 10
    console_top_padding: int = 10
    console_bottom_padding: int = 10

    def __init__(self, field: str, tests_folder: str = "tests") -> None:
        super().__init__()
        self.field = field
        self.tests_folder = tests_folder

    def generate(self, pdf: PDF, section: dict, report: Report):
        project_path = section[self.field]
        tests_folder = path.join(project_path, self.tests_folder)

        # If project dosen't have any tests, do nothing
        if not (tests_folder and ProjectTestsSection.has_subfolders(tests_folder)):
            return

        # Build project
        build_directory = TemporaryDirectory()
        executable = dotnet.build_project(project_path, build_directory.name, self.builld_arguments)
        assert executable != None, "Failed to build project"

        # Get folders in which there are test cases
        tests = ProjectTestsSection.list_subfolders(tests_folder)
        tests.sort()

        # Run each test-case one by one
        for i in range(len(tests)):
            test_folder = tests[i]
            test_name = path.relpath(test_folder, tests_folder)
            with pdf.section_block(self.test_label, test_index = i + 1, test_name = test_name):
                self.render_test(pdf, executable, test_folder)

        # Cleanup build files
        build_directory.cleanup()

    def render_test(self, pdf: PDF, executable: str, test_folder: str):
        """
        Render test case to the page
        """
        assert os.access(executable, os.X_OK), "Excpected to be able to run executable, insufficient permissions"
        assert path.isdir(test_folder), "Failed to verify that given test folder is a folder"

        # Run program
        errcode, stdout = dotnet.run_test(executable, test_folder)

        working_directory = path.dirname(executable)

        # Collect and sort used test files by creation time
        files_to_render = dotnet.list_test_files(executable)
        files_to_render.sort(key=lambda file: os.stat(file).st_ctime)

        for file in files_to_render:
            relpath = path.relpath(file, working_directory)
            content = None
            with open(file, "r", encoding="utf-8-sig") as f:
                content = f.read().strip()
            with pdf.unbreakable() as pdf: # type: ignore
                self.print_file(pdf, content, self.file_label.format(filename=relpath))

        # Render console output
        console_output = stdout.strip()
        if len(console_output) > 0:
            console_image = self.create_console_image(console_output)

            pdf.set_font("times-new-roman", 12)
            with pdf.unbreakable() as pdf: # type: ignore
                pdf.print(self.console_label)
                pdf.newline()
                pdf.image(console_image, w=pdf.epw)
                pdf.add_numbering(self.console_numbering_label)
                pdf.newline()

    def print_file(self, pdf: PDF, text: str, filename: str):
        pdf.set_font("times-new-roman", 12)
        with pdf.labeled_block(self.file_label.format(filename=filename)):
            pdf.set_font("courier-new", 10)
            pdf.print(text, multiline=True)

    def create_console_image(self, text: str):
        """
        Render text to image
        """
        font = ImageFont.truetype(self.console_font_file, self.console_font_size)
        w, h = font.getsize_multiline(text)

        bg = hex_to_rgb(self.console_background)
        fg = hex_to_rgb(self.console_foreground)

        lp = self.console_left_padding
        rp = self.console_right_padding
        tp = self.console_top_padding
        bp = self.console_bottom_padding
        image = Image.new("RGB", (w + lp + rp, h + tp + bp), bg)
        draw = ImageDraw.Draw(image)
        draw.text((lp, tp), text, fill=fg, font=font)

        return image

    def has_required_fields(self, section: dict, _: Report) -> bool:
        return self.field in section

    def assert_fields(self, section: dict, _: Report):
        project_path = section[self.field]
        assert dotnet.is_project_root(project_path), "Expected to receive path of root project folder"

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
