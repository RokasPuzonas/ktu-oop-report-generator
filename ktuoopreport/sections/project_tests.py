from glob import glob
from typing import Optional, Union

from PIL.Image import Image
from ..console_renderer import render_console
from . import SectionGenerator
from ..pdf import PDF
from ..report import Report
from .. import dotnet
from os import path
import os
from tempfile import TemporaryDirectory

class ProjectTestsSection(SectionGenerator):
    test_label: str = "{level} {test_name} Testas"
    file_label: str = "{filename}:"
    console_label: str = "Konsolės išvestis:"
    console_numbering_label: str = "{index} pav. Konsolės išvestis"

    image_numbering_label: str = "{index} pav. Ekrano vaizdas"

    builld_arguments: list[str] = ["--no-dependencies", "--nologo", "/nowarn:netsdk1138"]

    console_font_file: str = "fonts/consolas.ttf"
    console_font_size: int = 24

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

        tests_screenshots = section.get("tests_screenshots")
        if tests_screenshots:
            for file in tests_screenshots:
                self.display_numbered_image(pdf, file, self.image_numbering_label)

        if dotnet.is_web_project(project_path):
            self.generate_static(pdf, tests_folder)
        else:
            self.generate_dynamic(pdf, project_path, tests_folder)


    def generate_dynamic(self, pdf: PDF, project_path: str, tests_folder: str):
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

    def generate_static(self, pdf: PDF, tests_folder: str):
        # Get folders in which there are test cases
        tests = ProjectTestsSection.list_subfolders(tests_folder)
        tests.sort()

        for i in range(len(tests)):
            test_folder = tests[i]
            test_name = path.relpath(test_folder, tests_folder)
            with pdf.section_block(self.test_label, test_index = i + 1, test_name = test_name):
                input_dir = path.join(test_folder, "inputs")
                self.print_files(pdf, glob(f"{input_dir}/**"), input_dir)

                output_dir = path.join(test_folder, "outputs")
                self.print_files(pdf, glob(f"{output_dir}/**"), output_dir)

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

        self.print_files(pdf, files_to_render, working_directory)

        # Render console output
        console_output = stdout.strip()
        if len(console_output) > 0:
            console_image = render_console(console_output, self.console_font_file, self.console_font_size)

            self.display_numbered_image(pdf, console_image, self.console_numbering_label, self.console_label, full_width = True)

    def display_numbered_image(
            self,
            pdf: PDF,
            image: str|Image,
            numbering_label: str,
            label: Optional[str] = None,
            full_width: bool = False,
        ):
        pdf.set_font("times-new-roman", 12)
        with pdf.unbreakable() as pdf: # type: ignore
            if label:
                pdf.print(label)
                pdf.newline()
            if full_width:
                pdf.image(image, w=pdf.epw)
            else:
                pdf.image(image)
            pdf.add_numbering(numbering_label)
            pdf.newline()

    def print_files(self, pdf: PDF, files: list[str], root_dir: str):
        image_files = []

        for file in files:
            lower_file = file.lower()
            if lower_file.endswith(".png") or lower_file.endswith(".jpg") or lower_file.endswith(".jpeg"):
                image_files.append(file)
                continue

            relpath = path.relpath(file, root_dir)
            content = None
            with open(file, "r", encoding="utf-8-sig") as f:
                content = f.read().strip()
            self.print_file(pdf, content, relpath)

        for file in image_files:
            self.display_numbered_image(pdf, file, self.image_numbering_label)

    def print_file(self, pdf: PDF, text: str, filename: str):
        pdf.set_font("times-new-roman", 12)
        with pdf.labeled_block(self.file_label.format(filename=filename)):
            pdf.set_font("courier-new", 10)
            pdf.print(text, multiline=True)

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
