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
from ..report import Report
from . import SectionGenerator
from ..pdf import PDF

class ClassDiagramSection(SectionGenerator):
    diagram_font_file: str = "fonts/arial.ttf"
    diagram_font_size: int = 32

    def __init__(self,
            field: str,
            included_files: list[str],
            excluded_files: list[str]=[],
        ) -> None:
        super().__init__()
        self.field = field
        self.included_files = included_files
        self.excluded_files = excluded_files

    def generate(self, pdf: PDF, section: dict, report: Report):
        pass
        # pdf.set_font("times-new-roman", 12)
        # pdf.write_markdown(section[self.field])
        # pdf.newline()

    def has_required_fields(self, section: dict, report: Report) -> bool:
        return False
        # return self.field in section

    def assert_fields(self, section: dict, report: Report):
        pass
        # assert type(section.get(self.field)) == str, f"Expected field '{self.field}' in section to be str"
