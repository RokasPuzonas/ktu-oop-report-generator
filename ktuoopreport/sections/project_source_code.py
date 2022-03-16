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
from ..utils import list_files
from ..report import Report
from . import SectionGenerator
from ..pdf import PDF
import os.path as path

from .. import dotnet

class ProjectSourceCodeSection(SectionGenerator):
    file_label: str = "{filename}:"
    theme: str = "vs"

    def __init__(self,
            field: str,
            included_files: list[str],
            excluded_files: list[str]=[],
            sort_files=None
        ) -> None:
        super().__init__()
        self.field = field
        self.included_files = included_files
        self.excluded_files = excluded_files
        self.sort_files = sort_files

    def print_colored_file(self, pdf: PDF, filename: str, text: str):
        pdf.set_font("times-new-roman", 12)
        with pdf.labeled_block(self.file_label.format(filename=filename)):
            pdf.set_font("courier-new", 10)
            pdf.write_syntax_highlighted(text, self.theme, filename)

    def generate(self, pdf: PDF, section: dict, report: Report):
        project_path = section[self.field]
        project_files = list(list_files(project_path, self.included_files, self.excluded_files))
        if self.sort_files:
            project_files = self.sort_files(project_files)

        for filename in project_files:
            text = None
            with open(filename, "r", encoding="utf-8-sig") as f:
                text = f.read().strip().replace("\t", "    ")

            relpath = path.relpath(filename, project_path)
            self.print_colored_file(pdf, relpath, text)

    def has_required_fields(self, section: dict, _: Report) -> bool:
        return self.field in section

    def assert_fields(self, section: dict, _: Report):
        project_path = section[self.field]
        assert dotnet.is_project_root(project_path), "Expected to receive path of root project folder"
