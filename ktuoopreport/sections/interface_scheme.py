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
from os.path import exists

class InterfaceSchemeSection(SectionGenerator):
    numbering_label: str = "{index} pav. \"{title}\" sąsajos schema"

    def __init__(self, field: str):
        super().__init__()
        self.field = field

    def generate(self, pdf: PDF, section: dict, report: Report):
        pdf.set_font("times-new-roman", 12)
        with pdf.unbreakable() as pdf: # type: ignore
            pdf.newline()
            pdf.image(section[self.field])
            pdf.add_numbering(self.numbering_label.format(index="{index}", title=section["title"]))
            pdf.newline()

    def has_required_fields(self, section: dict, report: Report) -> bool:
        return self.field in section

    def assert_fields(self, section: dict, _: Report):
        assert type(section.get(self.field)) == str, f"Expected field '{self.field}' in section to be str"
        assert exists(section[self.field]), f"Image '{self.field}' not found"
