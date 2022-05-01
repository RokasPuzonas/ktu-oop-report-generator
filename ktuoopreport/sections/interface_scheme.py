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
        assert exists(section[self.field]), f"Image '{section[self.field]}' not found"
